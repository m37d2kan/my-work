from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderState:
    # 待機逆指値
    buy_order_active: bool = False
    sell_order_active: bool = False

    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None

    last_buy_order_price: Optional[float] = None
    last_sell_order_price: Optional[float] = None

    # 建玉
    position_side: Optional[str] = None   # "BUY" / "SELL" / None
    position_qty: int = 0
    entry_price: Optional[float] = None
    entry_atr: Optional[float] = None

    # 保護注文
    sl_order_id: Optional[str] = None
    tp_order_id: Optional[str] = None
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    be_moved: bool = False  # 建値移動済みフラグ

    # 制御
    emergency_stop: bool = False
    order_lock: bool = False

    # リスク管理
    daily_pnl: float = 0.0
    consecutive_losses: int = 0
