# Test comment for monorepo structure verification - engine project
import sys
sys.path.append('/home/freeksj/Workspace_Rule/trade')

from datetime import datetime, timedelta
from typing import List
from src.data.data_loader import IBKRData, target_symbols
from src.config import config
from ib_insync import IB, util, Contract
from src.data.connect_IBKR import ConnectIBKR
from src.order.runner import Runner
from src.strategies.example1_strategy import Example1Strategy
from src.order.order_manager import OrderManager
from src.order.broker_IBKR import BrokerIBKR
from common.logging import setup_logging, LogEvents

logger = setup_logging('trade_engine')


class Trade:
    def __init__(self):
        self.trade_mode = 'live'
        self.real_mode = 'paper'
        self.end_dt = datetime.now()
        self.stt_dt = self.end_dt - timedelta(days=7)
        self.interval = '1m'
        self.symbols = ['ES', 'NQ']
        self.strategy_name = "ExampleStrategy"

        self.host = config.IBKR_HOST
        self.port = config.IBKR_PORT
        self.client_id = config.IBKR_CLIENT_ID
        self.ibkr_conn = ConnectIBKR(self.host, self.port, self.client_id)
        self.ib = self.ibkr_conn.get_client()

        self.broker = BrokerIBKR(self.ib)
        self.order_manager = None

    def reload(self, symbols: List[str], trade_mode: str, real_mode: str,
               stt_dt: datetime, end_dt: datetime, strategy: str):
        self.symbols = symbols
        self.trade_mode = trade_mode
        self.real_mode = real_mode
        self.stt_dt = stt_dt
        self.end_dt = end_dt
        self.strategy_name = strategy
        self.port = config.IBKR_PORT
        self.client_id = config.IBKR_CLIENT_ID
        self.ibkr_conn = ConnectIBKR(self.host, self.port, self.client_id)
        self.ib = self.ibkr_conn.get_client()
        self.broker = BrokerIBKR(self.ib)
        self.run()

    def run(self):
        ibkr_data = IBKRData(self.ib)
        contracts = target_symbols(self.symbols)
        self.broker = BrokerIBKR(self.ib)
        # OrderManager 개발 중이므로 주석 처리 유지
        # self.order_manager = OrderManager(self.broker)

        if self.trade_mode == "back":
            return self.run_back_test(ibkr_data, contracts)
        elif self.trade_mode == "live":
            return self.run_live_trade(ibkr_data, contracts)

        self.ib.run()

    def run_back_test(self, ibkr_data: IBKRData, contracts: List[Contract]):
        print(f"[Backtest] {self.symbols} | {self.stt_dt} ~ {self.end_dt} | interval: {self.interval}")
        prices = ibkr_data.download(contracts, self.stt_dt, self.end_dt, self.interval)

        results = {}
        for symbol, df in prices.items():
            strategy = Example1Strategy(df["close"], direction="both")
            strategy.run()
            runner = Runner(strategy)
            entries, exits, direction = runner.run_back_signal()
            back_pf = runner.analyze_portfolio(entries, exits, direction)

            print(f"[{symbol}] Backtest 결과:")
            print(back_pf.stats())
            results[symbol] = back_pf

        print(f"[Backtest] End")
        return results

    def run_live_trade(self, ibkr_data: IBKRData, contracts: List[Contract]):
        print(f"[Live] {self.symbols} | {self.stt_dt} ~ {self.end_dt} | interval: {self.interval}")
        prices = ibkr_data.database(contracts, self.stt_dt, self.end_dt, self.interval)

        runners = {}
        for symbol, df in prices.items():
            strategy = Example1Strategy(df["close"], direction="both")
            strategy.run()
            runner = Runner(strategy)
            runners[symbol] = {"strategy": strategy, "runner": runner}

        print("[LIVE MODE] 실시간 데이터 수신 시작...")

        def on_stream(item_symbol, item_contract, item_df):
            print('... ')
            last_bar = item_df.iloc[-1]
            price_series = item_df["close"].iloc[-1:]

            item_runner = runners[item_symbol]["runner"]
            entries, exits, direction = item_runner.run_live_signal(price_series)

            # '외부에서 요청이 있을시'
            # live_pf = runner.analyze_portfolio(entries, exits, direction)

            signal = ""
            if entries.iloc[-1]:
                signal = "buy"
            elif exits.iloc[-1]:
                signal = "sell"
            else:
                signal = "hold"

            if signal in ("buy", "sell"):
                # OrderManager가 아직 개발되지 않았으므로 시그널만 출력
                print(f"[{item_symbol}] {signal.upper()} SIGNAL 발생 (주문 처리 스킵 - OrderManager 미구현)")

        ibkr_data.stream(contracts, on_stream)
        print(f"[Live] End")
        return runners


tradeApp = Trade()

if __name__ == "__main__":
    tradeApp.run()
