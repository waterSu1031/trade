#!/usr/bin/env python3
"""
IB Gateway Connection Test for trade_dashboard
Client ID: 10 (assigned for trade_dashboard)
"""
import asyncio
import sys
from datetime import datetime
from ib_insync import IB, util, Contract

# Configuration
IB_HOST = "localhost"  # IB Gateway host
IB_PORT = 4001        # Live trading port
CLIENT_ID = 10        # trade_dashboard client ID

async def test_ib_connection():
    """Test IB Gateway connection and basic functionality"""
    ib = IB()
    
    try:
        print(f"[{datetime.now()}] Attempting to connect to IB Gateway...")
        print(f"Host: {IB_HOST}, Port: {IB_PORT}, Client ID: {CLIENT_ID}")
        
        # Connect to IB Gateway
        await ib.connectAsync(IB_HOST, IB_PORT, clientId=CLIENT_ID)
        
        print(f"[{datetime.now()}] ✓ Successfully connected to IB Gateway!")
        print(f"Connected: {ib.isConnected()}")
        
        # Test 1: Get account information
        print(f"\n[{datetime.now()}] Testing account information...")
        accounts = ib.managedAccounts()
        print(f"✓ Managed Accounts: {accounts}")
        
        if accounts:
            account = accounts[0]
            account_values = ib.accountValues(account)
            print(f"✓ Account Values Retrieved: {len(account_values)} items")
            
            # Show some key account values
            for av in account_values[:5]:
                print(f"  - {av.tag}: {av.value} {av.currency}")
        
        # Test 2: Request market data for a test contract
        print(f"\n[{datetime.now()}] Testing market data request...")
        contract = Contract(
            symbol='EUR',
            secType='CASH',
            exchange='IDEALPRO',
            currency='USD'
        )
        
        # Request market data
        ticker = ib.reqMktData(contract, snapshot=True)
        await asyncio.sleep(2)  # Wait for data
        
        print(f"✓ Market Data for {contract.symbol}{contract.currency}:")
        print(f"  - Bid: {ticker.bid}")
        print(f"  - Ask: {ticker.ask}")
        print(f"  - Last: {ticker.last}")
        
        # Test 3: Check current positions
        print(f"\n[{datetime.now()}] Testing positions retrieval...")
        positions = ib.positions()
        print(f"✓ Current Positions: {len(positions)}")
        
        for pos in positions[:3]:  # Show first 3 positions
            print(f"  - {pos.contract.symbol}: {pos.position} @ {pos.avgCost}")
        
        # Test 4: Check open orders
        print(f"\n[{datetime.now()}] Testing open orders retrieval...")
        orders = ib.openOrders()
        print(f"✓ Open Orders: {len(orders)}")
        
        # Test 5: Historical data request
        print(f"\n[{datetime.now()}] Testing historical data request...")
        bars = await ib.reqHistoricalDataAsync(
            contract,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting='1 hour',
            whatToShow='MIDPOINT',
            useRTH=True
        )
        print(f"✓ Historical Data Retrieved: {len(bars)} bars")
        if bars:
            print(f"  - Latest bar: {bars[-1].date} Close: {bars[-1].close}")
        
        print(f"\n[{datetime.now()}] ✓ All tests completed successfully!")
        print(f"IB Gateway connection is working properly for trade_dashboard (client_id: {CLIENT_ID})")
        
        return True
        
    except Exception as e:
        print(f"\n[{datetime.now()}] ✗ Connection test failed!")
        print(f"Error: {type(e).__name__}: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure IB Gateway or TWS is running")
        print("2. Check if API connections are enabled in IB Gateway/TWS")
        print("3. Verify the port number (4001 for paper, 4002 for live)")
        print("4. Check if another client is using the same client ID")
        print("5. Ensure 'Enable ActiveX and Socket Clients' is checked in API settings")
        return False
        
    finally:
        if ib.isConnected():
            print(f"\n[{datetime.now()}] Disconnecting from IB Gateway...")
            ib.disconnect()
            print(f"[{datetime.now()}] Disconnected.")

def main():
    """Main entry point"""
    print("=" * 60)
    print("IB Gateway Connection Test - trade_dashboard")
    print("=" * 60)
    
    # Run the async test
    util.startLoop()
    success = asyncio.run(test_ib_connection())
    
    print("\n" + "=" * 60)
    if success:
        print("TEST RESULT: SUCCESS ✓")
    else:
        print("TEST RESULT: FAILED ✗")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())