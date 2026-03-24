from fastapi import APIRouter
from app.runtime import runtime_state
from app.config import settings

router = APIRouter()


@router.get("/status")
async def get_status():
    ss = runtime_state.signal_state
    os = runtime_state.order_state
    plan = runtime_state.last_plan

    return {
        "api_connected": runtime_state.api_connected,
        "push_connected": runtime_state.push_connected,
        "auto_enabled": settings.auto_enabled,
        "emergency_stop": os.emergency_stop,
        "current_price": runtime_state.current_price,
        "position_side": os.position_side,
        "position_qty": os.position_qty,
        "entry_price": os.entry_price,
        "sl_price": os.sl_price,
        "tp_price": os.tp_price,
        "tp_is_software": os.tp_order_id is None and os.tp_price is not None,
        "be_moved": os.be_moved,
        "daily_pnl": os.daily_pnl,
        "consecutive_losses": os.consecutive_losses,
        # 戦略情報
        "pbState1": ss.pbState1,
        "oshiYasune1": ss.oshiYasune1,
        "modoriTakane1": ss.modoriTakane1,
        "oshiBroken1": ss.oshiBroken1,
        "modoriBroken1": ss.modoriBroken1,
        "peakFalling1": ss.peakFalling1,
        "botRising1": ss.botRising1,
        "trend_status1": ss.trend_status1_confirmed,
        "prevPeak1": ss.prevPeak1,
        "prevBot1": ss.prevBot1,
        # プラン
        "plan": None if plan is None else {
            "entry_ma": plan.entry_ma,
            "atr_value": plan.atr_value,
            "ma_deviation_ok": plan.ma_deviation_ok,
            "signal_time_ok": plan.signal_time_ok,
            "buy_setup_active": plan.buy_setup_active,
            "sell_setup_active": plan.sell_setup_active,
            "buy_stop_price": plan.buy_stop_price,
            "sell_stop_price": plan.sell_stop_price,
        },
        # 注文
        "buy_order_active": os.buy_order_active,
        "sell_order_active": os.sell_order_active,
        "last_buy_order_price": os.last_buy_order_price,
        "last_sell_order_price": os.last_sell_order_price,
        # データギャップ
        "data_gap_detected": runtime_state.data_gap_detected,
        "data_gap_minutes": runtime_state.data_gap_minutes,
        "strategy_ready": runtime_state.strategy_ready,
    }


@router.get("/chart/5m")
async def get_chart_5m():
    candles = runtime_state.candles_5m[-300:]
    return [
        {
            "time": c.time.isoformat(),
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in candles
    ]


@router.get("/logs")
async def get_logs():
    return runtime_state.log_entries[-100:]
