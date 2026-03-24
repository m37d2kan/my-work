import logging
from app.order.order_state import OrderState

logger = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, broker_client, order_state: OrderState):
        self.broker = broker_client
        self.state = order_state

    async def sync_entry_orders(self, plan, qty: int):
        """planner の結果に基づいて逆指値を新規/差替/取消する。"""
        if plan.buy_setup_active:
            await self._ensure_buy_stop(plan.buy_stop_price, qty)
        else:
            await self._cancel_buy()

        if plan.sell_setup_active:
            await self._ensure_sell_stop(plan.sell_stop_price, qty)
        else:
            await self._cancel_sell()

    async def _ensure_buy_stop(self, price: float, qty: int):
        if self.state.buy_order_active and self.state.last_buy_order_price == price:
            return  # 同一価格なら再発注不要

        await self._cancel_buy()

        if self.state.order_lock or self.state.emergency_stop:
            return

        self.state.order_lock = True
        try:
            result = await self.broker.send_buy_stop(price=price, qty=qty)
            if result["ok"]:
                self.state.buy_order_active = True
                self.state.buy_order_id = result["order_id"]
                self.state.last_buy_order_price = price
                logger.info(f"BUY STOP placed @{price} qty={qty} id={result['order_id']}")
            else:
                logger.error(f"BUY STOP failed: {result}")
        finally:
            self.state.order_lock = False

    async def _ensure_sell_stop(self, price: float, qty: int):
        if self.state.sell_order_active and self.state.last_sell_order_price == price:
            return

        await self._cancel_sell()

        if self.state.order_lock or self.state.emergency_stop:
            return

        self.state.order_lock = True
        try:
            result = await self.broker.send_sell_stop(price=price, qty=qty)
            if result["ok"]:
                self.state.sell_order_active = True
                self.state.sell_order_id = result["order_id"]
                self.state.last_sell_order_price = price
                logger.info(f"SELL STOP placed @{price} qty={qty} id={result['order_id']}")
            else:
                logger.error(f"SELL STOP failed: {result}")
        finally:
            self.state.order_lock = False

    async def _cancel_buy(self):
        if self.state.buy_order_active and self.state.buy_order_id:
            await self.broker.cancel_order(self.state.buy_order_id)
            logger.info(f"BUY STOP cancelled id={self.state.buy_order_id}")
        self.state.buy_order_active = False
        self.state.buy_order_id = None
        self.state.last_buy_order_price = None

    async def _cancel_sell(self):
        if self.state.sell_order_active and self.state.sell_order_id:
            await self.broker.cancel_order(self.state.sell_order_id)
            logger.info(f"SELL STOP cancelled id={self.state.sell_order_id}")
        self.state.sell_order_active = False
        self.state.sell_order_id = None
        self.state.last_sell_order_price = None

    async def cancel_all_entry_orders(self):
        await self._cancel_buy()
        await self._cancel_sell()

    async def on_fill(self, side: str, price: float, qty: int, atr_value: float | None):
        """約定検知時の処理。"""
        self.state.position_side = side
        self.state.position_qty = qty
        self.state.entry_price = price
        self.state.entry_atr = atr_value
        self.state.be_moved = False

        # 逆指値待機を全部外す
        await self.cancel_all_entry_orders()

        logger.info(f"FILLED {side} @{price} qty={qty} atr={atr_value}")

    def clear_position(self):
        """決済完了時。"""
        self.state.position_side = None
        self.state.position_qty = 0
        self.state.entry_price = None
        self.state.entry_atr = None
        self.state.sl_order_id = None
        self.state.tp_order_id = None
        self.state.sl_price = None
        self.state.tp_price = None
        self.state.be_moved = False
