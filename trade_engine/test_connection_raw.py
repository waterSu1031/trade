#!/usr/bin/env python
"""
IB Gateway 연결 테스트 - Raw Socket 방식
ib_insync 없이 직접 소켓 연결 테스트
"""

import socket
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

from src.config import config

def test_socket_connection():
    """소켓 레벨에서 IB Gateway 연결 테스트"""
    
    print("=" * 60)
    print(f"IB Gateway Socket 연결 테스트 - {datetime.now()}")
    print("=" * 60)
    
    # 설정 정보
    host = config.IBKR_HOST
    port = config.IBKR_PORT
    client_id = config.IBKR_CLIENT_ID
    
    print(f"\n[연결 정보]")
    print(f"- Host: {host}")
    print(f"- Port: {port} (Paper Trading)")
    print(f"- Client ID: {client_id} (trade_engine)")
    print(f"- Environment: {config.ENV_MODE}")
    print(f"- Environment File: {config.ENV_FILE}")
    
    # 소켓 연결 테스트
    print(f"\n[소켓 연결 테스트]")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # 5초 타임아웃
    
    try:
        print(f"Connecting to {host}:{port}...")
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print("✅ 포트가 열려있습니다! IB Gateway가 실행 중입니다.")
            
            # 간단한 데이터 전송 테스트
            try:
                # IB API 프로토콜의 초기 핸드셰이크 시도
                # API 버전 전송 (간단한 테스트)
                test_msg = b"v100..\0"
                sock.send(test_msg)
                
                # 응답 대기 (1초)
                sock.settimeout(1)
                response = sock.recv(1024)
                if response:
                    print(f"✅ 서버로부터 응답 수신: {len(response)} bytes")
                else:
                    print("⚠️  서버 응답 없음")
            except socket.timeout:
                print("⚠️  서버 응답 타임아웃 (정상일 수 있음)")
            except Exception as e:
                print(f"⚠️  데이터 전송 중 오류: {e}")
                
        else:
            print(f"❌ 연결 실패! 오류 코드: {result}")
            print("\n[문제 해결 가이드]")
            print("1. IB Gateway 또는 TWS가 실행 중인지 확인하세요.")
            print("2. API 연결 설정을 확인하세요:")
            print("   - File > Global Configuration > API > Settings")
            print("   - 'Enable ActiveX and Socket Clients' 체크")
            print("   - 'Socket port' 확인 (Paper: 4002)")
            print("3. 방화벽 설정을 확인하세요.")
            
    except socket.timeout:
        print("❌ 연결 타임아웃!")
        print("IB Gateway가 실행 중이 아니거나 네트워크 문제가 있을 수 있습니다.")
    except socket.error as e:
        print(f"❌ 소켓 오류: {e}")
    finally:
        sock.close()
        print("\n소켓 연결 종료")
    
    # 추가 정보
    print(f"\n[추가 정보]")
    print("- Paper Trading Port: 4002")
    print("- Live Trading Port: 4001")
    print("- Client ID 할당:")
    print("  - trade_batch: 30")
    print("  - trade_engine: 20 (현재)")
    print("  - trade_dashboard: 10")
    
    print("\n" + "=" * 60)


def check_port_availability():
    """여러 포트 확인"""
    print("\n[포트 가용성 확인]")
    ports_to_check = [
        (4001, "Live Trading"),
        (4002, "Paper Trading"),
        (7497, "TWS Paper"),
        (7496, "TWS Live")
    ]
    
    for port, desc in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((config.IBKR_HOST, port))
        if result == 0:
            print(f"✅ Port {port} ({desc}): OPEN")
        else:
            print(f"❌ Port {port} ({desc}): CLOSED")
        sock.close()


if __name__ == "__main__":
    # 메인 연결 테스트
    test_socket_connection()
    
    # 모든 포트 확인
    check_port_availability()