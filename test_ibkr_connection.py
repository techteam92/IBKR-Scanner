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
    
    # Set up error collection
    print(f"\n2. Setting up error monitoring...")
    recent_errors = []
    def collect_error(reqId, errorCode, errorString, contract):
        recent_errors.append((errorCode, errorString))
    
    # Subscribe to error events
    client.ib.errorEvent += collect_error
    print("   ✓ Error monitoring ready")
    
    # Test with multiple tickers (try AAPL first as it's most reliable)
    test_tickers = ["AAPL", "TSLA"]
    
    try:
        for test_ticker in test_tickers:
            print(f"\n3. Testing data retrieval for {test_ticker}...")
            
            # Test RTH data
            print(f"   Requesting RTH data (useRTH=True) for {test_ticker}...")
            df_rth = client.get_historical_bars_sync(
                ticker=test_ticker,
                duration="7 D",
                bar_size="5 mins",  # Fixed: IBKR requires "5 mins" (plural) not "5 min"
                use_rth=True
            )
            
            print(f"   RTH DataFrame shape: {df_rth.shape}")
            if not df_rth.empty:
                print(f"   ✓ SUCCESS! Got {len(df_rth)} rows for {test_ticker}")
                print(f"   Columns: {list(df_rth.columns)}")
                print(f"   Date range: {df_rth['date'].min()} to {df_rth['date'].max()}")
                print(f"   Sample data:")
                print(df_rth.head())
                # If this ticker works, no need to test others
                break
            else:
                print(f"   ✗ No RTH data returned for {test_ticker}")
            
            # Test Pre-market data
            print(f"\n   Requesting Pre-market data (useRTH=False) for {test_ticker}...")
            df_pm = client.get_historical_bars_sync(
                ticker=test_ticker,
                duration="12 D",
                bar_size="1 min",
                use_rth=False
            )
            
            print(f"   Pre-market DataFrame shape: {df_pm.shape}")
            if not df_pm.empty:
                print(f"   ✓ SUCCESS! Got {len(df_pm)} rows for {test_ticker}")
                print(f"   Columns: {list(df_pm.columns)}")
                print(f"   Date range: {df_pm['date'].min()} to {df_pm['date'].max()}")
                break
            else:
                print(f"   ✗ No Pre-market data returned for {test_ticker}")
        
        # Check for errors after requests
        print(f"\n   Checking for errors after requests...")
        if recent_errors:
            print(f"   Found {len(recent_errors)} error(s) during test:")
            error_162_found = False
            for errorCode, errorString in recent_errors:
                error_str = f"Error {errorCode}: {errorString}"
                if errorCode == 162 or '162' in str(errorCode) or 'different IP' in str(errorString).lower():
                    error_162_found = True
                    print(f"     ✗ ERROR 162: {errorString}")
                elif errorCode >= 500:  # Warnings
                    print(f"     ⚠ Warning {errorCode}: {errorString}")
                else:
                    print(f"     ✗ {error_str}")
            
            if error_162_found:
                print(f"\n   {'='*70}")
                print(f"   ERROR 162 CONFIRMED!")
                print(f"   {'='*70}")
                print(f"   You MUST restart TWS/Gateway to fix this.")
                print(f"   See SOLUTION_ERROR_162.md for detailed instructions.")
                print(f"   {'='*70}")
        else:
            print("   ⚠ No errors captured")
            print("   If timeouts occur, possible causes:")
            print("     1. Market data subscription not enabled")
            print("     2. Symbol not subscribed (try AAPL)")
            print("     3. Multiple API connections (check other projects)")
            print("     4. Error 162 (IP mismatch)")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect
        print("\n4. Disconnecting...")
        client.disconnect()
        print("   ✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_connection()

