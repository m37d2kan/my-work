import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.market.market_models import Candle
from app.strategy.signal_state import SignalState
from app.strategy.pb_logic import update_pb1
from datetime import datetime


def make_candle(h, l):
    return Candle(time=datetime(2025, 1, 1), open=h, high=h, low=l, close=l)


def test_peak_detection():
    """安値がlength=5の直前最安値を下回ったらpeak検出。"""
    state = SignalState()

    # 6本のcandle (length=5 + 現在1本)
    candles = [
        make_candle(110, 100),
        make_candle(112, 102),
        make_candle(115, 105),
        make_candle(113, 103),
        make_candle(111, 101),
        make_candle(108, 98),  # low=98 < min(100,102,105,103,101)=100
    ]
    peak, bottom = update_pb1(state, candles, 5)
    assert peak is True
    assert state.lastPBSignal1 == "peak"
    assert state.pbState1 == "下落波動"


def test_bottom_detection():
    """高値がlength=5の直前最高値を上回ったらbottom検出。"""
    state = SignalState()

    candles = [
        make_candle(100, 90),
        make_candle(102, 92),
        make_candle(98, 88),
        make_candle(101, 91),
        make_candle(99, 89),
        make_candle(105, 95),  # high=105 > max(100,102,98,101,99)=102
    ]
    peak, bottom = update_pb1(state, candles, 5)
    assert bottom is True
    assert state.lastPBSignal1 == "bottom"
    assert state.pbState1 == "上昇波動"


def test_no_repeat_peak():
    """連続peakは出ない。"""
    state = SignalState()
    state.lastPBSignal1 = "peak"

    candles = [
        make_candle(110, 100),
        make_candle(112, 102),
        make_candle(115, 105),
        make_candle(113, 103),
        make_candle(111, 101),
        make_candle(108, 98),
    ]
    peak, bottom = update_pb1(state, candles, 5)
    assert peak is False


if __name__ == "__main__":
    test_peak_detection()
    test_bottom_detection()
    test_no_repeat_peak()
    print("All P&B tests passed")
