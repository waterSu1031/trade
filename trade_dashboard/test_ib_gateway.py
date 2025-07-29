#!/usr/bin/env python3
"""
Detailed IB Gateway connection test script
Tests various connection scenarios and provides debugging information
"""
import asyncio
import sys
import socket
import time
from ib_insync import IB, util
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Also enable ib_insync debug logging
util.logToConsole(logging.DEBUG)


def check_port_open(host, port):
    """Check if a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


async def test_basic_connection():
    """Test basic IB Gateway connection"""
    print("\n" + "="*60)
    print("IB Gateway Connection Test")
    print("="*60)
    
    # Connection parameters
    host = '127.0.0.1'
    ports_to_try = [
        (7497, "Paper Trading (TWS)"),
        (7496, "Live Trading (TWS)"),
        (4002, "Paper Trading (IB Gateway)"),
        (4001, "Live Trading (IB Gateway)")
    ]
    
    # First check which ports are open
    print("\n1. Checking open ports:")
    open_ports = []
    for port, description in ports_to_try:
        if check_port_open(host, port):
            print(f"   ✓ Port {port} ({description}) is OPEN")
            open_ports.append((port, description))
        else:
            print(f"   ✗ Port {port} ({description}) is CLOSED")
    
    if not open_ports:
        print("\n❌ No IB API ports are open!")
        print("\nPlease ensure:")
        print("1. IB Gateway or TWS is running")
        print("2. API connections are enabled in Configuration")
        print("3. Socket port is correctly configured")
        return False
    
    # Try to connect to each open port
    print("\n2. Attempting connections to open ports:")
    
    for port, description in open_ports:
        print(f"\n   Trying port {port} ({description})...")
        ib = IB()
        
        try:
            # Try different client IDs
            for client_id in [1, 0, 999]:
                print(f"   → Client ID {client_id}: ", end="", flush=True)
                
                try:
                    await ib.connectAsync(
                        host=host,
                        port=port,
                        clientId=client_id,
                        timeout=10
                    )
                    
                    print("✓ Connected!")
                    
                    # Test the connection
                    print("\n3. Testing connection functionality:")
                    
                    # Get server version
                    print(f"   → Server Version: {ib.client.serverVersion()}")
                    print(f"   → Connection Time: {ib.client.connTime}")
                    
                    # Request current time
                    server_time = ib.reqCurrentTime()
                    if server_time:
                        print(f"   → Server Time: {server_time}")
                    
                    # Get accounts
                    accounts = ib.managedAccounts()
                    if accounts:
                        print(f"   → Managed Accounts: {accounts}")
                    
                    # Test account summary
                    print("\n4. Requesting account summary...")
                    account_summary = ib.accountSummary()
                    if account_summary:
                        print(f"   → Received {len(account_summary)} account values")
                        
                        # Show some key values
                        important_tags = ['NetLiquidation', 'TotalCashValue', 'BuyingPower']
                        for tag in important_tags:
                            values = [av for av in account_summary if av.tag == tag]
                            if values:
                                print(f"     • {tag}: {values[0].value} {values[0].currency}")
                    
                    # Test positions
                    print("\n5. Requesting positions...")
                    positions = ib.positions()
                    print(f"   → Found {len(positions)} position(s)")
                    for pos in positions[:3]:  # Show first 3
                        print(f"     • {pos.contract.symbol}: {pos.position} @ ${pos.avgCost:.2f}")
                    
                    # Test orders
                    print("\n6. Requesting open orders...")
                    orders = ib.openOrders()
                    print(f"   → Found {len(orders)} open order(s)")
                    
                    print("\n✅ Connection test SUCCESSFUL!")
                    print(f"\nConnection details:")
                    print(f"  Host: {host}")
                    print(f"  Port: {port} ({description})")
                    print(f"  Client ID: {client_id}")
                    
                    # Disconnect
                    ib.disconnect()
                    return True
                    
                except asyncio.TimeoutError:
                    print("✗ Timeout")
                except ConnectionRefusedError:
                    print("✗ Connection refused")
                except Exception as e:
                    print(f"✗ Error: {type(e).__name__}: {str(e)[:50]}")
                
                # Small delay between attempts
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"\n   ❌ Failed to connect: {type(e).__name__}: {e}")
        finally:
            if ib.isConnected():
                ib.disconnect()
    
    return False


async def test_advanced_features():
    """Test advanced IB Gateway features"""
    print("\n" + "="*60)
    print("Advanced Feature Tests")
    print("="*60)
    
    ib = IB()
    
    # Use the working connection from basic test
    try:
        # Try to connect with default settings first
        await ib.connectAsync('127.0.0.1', 7497, clientId=1)
        
        print("\n1. Testing market data capabilities:")
        
        # Create a simple stock contract
        from ib_insync import Stock
        aapl = Stock('AAPL', 'SMART', 'USD')
        
        # Qualify the contract
        contracts = await ib.qualifyContractsAsync(aapl)
        if contracts:
            print(f"   ✓ Contract qualified: {contracts[0]}")
            
            # Request market data
            ticker = ib.reqMktData(contracts[0], snapshot=True)
            await asyncio.sleep(2)  # Wait for data
            
            if ticker.last:
                print(f"   ✓ Market data received: Last=${ticker.last}, Bid=${ticker.bid}, Ask=${ticker.ask}")
            else:
                print(f"   ⚠ No market data received (might need subscriptions)")
        
        print("\n2. Testing historical data:")
        try:
            bars = await ib.reqHistoricalDataAsync(
                contracts[0],
                endDateTime='',
                durationStr='1 D',
                barSizeSetting='1 hour',
                whatToShow='TRADES',
                useRTH=True
            )
            if bars:
                print(f"   ✓ Historical data received: {len(bars)} bars")
                print(f"     Last bar: {bars[-1].date} - Close: ${bars[-1].close}")
        except Exception as e:
            print(f"   ⚠ Historical data error: {e}")
        
        ib.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Advanced test failed: {e}")
        if ib.isConnected():
            ib.disconnect()
        return False


async def main():
    """Run all tests"""
    print("\nIB Gateway/TWS Connection Test Suite")
    print("Testing ib_insync connection...")
    
    # Run basic connection test
    basic_ok = await test_basic_connection()
    
    if basic_ok:
        # Run advanced tests only if basic connection works
        await test_advanced_features()
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    if not basic_ok:
        print("\n❌ Connection FAILED")
        print("\nTroubleshooting steps:")
        print("1. Ensure IB Gateway or TWS is running")
        print("2. In IB Gateway/TWS go to: Configure → Settings → API → Settings")
        print("3. Enable 'Enable ActiveX and Socket Clients'")
        print("4. Verify Socket port (default: 7497 for paper, 7496 for live)")
        print("5. Add 127.0.0.1 to 'Trusted IPs' (or check 'Allow connections from localhost only')")
        print("6. Uncheck 'Read-Only API' if you need trading capabilities")
        print("7. For IB Gateway, ensure you're logged in and it shows 'Connected'")
        print("8. Check Windows Firewall isn't blocking the connection")
    else:
        print("\n✅ Connection test PASSED!")
        print("\nYour IB Gateway/TWS is properly configured for API access.")


if __name__ == "__main__":
    asyncio.run(main())