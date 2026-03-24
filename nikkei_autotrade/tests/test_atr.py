import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.market.market_models import Candle
from app.indicators.atr import true_range, rma, atr_rma
from datetime import datetime


def make_candle(o, h, l, c):
    return Candle(time=datetime(2025, 1, 1), open=o, high=h, low=l, close=c)


def test_true_range():
    assert true_range(100, 90, 95) == 10
    assert true_range(100, 90, 85) == 15
    assert true_range(100, 90, 105) == 15


def test_rma_basic():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = rma(values, 3)
    assert result[0] is None
    assert result[1] is None
    assert abs(result[2] - 2.0) < 1e-10  # (1+2+3)/3 = 2.0
    # result[3] = (2.0 * 2 + 4.0) / 3 = 8/3 ≈ 2.666
    assert abs(result[3] - 8 / 3) < 1e-10


def test_atr_rma_basic():
    candles = [
        make_candle(100, 110, 95, 105),
        make_candle(105, 112, 98, 108),
        make_candle(108, 115, 100, 110),
    ]
    result = atr_rma(candles, 2)
    assert result is not None
    assert result > 0


def test_atr_rma_not_enough():
    candles = [make_candle(100, 110, 95, 105)]
    result = atr_rma(candles, 14)
    assert result is None


if __name__ == "__main__":
    test_true_range()
    test_rma_basic()
    test_atr_rma_basic()
    test_atr_rma_not_enough()
    print("All ATR tests passed")
