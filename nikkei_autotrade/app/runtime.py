from dataclasses import dataclass, field
from typing import Optional
from app.market.market_models import Candle
from app.strategy.signal_state import SignalState
from app.strategy.strategy_models import PlanResult
from app.order.order_state import OrderState


@dataclass
class RuntimeState:
    # 接続状態
    api_connected: bool = False
    push_connected: bool = False

    # 足データ
    candles_5m: list[Candle] = field(default_factory=list)

    # 戦略状態
    signal_state: SignalState = field(default_factory=SignalState)
    order_state: OrderState = field(default_factory=OrderState)

    # 最新結果
    last_plan: Optional[PlanResult] = None
    current_price: Optional[float] = None

    # データギャップ検知
    data_gap_detected: bool = False
    data_gap_minutes: int = 0
    strategy_ready: bool = False  # 戦略判定に十分な足が溜まったか

    # ログ (直近100件をメモリ保持)
    log_entries: list[dict] = field(default_factory=list)

    def add_log(self, category: str, message: str):
        from datetime import datetime
        entry = {
            "time": datetime.now().isoformat(),
            "category": category,
            "message": message,
        }
        self.log_entries.append(entry)
        if len(self.log_entries) > 200:
            self.log_entries = self.log_entries[-200:]


runtime_state = RuntimeState()
