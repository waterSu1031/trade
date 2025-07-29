#!/usr/bin/env python3
"""
Simple synchronous IB connection test
"""
from ib_insync import IB
import time

def test_simple_connection():
    """Test simple IB connection"""
    print("Simple IB Connection Test")
    print("=" * 40)
    
    ib = IB()
    
    # Test different ports
    test_configs = [
        {'host': '127.0.0.1', 'port': 7497, 'clientId': 1, 'desc': 'TWS Paper'},
        {'host': '127.0.0.1', 'port': 7496, 'clientId': 1, 'desc': 'TWS Live'},
        {'host': '127.0.0.1', 'port': 4002, 'clientId': 1, 'desc': 'Gateway Paper'},
        {'host': '127.0.0.1', 'port': 4001, 'clientId': 1, 'desc': 'Gateway Live'},
        {'host': 'localhost', 'port': 7497, 'clientId': 1, 'desc': 'TWS Paper (localhost)'},
    ]
    
    for config in test_configs:
        print(f"\nTrying {config['desc']} - {config['host']}:{config['port']}")
        try:
            ib.connect(
                host=config['host'], 
                port=config['port'], 
                clientId=config['clientId'],
                timeout=5
            )
            print(f"✓ SUCCESS! Connected to {config['desc']}")
            print(f"  Server Version: {ib.client.serverVersion()}")
            print(f"  Connection Time: {ib.client.connTime}")
            
            # Get account info
            accounts = ib.managedAccounts()
            print(f"  Accounts: {accounts}")
            
            # Get positions
            positions = ib.positions()
            print(f"  Positions: {len(positions)}")
            
            ib.disconnect()
            return True
            
        except Exception as e:
            print(f"✗ Failed: {type(e).__name__}: {str(e)[:60]}")
            continue
    
    print("\n" + "="*40)
    print("All connection attempts failed!")
    print("\nMake sure:")
    print("1. IB Gateway or TWS is running and logged in")
    print("2. API connections are enabled in settings")
    print("3. Check the correct port number")
    return False

if __name__ == "__main__":
    test_simple_connection()