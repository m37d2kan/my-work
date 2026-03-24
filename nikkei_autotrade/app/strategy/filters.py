from datetime import datetime


def calc_ma_deviation_ok(
    close: float,
    entry_ma: float | None,
    atr_value: float | None,
    entry_max_dev: float,
) -> bool:
    """MA乖離フィルタ。MA方向判定なし、乖離のみ。買い売り共通。"""
    if entry_ma is None or atr_value is None or atr_value <= 0:
        return False
    deviation = abs(close - entry_ma) / atr_value
    return deviation <= entry_max_dev


def in_signal_time(
    dt_tokyo: datetime,
    use_filter: bool,
    sh: int,
    sm: int,
    eh: int,
    em: int,
) -> bool:
    """時間フィルタ。Pine の f_inSignalTime() 相当。"""
    if not use_filter:
        return True

    current = dt_tokyo.hour * 60 + dt_tokyo.minute
    start_m = sh * 60 + sm
    end_m = eh * 60 + em

    if start_m <= end_m:
        return start_m <= current < end_m
    return current >= start_m or current < end_m
