from typing import Dict
from src.order.broker_IBKR import BrokerIBKR

def generate_report(broker: BrokerIBKR, starting_cash: float = 100_000) -> Dict:
    """
    모의 브로커로부터 실행 결과 요약 리포트 생성

    :param broker: MockBroker 인스턴스
    :param starting_cash: 초기 자본금
    :return: 리포트 딕셔너리
    """
    account = broker.get_account_info()
    orders = broker.orders.values()

    final_cash = account.get("cash", 0)
    positions = account.get("positions", {})
    total_equity = account.get("total_equity", 0)

    num_trades = sum(1 for o in orders if o.get("status") == "filled")
    gross_return = (total_equity - starting_cash) / starting_cash * 100

    # 최대 낙폭 계산 (optional)
    balance_over_time = simulate_balance_curve(broker, starting_cash)
    max_drawdown = calculate_max_drawdown(balance_over_time)

    return {
        "시작 자산": f"{starting_cash:,.2f} USD",
        "최종 잔고": f"{final_cash:,.2f} USD",
        "총 자산": f"{total_equity:,.2f} USD",
        "총 거래 수": num_trades,
        "총 수익률": f"{gross_return:.2f}%",
        "최대 낙폭": f"{max_drawdown:.2f}%",
        "최종 포지션": positions
    }

def simulate_balance_curve(broker: MockBroker, starting_cash: float):
    """
    체결된 주문 순서대로 가상의 잔고 흐름 생성
    """
    balance = starting_cash
    balances = []
    for o in sorted(broker.orders.values(), key=lambda x: x['timestamp']):
        if o['status'] == 'filled':
            side = o['side']
            qty = o['quantity']
            price = o['price']
            cost = qty * price
            if side == 'buy':
                balance -= cost
            else:
                balance += cost
            balances.append(balance)
    return balances

def calculate_max_drawdown(balances) -> float:
    """
    잔고 시계열에서 최대 낙폭 계산 (%)
    """
    if not balances:
        return 0.0
    peak = balances[0]
    max_dd = 0.0
    for b in balances:
        if b > peak:
            peak = b
        dd = (peak - b) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd * 100
