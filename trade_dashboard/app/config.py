import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # IBKR Configuration
    ib_host: str = os.getenv("IBKR_HOST", "localhost")
    ib_port: int = int(os.getenv("IBKR_PORT", "4002"))
    ib_client_id: int = 2  # trade_dashboard client ID
    ib_username: Optional[str] = os.getenv("IBKR_USERNAME")
    ib_password: Optional[str] = os.getenv("IBKR_PASSWORD")
    
    # Database Configuration
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "trade_db")
    db_user: str = os.getenv("DB_USER", "freeksj")
    db_password: str = os.getenv("DB_PASSWORD", "Lsld1501!")
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("DASHBOARD_PORT", "8000"))
    PORT: int = api_port  # alias for compatibility
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev_secret_key")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev_jwt_secret")
    
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # WebSocket settings
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()