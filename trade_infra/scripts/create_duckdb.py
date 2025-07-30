#!/usr/bin/env python3
"""
DuckDB 데이터베이스 생성 스크립트
사용 전 설치 필요: pip install duckdb
"""

import os
import sys

def create_duckdb():
    try:
        import duckdb
        print(f"DuckDB version: {duckdb.__version__}")
    except ImportError:
        print("ERROR: DuckDB is not installed.")
        print("Please install it first:")
        print("  pip install duckdb")
        sys.exit(1)
    
    # DuckDB 파일 경로
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(os.path.dirname(script_dir), 'volumes', 'duckdb')
    db_path = os.path.join(db_dir, 'analyze.duckdb')
    
    # 디렉토리 생성
    os.makedirs(db_dir, exist_ok=True)
    
    print(f"Creating DuckDB database at: {db_path}")
    
    # DuckDB 연결 (파일 자동 생성)
    conn = duckdb.connect(db_path)
    
    # 기본 테이블 생성
    print("Creating initial tables...")
    
    # 분석 결과 저장용 테이블
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY,
            analysis_date DATE DEFAULT CURRENT_DATE,
            symbol VARCHAR,
            metric_name VARCHAR,
            metric_value DECIMAL(20,8),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 백테스트 결과 테이블
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backtest_results (
            id INTEGER PRIMARY KEY,
            strategy_name VARCHAR,
            symbol VARCHAR,
            start_date DATE,
            end_date DATE,
            total_return DECIMAL(10,4),
            sharpe_ratio DECIMAL(10,4),
            max_drawdown DECIMAL(10,4),
            win_rate DECIMAL(5,2),
            parameters JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # PostgreSQL 연결 정보 저장
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pg_connections (
            name VARCHAR PRIMARY KEY,
            connection_string VARCHAR,
            description TEXT
        )
    """)
    
    # 연결 정보 삽입
    conn.execute("""
        INSERT OR REPLACE INTO pg_connections VALUES 
        ('data_db', 'postgresql://freeksj:Lsld1501!@localhost:5432/data_db', 'Market data database'),
        ('trade_db', 'postgresql://freeksj:Lsld1501!@localhost:5432/trade_db', 'Trading dashboard database')
    """)
    
    # 확인
    print("\nCreated tables:")
    tables = conn.execute("SHOW TABLES").fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    
    # 샘플 데이터
    conn.execute("""
        INSERT INTO analysis_results (id, symbol, metric_name, metric_value, description) 
        VALUES 
        (1, 'ES', 'volatility', 0.15, 'Daily volatility'),
        (2, 'NQ', 'correlation', 0.85, 'Correlation with SPY')
    """)
    
    print("\nSample data inserted.")
    
    # 파일 크기 확인
    conn.close()
    file_size = os.path.getsize(db_path)
    print(f"\nDuckDB file created successfully!")
    print(f"File size: {file_size:,} bytes")
    print(f"Location: {db_path}")
    
    # 사용법 출력
    print("\n" + "="*50)
    print("To use this database:")
    print("="*50)
    print("Python:")
    print(f"  import duckdb")
    print(f"  conn = duckdb.connect('{db_path}')")
    print(f"  conn.execute('SELECT * FROM analysis_results').fetchall()")
    print("\nDBeaver:")
    print(f"  Connection type: DuckDB")
    print(f"  Path: {db_path}")

if __name__ == "__main__":
    create_duckdb()