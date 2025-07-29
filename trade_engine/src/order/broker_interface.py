from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from ib_insync import Contract


class BrokerInterface(ABC):
    """
    전략이 브로커와 상호작용할 수 있도록 정의된 추상 인터페이스 (contract_vo 기반)
    """

    @abstractmethod
    def send_order(self, contract: Contract, side: str, quantity: float,
                   order_type: str = "market", price: Optional[float] = None,
                   tag: Optional[str] = None) -> Dict:
        """시장/지정가 주문 전송"""

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """특정 주문 취소"""

    @abstractmethod
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """모든 열린 주문 취소"""

    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """현재 미체결 주문 리스트"""

    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict:
        """특정 주문의 상태 조회"""

    # --- 포지션 및 계좌 정보 ---
    @abstractmethod
    def get_position(self, contract: Contract) -> Dict:
        """특정 종목 포지션 정보"""

    @abstractmethod
    def get_all_positions(self) -> Dict[str, Dict]:
        """모든 보유 포지션 반환"""

    @abstractmethod
    def get_account_info(self) -> Dict:
        """총 자산, 잔고, 미실현 손익 등 계좌 정보"""
