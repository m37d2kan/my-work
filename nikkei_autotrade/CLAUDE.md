# Nikkei225 Auto Dashboard

## 概要
SwingFusion Pro v5.0A Light2 の最小売買版。
Swing1/P&B1 による押し安値・戻り高値に逆指値を事前配置し、
ATRベースで利確・損切りを管理する自動売買ダッシュボード。

## 起動
```bash
cd C:\trading\nikkei_autotrade
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
UI: http://localhost:8000/ui/

## 技術スタック
- Backend: Python / FastAPI (port 8000)
- Frontend: Vanilla HTML/JS/CSS (静的ファイル)
- Broker: kabuSTATION API (REST + WebSocket PUSH)

## ディレクトリ構造
```
app/
  config.py          - 設定 (SMA_MAP, Settings)
  runtime.py         - 共有状態 (RuntimeState)
  scheduler.py       - StrategyRunner (ティック→足確定→判定→注文)
  main.py            - FastAPI エントリポイント
  market/            - Candle, CandleBuilder
  indicators/        - SMA, ATR(RMA), rolling_extrema
  strategy/          - SignalState, P&B1, Swing1, realtime, filters, planner
  order/             - OrderState, OrderManager, ProtectiveManager
  broker/            - KabuRestClient, KabuPushClient
  api/               - routes_status, routes_control
  ui/                - index.html, dashboard.js, styles.css
```

## 売買ロジック概要
1. P&B1 で peak/bottom 検出 → Swing1 確定
2. 高値切下(peakFalling1) + 安値切下 → modoriTakane1 (戻り高値) セット → BUY逆指値候補
3. 安値切上(botRising1) + 高値切上 → oshiYasune1 (押し安値) セット → SELL逆指値候補
4. MA乖離フィルタ + 時間フィルタ通過 → 逆指値待機(setup active)
5. 約定後 → ATR × sl_mult でSL, ATR × tp_mult でTP設定
6. +1 ATR で建値移動(1回のみ)

## API
- GET /api/status - 全状態
- GET /api/chart/5m - 5分足データ
- GET /api/logs - ログ
- POST /api/control/auto-on
- POST /api/control/auto-off
- POST /api/control/emergency-stop
- POST /api/control/recover
- POST /api/control/cancel-all

## kabuSTATION 設定
config.py の `kabus_password` に API パスワードをセット。
未設定時は monitor-only モードで起動。
