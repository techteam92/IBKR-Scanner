"""
Direct test of historical data request to diagnose the issue
"""
from ibkr_client import IBKRClient
from config import DEFAULT_IBKR_CONFIG
from ib_insync import Stock, util
import time

def test_direct():
    """Test historical data request directly"""
    print("=" * 80)
    print("Direct Historical Data Test")
    print("=" * 80)
    
    client = IBKRClient(
        host=DEFAULT_IBKR_CONFIG.host,
        port=DEFAULT_IBKR_CONFIG.port,
        client_id=DEFAULT_IBKR_CONFIG.client_id
    )
    
    print("\n1. Connecting...")
    if not client.connect_sync():
        print("Connection failed!")
        return
    
    print("✓ Connected")
    
    print("\n2. Testing contract qualification...")
    contract = Stock("AAPL", "SMART", "USD")
    try:
        qualified = client.ib.qualifyContracts(contract)
        if qualified:
            contract = qualified[0]
            print(f"✓ Contract qualified: {contract.symbol} on {contract.exchange}, conId: {contract.conId}")
        else:
            print("✗ Contract not qualified")
            return
    except Exception as e:
        print(f"✗ Error qualifying: {e}")
        return
    
    print("\n3. Requesting historical data...")
    print("   This should block until data arrives...")
    
    try:
        # Request historical data
        # CRITICAL: IBKR requires "5 mins" (plural) not "5 min" (singular)
        # Legal formats per Error 321: "1 secs", "5 secs", "1 min" (singular only!), 
        #                              "2 mins", "5 mins", "10 mins", etc.
        #                              "1 hour" (singular), "2 hours" (plural), etc.
        bars = client.ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr="7 D",
            barSizeSetting="5 mins",  # MUST be "5 mins" not "5 min"
            whatToShow="TRADES",
            useRTH=True,
            formatDate=1
        )
        
        print(f"\n   reqHistoricalData returned: {type(bars)}")
        print(f"   Length: {len(bars) if bars else 0}")
        
        if not bars:
            print("\n   ⚠ No bars returned immediately")
            print("   Checking contract.historicalData...")
            
            # Wait and check
            for i in range(15):
                time.sleep(1)
                if hasattr(contract, 'historicalData') and contract.historicalData:
                    print(f"   ✓ Found data in contract.historicalData after {i+1}s: {len(contract.historicalData)} bars")
                    bars = contract.historicalData
                    break
                if i % 3 == 0:
                    print(f"   Still waiting... ({i+1}s)")
        
        if bars:
            print(f"\n✓ SUCCESS! Got {len(bars)} bars")
            df = util.df(bars)
            print(f"  DataFrame shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Sample:")
            print(df.head())
        else:
            print("\n✗ FAILED: No data received")
            print("\nPossible causes:")
            print("  1. Market data subscription not enabled")
            print("  2. Symbol not subscribed")
            print("  3. Error 162 (IP mismatch) - check TWS/Gateway logs")
            print("  4. Market closed or insufficient permissions")
            
    except Exception as e:
        print(f"\n✗ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n4. Disconnecting...")
        client.disconnect()
        print("✓ Disconnected")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_direct()

