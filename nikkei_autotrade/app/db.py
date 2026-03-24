import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from app.market.market_models import Candle

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))
DB_PATH = Path(__file__).parent.parent / "data" / "autotrade.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """テーブル作成。起動時に1回呼ぶ。"""
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candles_5m (
            time TEXT PRIMARY KEY,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"DB initialized: {DB_PATH}")


def save_candle(candle: Candle):
    """5分足1本を保存。重複時は上書き。"""
    conn = _connect()
    conn.execute(
        """INSERT OR REPLACE INTO candles_5m (time, open, high, low, close, volume)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (candle.time.isoformat(), candle.open, candle.high, candle.low, candle.close, candle.volume),
    )
    conn.commit()
    conn.close()


def load_candles(limit: int = 600) -> list[Candle]:
    """過去の5分足を時系列順で読み込む。デフォルト600本(約50時間分)。"""
    conn = _connect()
    rows = conn.execute(
        "SELECT time, open, high, low, close, volume FROM candles_5m ORDER BY time DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()

    candles = []
    for row in reversed(rows):  # 古い順に並べ直す
        ts = datetime.fromisoformat(row[0])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=JST)
        candles.append(Candle(
            time=ts,
            open=row[1],
            high=row[2],
            low=row[3],
            close=row[4],
            volume=row[5],
        ))

    logger.info(f"Loaded {len(candles)} historical candles from DB")
    return candles


def get_candle_count() -> int:
    """保存済みの足数を返す。"""
    conn = _connect()
    count = conn.execute("SELECT COUNT(*) FROM candles_5m").fetchone()[0]
    conn.close()
    return count
