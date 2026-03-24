from dataclasses import dataclass

SMA_MAP = {
    "SMA1 (20)": 20,
    "SMA2 (94)": 94,
    "SMA3 (200)": 200,
    "SMA4 (480)": 480,
    "SMA5 (600)": 600,
}


@dataclass
class Settings:
    # 銘柄
    symbol: str = "161060023"  # 日経225マイクロ先物 26/06
    future_code: str = "NK225micro"  # symbolname API用
    deriv_month: int = 202606       # 限月 yyyyMM
    exchange: int = 2        # 2=日通し, 23=日中, 24=夜間
    security_type: int = 104  # 101=大型, 103=mini, 104=マイクロ
    bar_seconds: int = 300

    # Swing1 / P&B1
    length1: int = 7

    # ATR
    atr_period: int = 14

    # MA乖離フィルタ (MA方向判定なし)
    entry_ma_source: str = "SMA1 (20)"
    entry_max_dev: float = 3.0

    # 時間フィルタ
    use_signal_time_filter: bool = False
    signal_start_hour: int = 8
    signal_start_min: int = 45
    signal_end_hour: int = 15
    signal_end_min: int = 15

    # 注文
    order_qty: int = 1
    max_position: int = 1

    # 利確損切り (ATR倍率)
    sl_atr_mult: float = 1.0
    tp_atr_mult: float = 1.8
    be_atr_trigger: float = 1.0  # 建値移動トリガー

    # 制御
    auto_enabled: bool = False
    order_expire_on_next_bar: bool = True

    # リスク管理
    max_daily_loss: int = 120000
    max_consecutive_losses: int = 3

    # kabuSTATION
    kabus_url: str = "http://localhost:18080/kabusapi"
    kabus_password: str = "860622"


settings = Settings()
