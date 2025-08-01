#!/usr/bin/env python3
"""
Connection test script for Trade Dashboard
Tests database and IBKR connections
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.config import settings
from app.database.database import engine
from app.services.ibkr_service import ibkr_service
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test PostgreSQL database connection"""
    print("\n=== Testing Database Connection ===")
    print(f"Database URL: postgresql://{settings.db_user}:****@{settings.db_host}:{settings.db_port}/{settings.db_name}")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ Database connected successfully")
            print(f"  PostgreSQL version: {version}")
            
            # Test if we can create tables
            conn.execute(text("SELECT 1"))
            print(f"✓ Database is responsive")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


async def test_ibkr_connection():
    """Test IBKR Gateway connection"""
    print("\n=== Testing IBKR Connection ===")
    print(f"IBKR Host: {settings.ib_host}")
    print(f"IBKR Port: {settings.ib_port}")
    print(f"Client ID: {settings.ib_client_id}")
    
    try:
        connected = await ibkr_service.connect()
        if connected:
            print("✓ IBKR Gateway connected successfully")
            
            # Test getting account summary
            try:
                summary = await ibkr_service.get_account_summary()
                if summary:
                    print("✓ Successfully retrieved account summary")
                    # Print some account info (but not sensitive data)
                    if 'AccountType' in summary:
                        print(f"  Account Type: {summary['AccountType']['value']}")
            except Exception as e:
                print(f"⚠ Could not retrieve account summary: {e}")
            
            await ibkr_service.disconnect()
            return True
        else:
            print("✗ IBKR Gateway connection failed")
            print("  Please ensure:")
            print("  1. IB Gateway or TWS is running")
            print("  2. API connections are enabled")
            print("  3. Port 4002 (dev) or 4001 (prod) is correct")
            return False
    except Exception as e:
        print(f"✗ IBKR connection error: {e}")
        return False


def check_environment():
    """Check environment configuration"""
    print("\n=== Environment Configuration ===")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Backend Port: {settings.api_port}")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file found")
    else:
        print("⚠ .env file not found, using defaults")


async def main():
    """Run all connection tests"""
    print("Trade Dashboard Connection Test")
    print("==============================")
    
    check_environment()
    
    # Test database
    db_ok = test_database_connection()
    
    # Test IBKR
    ibkr_ok = await test_ibkr_connection()
    
    print("\n=== Summary ===")
    print(f"Database: {'✓ OK' if db_ok else '✗ Failed'}")
    print(f"IBKR Gateway: {'✓ OK' if ibkr_ok else '✗ Failed'}")
    
    if not db_ok:
        print("\nDatabase troubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify credentials in .env file")
        print("3. Run: docker-compose up -d")
    
    if not ibkr_ok:
        print("\nIBKR troubleshooting:")
        print("1. Start IB Gateway or TWS")
        print("2. Enable API connections in configuration")
        print("3. Check firewall settings for port 4002")
    
    return db_ok and ibkr_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)