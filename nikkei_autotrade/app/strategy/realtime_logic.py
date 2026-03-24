from app.strategy.signal_state import SignalState


def update_realtime_levels(state: SignalState, current_high: float, current_low: float):
    """形成中バーでの押し安値・戻り高値のリアルタイム更新。"""

    # 押し安値更新: high > prevPeak1 かつ botRising1
    if state.prevPeak1 is not None and state.prevBot1 is not None:
        if current_high > state.prevPeak1 and state.botRising1:
            if state.oshiYasune1 is None or state.prevBot1 > state.oshiYasune1:
                state.oshiYasune1 = state.prevBot1
                state.oshiYasuneIdx1 = state.prevBotIdx1
                state.oshiBroken1 = False
                state.oshiPrevBot1 = state.prevBot2nd1

    # 戻り高値更新: low < prevBot1 かつ peakFalling1
    if state.prevBot1 is not None and state.prevPeak1 is not None:
        if current_low < state.prevBot1 and state.peakFalling1:
            if state.modoriTakane1 is None or state.prevPeak1 < state.modoriTakane1:
                state.modoriTakane1 = state.prevPeak1
                state.modoriTakaneIdx1 = state.prevPeakIdx1
                state.modoriBroken1 = False
                state.modoriPrevPeak1 = state.prevPeak2nd1
