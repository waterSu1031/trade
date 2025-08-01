#!/usr/bin/env python3
"""
데이터베이스 연결 및 테이블 구조 호환성 테스트
"""
import sys
from sqlalchemy import create_engine, text
import pandas as pd
from src.config import Config

def test_database_connection():
    """데이터베이스 연결 테스트"""
    config = Config()
    
    print("=== 데이터베이스 연결 테스트 ===")
    print(f"DB URL: {config.DATABASE_URL}")
    
    try:
        # PostgreSQL 연결 테스트 (trade_db)
        pg_url = "postgresql://freeksj:Lsld1501!@localhost:5432/trade_db"
        pg_engine = create_engine(pg_url)
        
        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            print(f"✓ PostgreSQL 연결 성공: {result.scalar()}")
            
            # 테이블 목록 확인
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """
            tables = pd.read_sql(tables_query, conn)
            print(f"\n테이블 목록 ({len(tables)} 개):")
            for table in tables['table_name']:
                print(f"  - {table}")
                
    except Exception as e:
        print(f"✗ PostgreSQL 연결 실패: {e}")
        return False
        
    # DuckDB 연결 테스트 (analyze_db)
    try:
        duckdb_path = "/home/freeksj/Workspace_Rule/trade/trade_infra/analyze_db.duckdb"
        duckdb_url = f"duckdb:///{duckdb_path}"
        duckdb_engine = create_engine(duckdb_url)
        
        with duckdb_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            print(f"\n✓ DuckDB 연결 성공: {result.scalar()}")
            
    except Exception as e:
        print(f"✗ DuckDB 연결 실패: {e}")
    
    return True

def test_table_compatibility():
    """테이블 구조 호환성 검사"""
    print("\n=== 테이블 구조 호환성 검사 ===")
    
    pg_url = "postgresql://freeksj:Lsld1501!@localhost:5432/trade_db"
    engine = create_engine(pg_url)
    
    # 코드에서 기대하는 테이블들
    expected_tables = {
        'trades': ['id', 'symbol', 'side', 'price', 'quantity', 'timestamp'],
        'positions': ['symbol', 'quantity', 'avg_price', 'current_price'],
        'accounts': ['account_id', 'balance', 'equity', 'buying_power'],
        'trade_events': ['execId', 'orderId', 'time', 'symbol', 'side', 'shares', 'price'],
        'orders': ['orderId', 'symbol', 'action', 'orderType', 'totalQuantity'],
        'contracts': ['conId', 'symbol', 'secType', 'exchange', 'currency']
    }
    
    with engine.connect() as conn:
        for table_name, expected_cols in expected_tables.items():
            try:
                # 테이블 컬럼 조회
                col_query = f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """
                columns = pd.read_sql(col_query, conn)
                
                if len(columns) == 0:
                    print(f"\n✗ {table_name}: 테이블이 존재하지 않음")
                else:
                    print(f"\n✓ {table_name}: 테이블 존재 ({len(columns)} 컬럼)")
                    
                    # 주요 컬럼 확인
                    existing_cols = columns['column_name'].tolist()
                    for col in expected_cols:
                        if col in existing_cols:
                            print(f"  ✓ {col}")
                        else:
                            print(f"  ✗ {col} (누락)")
                            
            except Exception as e:
                print(f"\n✗ {table_name}: 조회 실패 - {e}")

def test_sample_queries():
    """실제 쿼리 테스트"""
    print("\n=== 샘플 쿼리 테스트 ===")
    
    pg_url = "postgresql://freeksj:Lsld1501!@localhost:5432/trade_db"
    engine = create_engine(pg_url)
    
    test_queries = [
        ("최근 거래 조회", "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 5"),
        ("포지션 조회", "SELECT * FROM positions WHERE quantity != 0"),
        ("계좌 정보 조회", "SELECT * FROM accounts"),
        ("거래 이벤트 조회", "SELECT * FROM trade_events ORDER BY time DESC LIMIT 5")
    ]
    
    with engine.connect() as conn:
        for query_name, query in test_queries:
            try:
                df = pd.read_sql(query, conn)
                print(f"\n✓ {query_name}: 성공 ({len(df)} 행)")
                if len(df) > 0:
                    print(f"  컬럼: {', '.join(df.columns)}")
            except Exception as e:
                print(f"\n✗ {query_name}: 실패 - {str(e)[:100]}")

if __name__ == "__main__":
    print("trade_engine 데이터베이스 호환성 테스트")
    print("=" * 50)
    
    if test_database_connection():
        test_table_compatibility()
        test_sample_queries()
    
    print("\n테스트 완료!")