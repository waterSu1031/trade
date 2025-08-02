import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://freeksj:freeksj@localhost:5432/trade"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # IBKR
    ibkr_host: str = "localhost"
    ibkr_port: int = 4002
    ibkr_client_id: int = 2
    
    # Environment
    environment: str = "development"
    log_level: str = "DEBUG"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()