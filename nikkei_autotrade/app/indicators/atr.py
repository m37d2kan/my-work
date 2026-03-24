from app.market.market_models import Candle


def true_range(high: float, low: float, prev_close: float) -> float:
    return max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close),
    )


def rma(values: list[float], length: int) -> list[float | None]:
    """TradingView の ta.rma() 相当。"""
    out: list[float | None] = [None] * len(values)
    if len(values) < length:
        return out

    first = sum(values[:length]) / length
    out[length - 1] = first
    prev = first

    for i in range(length, len(values)):
        prev = (prev * (length - 1) + values[i]) / length
        out[i] = prev
    return out


def atr_rma(candles: list[Candle], length: int) -> float | None:
    """TradingView の ta.atr() 相当 (RMA方式)。"""
    if not candles:
        return None

    trs: list[float] = []
    for i, c in enumerate(candles):
        if i == 0:
            trs.append(c.high - c.low)
        else:
            prev_close = candles[i - 1].close
            trs.append(true_range(c.high, c.low, prev_close))

    atrs = rma(trs, length)
    return atrs[-1]
