# DuckDB Analytics Database Guide

## 개요
DuckDB는 분석용 임베디드 데이터베이스입니다. Docker 대신 로컬 파일로 사용합니다.

## 설치

```bash
# Python에서 사용하려면
pip install duckdb

# CLI 도구 (선택사항)
# https://duckdb.org/docs/installation 참고
```

## 파일 위치
- DuckDB 데이터베이스: `/trade_infra/volumes/duckdb/analyze.duckdb`
- 초기화 스크립트: `/trade_infra/scripts/init_duckdb.py`

## 사용 예시

### 1. Python에서 기본 사용
```python
import duckdb

# 데이터베이스 연결
conn = duckdb.connect('trade_infra/volumes/duckdb/analyze.duckdb')

# 테이블 생성
conn.execute("""
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY,
        symbol VARCHAR,
        analysis_date DATE,
        metric_name VARCHAR,
        metric_value DECIMAL
    )
""")

# 데이터 삽입
conn.execute("""
    INSERT INTO analysis_results VALUES 
    (1, 'ES', '2024-01-30', 'sharpe_ratio', 1.25),
    (2, 'NQ', '2024-01-30', 'max_drawdown', -0.15)
""")

# 조회
result = conn.execute("SELECT * FROM analysis_results").fetchall()
print(result)
```

### 2. PostgreSQL 데이터 연동
```python
import duckdb

conn = duckdb.connect('trade_infra/volumes/duckdb/analyze.duckdb')

# PostgreSQL 연결 설정
conn.execute("""
    INSTALL postgres_scanner;
    LOAD postgres_scanner;
    
    -- data_db 연결
    CALL postgres_attach(
        'postgresql://freeksj:Lsld1501!@localhost:5432/data_db',
        source_schema='public',
        sink_schema='data_db'
    );
    
    -- trade_db 연결
    CALL postgres_attach(
        'postgresql://freeksj:Lsld1501!@localhost:5432/trade_db',
        source_schema='public',
        sink_schema='trade_db'
    );
""")

# 이제 PostgreSQL 테이블 직접 조회 가능
# data_db의 price_time 테이블 조회
result = conn.execute("""
    SELECT 
        symbol,
        COUNT(*) as record_count,
        MIN(time) as first_record,
        MAX(time) as last_record
    FROM data_db.price_time
    GROUP BY symbol
""").fetchall()
```

### 3. 분석 예시
```python
# 복잡한 분석 쿼리
conn.execute("""
    -- 일별 수익률 계산
    CREATE TABLE daily_returns AS
    SELECT 
        symbol,
        DATE(time) as trading_date,
        FIRST(open) as day_open,
        LAST(close) as day_close,
        (LAST(close) - FIRST(open)) / FIRST(open) * 100 as daily_return_pct,
        SUM(volume) as total_volume
    FROM data_db.price_time
    GROUP BY symbol, DATE(time)
    ORDER BY symbol, trading_date;
    
    -- 통계 요약
    SELECT 
        symbol,
        AVG(daily_return_pct) as avg_daily_return,
        STDDEV(daily_return_pct) as volatility,
        AVG(daily_return_pct) / STDDEV(daily_return_pct) * SQRT(252) as sharpe_ratio
    FROM daily_returns
    GROUP BY symbol;
""")
```

### 4. 데이터 내보내기
```python
# Parquet 형식으로 내보내기
conn.execute("""
    COPY daily_returns 
    TO 'trade_infra/volumes/duckdb/exports/daily_returns.parquet' 
    (FORMAT PARQUET)
""")

# CSV로 내보내기
conn.execute("""
    COPY (SELECT * FROM analysis_results) 
    TO 'trade_infra/volumes/duckdb/exports/analysis.csv' 
    (HEADER, DELIMITER ',')
""")
```

## DBeaver 연결
1. Connection Type: DuckDB
2. Path: 절대 경로 입력
   `/home/freeksj/Workspace_Rule/trade/trade_infra/volumes/duckdb/analyze.duckdb`
3. 연결 후 사용

## 주의사항
- DuckDB 파일은 단일 프로세스 접근만 가능 (동시 쓰기 불가)
- 읽기는 여러 프로세스에서 가능
- 파일 크기가 커질 수 있으므로 주기적 정리 필요

## 디렉토리 권한
만약 권한 문제가 있다면:
```bash
sudo chown -R $USER:$USER trade_infra/volumes/duckdb
chmod 755 trade_infra/volumes/duckdb
```