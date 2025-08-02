from pydantic_settings import BaseSettings as PydanticBaseSettings
from typing import Optional
import os


class BaseSettings(PydanticBaseSettings):
    """기본 설정 클래스 - 모든 서비스가 상속"""
    
    # Database
    database_url: str = "postgresql://freeksj:freeksj@localhost:5432/trade"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # IBKR
    ibkr_host: str = "localhost"
    ibkr_port: int = 4002
    ibkr_client_id: int = 1
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False