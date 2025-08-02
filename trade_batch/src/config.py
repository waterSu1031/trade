import os
from trade_common.config import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """배치 서비스 설정 - trade-common의 BaseSettings를 상속"""
    
    # Batch 전용 설정
    symbol_csv_path: str = "./data/symbols.csv"
    batch_size: int = 100
    cleanup_days: int = 30
    
    # IBKR client ID override for batch
    ibkr_client_id: int = 2


@lru_cache()
def get_settings():
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()