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
            # Get local IP info for diagnostic
            try:
                import socket
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
            except:
                local_ip = "Unknown"
            
            print(f"\n{'='*80}")
            print(f"ERROR 162 DETECTED!")
            print(f"{'='*80}")
            print(f"Error Code: {errorCode}")
            print(f"Error Message: {errorString}")
            print(f"\nIP Address Information:")
            print(f"  Local IP: {local_ip}")
            print(f"  Connection IP: 127.0.0.1 (localhost)")
            print(f"  TWS/Gateway should be on: 127.0.0.1")
            print(f"\nThis means:")
            print(f"  - Your TWS/Gateway login and API connection are from different IPs")
            print(f"  - IBKR blocks historical data requests for security")
            print(f"\nSOLUTION:")
            print(f"  1. Close TWS/Gateway completely")
            print(f"  2. Close this application")
            print(f"  3. Restart TWS/Gateway and LOG IN")
            print(f"  4. Wait for TWS to fully connect (all green)")
            print(f"  5. Then restart this application and connect")
            print(f"\nRun 'python check_ip_addresses.py' for detailed IP diagnostics")
            print(f"{'='*80}\n")
        elif errorCode == 321:
            # Error 321: Read-Only mode - not critical, just informational
            print(f"  ℹ️  IBKR Info {errorCode}: {errorString} (Read-Only mode is normal)")
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
            print(f"Attempting to connect to {self.host}:{self.port}...")
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id
            )
            self.connected = True
            return True
        except ConnectionRefusedError as e:
            print(f"\n{'='*70}")
            print(f"CONNECTION REFUSED!")
            print(f"{'='*70}")
            print(f"TWS/Gateway is not accepting connections on port {self.port}")
            print(f"\nSOLUTION:")
            print(f"1. Make sure TWS or IB Gateway is RUNNING")
            print(f"2. TWS → Configure → API → Settings")
            print(f"3. ✅ Enable 'Enable ActiveX and Socket Clients'")
            print(f"4. Set 'Socket port' to {self.port}")
            print(f"5. Click OK and RESTART TWS/Gateway")
            print(f"6. Make sure you're LOGGED IN to TWS/Gateway")
            print(f"\nIf using IB Gateway, port should be 4001 (paper) or 4002 (live)")
            print(f"If using TWS, port should be 7497 (paper) or 7496 (live)")
            print(f"{'='*70}\n")
            self.connected = False
            return False
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"CONNECTION FAILED!")
            print(f"{'='*70}")
            print(f"Error: {e}")
            print(f"\nCheck:")
            print(f"1. TWS/Gateway is running")
            print(f"2. API is enabled in TWS/Gateway settings")
            print(f"3. Port {self.port} is correct")
            print(f"4. Firewall is not blocking")
            print(f"{'='*70}\n")
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
        bar_size: str = "5 mins",  # IBKR requires "mins" not "min"
        use_rth: bool = True,
        end_time: Optional[datetime] = None,
        timeout: int = 60  # Increased to 60 seconds for "1 min" data (12 days = ~6000+ bars, takes longer)
    ) -> pd.DataFrame:
        """
        Synchronous wrapper for get_historical_bars.
        
        CRITICAL: ib_insync requires the event loop to run in the main thread.
        Calling reqHistoricalData() from a thread doesn't work because the event loop
        isn't running in that thread. So we call it directly from the main thread.
        """
        print(f"Connected: {self.connected}")
        if not self.connected:
            print("Not connected to IBKR")
            raise ConnectionError("Not connected to IBKR")
        
        import time
        import sys
        
        try:
            print(f"\n  {'='*70}")
            print(f"  Requesting historical data for {ticker}")
            print(f"  {'='*70}")
            print(f"  Parameters:")
            print(f"    duration: {duration}")
            print(f"    bar_size: {bar_size}")
            print(f"    useRTH: {use_rth}")
            print(f"    end_time: {end_time}")
            
            # Get contract
            contract = self.get_contract(ticker)
            print(f"  Contract: {contract.symbol} on {contract.exchange}")
            print(f"  Contract qualified: {hasattr(contract, 'conId') and contract.conId > 0 if hasattr(contract, 'conId') else 'Unknown'}")
            if hasattr(contract, 'conId'):
                print(f"  Contract ID (conId): {contract.conId}")
            
            # IBKR API requirement: endDateTime must be empty string if None
            end_date_time = "" if end_time is None else end_time
            
            # Ensure contract is qualified before requesting data
            if not hasattr(contract, 'conId') or contract.conId == 0:
                print(f"  ⚠ Contract not qualified, qualifying now...")
                qualified = self.ib.qualifyContracts(contract)
                if qualified:
                    contract = qualified[0]
                    print(f"  ✓ Contract qualified: conId={contract.conId}")
                else:
                    print(f"  ✗ Failed to qualify contract")
                    return pd.DataFrame()
            
            # Fix bar_size format: IBKR requires specific formats
            bar_size_fixed = bar_size
            if bar_size == "1 min":
                bar_size_fixed = "1 min"  # "1 min" is correct (singular, no 's')
            elif bar_size.endswith(" min") and bar_size != "1 min":
                bar_size_fixed = bar_size.replace(" min", " mins")
            elif bar_size.endswith(" sec"):
                bar_size_fixed = bar_size.replace(" sec", " secs")
            elif bar_size.endswith(" hour") and not bar_size.startswith("1 "):
                bar_size_fixed = bar_size.replace(" hour", " hours")
            
            print(f"\n  Final request parameters:")
            print(f"    endDateTime: '{end_date_time}' (was: {end_time})")
            print(f"    contract.conId: {contract.conId}")
            print(f"    barSizeSetting: '{bar_size_fixed}' (was: '{bar_size}')")
            print(f"    durationStr: '{duration}'")
            print(f"    useRTH: {use_rth}")
            sys.stdout.flush()
            
            # Call reqHistoricalData directly (same as direct test)
            # This blocks until data arrives - no threading needed
            print(f"\n  Calling reqHistoricalData (this may take a few seconds)...")
            sys.stdout.flush()
            
            start_time = time.time()
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime=end_date_time,
                durationStr=duration,
                barSizeSetting=bar_size_fixed,
                whatToShow="TRADES",
                useRTH=use_rth,
                formatDate=1
            )
            elapsed = time.time() - start_time
            
            print(f"\n  ✓ reqHistoricalData returned after {elapsed:.2f} seconds")
            print(f"  Return type: {type(bars)}")
            print(f"  Return length: {len(bars) if bars else 0}")
            sys.stdout.flush()
            
            # Check if data arrived asynchronously in contract.historicalData
            if not bars and hasattr(contract, 'historicalData') and contract.historicalData:
                print(f"  Data found in contract.historicalData: {len(contract.historicalData)} bars")
                bars = contract.historicalData
            
            if not bars:
                print(f"  ✗ No bars returned for {ticker}")
                return pd.DataFrame()
            
            print(f"  ✓ Received {len(bars)} bars for {ticker}")
            
            # Convert to DataFrame
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

