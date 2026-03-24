def lowest_prev(lows: list[float], length: int) -> float | None:
    """ta.lowest(low, length)[1] 相当。現在足を除く直前 length 本の最安値。"""
    if len(lows) < length + 1:
        return None
    return min(lows[-length - 1:-1])


def highest_prev(highs: list[float], length: int) -> float | None:
    """ta.highest(high, length)[1] 相当。現在足を除く直前 length 本の最高値。"""
    if len(highs) < length + 1:
        return None
    return max(highs[-length - 1:-1])
