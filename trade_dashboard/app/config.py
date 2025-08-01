import os
import sys
sys.path.append('/home/freeksj/Workspace_Rule/trade')

from pydantic_settings import BaseSettings
from typing import Optional
from common.config import CommonSettings

class Settings(BaseSettings):
    # IBKR Configuration
    ib_host: str = CommonSettings.IBKR_HOST
    ib_port: int = CommonSettings.IBKR_PORT
    ib_client_id: int = CommonSettings.get_client_id('trade_dashboard')
    ib_username: Optional[str] = os.getenv("IBKR_USERNAME")
    ib_password: Optional[str] = os.getenv("IBKR_PASSWORD")
    
    # Database Configuration
    db_host: str = CommonSettings.DB_HOST
    db_port: int = CommonSettings.DB_PORT
    db_name: str = CommonSettings.DB_NAME
    db_user: str = CommonSettings.DB_USER
    db_password: str = CommonSettings.DB_PASSWORD
    
    @property
    def database_url(self) -> str:
        return CommonSettings.get_database_url()
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    PORT: int = api_port  # alias for compatibility
    
    # Environment
    environment: str = CommonSettings.ENVIRONMENT
    debug: bool = not CommonSettings.IS_PRODUCTION
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev_secret_key")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev_jwt_secret")
    
    # Redis Configuration
    redis_host: str = CommonSettings.REDIS_HOST
    redis_port: int = CommonSettings.REDIS_PORT
    redis_db: int = CommonSettings.REDIS_DB
    redis_password: Optional[str] = CommonSettings.REDIS_PASSWORD
    
    # WebSocket settings
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100
    
    # Logging
    LOG_LEVEL: str = CommonSettings.LOG_LEVEL
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()