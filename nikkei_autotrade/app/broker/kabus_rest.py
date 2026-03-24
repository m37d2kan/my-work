import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class KabuRestClient:
    """kabuSTATION REST API クライアント。"""

    def __init__(self):
        self.base_url = settings.kabus_url
        self.password = settings.kabus_password
        self.token: str | None = None

    def _headers(self):
        return {"X-API-KEY": self.token, "Content-Type": "application/json"}

    # ── トークン ──
    async def fetch_token(self) -> str:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/token",
                json={"APIPassword": self.password},
            )
            r.raise_for_status()
            self.token = r.json()["Token"]
            logger.info("kabuSTATION token acquired")
            return self.token

    # ── 銘柄登録解除 (PUSH用) ──
    async def unregister_all(self) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.put(
                f"{self.base_url}/unregister/all",
                headers=self._headers(),
                json={},
            )
            logger.info(f"Unregistered all symbols")
            return r.json()

    # ── 銘柄登録 (PUSH用) ──
    async def register_symbol(self, symbol: str, exchange: int) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.put(
                f"{self.base_url}/register",
                headers=self._headers(),
                json={"Symbols": [{"Symbol": symbol, "Exchange": exchange}]},
            )
            data = r.json()
            logger.info(f"Registered symbol: {symbol}@{exchange} -> {data}")
            return data

    # ── 買い逆指値 ──
    async def send_buy_stop(self, price: float, qty: int) -> dict:
        payload = self._build_stop_payload(
            side="2",  # 買
            trigger_price=price,
            under_over=2,  # 以上
            qty=qty,
        )
        return await self._send_order(payload)

    # ── 売り逆指値 ──
    async def send_sell_stop(self, price: float, qty: int) -> dict:
        payload = self._build_stop_payload(
            side="1",  # 売
            trigger_price=price,
            under_over=1,  # 以下
            qty=qty,
        )
        return await self._send_order(payload)

    # ── 取消 ──
    async def cancel_order(self, order_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.put(
                f"{self.base_url}/cancelorder",
                headers=self._headers(),
                json={"OrderId": order_id},
            )
            if r.status_code == 200:
                return {"ok": True, "order_id": order_id}
            return {"ok": False, "error": r.text}

    # ── 決済注文 (SLのみ返済逆指値) ──
    async def place_sl_return(self, side: str, qty: int, sl_price: float) -> dict:
        """SLを返済逆指値で発注。TPはソフトウェア監視のため発注しない。"""
        exit_side = "1" if side == "BUY" else "2"  # 反対売買
        sl_under_over = 1 if side == "BUY" else 2

        sl_payload = self._build_stop_payload(
            side=exit_side,
            trigger_price=sl_price,
            under_over=sl_under_over,
            qty=qty,
            trade_type=2,  # 返済
        )
        result = await self._send_order(sl_payload)
        return {
            "ok": result["ok"],
            "sl_order_id": result.get("order_id"),
        }

    # ── 成行返済 (TP到達時に使用) ──
    async def send_market_close(self, side: str, qty: int) -> dict:
        """成行で返済注文を発注。TP到達時にSL取消後に呼ぶ。"""
        exit_side = "1" if side == "BUY" else "2"
        payload = {
            "Password": self.password,
            "Symbol": settings.symbol,
            "Exchange": settings.exchange,
            "SecurityType": settings.security_type,
            "Side": exit_side,
            "CashMargin": 0,
            "DelivType": 0,
            "AccountType": 2,
            "Qty": qty,
            "TradeType": 2,  # 返済
            "FrontOrderType": 120,  # 成行
            "Price": 0.0,
            "ExpireDay": 0,
            "ClosePositionOrder": 0,  # 日付優先
        }
        return await self._send_order(payload)

    # ── 建値移動 (SL差替え) ──
    async def modify_sl(self, side: str, qty: int, sl_price: float) -> dict:
        exit_side = "1" if side == "BUY" else "2"
        sl_under_over = 1 if side == "BUY" else 2
        payload = self._build_stop_payload(
            side=exit_side,
            trigger_price=sl_price,
            under_over=sl_under_over,
            qty=qty,
            trade_type=2,
        )
        result = await self._send_order(payload)
        return {
            "ok": result["ok"],
            "sl_order_id": result.get("order_id"),
        }

    # ── 注文照会 ──
    async def get_orders(self) -> list:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/orders",
                headers=self._headers(),
            )
            if r.status_code == 200:
                return r.json()
            return []

    # ── 建玉照会 ──
    async def get_positions(self) -> list:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/positions",
                headers=self._headers(),
            )
            if r.status_code == 200:
                return r.json()
            return []

    # ── 内部ヘルパ ──
    def _build_stop_payload(
        self, side: str, trigger_price: float, under_over: int, qty: int, trade_type: int = 1
    ) -> dict:
        payload = {
            "Password": self.password,
            "Symbol": settings.symbol,
            "Exchange": settings.exchange,
            "SecurityType": settings.security_type,
            "Side": side,
            "CashMargin": 0,
            "DelivType": 0,
            "AccountType": 2,
            "Qty": qty,
            "TradeType": trade_type,
            "FrontOrderType": 30,  # 逆指値
            "Price": 0.0,
            "ExpireDay": 0,
            "ReverseLimitOrder": {
                "TriggerSec": 1,
                "TriggerPrice": float(trigger_price),
                "UnderOver": under_over,
                "AfterHitOrderType": 2,  # 指値
                "AfterHitPrice": float(trigger_price),
            },
        }
        if trade_type == 2:
            payload["ClosePositionOrder"] = 0  # 日付優先
        return payload

    def _build_limit_payload(
        self, side: str, price: float, qty: int, trade_type: int = 1
    ) -> dict:
        payload = {
            "Password": self.password,
            "Symbol": settings.symbol,
            "Exchange": settings.exchange,
            "SecurityType": settings.security_type,
            "Side": side,
            "CashMargin": 0,
            "DelivType": 0,
            "AccountType": 2,
            "Qty": qty,
            "TradeType": trade_type,
            "FrontOrderType": 20,  # 指値
            "Price": float(price),
            "ExpireDay": 0,
        }
        if trade_type == 2:
            payload["ClosePositionOrder"] = 0
        return payload

    async def _send_order(self, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/sendorder/future",
                headers=self._headers(),
                json=payload,
            )
            if r.status_code == 200:
                data = r.json()
                return {"ok": True, "order_id": data.get("OrderId")}
            logger.error(f"Order failed: {r.status_code} {r.text}")
            return {"ok": False, "error": r.text}
