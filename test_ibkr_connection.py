"""
Test script to diagnose IBKR connection and data retrieval issues
"""
from ibkr_client import IBKRClient
from config import DEFAULT_IBKR_CONFIG
import pandas as pd

def test_connection():
    """Test IBKR connection and data retrieval"""
    print("=" * 80)
    print("IBKR Connection Test")
    print("=" * 80)
    print("\nIMPORTANT: If you see Error 162, you MUST:")
    print("  1. Close TWS/Gateway completely")
    print("  2. Close this test script")
    print("  3. Restart TWS/Gateway and LOG IN")
    print("  4. Wait for full connection (all green)")
    print("  5. Then run this test again")
    print("=" * 80 + "\n")
    
    # Create client
    client = IBKRClient(
        host=DEFAULT_IBKR_CONFIG.host,
        port=DEFAULT_IBKR_CONFIG.port,
        client_id=DEFAULT_IBKR_CONFIG.client_id
    )
    
    # Connect
    print("\n1. Connecting to IBKR...")
    if client.connect_sync():
        print("   ✓ Connected successfully")
    else:
        print("   ✗ Failed to connect")
        print("   Make sure TWS or IB Gateway is running")
        print(f"   Expected port: {DEFAULT_IBKR_CONFIG.port}")
        return
    
    # Test with a well-known ticker
    test_ticker = "AAPL"
    print(f"\n2. Testing data retrieval for {test_ticker}...")
    
    try:
        # Test RTH data
        print("   Requesting RTH data (useRTH=True)...")
        df_rth = client.get_historical_bars_sync(
            ticker=test_ticker,
            duration="12 D",
            bar_size="1 min",
            use_rth=True
        )
        
        print(f"   RTH DataFrame shape: {df_rth.shape}")
        if not df_rth.empty:
            print(f"   Columns: {list(df_rth.columns)}")
            print(f"   Date range: {df_rth['date'].min()} to {df_rth['date'].max()}")
            print(f"   Sample data:")
            print(df_rth.head())
        else:
            print("   ✗ No RTH data returned")
        
        # Test Pre-market data
        print("\n   Requesting Pre-market data (useRTH=False)...")
        df_pm = client.get_historical_bars_sync(
            ticker=test_ticker,
            duration="12 D",
            bar_size="1 min",
            use_rth=False
        )
        
        print(f"   Pre-market DataFrame shape: {df_pm.shape}")
        if not df_pm.empty:
            print(f"   Columns: {list(df_pm.columns)}")
            print(f"   Date range: {df_pm['date'].min()} to {df_pm['date'].max()}")
        else:
            print("   ✗ No Pre-market data returned")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect
        print("\n3. Disconnecting...")
        client.disconnect()
        print("   ✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_connection()

