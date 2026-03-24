from app.strategy.signal_state import SignalState
from app.market.market_models import Candle
from app.indicators.rolling_extrema import lowest_prev, highest_prev


def calc_trend_status(peaks: list[float], bots: list[float]) -> str:
    if len(peaks) >= 2 and len(bots) >= 2:
        p0, p1 = peaks[-2], peaks[-1]
        b0, b1 = bots[-2], bots[-1]
        if p1 > p0 and b1 > b0:
            return "UP"
        if p1 < p0 and b1 < b0:
            return "DOWN"
    return "FLAT"


def _push_keep_last2(values: list, value):
    values.append(value)
    if len(values) > 2:
        values.pop(0)


def update_swing1_confirmed(
    state: SignalState,
    candles: list[Candle],
    bar_index: int,
    length1: int,
):
    """Swing1 確定処理。確定足ごとに1回だけ実行。"""
    c = candles[-1]

    # 最安値・最高値探索
    if state.ssb_findingMin1 and (state.ssb_minPrice1 is None or c.low < state.ssb_minPrice1):
        state.ssb_minPrice1 = c.low
        state.ssb_minIdx1 = bar_index
        state.ssb_minClose1 = c.close

    if state.ssb_findingMax1 and (state.ssb_maxPrice1 is None or c.high > state.ssb_maxPrice1):
        state.ssb_maxPrice1 = c.high
        state.ssb_maxIdx1 = bar_index
        state.ssb_maxClose1 = c.close

    lows = [x.low for x in candles]
    highs = [x.high for x in candles]

    lp = lowest_prev(lows, length1)
    hp = highest_prev(highs, length1)

    peak_conf1 = state.ssb_findingMax1 and lp is not None and c.low < lp
    bottom_conf1 = state.ssb_findingMin1 and hp is not None and c.high > hp

    # ── peak 確定 ──
    if peak_conf1:
        _push_keep_last2(state.peakPx1, state.ssb_maxPrice1)
        _push_keep_last2(state.peakIx1, state.ssb_maxIdx1)
        state.trend_status1_confirmed = calc_trend_status(state.peakPx1, state.botPx1)

        if state.prevPeak1 is not None:
            if state.ssb_maxPrice1 > state.prevPeak1:
                # 高値切り上げ → 押し安値候補更新
                if state.botRising1 and state.prevBot1 is not None:
                    if state.oshiYasune1 is None or state.prevBot1 > state.oshiYasune1:
                        state.oshiYasune1 = state.prevBot1
                        state.oshiYasuneIdx1 = state.prevBotIdx1
                        state.oshiBroken1 = False
                        state.oshiPrevBot1 = state.prevBot2nd1
                state.peakFalling1 = False
                # 高値更新で戻り高値リセット
                state.modoriTakane1 = None
                state.modoriTakaneIdx1 = None
                state.modoriBroken1 = False
                state.modoriPrevPeak1 = None
            elif state.ssb_maxPrice1 < state.prevPeak1:
                state.peakFalling1 = True

        state.prevPeak2ndClose1 = state.prevPeakClose1
        state.prevPeak2ndIdx1 = state.prevPeakIdx1
        state.prevPeak2nd1 = state.prevPeak1

        state.prevPeakClose1 = state.ssb_maxClose1
        state.prevPeakIdx1 = state.ssb_maxIdx1
        state.prevPeak1 = state.ssb_maxPrice1

        state.ssb_findingMax1 = False
        state.ssb_findingMin1 = True
        state.ssb_minPrice1 = c.low
        state.ssb_minIdx1 = bar_index
        state.ssb_minClose1 = c.close
        state.p1_broken1 = False

    # ── bottom 確定 ──
    if bottom_conf1:
        _push_keep_last2(state.botPx1, state.ssb_minPrice1)
        _push_keep_last2(state.botIx1, state.ssb_minIdx1)
        state.trend_status1_confirmed = calc_trend_status(state.peakPx1, state.botPx1)

        if state.prevBot1 is not None:
            if state.ssb_minPrice1 < state.prevBot1:
                # 安値切り下げ → 戻り高値候補更新
                if state.peakFalling1 and state.prevPeak1 is not None:
                    if state.modoriTakane1 is None or state.prevPeak1 < state.modoriTakane1:
                        state.modoriTakane1 = state.prevPeak1
                        state.modoriTakaneIdx1 = state.prevPeakIdx1
                        state.modoriBroken1 = False
                        state.modoriPrevPeak1 = state.prevPeak2nd1
                state.botRising1 = False
                # 安値更新で押し安値リセット
                state.oshiYasune1 = None
                state.oshiYasuneIdx1 = None
                state.oshiBroken1 = False
                state.oshiPrevBot1 = None
            elif state.ssb_minPrice1 > state.prevBot1:
                state.botRising1 = True

        state.prevBot2ndClose1 = state.prevBotClose1
        state.prevBot2ndIdx1 = state.prevBotIdx1
        state.prevBot2nd1 = state.prevBot1

        state.prevBotClose1 = state.ssb_minClose1
        state.prevBotIdx1 = state.ssb_minIdx1
        state.prevBot1 = state.ssb_minPrice1

        state.ssb_findingMin1 = False
        state.ssb_findingMax1 = True
        state.ssb_maxPrice1 = c.high
        state.ssb_maxIdx1 = bar_index
        state.ssb_maxClose1 = c.close
        state.b1_broken1 = False
