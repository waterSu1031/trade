#!/usr/bin/env python
"""
IB Gateway 연결 테스트 스크립트
trade_engine 프로젝트의 client_id: 20 사용
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

from ib_insync import IB, util
from src.config import config


def test_ib_connection():
    """IB Gateway 연결 테스트"""
    
    print("=" * 60)
    print(f"IB Gateway 연결 테스트 시작 - {datetime.now()}")
    print("=" * 60)
    
    # 설정 정보 출력
    print(f"\n[설정 정보]")
    print(f"- Host: {config.IBKR_HOST}")
    print(f"- Port: {config.IBKR_PORT}")
    print(f"- Client ID: {config.IBKR_CLIENT_ID}")
    print(f"- Trade Mode: {config.TRADE_REAL}")
    print(f"- Environment: {config.ENV_MODE}")
    print(f"- Environment File: {config.ENV_FILE}")
    
    # IB 객체 생성
    ib = IB()
    
    try:
        print(f"\n[연결 시도]")
        print(f"Connecting to {config.IBKR_HOST}:{config.IBKR_PORT} with client_id={config.IBKR_CLIENT_ID}...")
        
        # 연결 시도
        ib.connect(
            host=config.IBKR_HOST,
            port=config.IBKR_PORT,
            clientId=config.IBKR_CLIENT_ID,
            timeout=10
        )
        
        # 연결 성공
        print(f"\n✅ 연결 성공!")
        
        # 연결 상태 확인
        print(f"\n[연결 상태]")
        print(f"- Connected: {ib.isConnected()}")
        print(f"- Client ID: {ib.client.clientId}")
        print(f"- Server Version: {ib.client.serverVersion()}")
        print(f"- Connection Time: {ib.client.connTime}")
        
        # 계정 정보 조회
        print(f"\n[계정 정보]")
        accounts = ib.managedAccounts()
        print(f"- Managed Accounts: {accounts}")
        
        if accounts:
            # 첫 번째 계정의 요약 정보 조회
            account = accounts[0]
            account_summary = ib.accountSummary(account)
            
            print(f"\n[계정 요약 - {account}]")
            for item in account_summary[:5]:  # 처음 5개만 표시
                print(f"- {item.tag}: {item.value} {item.currency}")
        
        # 포지션 조회
        print(f"\n[현재 포지션]")
        positions = ib.positions()
        if positions:
            for pos in positions[:3]:  # 처음 3개만 표시
                print(f"- {pos.contract.symbol}: {pos.position} @ {pos.avgCost}")
        else:
            print("- 보유 포지션 없음")
        
        # 주문 조회
        print(f"\n[활성 주문]")
        orders = ib.orders()
        if orders:
            for order in orders[:3]:  # 처음 3개만 표시
                print(f"- Order ID: {order.orderId}, Symbol: {order.contract.symbol}, Action: {order.action}")
        else:
            print("- 활성 주문 없음")
        
        # 시스템 시간 확인
        print(f"\n[시스템 시간]")
        server_time = ib.reqCurrentTime()
        print(f"- IB Server Time: {datetime.fromtimestamp(server_time)}")
        print(f"- Local Time: {datetime.now()}")
        
        print(f"\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 연결 실패!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        print(f"\n[문제 해결 가이드]")
        print("1. IB Gateway 또는 TWS가 실행 중인지 확인하세요.")
        print("2. API 연결이 활성화되어 있는지 확인하세요:")
        print("   - TWS/Gateway > File > Global Configuration > API > Settings")
        print("   - 'Enable ActiveX and Socket Clients' 체크")
        print("   - 'Socket port' 확인 (Paper: 4002, Live: 4001)")
        print(f"3. Client ID {config.IBKR_CLIENT_ID}가 이미 사용 중이 아닌지 확인하세요.")
        print("4. 방화벽이 연결을 차단하지 않는지 확인하세요.")
        
    finally:
        # 연결 종료
        if ib.isConnected():
            print(f"\n[연결 종료]")
            ib.disconnect()
            print("- 연결이 정상적으로 종료되었습니다.")
    
    print("\n" + "=" * 60)


def test_data_streaming():
    """실시간 데이터 스트리밍 테스트"""
    
    print("\n" + "=" * 60)
    print("실시간 데이터 스트리밍 테스트")
    print("=" * 60)
    
    ib = IB()
    
    try:
        # 연결
        ib.connect(
            host=config.IBKR_HOST,
            port=config.IBKR_PORT,
            clientId=config.IBKR_CLIENT_ID
        )
        
        # 테스트용 계약 생성 (SPY ETF)
        from ib_insync import Stock
        contract = Stock('SPY', 'SMART', 'USD')
        
        print(f"\n[계약 상세 정보 조회]")
        ib.qualifyContracts(contract)
        print(f"- Symbol: {contract.symbol}")
        print(f"- Exchange: {contract.exchange}")
        print(f"- Currency: {contract.currency}")
        
        # 실시간 데이터 요청
        print(f"\n[실시간 시장 데이터 요청]")
        ticker = ib.reqMktData(contract, '', False, False)
        
        # 5초간 데이터 수신
        print("5초간 데이터 수신 중...")
        for i in range(5):
            ib.sleep(1)
            print(f"\n시간: {i+1}초")
            print(f"- Bid: {ticker.bid}")
            print(f"- Ask: {ticker.ask}")
            print(f"- Last: {ticker.last}")
            print(f"- Volume: {ticker.volume}")
        
        # 데이터 구독 취소
        ib.cancelMktData(contract)
        print("\n✅ 실시간 데이터 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 실시간 데이터 테스트 실패!")
        print(f"Error: {str(e)}")
    
    finally:
        if ib.isConnected():
            ib.disconnect()


if __name__ == "__main__":
    # 기본 연결 테스트
    test_ib_connection()
    
    # 실시간 데이터 테스트 (선택사항)
    user_input = input("\n실시간 데이터 스트리밍도 테스트하시겠습니까? (y/N): ")
    if user_input.lower() == 'y':
        test_data_streaming()
    
    print("\n테스트 완료!")