import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
import psycopg2
from src.config import config

# from src.db.sqlite.model.asset import stock_table_sql, futures_table_sql, cash_table_sql

from src.infra.sqlite.model.info_ddl import exchange_table_sql, exc_x_sym_table_sql, symbol_table_sql, sym_x_data_table_sql
from src.infra.sqlite.model.info_ddl import insert_exchange

# 공통 경로
if config.DATABASE_ACCESS == "ORM":
    # print("🔵 SQLAlchemy ORM 모드 활성화")
    engine = create_engine(config.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base = declarative_base()

    def get_session():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

elif config.DATABASE_ACCESS == "Raw SQL":
    # print("🟢 Raw SQL 방식 활성화")

    def get_connection(sel_db=None):
        # PostgreSQL 단일 데이터베이스 TRADE 사용
        return psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            database=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD
        )

elif config.DATABASE_ACCESS == "Query Builder":
    pass
    # print("🟢 Query Builder 방식 활성화")


def create_trade_tables():
    conn_trade = get_connection()
    cursor = conn_trade.cursor()
    # for sql in [stock_table_sql, futures_table_sql, cash_table_sql]:
    #     cursor.execute(sql)
    for sql in [exchange_table_sql, exc_x_sym_table_sql, symbol_table_sql, sym_x_data_table_sql]:
        cursor.execute(sql)
    for sql in [insert_exchange]:
        cursor.execute(sql)
    
    conn_trade.commit()
    conn_trade.close()
    print("✅ PostgreSQL DB 테이블 생성 완료")


def create_data_tables():
    conn_trade = get_connection()
    cursor = conn_trade.cursor()
    cursor.execute("""
        SELECT symbol, con_id, database, interval as interval_str
        FROM sym_x_data
        WHERE is_active = 'Y'
    """)
    rows = cursor.fetchall()
    
    for symbol, con_id, database, interval_str in rows:
        print(f"처리 중: {symbol}")
        
        # intervals = [x.strip() for x in interval_str.split(",") if x.strip()]
        intervals = [x.strip() for x in (interval_str or "").split(",") if x.strip()]
        for interval in intervals:
            try:
                table_name = f"{symbol}_{interval}".replace("-", "_").replace(".", "_")
                ddl = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    timestamp TIMESTAMP NOT NULL,     -- 각 캔들의 시작 시간
                    idx INTEGER DEFAULT 0 NOT NULL,   -- 레인지 바일 경우 순번 또는 범위 구분용
                    open DOUBLE PRECISION,
                    high DOUBLE PRECISION,
                    low DOUBLE PRECISION,
                    close DOUBLE PRECISION,
                    volume DOUBLE PRECISION,
                    PRIMARY KEY (timestamp, idx)       -- 데이터 중복 방지
                );
                """
                cursor.execute(ddl)
                conn_trade.commit()
            except Exception as e:
                print(f"오류 발생 ({symbol}_{interval}): {e}")

            print(f"✅ 생성됨: TRADE.{table_name}")
    
    conn_trade.close()


if __name__ == "__main__":
    create_trade_tables()
    create_data_tables()
