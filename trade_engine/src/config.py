import os, platform
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass

# Load main .env file
load_dotenv()

@dataclass
class Config:

    DATABASE_ACCESS = "Raw SQL"                     # Database Access Paradigm)


    # ▶️ 시스템 환경
    ENV_MODE: str = os.getenv("ENVIRONMENT", "development")

    # # 📁 Base Path 정의
    ROOT_DIR = Path(__file__).resolve().parent.parent  # 프로젝트 루트
    
    # PostgreSQL 연결 설정
    POSTGRES_HOST: str = os.getenv("DB_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("DB_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("DB_NAME", "trade_db")
    POSTGRES_USER: str = os.getenv("DB_USER", "freeksj")
    POSTGRES_PASSWORD: str = os.getenv("DB_PASSWORD", "Lsld1501!")
    
    # PostgreSQL URL 생성
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    # 📁 Infra Path 정의
    STORAGE_DIR = ROOT_DIR / "storage"
    LOGS_DIR = STORAGE_DIR / "storage" / "logs"
    REPORTS_DIR = STORAGE_DIR / "trading_records" / "reports"
    SCREENSHOTS_DIR = STORAGE_DIR / "trading_records" / "screenshots"


    #  mode back/live   real paper/live   broker ibkr/binance
    TRAD_MODE = "back"     # back/live
    TRADE_BROKER = "IBKR"  # IBKR/Binance
    TRADE_REAL = "paper"    # paper/live


    # ▶️ IBKR 접속 정보
    IBKR_HOST: str = os.getenv("IBKR_HOST", "localhost")
    IBKR_PORT: int = int(os.getenv("IBKR_PORT", "4002"))
    IBKR_CLIENT_ID: int = 3  # trade_engine client ID
    IBKR_USERNAME: str = os.getenv("IBKR_USERNAME", "")
    IBKR_PASSWORD: str = os.getenv("IBKR_PASSWORD", "")

    # WEB_HOST: str = os.getenv("WEB_HOST", "localhost")
    # WEB_PORT: int = int(os.getenv("WEB_PORT", 8000))
    #
    # # ▶️ 데이터베이스, Redis 설정
    # SQLITE_URL: str = f"sqlite:///{DATABASE_DIR}"               # SQLite는 파일기반
    # MARIA_HOST: str = os.getenv("MARIA_HOST", "localhost")
    # MARIA_PORT: int = int(os.getenv("MARIA_PORT", 3306))
    # POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    # POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    # # f"redis://localhost:6379/0"
    #
    # REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    # REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    # REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    #
    # # ▶️ 이메일 설정
    # REPORT_EMAIL: str = os.getenv("REPORT_EMAIL", "")
    # EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    # EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    # SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    # SMTP_PORT: int = int(os.getenv("SMTP_PORT", 25))
    #
    # # ▶️ 기타 서비스 예비 슬롯 (확장 가능)
    # USE_WEBSOCKET: bool = os.getenv("USE_WEBSOCKET", "true").lower() == "true"
    # API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", 30))

config = Config()

