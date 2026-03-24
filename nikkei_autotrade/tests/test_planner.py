import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone, timedelta
from app.market.market_models import Candle
from app.strategy.signal_state import SignalState
from app.strategy.planner import evaluate_and_plan
from app.order.order_state import OrderState
from app.config import Settings

JST = timezone(timedelta(hours=9))


def make_candles(n, base_price=36000):
    """テスト用の n 本のキャンドルを生成。"""
    candles = []
    base_ts = datetime(2025, 1, 1, 9, 0, tzinfo=JST)
    for i in range(n):
        p = base_price + i * 10
        ts = base_ts + timedelta(minutes=i * 5)
        candles.append(Candle(
            time=ts,
            open=p,
            high=p + 50,
            low=p - 50,
            close=p + 5,
        ))
    return candles


def test_buy_setup_active():
    state = SignalState()
    state.modoriTakane1 = 36500.0
    state.modoriBroken1 = False

    order_state = OrderState()
    cfg = Settings()
    cfg.entry_ma_source = "SMA1 (20)"

    candles = make_candles(25)
    now = datetime(2025, 1, 1, 10, 0, tzinfo=JST)

    plan = evaluate_and_plan(state, candles, now, cfg, order_state)

    assert plan.buy_setup_active is True
    assert plan.buy_stop_price == 36500.0


def test_sell_setup_active():
    state = SignalState()
    state.oshiYasune1 = 35800.0
    state.oshiBroken1 = False

    order_state = OrderState()
    cfg = Settings()
    cfg.entry_ma_source = "SMA1 (20)"

    candles = make_candles(25)
    now = datetime(2025, 1, 1, 10, 0, tzinfo=JST)

    plan = evaluate_and_plan(state, candles, now, cfg, order_state)

    assert plan.sell_setup_active is True
    assert plan.sell_stop_price == 35800.0


def test_no_setup_with_position():
    state = SignalState()
    state.modoriTakane1 = 36500.0

    order_state = OrderState()
    order_state.position_side = "BUY"  # ポジション保有中

    cfg = Settings()
    cfg.entry_ma_source = "SMA1 (20)"

    candles = make_candles(25)
    now = datetime(2025, 1, 1, 10, 0, tzinfo=JST)

    plan = evaluate_and_plan(state, candles, now, cfg, order_state)

    assert plan.buy_setup_active is False
    assert plan.buy_stop_price is None


def test_no_setup_emergency():
    state = SignalState()
    state.modoriTakane1 = 36500.0

    order_state = OrderState()
    order_state.emergency_stop = True

    cfg = Settings()
    cfg.entry_ma_source = "SMA1 (20)"

    candles = make_candles(25)
    now = datetime(2025, 1, 1, 10, 0, tzinfo=JST)

    plan = evaluate_and_plan(state, candles, now, cfg, order_state)

    assert plan.buy_setup_active is False


if __name__ == "__main__":
    test_buy_setup_active()
    test_sell_setup_active()
    test_no_setup_with_position()
    test_no_setup_emergency()
    print("All Planner tests passed")
