from dataclasses import dataclass
from typing import Optional


@dataclass
class PlanResult:
    entry_ma: Optional[float]
    atr_value: Optional[float]
    ma_deviation_ok: bool
    signal_time_ok: bool

    buy_setup_active: bool
    sell_setup_active: bool

    buy_stop_price: Optional[float]
    sell_stop_price: Optional[float]
