from ib_insync import IB, Order, Contract
from typing import Dict, List, Optional
from src.order.broker_interface import BrokerInterface


class BrokerIBKR(BrokerInterface):

    def __init__(self, ib: IB):
        self.ib = ib

    def send_order(self, contract: Contract, side: str, quantity: float,
                   order_type: str = "market", price: Optional[float] = None,
                   tag: Optional[str] = None) -> Dict:
        # contract는 이미 Contract 객체이므로 그대로 사용
        if order_type == "market":
            order = Order(action=side.upper(), totalQuantity=quantity, orderType="MKT")
        elif order_type == "limit":
            order = Order(action=side.upper(), totalQuantity=quantity, orderType="LMT", lmtPrice=price)
        else:
            raise ValueError(f"지원되지 않는 주문 유형: {order_type}")

        trade = self.ib.placeOrder(contract, order)
        self.ib.sleep(1)  # 체결 대기

        status = trade.orderStatus.status
        fill_price = trade.fills[0].execution.price if trade.fills else None

        return {
            "order_id": trade.order.permId,
            "symbol": contract.symbol,
            "side": side,
            "quantity": quantity,
            "price": fill_price,
            "status": status,
            "tag": tag
        }

    def cancel_order(self, order_id: str) -> bool:
        for trade in self.ib.trades():
            if str(trade.order.permId) == order_id:
                self.ib.cancelOrder(trade.order)
                return True
        return False

    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        count = 0
        for trade in self.ib.trades():
            if trade.orderStatus.status == "Submitted":
                if symbol is None or trade.contract.symbol == symbol:
                    self.ib.cancelOrder(trade.order)
                    count += 1
        return count

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        result = []
        for trade in self.ib.trades():
            if trade.orderStatus.status == "Submitted":
                if symbol is None or trade.contract.symbol == symbol:
                    result.append({
                        "order_id": trade.order.permId,
                        "symbol": trade.contract.symbol,
                        "side": trade.order.action.lower(),
                        "quantity": trade.order.totalQuantity,
                        "status": trade.orderStatus.status
                    })
        return result

    def get_order_status(self, order_id: str) -> Dict:
        for trade in self.ib.trades():
            if str(trade.order.permId) == order_id:
                return {
                    "order_id": order_id,
                    "symbol": trade.contract.symbol,
                    "status": trade.orderStatus.status,
                    "filled": trade.orderStatus.filled,
                    "remaining": trade.orderStatus.remaining
                }
        return {"order_id": order_id, "status": "unknown"}

    def get_position(self, contract: Contract) -> Dict:
        self.ib.reqPositions()
        for pos in self.ib.positions():
            # 종목 종류별(주식, 선물 등) 비교 필요시 contract_vo의 기타 필드도 활용 가능
            if pos.contract.symbol == contract.symbol:
                return {
                    "symbol": contract.symbol,
                    "size": pos.position,
                    "avg_price": pos.avgCost
                }
        return {"symbol": contract.symbol, "size": 0.0, "avg_price": 0.0}

    def get_all_positions(self) -> Dict[str, Dict]:
        positions = {}
        self.ib.reqPositions()
        for pos in self.ib.positions():
            positions[pos.contract.symbol] = {
                "size": pos.position,
                "avg_price": pos.avgCost
            }
        return positions

    def get_account_info(self) -> Dict:
        account = self.ib.accountSummary()
        return {
            "cash": float(account.loc["NetLiquidation", "value"]),
            "buying_power": float(account.loc["AvailableFunds", "value"]),
            "margin": float(account.loc["MaintMarginReq", "value"]),
        }
