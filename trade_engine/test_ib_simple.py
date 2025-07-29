#!/usr/bin/env python
"""
간단한 IB Gateway 연결 테스트
기존 프로젝트의 연결 방식 사용
"""

import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

try:
    from src.config import config
    from src.data.connect_IBKR import IBConnection
    
    print("=" * 60)
    print(f"IB Gateway 연결 테스트 - {datetime.now()}")
    print("=" * 60)
    
    # 설정 정보 출력
    print(f"\n[설정 정보]")
    print(f"- Host: {config.IBKR_HOST}")
    print(f"- Port: {config.IBKR_PORT}")
    print(f"- Client ID: {config.IBKR_CLIENT_ID}")
    print(f"- Trade Mode: {config.TRADE_REAL}")
    print(f"- Environment: {config.ENV_MODE}")
    
    # IBConnection 클래스를 사용한 연결 테스트
    print(f"\n[연결 시도]")
    ib_conn = IBConnection()
    
    if hasattr(ib_conn, 'ib'):
        print("✅ IBConnection 객체 생성 성공")
        
        # 연결 시도
        result = ib_conn.connect(
            host=config.IBKR_HOST,
            port=config.IBKR_PORT,
            clientId=config.IBKR_CLIENT_ID
        )
        
        if result:
            print("✅ IB Gateway 연결 성공!")
        else:
            print("❌ IB Gateway 연결 실패!")
    else:
        print("❌ IBConnection 객체 생성 실패")
        
except ImportError as e:
    print(f"Import Error: {e}")
    print("\n다른 방법으로 테스트를 시도합니다...")
    
    # Trade 클래스를 직접 사용
    try:
        from src.trade import Trade
        
        print("\n[Trade 클래스 사용 테스트]")
        trade_app = Trade()
        
        if hasattr(trade_app, 'ib') and trade_app.ib:
            if trade_app.ib.isConnected():
                print("✅ Trade 클래스를 통한 연결 성공!")
                print(f"- Connected: {trade_app.ib.isConnected()}")
                print(f"- Client ID: {trade_app.ib.client.clientId}")
                
                # 계정 정보
                accounts = trade_app.ib.managedAccounts()
                print(f"- Managed Accounts: {accounts}")
                
                trade_app.ib.disconnect()
                print("\n연결이 정상적으로 종료되었습니다.")
            else:
                print("❌ Trade 클래스를 통한 연결 실패")
        else:
            print("❌ Trade 객체에 IB 연결이 없습니다")
            
    except Exception as e2:
        print(f"Trade 클래스 테스트도 실패: {e2}")
        
except Exception as e:
    print(f"예상치 못한 오류: {e}")
    print(f"Error Type: {type(e).__name__}")

print("\n" + "=" * 60)