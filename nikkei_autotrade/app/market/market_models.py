from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Tick:
    ts: datetime
    price: float
    volume: float = 0.0


@dataclass
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class CandleUpdateResult:
    finished_candle: Optional[Candle]
    current_candle: Candle
