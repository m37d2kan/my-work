import logging
from app.order.order_state import OrderState

logger = logging.getLogger(__name__)


class ProtectiveManager:
    def __init__(self, broker_client, order_state: OrderState):
        self.broker = broker_client
        self.state = order_state

    async def place_sl_only(self, sl_mult: float, tp_mult: float):
        """約定後: SLを返済逆指値で発注 + TPレベルをメモリに記録（発注しない）。"""
        if self.state.entry_price is None or self.state.entry_atr is None:
            return
        if self.state.position_side is None:
            return

        entry = self.state.entry_price
        atr = self.state.entry_atr
        side = self.state.position_side
        qty = self.state.position_qty

        if side == "BUY":
            sl_price = round(entry - atr * sl_mult)
            tp_price = round(entry + atr * tp_mult)
        else:
            sl_price = round(entry + atr * sl_mult)
            tp_price = round(entry - atr * tp_mult)

        # SLのみ返済逆指値で発注
        result = await self.broker.place_sl_return(
            side=side, qty=qty, sl_price=sl_price
        )

        if result["ok"]:
            self.state.sl_price = sl_price
            self.state.sl_order_id = result.get("sl_order_id")
            self.state.tp_price = tp_price
            self.state.tp_order_id = None  # TPは発注しない
            logger.info(f"SL PLACED @{sl_price} (返済逆指値) | TP TARGET @{tp_price} (ソフトウェア監視)")
        else:
            logger.error(f"SL PLACEMENT FAILED: {result}")

    async def check_tp_level(self, current_price: float) -> bool:
        """ティックごとにTP到達をチェック。到達時はSL取消→成行返済。
        Returns True if TP was triggered."""
        if self.state.position_side is None or self.state.tp_price is None:
            return False

        triggered = False
        if self.state.position_side == "BUY" and current_price >= self.state.tp_price:
            triggered = True
        elif self.state.position_side == "SELL" and current_price <= self.state.tp_price:
            triggered = True

        if not triggered:
            return False

        logger.info(f"TP TRIGGERED @{current_price} (target={self.state.tp_price})")

        # SL取消
        if self.state.sl_order_id:
            await self.broker.cancel_order(self.state.sl_order_id)
            logger.info(f"SL cancelled (TP triggered) id={self.state.sl_order_id}")

        # 成行返済
        result = await self.broker.send_market_close(
            side=self.state.position_side,
            qty=self.state.position_qty,
        )

        if result["ok"]:
            logger.info(f"MARKET CLOSE sent (TP)")
        else:
            logger.error(f"MARKET CLOSE FAILED: {result}")

        return True

    async def check_breakeven(self, current_price: float, be_trigger_atr: float):
        """建値移動チェック。+1ATR で SL を entry_price に移動（1回のみ）。"""
        if self.state.be_moved:
            return
        if self.state.entry_price is None or self.state.entry_atr is None:
            return
        if self.state.position_side is None:
            return

        entry = self.state.entry_price
        atr = self.state.entry_atr
        threshold = atr * be_trigger_atr

        triggered = False
        if self.state.position_side == "BUY" and current_price >= entry + threshold:
            triggered = True
        elif self.state.position_side == "SELL" and current_price <= entry - threshold:
            triggered = True

        if triggered:
            new_sl = entry
            if self.state.sl_order_id:
                await self.broker.cancel_order(self.state.sl_order_id)
            result = await self.broker.modify_sl(
                side=self.state.position_side,
                qty=self.state.position_qty,
                sl_price=new_sl,
            )
            if result.get("ok"):
                self.state.sl_price = new_sl
                self.state.sl_order_id = result.get("sl_order_id")
                self.state.be_moved = True
                logger.info(f"BREAKEVEN MOVED SL to {new_sl}")
