from typing import Optional, Dict
from src.order.broker_interface import BrokerInterface
from ib_insync import Contract
import logging

logger = logging.getLogger("OrderManager")


class OrderManager:

    def __init__(self, broker: BrokerInterface):
        self.broker = broker
        self.symbol_positions: Dict[str, float] = {}

    def handle_signal(self, contract: Contract, signal: str, quantity: float, order_type: str = "market",
                      price: Optional[float] = None, tag: Optional[str] = None):

        symbol = contract.symbol
        current_pos = self.get_position_size(contract)

        if signal == "buy":
            if current_pos > 0:
                logger.info(f"[{symbol}] 이미 롱 포지션 보유 → 생략")
                return
            elif current_pos < 0:
                logger.info(f"[{symbol}] 숏 청산 후 롱 진입")
                self._send_order(contract, "buy", abs(current_pos) + quantity, order_type, price, tag)
            else:
                logger.info(f"[{symbol}] 신규 롱 진입")
                self._send_order(contract, "buy", quantity, order_type, price, tag)

        elif signal == "sell":
            if current_pos < 0:
                logger.info(f"[{symbol}] 이미 숏 포지션 보유 → 생략")
                return
            elif current_pos > 0:
                logger.info(f"[{symbol}] 롱 청산 후 숏 진입")
                self._send_order(contract, "sell", abs(current_pos) + quantity, order_type, price, tag)
            else:
                logger.info(f"[{symbol}] 신규 숏 진입")
                self._send_order(contract, "sell", quantity, order_type, price, tag)

        elif signal == "exit":
            # 주식 등 롱만 진입하고 exit 신호에 롱 청산
            if current_pos > 0:
                logger.info(f"[{symbol}] 롱 포지션 청산")
                self._send_order(contract, "sell", current_pos, order_type, price, tag)
            elif current_pos < 0:
                logger.info(f"[{symbol}] 숏 포지션 청산")
                self._send_order(contract, "buy", abs(current_pos), order_type, price, tag)

    def _send_order(self, contract: Contract, side: str, quantity: float, order_type: str,
                    price: Optional[float], tag: Optional[str] ):
        order = self.broker.send_order(
            contract=contract,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            tag=tag
        )

        symbol = contract.symbol
        if order.get("status") == "filled":
            logger.info(f"[{symbol}] 주문 체결 완료: {order}")
        elif order.get("status") == "submitted":
            logger.info(f"[{symbol}] 주문 제출됨: {order}")
        else:
            logger.warning(f"[{symbol}] 주문 실패 또는 거절: {order}")

        self._update_position(contract)

    def get_position_size(self, contract: Contract) -> float:
        pos = self.broker.get_position(contract)
        return pos.get("size", 0.0)

    def _update_position(self, contract: Contract):
        pos = self.broker.get_position(contract)
        self.symbol_positions[contract.symbol] = pos.get("size", 0.0)

    def refresh_all_positions(self, contract_list):
        for contract in contract_list:
            pos = self.broker.get_position(contract)
            self.symbol_positions[contract.symbol] = pos.get("size", 0.0)

    def close_all_positions(self, contract_list):
        for contract in contract_list:
            size = self.symbol_positions.get(contract.symbol, 0.0)
            if size > 0:
                self._send_order(contract, "sell", size, order_type="market", price=None, tag="close_all")
            elif size < 0:
                self._send_order(contract, "buy", abs(size), order_type="market", price=None, tag="close_all")
