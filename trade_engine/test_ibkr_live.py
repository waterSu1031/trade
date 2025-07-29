#!/usr/bin/env python
"""
IB Gateway 연결 테스트 - Live Trading (Port 4001)
"""

import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

def test_ibkr_live_connection():
    print("=" * 60)
    print(f"IB Gateway Live Trading 연결 테스트 - {datetime.now()}")
    print("=" * 60)
    
    try:
        from src.data.connect_IBKR import ConnectIBKR
        from src.config import config
        
        # 연결 정보 - Live Trading으로 변경
        host = config.IBKR_HOST
        port = 4001  # Live Trading Port
        client_id = 20  # trade_engine client ID
        
        print(f"\n[연결 정보]")
        print(f"- Host: {host}")
        print(f"- Port: {port} (Live Trading)")
        print(f"- Client ID: {client_id}")
        print(f"- Account: freeksj1031")
        
        # ConnectIBKR 인스턴스 생성
        print(f"\n[연결 시도]")
        ib_conn = ConnectIBKR(host=host, port=port, client_id=client_id)
        
        # 연결
        ib_conn.connect()
        
        # 연결 확인
        if ib_conn.is_connected():
            print("✅ IB Gateway Live Trading 연결 성공!")
            
            # IB 객체 가져오기
            ib = ib_conn.ib
            
            # 기본 정보 확인
            print(f"\n[연결 상태]")
            print(f"- Connected: {ib.isConnected()}")
            print(f"- Client ID: {ib.client.clientId}")
            
            # 계정 정보
            print(f"\n[계정 정보]")
            accounts = ib.managedAccounts()
            print(f"- Managed Accounts: {accounts}")
            
            if accounts:
                account = accounts[0]
                
                # 계정 요약 정보
                account_values = ib.accountValues(account)
                print(f"\n[계정 요약 - {account}]")
                important_tags = ['NetLiquidation', 'TotalCashValue', 'BuyingPower', 'AvailableFunds']
                for av in account_values:
                    if av.tag in important_tags:
                        print(f"- {av.tag}: {av.value} {av.currency}")
                
                # 포지션 확인
                print(f"\n[현재 포지션]")
                positions = ib.positions(account)
                if positions:
                    for pos in positions[:5]:  # 처음 5개만
                        print(f"- {pos.contract.symbol}: {pos.position} @ {pos.avgCost}")
                else:
                    print("- 보유 포지션 없음")
                
                # 미체결 주문 확인
                print(f"\n[미체결 주문]")
                open_orders = ib.openOrders()
                if open_orders:
                    for order in open_orders[:5]:  # 처음 5개만
                        print(f"- Order {order.orderId}: {order.action} {order.totalQuantity} {order.contract.symbol}")
                else:
                    print("- 미체결 주문 없음")
            
            # 시스템 시간 확인
            print(f"\n[시스템 시간]")
            try:
                server_time = ib.reqCurrentTime()
                if isinstance(server_time, datetime):
                    print(f"- Server Time: {server_time}")
                else:
                    print(f"- Server Time: {datetime.fromtimestamp(server_time)}")
                print(f"- Local Time: {datetime.now()}")
            except Exception as e:
                print(f"- 시간 정보 조회 실패: {e}")
            
            print(f"\n✅ Live Trading 연결 테스트 완료!")
            print("⚠️  주의: 실거래 계정에 연결되었습니다!")
            
        else:
            print("❌ 연결 실패!")
            
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        print(f"Error Type: {type(e).__name__}")
        
        print(f"\n[문제 해결 가이드]")
        print("1. IB Gateway가 Live Trading 모드로 실행 중인지 확인")
        print("2. API 연결 설정 확인:")
        print("   - File > Global Configuration > API > Settings")
        print("   - 'Enable ActiveX and Socket Clients' 체크")
        print("   - Socket port: 4001 (Live Trading)")
        print("3. Client ID 20이 이미 사용 중이 아닌지 확인")
        print("4. Live Trading 계정 로그인 상태 확인")
        
    finally:
        try:
            if 'ib_conn' in locals() and ib_conn.is_connected():
                ib_conn.ib.disconnect()
                print("\n연결이 정상적으로 종료되었습니다.")
        except:
            pass
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Live Trading 연결 테스트
    test_ibkr_live_connection()