from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SignalState:
    # P&B1
    lastPBSignal1: Optional[str] = None   # "peak" / "bottom"
    pbState1: str = "---"                 # "上昇波動" / "下落波動" / "---"

    # Swing1 探索状態
    ssb_findingMin1: bool = True
    ssb_findingMax1: bool = False
    ssb_minPrice1: Optional[float] = None
    ssb_minIdx1: Optional[int] = None
    ssb_maxPrice1: Optional[float] = None
    ssb_maxIdx1: Optional[int] = None
    ssb_minClose1: Optional[float] = None
    ssb_maxClose1: Optional[float] = None

    # 直近2個のピーク・ボトム
    peakPx1: list[float] = field(default_factory=list)
    peakIx1: list[int] = field(default_factory=list)
    botPx1: list[float] = field(default_factory=list)
    botIx1: list[int] = field(default_factory=list)

    trend_status1_confirmed: str = "FLAT"

    b1_broken1: bool = False
    p1_broken1: bool = False

    prevPeak1: Optional[float] = None
    prevBot1: Optional[float] = None
    prevPeak2nd1: Optional[float] = None
    prevBot2nd1: Optional[float] = None

    prevPeakClose1: Optional[float] = None
    prevBotClose1: Optional[float] = None
    prevPeak2ndClose1: Optional[float] = None
    prevBot2ndClose1: Optional[float] = None

    prevPeakIdx1: Optional[int] = None
    prevBotIdx1: Optional[int] = None
    prevPeak2ndIdx1: Optional[int] = None
    prevBot2ndIdx1: Optional[int] = None

    peakFalling1: bool = False
    botRising1: bool = False

    # 押し安値
    oshiYasune1: Optional[float] = None
    oshiYasuneIdx1: Optional[int] = None
    oshiBroken1: bool = False
    oshiPrevBot1: Optional[float] = None

    # 戻り高値
    modoriTakane1: Optional[float] = None
    modoriTakaneIdx1: Optional[int] = None
    modoriBroken1: bool = False
    modoriPrevPeak1: Optional[float] = None
