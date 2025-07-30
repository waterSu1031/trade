#!/usr/bin/env python3
"""
DuckDB 초기화 스크립트
analyze.duckdb 파일을 생성하고 PostgreSQL 연결 설정
"""

import duckdb
import os

# DuckDB 파일 경로
db_path = os.path.join(os.path.dirname(__file__), '../volumes/duckdb/analyze.duckdb')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# DuckDB 연결
print(f"Creating DuckDB at: {db_path}")
conn = duckdb.connect(db_path)

# PostgreSQL 연결 설정
print("Setting up PostgreSQL connection...")
conn.execute("""
    -- PostgreSQL Scanner 설치
    INSTALL postgres_scanner;
    LOAD postgres_scanner;
""")

# 연결 정보 저장 (실제 사용 시 연결)
conn.execute("""
    -- 연결 예시 (실제 사용 시 활성화)
    -- CALL postgres_attach(
    --     'postgresql://freeksj:Lsld1501!@localhost:5432/data_db',
    --     source_schema='public',
    --     sink_schema='data'
    -- );
    
    -- 테스트 테이블 생성
    CREATE TABLE IF NOT EXISTS test_data (
        id INTEGER PRIMARY KEY,
        name VARCHAR,
        value DECIMAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 샘플 데이터 삽입
    INSERT INTO test_data (id, name, value) VALUES 
        (1, 'test1', 100.50),
        (2, 'test2', 200.75),
        (3, 'test3', 300.25);
    
    -- 분석용 뷰 생성
    CREATE VIEW IF NOT EXISTS v_summary AS
    SELECT 
        COUNT(*) as total_count,
        SUM(value) as total_value,
        AVG(value) as avg_value
    FROM test_data;
""")

# 연결 정보 확인
print("\nDuckDB tables:")
tables = conn.execute("SHOW TABLES").fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\nDuckDB views:")
views = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'VIEW'").fetchall()
for view in views:
    print(f"  - {view[0]}")

# 테스트 쿼리
print("\nTest query result:")
result = conn.execute("SELECT * FROM v_summary").fetchone()
print(f"  Total count: {result[0]}")
print(f"  Total value: {result[1]}")
print(f"  Average value: {result[2]}")

conn.close()
print("\nDuckDB initialization completed!")
print(f"Database file created at: {db_path}")
print("\nTo use in Python:")
print("  import duckdb")
print(f"  conn = duckdb.connect('{db_path}')")
print("\nTo connect to PostgreSQL:")
print("  conn.execute(\"CALL postgres_attach('postgresql://freeksj:Lsld1501!@localhost:5432/data_db')\")")