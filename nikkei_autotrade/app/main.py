import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes_status import router as status_router
from app.api.routes_control import router as control_router
from app.runtime import runtime_state
from app.config import settings
from app.broker.kabus_rest import KabuRestClient
from app.broker.kabus_push import KabuPushClient
from app.order.order_manager import OrderManager
from app.order.protective_manager import ProtectiveManager
from app.scheduler import StrategyRunner, on_push_message, set_runner, tick_consumer_loop, fill_monitor_loop
from app.db import init_db, load_candles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

broker = KabuRestClient()
order_manager = OrderManager(broker, runtime_state.order_state)
protective_manager = ProtectiveManager(broker, runtime_state.order_state)
runner = StrategyRunner(order_manager, protective_manager)
set_runner(runner)

push_client: KabuPushClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global push_client

    # DB初期化 + 過去データ読込
    init_db()
    historical = load_candles(limit=600)

    from datetime import datetime, timezone, timedelta
    from app.strategy.pb_logic import update_pb1
    from app.strategy.swing_logic import update_swing1_confirmed
    from app.strategy.planner import evaluate_and_plan
    from app.strategy.signal_state import SignalState

    JST = timezone(timedelta(hours=9))
    GAP_THRESHOLD_MINUTES = 10  # 10分以上の欠損で警告

    if historical:
        # ギャップ検出: 最新足の時刻と現在時刻を比較
        now_jst = datetime.now(JST)
        last_candle_time = historical[-1].time
        if last_candle_time.tzinfo is None:
            last_candle_time = last_candle_time.replace(tzinfo=JST)
        gap_minutes = int((now_jst - last_candle_time).total_seconds() / 60)

        if gap_minutes > GAP_THRESHOLD_MINUTES:
            runtime_state.data_gap_detected = True
            runtime_state.data_gap_minutes = gap_minutes
            runtime_state.add_log("WARNING", f"DATA GAP: {gap_minutes}分の欠損検出（最終足: {last_candle_time.strftime('%H:%M')} → 現在: {now_jst.strftime('%H:%M')}）")
            runtime_state.add_log("WARNING", "戦略状態をリセット。新しい足が溜まるまで再蓄積モード")

            # 足データは保持するが、戦略状態はリセット
            runtime_state.candles_5m = historical
            runner.bar_index = len(historical)
            runtime_state.signal_state = SignalState()  # リセット
            runtime_state.strategy_ready = False
            runtime_state.add_log("SYSTEM", f"Loaded {len(historical)} candles (strategy RESET due to gap)")
        else:
            # 欠損なし: 通常リプレイ
            runtime_state.data_gap_detected = False
            runtime_state.candles_5m = historical
            runner.bar_index = len(historical)
            runtime_state.add_log("SYSTEM", f"Loaded {len(historical)} historical candles (no gap)")

            for i in range(2, len(historical) + 1):
                slice_ = historical[:i]
                update_pb1(runtime_state.signal_state, slice_, settings.length1)
                update_swing1_confirmed(runtime_state.signal_state, slice_, i, settings.length1)
            if len(historical) >= 2:
                plan = evaluate_and_plan(
                    state=runtime_state.signal_state,
                    candles=historical,
                    now_tokyo=historical[-1].time,
                    cfg=settings,
                    order_state=runtime_state.order_state,
                )
                runtime_state.last_plan = plan
            runtime_state.strategy_ready = True
            runtime_state.add_log("SYSTEM", f"Strategy replayed: peak={runtime_state.signal_state.prevPeak1} bot={runtime_state.signal_state.prevBot1}")

    # バックグラウンドタスク起動
    consumer_task = asyncio.create_task(tick_consumer_loop())
    fill_task = asyncio.create_task(fill_monitor_loop())

    # 起動時: kabuSTATION 接続
    try:
        if settings.kabus_password:
            await broker.fetch_token()
            runtime_state.api_connected = True
            runtime_state.add_log("SYSTEM", "API connected")

            # 銘柄登録 (旧登録を全解除してから、PUSH接続より先に)
            await broker.unregister_all()
            await broker.register_symbol(settings.symbol, settings.exchange)
            runtime_state.add_log("SYSTEM", f"Symbol registered: {settings.symbol}")

            # PUSH 開始 (銘柄登録後に接続)
            push_client = KabuPushClient(on_tick=on_push_message)
            push_client.start()
            runtime_state.push_connected = True
            runtime_state.add_log("SYSTEM", "PUSH started")
        else:
            logger.warning("No kabus_password set - running in monitor-only mode")
            runtime_state.add_log("SYSTEM", "Monitor-only mode (no API password)")
    except Exception:
        logger.exception("Startup connection failed")
        runtime_state.add_log("SYSTEM", "Startup connection failed")

    yield

    # シャットダウン
    consumer_task.cancel()
    fill_task.cancel()
    if push_client:
        push_client.stop()
    runtime_state.api_connected = False
    runtime_state.push_connected = False


app = FastAPI(title="Nikkei225 Auto Dashboard", lifespan=lifespan)

app.include_router(status_router, prefix="/api")
app.include_router(control_router, prefix="/api")
app.mount("/ui", StaticFiles(directory="app/ui", html=True), name="ui")
