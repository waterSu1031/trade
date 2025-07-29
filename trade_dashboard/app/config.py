from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # IBKR Configuration
    ib_host: str = "127.0.0.1"
    ib_port: int = 4002  # IB Gateway port (4001: live, 4002: paper)
    ib_client_id: int = 10  # trade_dashboard client ID
    
    # Database Configuration
    database_url: str = "postgresql://trade_user:trade_password@localhost:5432/trade_dashboard"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()