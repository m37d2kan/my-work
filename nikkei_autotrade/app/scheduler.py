import asyncio
import logging
import queue
from datetime import datetime, timezone, timedelta

from app.config import settings
from app.runtime import runtime_state
from app.market.market_models import Tick
from app.market.candle_builder import CandleBuilder
from app.strategy.pb_logic import update_pb1
from app.strategy.swing_logic import update_swing1_confirmed
from app.strategy.realtime_logic import update_realtime_levels
from app.strategy.planner import evaluate_and_plan
from app.db import save_candle

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

# スレッド間通信用キュー
_tick_queue: queue.Queue[Tick] = queue.Queue(maxsize=1000)


class StrategyRunner:
    def __init__(self, order_manager, protective_manager):
        self.order_manager = order_manager
        self.protective_manager = protective_manager
        self.builder = CandleBuilder(settings.bar_seconds)
        self.bar_index = 0
        self.broker = order_manager.broker

    async def on_tick(self, tick: Tick):
        """ティック受信ごとに呼ばれる。"""
        runtime_state.current_price = tick.price

        result = self.builder.update(tick.ts, tick.price, tick.volume)

        # リアルタイム更新 (形成中バー)
        update_realtime_levels(
            runtime_state.signal_state,
            current_high=result.current_candle.high,
            current_low=result.current_candle.low,
        )

        # ポジション保有中のチェック
        if runtime_state.order_state.position_side is not None:
            # 建値移動チェック
            await self.protective_manager.check_breakeven(
                current_price=tick.price,
                be_trigger_atr=settings.be_atr_trigger,
            )
            # TP到達チェック（ソフトウェア監視）
            tp_hit = await self.protective_manager.check_tp_level(
                current_price=tick.price,
            )
            if tp_hit:
                pnl = self._calc_pnl(tick.price)
                runtime_state.add_log(
                    "ORDER",
                    f"TP HIT @{tick.price} P&L={pnl:+.0f}",
                )
                self.order_manager.clear_position()

        # 5分足確定
        if result.finished_candle:
            runtime_state.candles_5m.append(result.finished_candle)
            save_candle(result.finished_candle)  # SQLite保存
            self.bar_index += 1
            runtime_state.add_log(
                "BAR",
                f"5m close O={result.finished_candle.open} "
                f"H={result.finished_candle.high} "
                f"L={result.finished_candle.low} "
                f"C={result.finished_candle.close}",
            )
            await self.on_bar_close(result.finished_candle.time)

    async def on_bar_close(self, bar_time):
        """5分足確定時の処理。"""
        candles = runtime_state.candles_5m
        if len(candles) < 2:
            return

        # ギャップ後の再蓄積: 新しい足が十分溜まったら全足リプレイ
        if runtime_state.data_gap_detected and not runtime_state.strategy_ready:
            min_bars_for_ready = max(settings.length1 + 2, 10)  # 最低でもlength1+2本
            gap_bars = self._count_post_gap_bars(candles)
            if gap_bars >= min_bars_for_ready:
                runtime_state.add_log("SYSTEM", f"再蓄積完了: {gap_bars}本 ≥ {min_bars_for_ready}本。全足リプレイ実行")
                # 全足でリプレイ
                from app.strategy.signal_state import SignalState
                runtime_state.signal_state = SignalState()
                for i in range(2, len(candles) + 1):
                    slice_ = candles[:i]
                    update_pb1(runtime_state.signal_state, slice_, settings.length1)
                    update_swing1_confirmed(runtime_state.signal_state, slice_, i, settings.length1)
                runtime_state.strategy_ready = True
                runtime_state.data_gap_detected = False
                runtime_state.add_log("SYSTEM", f"Strategy READY: peak={runtime_state.signal_state.prevPeak1} bot={runtime_state.signal_state.prevBot1}")
            else:
                runtime_state.add_log("SYSTEM", f"再蓄積中: {gap_bars}/{min_bars_for_ready}本")
                return  # まだ戦略判定しない

        state = runtime_state.signal_state

        # P&B1
        update_pb1(state, candles, settings.length1)

        # Swing1 確定処理
        update_swing1_confirmed(state, candles, self.bar_index, settings.length1)

        # 東京時間取得
        now_tokyo = bar_time
        if now_tokyo.tzinfo is None:
            now_tokyo = now_tokyo.replace(tzinfo=JST)

        # 売買判定
        plan = evaluate_and_plan(
            state=state,
            candles=candles,
            now_tokyo=now_tokyo,
            cfg=settings,
            order_state=runtime_state.order_state,
        )
        runtime_state.last_plan = plan

        runtime_state.add_log(
            "PLAN",
            f"buy={plan.buy_setup_active}({plan.buy_stop_price}) "
            f"sell={plan.sell_setup_active}({plan.sell_stop_price}) "
            f"ma_ok={plan.ma_deviation_ok} time_ok={plan.signal_time_ok}",
        )

        # 自動有効なら注文同期
        if settings.auto_enabled:
            await self.order_manager.sync_entry_orders(plan, settings.order_qty)

    def _count_post_gap_bars(self, candles: list) -> int:
        """欠損後に連続している足の数をカウント。
        最新から遡って、5分間隔で連続している足を数える。"""
        if len(candles) < 2:
            return len(candles)
        count = 1
        for i in range(len(candles) - 1, 0, -1):
            diff = (candles[i].time - candles[i - 1].time).total_seconds()
            if diff <= settings.bar_seconds * 1.5:  # 5分の1.5倍以内なら連続
                count += 1
            else:
                break
        return count

    def _calc_pnl(self, exit_price: float) -> float:
        """損益計算（マイクロ5円刻み）。"""
        state = runtime_state.order_state
        if state.entry_price is None:
            return 0.0
        if state.position_side == "BUY":
            return (exit_price - state.entry_price) * state.position_qty
        else:
            return (state.entry_price - exit_price) * state.position_qty


def on_push_message(data: dict):
    """kabuSTATION PUSH 受信コールバック。別スレッドから呼ばれる。
    キューに入れてメインループ側で処理する。"""
    try:
        price = data.get("CurrentPrice")
        if price is None:
            return

        ts_str = data.get("CurrentPriceTime")
        if ts_str:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
        else:
            ts = datetime.now(tz=JST)

        volume = data.get("TradingVolume", 0)
        tick = Tick(ts=ts, price=float(price), volume=float(volume))

        try:
            _tick_queue.put_nowait(tick)
        except queue.Full:
            pass  # キュー満杯時は古いデータを捨てる
    except Exception:
        logger.exception("on_push_message error")


_runner: StrategyRunner | None = None


async def tick_consumer_loop():
    """メインのevent loop上でキューからティックを取り出して処理する。"""
    while True:
        try:
            tick = _tick_queue.get_nowait()
            if _runner:
                await _runner.on_tick(tick)
        except queue.Empty:
            pass
        await asyncio.sleep(0.05)  # 50ms間隔でポーリング


async def fill_monitor_loop():
    """注文の約定を2秒ポーリングで検知する。"""
    while True:
        try:
            if _runner and _runner.broker.token and settings.auto_enabled:
                await _check_fills()
        except Exception:
            logger.exception("fill_monitor error")
        await asyncio.sleep(2)


async def _check_fills():
    """注文一覧から約定を検知して処理する。"""
    state = runtime_state.order_state
    has_entry_order = state.buy_order_id or state.sell_order_id
    has_sl_order = state.sl_order_id and state.position_side

    if not has_entry_order and not has_sl_order:
        return

    orders = await _runner.broker.get_orders()
    if not orders:
        return

    # エントリー逆指値の約定チェック
    for order_id, side_label in [
        (state.buy_order_id, "BUY"),
        (state.sell_order_id, "SELL"),
    ]:
        if not order_id:
            continue
        order = _find_order(orders, order_id)
        if order and _is_filled(order):
            fill_price = _get_fill_price(order)
            if fill_price is None:
                fill_price = float(order.get("Price", 0))

            # ATR取得
            atr_value = None
            if runtime_state.last_plan and runtime_state.last_plan.atr_value:
                atr_value = runtime_state.last_plan.atr_value

            runtime_state.add_log(
                "ORDER",
                f"ENTRY FILLED: {side_label} @{fill_price} ATR={atr_value}",
            )

            # ポジション記録 + エントリー注文クリア
            await _runner.order_manager.on_fill(
                side=side_label,
                price=fill_price,
                qty=settings.order_qty,
                atr_value=atr_value,
            )

            # SLのみ返済逆指値で発注 + TPレベル記録
            await _runner.protective_manager.place_sl_only(
                sl_mult=settings.sl_atr_mult,
                tp_mult=settings.tp_atr_mult,
            )

            runtime_state.add_log(
                "ORDER",
                f"SL={state.sl_price} TP={state.tp_price}(ソフトウェア監視)",
            )
            break  # 1約定ずつ処理

    # SL返済逆指値の約定チェック
    if state.sl_order_id and state.position_side:
        order = _find_order(orders, state.sl_order_id)
        if order and _is_filled(order):
            fill_price = _get_fill_price(order) or state.sl_price
            pnl = 0.0
            if state.entry_price:
                if state.position_side == "BUY":
                    pnl = (fill_price - state.entry_price) * state.position_qty
                else:
                    pnl = (state.entry_price - fill_price) * state.position_qty

            runtime_state.add_log(
                "ORDER",
                f"SL FILLED @{fill_price} P&L={pnl:+.0f}",
            )

            # リスク管理更新
            state.daily_pnl += pnl
            if pnl < 0:
                state.consecutive_losses += 1
            else:
                state.consecutive_losses = 0

            _runner.order_manager.clear_position()

            # 最大損失・連敗チェック
            if state.daily_pnl <= -settings.max_daily_loss:
                state.emergency_stop = True
                runtime_state.add_log("CONTROL", f"MAX DAILY LOSS reached: {state.daily_pnl}")
            if state.consecutive_losses >= settings.max_consecutive_losses:
                state.emergency_stop = True
                runtime_state.add_log("CONTROL", f"MAX CONSECUTIVE LOSSES: {state.consecutive_losses}")


def _find_order(orders: list, order_id: str) -> dict | None:
    """注文一覧からIDで検索。"""
    for o in orders:
        # kabuSTATION: GET /orders は "ID" キー
        oid = o.get("ID") or o.get("OrderId") or ""
        if str(oid) == str(order_id):
            return o
    return None


def _is_filled(order: dict) -> bool:
    """注文が約定済みか判定。"""
    # State==5 (終了) かつ Details に RecType==8 (約定) があれば約定
    state = order.get("State", 0)
    if state != 5:
        return False

    details = order.get("Details", [])
    for d in details:
        if d.get("RecType") == 8:
            return True

    # State==5 で CumQty > 0 のパターンにも対応
    cum_qty = order.get("CumQty", 0)
    if cum_qty and float(cum_qty) > 0:
        return True

    return False


def _get_fill_price(order: dict) -> float | None:
    """約定価格を取得。Details の RecType==8 から取る。"""
    details = order.get("Details", [])
    for d in details:
        if d.get("RecType") == 8:
            price = d.get("Price")
            if price is not None:
                return float(price)
    return None


def set_runner(runner: StrategyRunner):
    global _runner
    _runner = runner
