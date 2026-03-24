from datetime import datetime
from app.market.market_models import Candle, CandleUpdateResult


def floor_time(ts: datetime, seconds: int) -> datetime:
    epoch = int(ts.timestamp())
    floored = epoch - (epoch % seconds)
    return datetime.fromtimestamp(floored, tz=ts.tzinfo)


class CandleBuilder:
    def __init__(self, bar_seconds: int):
        self.bar_seconds = bar_seconds
        self.current: Candle | None = None

    def update(self, ts: datetime, price: float, volume: float = 0.0) -> CandleUpdateResult:
        bucket = floor_time(ts, self.bar_seconds)

        if self.current is None or self.current.time != bucket:
            finished = self.current
            self.current = Candle(
                time=bucket,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume,
            )
            return CandleUpdateResult(finished_candle=finished, current_candle=self.current)

        self.current.high = max(self.current.high, price)
        self.current.low = min(self.current.low, price)
        self.current.close = price
        self.current.volume += volume
        return CandleUpdateResult(finished_candle=None, current_candle=self.current)
