import sys
sys.path.append('/home/freeksj/Workspace_Rule/trade')

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
from common.config import CommonSettings

# Database engine configuration
if settings.database_url.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration with standardized settings
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        **CommonSettings.get_sqlalchemy_config()
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()