#!/usr/bin/env python3
"""
Test script to verify IBKR and Database connections
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database.database import engine, SessionLocal, Base
from app.services.ibkr_service import IBKRService
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test database connection"""
    print("\n" + "="*50)
    print("Testing Database Connection")
    print("="*50)
    
    try:
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✓ Database connection successful")
            print(f"  Database URL: {settings.database_url}")
            
        # Test session creation
        with SessionLocal() as session:
            # Try to query tables
            result = session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = result.fetchall()
            print(f"✓ Database session creation successful")
            print(f"  Tables found: {len(tables)}")
            for table in tables:
                print(f"    - {table[0]}")
                
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


async def test_ibkr_connection():
    """Test IBKR API connection"""
    print("\n" + "="*50)
    print("Testing IBKR Connection")
    print("="*50)
    
    print(f"Configuration:")
    print(f"  Host: {settings.ib_host}")
    print(f"  Port: {settings.ib_port}")
    print(f"  Client ID: {settings.ib_client_id}")
    
    ibkr_service = IBKRService()
    
    try:
        # Test connection
        connected = await ibkr_service.connect()
        
        if connected:
            print(f"✓ IBKR connection successful")
            
            # Test account summary
            print("\nFetching account information...")
            account_summary = await ibkr_service.get_account_summary()
            
            if account_summary:
                print(f"✓ Account data retrieved successfully")
                # Print some key account values
                important_fields = ['TotalCashValue', 'NetLiquidation', 'BuyingPower']
                for field in important_fields:
                    if field in account_summary:
                        print(f"    {field}: {account_summary[field]}")
            else:
                print(f"⚠ No account data received")
                
            # Test positions
            print("\nFetching positions...")
            positions = await ibkr_service.get_positions()
            if positions is not None:
                print(f"✓ Positions retrieved: {len(positions)} position(s)")
                for pos in positions[:3]:  # Show first 3 positions
                    print(f"    - {pos.contract.symbol}: {pos.position} @ ${pos.avgCost}")
            else:
                print(f"⚠ No positions data received")
                
            # Disconnect
            await ibkr_service.disconnect()
            print(f"\n✓ IBKR disconnection successful")
            
            return True
            
        else:
            print(f"✗ IBKR connection failed")
            print(f"\nTroubleshooting tips:")
            print(f"  1. Make sure TWS or IB Gateway is running")
            print(f"  2. Enable API connections in TWS/Gateway settings")
            print(f"  3. Check the port number (4002 for paper, 4001 for live)")
            print(f"  4. Verify 'Enable ActiveX and Socket Clients' is checked")
            print(f"  5. Add 127.0.0.1 to trusted IPs in API settings")
            return False
            
    except Exception as e:
        print(f"✗ IBKR connection error: {e}")
        print(f"\nError details: {type(e).__name__}")
        return False


async def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "="*50)
    print("Testing API Endpoints")
    print("="*50)
    
    import httpx
    
    base_url = f"http://localhost:{settings.api_port}"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print(f"✓ Health endpoint: {response.json()}")
            else:
                print(f"✗ Health endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Cannot connect to API server: {e}")
            print(f"  Make sure the server is running with: uvicorn app.main:app --reload")
            return False
            
        # Test WebSocket status
        try:
            response = await client.get(f"{base_url}/api/ws/status")
            if response.status_code == 200:
                print(f"✓ WebSocket status: {response.json()}")
            else:
                print(f"✗ WebSocket status failed: {response.status_code}")
        except Exception as e:
            print(f"✗ WebSocket status error: {e}")
            
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("Trade Dashboard Connection Tests")
    print("="*50)
    
    # Test database
    db_ok = test_database_connection()
    
    # Test IBKR
    ibkr_ok = await test_ibkr_connection()
    
    # Test API (optional - only if server is running)
    print("\n" + "="*50)
    print("Optional: API Server Test")
    print("="*50)
    print("To test API endpoints, start the server first:")
    print("  uvicorn app.main:app --reload")
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    print(f"Database Connection: {'✓ PASS' if db_ok else '✗ FAIL'}")
    print(f"IBKR Connection: {'✓ PASS' if ibkr_ok else '✗ FAIL'}")
    
    if not ibkr_ok:
        print("\nIBKR Connection Requirements:")
        print("1. TWS or IB Gateway must be running")
        print("2. API connections must be enabled in settings")
        print("3. Socket port must match configuration (4001 for live, 4002 for paper trading)")
        print("4. 'Read-Only API' should be unchecked for full functionality")


if __name__ == "__main__":
    asyncio.run(main())