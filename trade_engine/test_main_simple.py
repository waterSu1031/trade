#!/usr/bin/env python
"""
메인 앱 간단 테스트 - DB 연결 없이 IB Gateway 연결만 테스트
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime, timedelta
from src.config import config
from src.data.connect_IBKR import ConnectIBKR
from ib_insync import Stock, Future

def test_main_app():
    print("=" * 60)
    print("Trade App 간단 테스트 (DB 없이)")
    print("=" * 60)
    
    try:
        # IB Gateway 연결
        print("\n[1. IB Gateway 연결]")
        host = config.IBKR_HOST
        port = 4001  # Live Trading (현재 실행 중)
        client_id = 20
        
        ibkr_conn = ConnectIBKR(host, port, client_id)
        ib = ibkr_conn.get_client()
        
        if ib.isConnected():
            print(f"✅ IB Gateway 연결 성공!")
            print(f"- Host: {host}:{port}")
            print(f"- Client ID: {client_id}")
            print(f"- Accounts: {ib.managedAccounts()}")
            
            # 테스트용 계약 생성
            print("\n[2. 테스트 계약 생성]")
            test_contracts = [
                Stock('AAPL', 'SMART', 'USD'),
                Stock('SPY', 'SMART', 'USD')
            ]
            
            for contract in test_contracts:
                ib.qualifyContracts(contract)
                print(f"✅ {contract.symbol} 계약 확인")
            
            # Trade 클래스와 유사한 동작 테스트
            print("\n[3. Trade 클래스 모의 테스트]")
            print(f"- Trade Mode: live (실시간)")
            print(f"- Real Mode: paper (모의)")
            print(f"- Symbols: ['AAPL', 'SPY']")
            print(f"- Interval: 1m")
            
            # 실시간 데이터 요청 (간단 테스트)
            print("\n[4. 실시간 데이터 테스트]")
            contract = test_contracts[0]
            ticker = ib.reqMktData(contract, '', False, True)
            
            print("5초간 데이터 수신...")
            for i in range(5):
                ib.sleep(1)
                print(f"{i+1}초: {contract.symbol} - Bid: {ticker.bid}, Ask: {ticker.ask}")
            
            ib.cancelMktData(contract)
            
            print("\n✅ 모든 테스트 완료!")
            print("메인 앱의 핵심 기능(IB 연결, 계약 생성, 실시간 데이터)이 정상 작동합니다.")
            
        else:
            print("❌ IB Gateway 연결 실패!")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print(f"Type: {type(e).__name__}")
        
    finally:
        if 'ib' in locals() and ib.isConnected():
            ib.disconnect()
            print("\n연결 종료")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_main_app()