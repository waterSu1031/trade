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
    # 이제 개별 테이블을 생성하지 않고 price_US_time 테이블을 사용
    # 필요한 경우 파티션 테이블 생성만 수행
    conn_trade = get_connection()
    cursor = conn_trade.cursor()
    
    # price_US_time 테이블이 이미 schema.sql에서 생성되므로 별도 작업 불필요
    print("✅ 가격 데이터는 price_US_time 테이블에 저장됩니다.")
    
    conn_trade.close()


if __name__ == "__main__":
    create_trade_tables()
    create_data_tables()
