#!/usr/bin/env python
"""
IB Gateway 연결 테스트 - Live Trading (Port 4001)
3분간 연결 유지 및 상태 모니터링
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

def test_ibkr_live_connection_3min():
    print("=" * 60)
    print(f"IB Gateway Live Trading 연결 테스트 (3분 유지) - {datetime.now()}")
    print("=" * 60)
    
    ib_conn = None
    
    try:
        from src.data.connect_IBKR import ConnectIBKR
        from src.config import config
        from ib_insync import Stock, Forex
        
        # 연결 정보 - Live Trading
        host = config.IBKR_HOST
        port = 4001  # Live Trading Port
        client_id = 20  # trade_engine client ID
        
        print(f"\n[연결 정보]")
        print(f"- Host: {host}")
        print(f"- Port: {port} (Live Trading)")
        print(f"- Client ID: {client_id}")
        print(f"- Account: freeksj1031")
        
        # ConnectIBKR 인스턴스 생성 및 연결
        print(f"\n[연결 시도]")
        ib_conn = ConnectIBKR(host=host, port=port, client_id=client_id)
        ib_conn.connect()
        
        if ib_conn.is_connected():
            print("✅ IB Gateway Live Trading 연결 성공!")
            print("⚠️  주의: 실거래 계정에 연결되었습니다!")
            
            ib = ib_conn.ib
            
            # 초기 계정 정보
            print(f"\n[초기 연결 상태]")
            print(f"- Connected: {ib.isConnected()}")
            print(f"- Client ID: {ib.client.clientId}")
            accounts = ib.managedAccounts()
            print(f"- Managed Accounts: {accounts}")
            
            # 3분 연결 유지 시작
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=3)
            
            print(f"\n[3분간 연결 유지 시작]")
            print(f"- 시작 시간: {start_time.strftime('%H:%M:%S')}")
            print(f"- 종료 예정: {end_time.strftime('%H:%M:%S')}")
            print("\n매 30초마다 상태를 확인합니다...")
            
            # 실시간 데이터 구독 (SPY)
            contract = Stock('SPY', 'SMART', 'USD')
            ib.qualifyContracts(contract)
            ticker = ib.reqMktData(contract, '', False, True)  # True로 변경하여 delayed data 사용
            
            check_count = 0
            while datetime.now() < end_time:
                check_count += 1
                elapsed = datetime.now() - start_time
                remaining = end_time - datetime.now()
                
                print(f"\n[상태 확인 #{check_count}] - 경과: {elapsed.seconds}초, 남은 시간: {remaining.seconds}초")
                
                # 연결 상태 확인
                if ib.isConnected():
                    print("✅ 연결 상태: 정상")
                    
                    # 계정 정보 조회
                    if accounts:
                        account = accounts[0]
                        account_values = ib.accountValues(account)
                        for av in account_values:
                            if av.tag == 'NetLiquidation':
                                print(f"- 순자산: {av.value} {av.currency}")
                                break
                    
                    # 실시간 시장 데이터
                    print(f"- SPY 실시간: Bid={ticker.bid}, Ask={ticker.ask}, Last={ticker.last}")
                    
                    # 서버 시간
                    try:
                        server_time = ib.reqCurrentTime()
                        print(f"- 서버 시간: {server_time}")
                    except:
                        pass
                else:
                    print("❌ 연결이 끊어졌습니다!")
                    break
                
                # 30초 대기 (마지막 체크가 아닌 경우)
                if datetime.now() < end_time:
                    time.sleep(30)
            
            # 데이터 구독 취소
            ib.cancelMktData(contract)
            
            # 최종 상태
            print(f"\n[3분 연결 유지 완료]")
            print(f"- 총 경과 시간: {(datetime.now() - start_time).seconds}초")
            print(f"- 최종 연결 상태: {'연결됨' if ib.isConnected() else '연결 끊김'}")
            
            if ib.isConnected():
                # 최종 계정 정보
                print(f"\n[최종 계정 정보]")
                if accounts:
                    account = accounts[0]
                    account_values = ib.accountValues(account)
                    important_tags = ['NetLiquidation', 'TotalCashValue', 'BuyingPower', 'AvailableFunds']
                    for av in account_values:
                        if av.tag in important_tags:
                            print(f"- {av.tag}: {av.value} {av.currency}")
                
                # 포지션 확인
                positions = ib.positions(account)
                if positions:
                    print(f"\n[보유 포지션]")
                    for pos in positions:
                        print(f"- {pos.contract.symbol}: {pos.position} @ {pos.avgCost}")
                
                print("\n✅ 3분간 연결이 안정적으로 유지되었습니다!")
            
        else:
            print("❌ 초기 연결 실패!")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print(f"Error Type: {type(e).__name__}")
        
    finally:
        if ib_conn and ib_conn.is_connected():
            ib_conn.ib.disconnect()
            print("\n연결이 정상적으로 종료되었습니다.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_ibkr_live_connection_3min()