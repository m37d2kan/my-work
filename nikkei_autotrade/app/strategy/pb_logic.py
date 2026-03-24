from app.strategy.signal_state import SignalState
from app.market.market_models import Candle
from app.indicators.rolling_extrema import lowest_prev, highest_prev


def update_pb1(state: SignalState, candles: list[Candle], length1: int) -> tuple[bool, bool]:
    """P&B1 判定。Pine の peakCondition1 / bottomCondition1 に対応。"""
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]

    high = highs[-1]
    low = lows[-1]

    low_prev = lowest_prev(lows, length1)
    high_prev = highest_prev(highs, length1)

    peak_condition = (
        low_prev is not None
        and low < low_prev
        and state.lastPBSignal1 != "peak"
    )
    bottom_condition = (
        high_prev is not None
        and high > high_prev
        and state.lastPBSignal1 != "bottom"
    )

    if peak_condition:
        state.lastPBSignal1 = "peak"
        state.pbState1 = "下落波動"

    if bottom_condition:
        state.lastPBSignal1 = "bottom"
        state.pbState1 = "上昇波動"

    return peak_condition, bottom_condition
