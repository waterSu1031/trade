import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # IBKR Configuration - from environment variables
    ib_host: str = os.getenv("IB_HOST", "localhost")
    ib_port: int = int(os.getenv("IB_PORT", "4002"))
    ib_client_id: int = int(os.getenv("IB_CLIENT_ID_DASHBOARD", "10"))
    ib_username: Optional[str] = os.getenv("IB_USERNAME")
    ib_password: Optional[str] = os.getenv("IB_PASSWORD")
    
    # Database Configuration
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "trade_db")
    db_user: str = os.getenv("DB_USER", "trade_user")
    db_password: str = os.getenv("DB_PASSWORD", "trade_password")
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev_secret_key")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev_jwt_secret")
    
    class Config:
        env_file = ".env"

settings = Settings()