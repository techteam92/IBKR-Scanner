"""
Pre-Market Volume Scanner
"""
import pandas as pd
from typing import List, Optional
from datetime import datetime
from ibkr_client import IBKRClient
from volume_model import VolumeCalculator
from config import PreMarketConfig


class PreMarketScanner:
    """Scanner for pre-market volume analysis"""
    
    def __init__(self, config: PreMarketConfig, ibkr_client: IBKRClient):
        """
        Initialize pre-market scanner
        
        Args:
            config: Pre-market scanner configuration
            ibkr_client: IBKR client instance
        """
        self.config = config
        self.ibkr_client = ibkr_client
        self.calculator = VolumeCalculator(lookback_days=config.lookback_days)
    
    def scan_ticker(
        self,
        ticker: str,
        timeframes: Optional[List[int]] = None,
        target_date: Optional[datetime] = None
    ) -> List[dict]:
        """
        Scan a single ticker for pre-market volume
        
        Args:
            ticker: Stock ticker symbol
            timeframes: List of timeframes in minutes (default: from config)
            target_date: Target date for "today" (default: latest available)
        
        Returns:
            List of dictionaries with scan results for each timeframe
        """
        if timeframes is None:
            timeframes = self.config.timeframes
        
        results = []
        
        try:
            # Fetch historical data (lookback_days + buffer)
            duration = f"{self.config.lookback_days + 2} D"
            df = self.ibkr_client.get_historical_bars_sync(
                ticker=ticker,
                duration=duration,
                bar_size="1 min",
                use_rth=self.config.use_rth
            )
            
            if df.empty:
                # Check for Error 162
                error_162 = False
                try:
                    for error in self.ibkr_client.ib.errorEvent:
                        if '162' in str(error) or 'different IP address' in str(error):
                            error_162 = True
                            break
                except:
                    pass
                
                if error_162:
                    error_msg = "Error 162: IP mismatch - Restart TWS/Gateway and reconnect"
                else:
                    error_msg = f"No data available from IBKR for {ticker}"
                
                print(f"Pre-Market Scanner: {error_msg}")
                for tf in timeframes:
                    results.append({
                        'Ticker': ticker,
                        'Timeframe': f"{tf}m",
                        'TodayVol': 0,
                        'Avg10DVol': 0,
                        'RelVol': 0.0,
                        'PercentDiff': 0.0,
                        'Notes': error_msg
                    })
                return results
            
            # Check if we have the required columns
            if 'volume' not in df.columns:
                error_msg = f"No volume column in data for {ticker}. Columns: {list(df.columns)}"
                print(f"Pre-Market Scanner: {error_msg}")
                for tf in timeframes:
                    results.append({
                        'Ticker': ticker,
                        'Timeframe': f"{tf}m",
                        'TodayVol': 0,
                        'Avg10DVol': 0,
                        'RelVol': 0.0,
                        'PercentDiff': 0.0,
                        'Notes': error_msg
                    })
                return results
            
            # Scan each timeframe
            # Calculate total daily volume (all bars for the target date)
            daily_vol = self.calculator.calculate_daily_volume(df, target_date)
            
            for tf in timeframes:
                today_vol, avg_10d_vol = self.calculator.calculate_premarket_volume(
                    df, tf, target_date
                )
                
                rel_vol = self.calculator.calculate_relative_volume(today_vol, avg_10d_vol)
                percent_diff = self.calculator.calculate_percent_difference(today_vol, avg_10d_vol)
                
                # Apply filters
                notes = ""
                if avg_10d_vol < self.config.min_avg_volume:
                    notes = f"Low baseline volume ({avg_10d_vol:.0f})"
                
                if rel_vol < self.config.min_relative_volume:
                    notes = f"Below min rel vol threshold ({rel_vol:.2f}x)"
                
                result = {
                    'Ticker': ticker,
                    'Timeframe': f"{tf}m",
                    'TodayVol': int(today_vol),
                    'Avg10DVol': int(avg_10d_vol),
                    'DailyVol': int(daily_vol),
                    'RelVol': round(rel_vol, 2),
                    'PercentDiff': round(percent_diff, 2),
                    'Notes': notes
                }
                results.append(result)
                
                # Print result to terminal
                print(f"    {tf}m: Today={int(today_vol):,} | Avg10D={int(avg_10d_vol):,} | RelVol={rel_vol:.2f}x | %Diff={percent_diff:.1f}% {notes}")
        
        except Exception as e:
            # Error handling
            for tf in timeframes:
                results.append({
                    'Ticker': ticker,
                    'Timeframe': f"{tf}m",
                    'TodayVol': 0,
                    'Avg10DVol': 0,
                    'RelVol': 0.0,
                    'PercentDiff': 0.0,
                    'Notes': f"Error: {str(e)}"
                })
        
        return results
    
    def scan_tickers(
        self,
        tickers: List[str],
        timeframes: Optional[List[int]] = None,
        target_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Scan multiple tickers
        
        Args:
            tickers: List of ticker symbols
            timeframes: List of timeframes in minutes (default: from config)
            target_date: Target date for "today" (default: latest available)
        
        Returns:
            DataFrame with scan results
        """
        if not self.config.enabled:
            return pd.DataFrame()
        
        if timeframes is None:
            timeframes = self.config.timeframes
        
        all_results = []
        
        for ticker in tickers:
            ticker_results = self.scan_ticker(ticker, timeframes, target_date)
            all_results.extend(ticker_results)
        
        df = pd.DataFrame(all_results)
        
        # Apply filters - but keep errors and "No data" results
        if not df.empty:
            # Separate valid results from errors/no data
            valid_mask = (~df['Notes'].str.contains('Error|No data', case=False, na=False))
            
            # For valid results, apply filters
            if valid_mask.any():
                valid_df = df[valid_mask]
                filtered_valid = valid_df[
                    (valid_df['RelVol'] >= self.config.min_relative_volume) &
                    (valid_df['Avg10DVol'] >= self.config.min_avg_volume)
                ]
                
                # Combine filtered valid results with errors/no data
                error_df = df[~valid_mask]
                df = pd.concat([filtered_valid, error_df], ignore_index=True)
                
                # Debug: print summary if valid results were filtered out
                if len(filtered_valid) < len(valid_df):
                    print(f"Pre-Market Scanner: {len(valid_df)} valid results, {len(filtered_valid)} passed filters")
                    print(f"  Min Rel Vol: {self.config.min_relative_volume}, Min Avg Vol: {self.config.min_avg_volume}")
            # If no valid results, keep all (they're all errors/no data)
        
        return df

