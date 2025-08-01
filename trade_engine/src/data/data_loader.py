from typing import List, Dict


from ib_insync import IB, util, Contract, Stock, Future
from src.infra.sqlite.database import get_connection

import pandas as pd
from datetime import datetime

# DB 연결 지연 - 함수 호출시에만 연결
conn_DB_trade = None


def target_symbols(symbols: List[str]) -> List[Contract]:
    # DB 연결 없이 테스트용 데이터 반환
    print(f"[WARNING] DB 연결 없이 테스트용 Contract 생성: {symbols}")
    
    test_contracts = []
    for symbol in symbols:
        if symbol == 'ES':
            # E-mini S&P 500 Futures
            contract = Future(symbol='ES', exchange='GLOBEX', currency='USD')
            contract.conId = 495512566
        elif symbol == 'NQ':
            # E-mini Nasdaq-100 Futures  
            contract = Future(symbol='NQ', exchange='GLOBEX', currency='USD')
            contract.conId = 495512572
        else:
            # 기본값으로 주식 처리
            contract = Stock(symbol=symbol, exchange='SMART', currency='USD')
            contract.conId = 0
        test_contracts.append(contract)
    
    return test_contracts


class IBKRData:
    def __init__(self, ib: IB):
        self.ib = ib
        self.conn = None  # DB 연결 비활성화
        self.data = None

    def database(self, contracts: List[Contract], stt_dt: datetime, end_dt: datetime, interval: str) \
            -> Dict[str, pd.DataFrame]:

        print(f"[WARNING] DB 연결 없이 빈 DataFrame 반환")
        all_data = {}

        for contract in contracts:
            # 빈 DataFrame 생성
            df = pd.DataFrame({
                'timestamp': pd.date_range(stt_dt, end_dt, freq='1min')[:100],
                'open': [100.0] * 100,
                'high': [101.0] * 100,
                'low': [99.0] * 100,
                'close': [100.5] * 100,
                'volume': [10000] * 100
            })
            df["con_id"] = contract.conId
            all_data[contract.symbol] = df

        return all_data

    def download(self, contracts: List[Contract], stt_dt: datetime, end_dt: datetime, interval: str) \
            -> Dict[str, pd.DataFrame]:

        all_data = {}
        interval_str, max_duration = MAX_DURATION_BY_BAR_SIZE[interval]
        delta = parse_duration_str(max_duration)

        for contract in contracts:
            current_end = end_dt
            dfs = []

            while current_end > stt_dt:
                current_start = max(stt_dt, current_end - delta)
                bars = []
                try:
                    bars = self.ib.reqHistoricalData(
                        contract,
                        endDateTime=current_end.strftime("%Y%m%d %H:%M:%S"),
                        durationStr=max_duration,
                        barSizeSetting=interval_str,
                        whatToShow='TRADES',
                        useRTH=False,
                        formatDate=1
                    )
                except Exception as e:
                    print(f"data_loader.download.reqHistoricalData : {e}")
                if bars is None or len(bars) == 0:
                    break

                df = util.df(bars)
                df["symbol"] = contract.symbol
                dfs.append(df)
                current_end = current_start

            if dfs:
                all_data[contract.symbol] = pd.concat(dfs).sort_values("timestamp")

        return all_data

    def stream(self, contracts: List[Contract], callback):
        for contract in contracts:
            try:
                self.ib.qualifyContracts(contract)
                bars = self.ib.reqRealTimeBars(contract, 5, 'TRADES', False)
                df = util.df(bars)
                callback(contract.symbol, contract, df)
            except Exception as e:
                print(f"오류 발생 ({contract.symbol}): {e}")

    def check_market_data_status(self, contracts: List[Contract]):
        error_contracts = []

        for contract in contracts:
            try:
                ticker = self.ib.reqMktData(contract, '', False, False)
                self.ib.sleep(2)
                if ticker.lastError():
                    error_contracts.append(f"{contract.localSymbol or contract.symbol}: {ticker.lastError()}")
            except Exception as e:
                error_contracts.append(f"{contract.localSymbol or contract.symbol}: Exception - {e}")

        if error_contracts:
            print("\n📌 Market Data Issues:")
            print("\n".join(error_contracts))
        else:
            print("✅ All market data requests succeeded.")


MAX_DURATION_BY_BAR_SIZE = {
        "1s": ("1 sec", "1 D"), "5s": ("5 secs", "1 D"), "1m": ("1 min",  "1 W"), "3m": ("3 mins", "1 W"),
        "5m": ("5 mins", "1 M"), "20m": ("20 mins","1 M"), "1h": ("1 hour", "1 M"), "1d": ("1 day",  "1 Y")}


def parse_duration_str(duration: str):
    num, unit = duration.split()
    num = int(num)
    if unit == "D":
        return pd.Timedelta(days=num)
    elif unit == "W":
        return pd.Timedelta(weeks=num)
    elif unit == "M":
        return pd.Timedelta(days=30 * num)
    elif unit == "Y":
        return pd.Timedelta(days=365 * num)
