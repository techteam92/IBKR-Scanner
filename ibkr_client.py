"""
IBKR API client for fetching historical bar data
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from ib_insync import IB, Stock, util
import nest_asyncio

nest_asyncio.apply()


class IBKRClient:
    """Client for interacting with Interactive Brokers API"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        """
        Initialize IBKR client
        
        Args:
            host: IBKR host (default: 127.0.0.1 for local TWS/Gateway)
            port: IBKR port (7497 for TWS, 4001 for IB Gateway)
            client_id: Unique client ID
        """
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connected = False
        
        # Set up error handler to capture Error 162
        self.ib.errorEvent += self._on_error
    
    def _on_error(self, reqId, errorCode, errorString, contract):
        """Handle IBKR errors"""
        if errorCode == 162:
            print(f"\n{'='*80}")
            print(f"ERROR 162 DETECTED!")
            print(f"{'='*80}")
            print(f"Error Code: {errorCode}")
            print(f"Error Message: {errorString}")
            print(f"\nThis means:")
            print(f"  - Your TWS/Gateway login and API connection are from different IPs")
            print(f"  - IBKR blocks historical data requests for security")
            print(f"\nSOLUTION:")
            print(f"  1. Close TWS/Gateway completely")
            print(f"  2. Close this application")
            print(f"  3. Restart TWS/Gateway and LOG IN")
            print(f"  4. Wait for TWS to fully connect (all green)")
            print(f"  5. Then restart this application and connect")
            print(f"{'='*80}\n")
        elif errorCode >= 500:  # Warning codes
            print(f"  ⚠ IBKR Warning {errorCode}: {errorString}")
        else:
            print(f"  ✗ IBKR Error {errorCode}: {errorString}")
    
    async def connect(self) -> bool:
        """Connect to IBKR"""
        try:
            await self.ib.connectAsync(
                host=self.host,
                port=self.port,
                clientId=self.client_id
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    def connect_sync(self) -> bool:
        """Synchronous wrapper for connect"""
        try:
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
    
    def get_contract(self, ticker: str, exchange: str = "SMART") -> Stock:
        """
        Get IBKR contract for a ticker
        
        Args:
            ticker: Stock ticker symbol
            exchange: Exchange (default: SMART)
        
        Returns:
            Stock contract object
        """
        contract = Stock(ticker, exchange, "USD")
        # Qualify the contract to ensure it's valid
        try:
            qualified = self.ib.qualifyContracts(contract)
            if qualified:
                return qualified[0]
            else:
                print(f"Warning: Could not qualify contract for {ticker}")
                return contract
        except Exception as e:
            print(f"Warning: Error qualifying contract for {ticker}: {e}")
            return contract
    
    async def get_historical_bars(
        self,
        ticker: str,
        duration: str,
        bar_size: str = "1 min",
        use_rth: bool = True,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch historical bar data
        
        Args:
            ticker: Stock ticker symbol
            duration: Duration string (e.g., "10 D" for 10 days)
            bar_size: Bar size (default: "1 min")
            use_rth: Use regular trading hours only (True) or include pre/post market (False)
            end_time: End time for historical data (default: now)
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        contract = self.get_contract(ticker)
        
        # Request historical data
        bars = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime=end_time,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=use_rth,
            formatDate=1
        )
        
        if not bars:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = util.df(bars)
        if df.empty:
            return df
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def get_historical_bars_sync(
        self,
        ticker: str,
        duration: str,
        bar_size: str = "1 min",
        use_rth: bool = True,
        end_time: Optional[datetime] = None,
        timeout: int = 15
    ) -> pd.DataFrame:
        """Synchronous wrapper for get_historical_bars with timeout"""
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        import threading
        import time
        
        bars_result = [None]  # Use list to allow modification in nested function
        error_occurred = [False]
        error_message = [None]
        
        def request_data():
            try:
                contract = self.get_contract(ticker)
                print(f"Requesting historical data for {ticker}: duration={duration}, bar_size={bar_size}, useRTH={use_rth}")
                
                # Check for Error 162 before requesting
                initial_errors = len(self.ib.errorEvent)
                
                bars = self.ib.reqHistoricalData(
                    contract,
                    endDateTime=end_time,
                    durationStr=duration,
                    barSizeSetting=bar_size,
                    whatToShow="TRADES",
                    useRTH=use_rth,
                    formatDate=1
                )
                
                # Check for new errors (like Error 162)
                if len(self.ib.errorEvent) > initial_errors:
                    for error in self.ib.errorEvent[initial_errors:]:
                        error_str = str(error)
                        if '162' in error_str or 'different IP address' in error_str:
                            error_occurred[0] = True
                            error_message[0] = "Error 162: IP mismatch - Restart TWS/Gateway and reconnect"
                            print(f"  ✗ ERROR 162 detected for {ticker}")
                            print(f"  → TWS session and API are from different IP addresses")
                            print(f"  → SOLUTION: Close everything, restart TWS/Gateway, then reconnect")
                            bars_result[0] = []
                            return
                
                # Wait a bit for data if empty
                if not bars:
                    time.sleep(2)
                    if hasattr(contract, 'historicalData') and contract.historicalData:
                        bars = contract.historicalData
                
                bars_result[0] = bars if bars else []
                
            except Exception as e:
                error_occurred[0] = True
                error_message[0] = str(e)
                print(f"  ✗ Exception during reqHistoricalData for {ticker}: {e}")
                bars_result[0] = []
        
        # Run request in thread with timeout
        request_thread = threading.Thread(target=request_data, daemon=True)
        request_thread.start()
        request_thread.join(timeout=timeout)
        
        if request_thread.is_alive():
            print(f"  ⚠ Timeout ({timeout}s) waiting for data for {ticker}")
            print(f"  This usually means Error 162 (IP mismatch) or no data subscription")
            return pd.DataFrame()
        
        if error_occurred[0]:
            print(f"  ✗ Error requesting data for {ticker}: {error_message[0]}")
            return pd.DataFrame()
        
        bars = bars_result[0]
        
        if not bars:
            print(f"  ✗ No bars returned for {ticker}")
            print(f"  Common causes:")
            print(f"    - Error 162: IP mismatch (restart TWS/Gateway)")
            print(f"    - No market data subscription")
            print(f"    - Market closed or no historical data")
            return pd.DataFrame()
        
        print(f"  ✓ Received {len(bars)} bars for {ticker}")
        
        # Convert to DataFrame
        try:
            df = util.df(bars)
            if df.empty:
                print(f"  ⚠ DataFrame is empty for {ticker}")
                return df
            
            print(f"  ✓ DataFrame shape: {df.shape}, columns: {list(df.columns)}")
            
            # Ensure date column is datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif 'time' in df.columns:
                df['date'] = pd.to_datetime(df['time'])
                df = df.rename(columns={'time': 'date'})
            
            # Check if volume column exists
            if 'volume' not in df.columns:
                print(f"  ⚠ No 'volume' column found. Available columns: {list(df.columns)}")
                # Try common alternatives
                if 'Volume' in df.columns:
                    df['volume'] = df['Volume']
                elif 'vol' in df.columns:
                    df['volume'] = df['vol']
                else:
                    print(f"  ✗ Cannot find volume column for {ticker}")
                    return pd.DataFrame()
            
            return df
            
        except Exception as e:
            print(f"  ✗ Error processing data for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

