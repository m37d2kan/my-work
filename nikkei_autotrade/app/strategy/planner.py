from app.config import SMA_MAP
from app.market.market_models import Candle
from app.indicators.ma import sma
from app.indicators.atr import atr_rma
from app.strategy.signal_state import SignalState
from app.strategy.filters import calc_ma_deviation_ok, in_signal_time
from app.strategy.strategy_models import PlanResult
from app.order.order_state import OrderState


def evaluate_and_plan(
    state: SignalState,
    candles: list[Candle],
    now_tokyo,
    cfg,
    order_state: OrderState,
) -> PlanResult:
    """現在環境から買い/売り待機の有無と逆指値価格を算出。"""
    closes = [c.close for c in candles]
    close = closes[-1]

    sma_len = SMA_MAP[cfg.entry_ma_source]
    entry_ma = sma(closes, sma_len)
    atr_value = atr_rma(candles, cfg.atr_period)

    signal_time_ok = in_signal_time(
        now_tokyo,
        cfg.use_signal_time_filter,
        cfg.signal_start_hour,
        cfg.signal_start_min,
        cfg.signal_end_hour,
        cfg.signal_end_min,
    )

    ma_deviation_ok = calc_ma_deviation_ok(
        close=close,
        entry_ma=entry_ma,
        atr_value=atr_value,
        entry_max_dev=cfg.entry_max_dev,
    )

    buy_setup_active = (
        state.modoriTakane1 is not None
        and not state.modoriBroken1
        and order_state.position_side is None
        and signal_time_ok
        and ma_deviation_ok
        and not order_state.emergency_stop
    )

    sell_setup_active = (
        state.oshiYasune1 is not None
        and not state.oshiBroken1
        and order_state.position_side is None
        and signal_time_ok
        and ma_deviation_ok
        and not order_state.emergency_stop
    )

    return PlanResult(
        entry_ma=entry_ma,
        atr_value=atr_value,
        ma_deviation_ok=ma_deviation_ok,
        signal_time_ok=signal_time_ok,
        buy_setup_active=buy_setup_active,
        sell_setup_active=sell_setup_active,
        buy_stop_price=state.modoriTakane1 if buy_setup_active else None,
        sell_stop_price=state.oshiYasune1 if sell_setup_active else None,
    )
