import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.market.market_models import Candle
from app.strategy.signal_state import SignalState
from app.strategy.swing_logic import update_swing1_confirmed, calc_trend_status
from datetime import datetime


def make_candle(h, l, c=None):
    if c is None:
        c = (h + l) / 2
    return Candle(time=datetime(2025, 1, 1), open=h, high=h, low=l, close=c)


def test_trend_status():
    assert calc_trend_status([100, 110], [90, 95]) == "UP"
    assert calc_trend_status([110, 100], [95, 90]) == "DOWN"
    assert calc_trend_status([100, 110], [95, 90]) == "FLAT"
    assert calc_trend_status([100], [90]) == "FLAT"


def test_swing_basic_bottom_conf():
    """底探索中に高値更新でbottom確定するか。"""
    state = SignalState()
    state.ssb_findingMin1 = True
    state.ssb_minPrice1 = 95.0
    state.ssb_minIdx1 = 2

    # length=5, 6本必要
    candles = [
        make_candle(100, 90),
        make_candle(102, 92),
        make_candle(98, 88),
        make_candle(99, 89),
        make_candle(101, 91),
        make_candle(108, 98),  # high=108 > highest_prev(100,102,98,99,101)=102
    ]

    update_swing1_confirmed(state, candles, 5, 5)

    # bottom確定すると findingMax に切替
    assert state.ssb_findingMax1 is True
    assert state.ssb_findingMin1 is False
    assert state.prevBot1 == 95.0


def test_swing_basic_peak_conf():
    """山探索中に安値更新でpeak確定するか。"""
    state = SignalState()
    state.ssb_findingMax1 = True
    state.ssb_findingMin1 = False
    state.ssb_maxPrice1 = 115.0
    state.ssb_maxIdx1 = 3

    candles = [
        make_candle(110, 100),
        make_candle(112, 102),
        make_candle(115, 105),
        make_candle(113, 103),
        make_candle(111, 101),
        make_candle(108, 98),  # low=98 < lowest_prev(100,102,105,103,101)=100
    ]

    update_swing1_confirmed(state, candles, 5, 5)

    assert state.ssb_findingMin1 is True
    assert state.ssb_findingMax1 is False
    assert state.prevPeak1 == 115.0


if __name__ == "__main__":
    test_trend_status()
    test_swing_basic_bottom_conf()
    test_swing_basic_peak_conf()
    print("All Swing tests passed")
