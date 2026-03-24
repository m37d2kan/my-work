import json
import logging
import threading
from typing import Callable

import websocket

logger = logging.getLogger(__name__)

PUSH_URL = "ws://localhost:18080/kabusapi/websocket"


class KabuPushClient:
    """kabuSTATION PUSH (WebSocket) 受信クライアント。"""

    def __init__(self, on_tick: Callable[[dict], None]):
        self.on_tick = on_tick
        self.ws: websocket.WebSocketApp | None = None
        self._thread: threading.Thread | None = None
        self.connected = False

    def start(self):
        self.ws = websocket.WebSocketApp(
            PUSH_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        if self.ws:
            self.ws.run_forever()

    def _on_open(self, ws):
        self.connected = True
        logger.info("PUSH connected")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.on_tick(data)
        except Exception:
            logger.exception("PUSH message parse error")

    def _on_error(self, ws, error):
        logger.error(f"PUSH error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        logger.warning(f"PUSH closed: {close_status_code} {close_msg}")

    def stop(self):
        if self.ws:
            self.ws.close()
        self.connected = False
