#!/usr/bin/env python3
"""
Simple synchronous IB Gateway connection test
"""
from ib_insync import IB, util
import sys

def test_connection():
    """Test basic IB Gateway connection"""
    ib = IB()
    
    # Try different ports
    ports = [4002, 4001, 7497, 7496]  # Paper and Live ports for both IB Gateway and TWS
    
    for port in ports:
        print(f"\nTrying port {port}...")
        try:
            ib.connect('localhost', port, clientId=10, timeout=5)
            print(f"✓ Successfully connected on port {port}!")
            print(f"Server Version: {ib.serverVersion()}")
            print(f"Connection Time: {ib.connectionTime()}")
            
            # Get account info
            accounts = ib.managedAccounts()
            print(f"Managed Accounts: {accounts}")
            
            ib.disconnect()
            return True
            
        except Exception as e:
            print(f"✗ Failed on port {port}: {type(e).__name__}: {e}")
            continue
    
    print("\n✗ Could not connect to IB Gateway on any port.")
    print("\nPlease ensure:")
    print("1. IB Gateway or TWS is running on your PC")
    print("2. API connections are enabled (File -> Global Configuration -> API -> Settings)")
    print("3. 'Enable ActiveX and Socket Clients' is checked")
    print("4. 'Read-Only API' is unchecked if you need trading capabilities")
    print("5. Socket port is set (default: 7497 for TWS paper, 7496 for TWS live, 4002 for Gateway paper, 4001 for Gateway live)")
    
    return False

if __name__ == "__main__":
    util.startLoop()
    success = test_connection()
    sys.exit(0 if success else 1)