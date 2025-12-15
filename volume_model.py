"""
Volume calculation and aggregation models
"""
import pandas as pd
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple
import pytz


class VolumeCalculator:
    """Calculate volume metrics for different timeframes"""
    
    ET = pytz.timezone('US/Eastern')
    
    def __init__(self, lookback_days: int = 10):
        """
        Initialize volume calculator
        
        Args:
            lookback_days: Number of days to look back for average calculation
        """
        self.lookback_days = lookback_days
    
    @staticmethod
    def filter_time_range(
        df: pd.DataFrame,
        start_time: str,
        end_time: str,
        date_col: str = 'date'
    ) -> pd.DataFrame:
        """
        Filter DataFrame to specific time range (ET timezone)
        
        Args:
            df: DataFrame with datetime index or date column
            start_time: Start time in "HH:MM" format (ET)
            end_time: End time in "HH:MM" format (ET)
            date_col: Name of date column if not index
        
        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df
        
        # Ensure we have a datetime column
        if date_col in df.columns:
            df = df.copy()
            df['_datetime'] = pd.to_datetime(df[date_col])
        else:
            df = df.copy()
            df['_datetime'] = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index)
        
        # Convert to ET timezone if not already
        if df['_datetime'].dt.tz is None:
            # Assume ET if no timezone
            df['_datetime'] = df['_datetime'].dt.tz_localize('US/Eastern')
        else:
            df['_datetime'] = df['_datetime'].dt.tz_convert('US/Eastern')
        
        # Parse time strings
        start_hour, start_min = map(int, start_time.split(':'))
        end_hour, end_min = map(int, end_time.split(':'))
        
        start_t = time(start_hour, start_min)
        end_t = time(end_hour, end_min)
        
        # Filter by time of day
        df['_time'] = df['_datetime'].dt.time
        
        if start_t < end_t:
            # Normal case: start < end (e.g., 09:30 to 16:00)
            mask = (df['_time'] >= start_t) & (df['_time'] < end_t)
        else:
            # Overnight case: start > end (e.g., 04:00 to 09:30)
            mask = (df['_time'] >= start_t) | (df['_time'] < end_t)
        
        filtered = df[mask].copy()
        
        # Clean up temporary columns
        if '_datetime' in filtered.columns:
            filtered = filtered.drop(columns=['_datetime', '_time'])
        
        return filtered
    
    def calculate_premarket_volume(
        self,
        df: pd.DataFrame,
        timeframe_minutes: int,
        target_date: Optional[datetime] = None
    ) -> Tuple[float, float]:
        """
        Calculate pre-market volume for a specific timeframe
        
        Pre-market window: 04:00-09:30 ET
        For timeframe T: volume in [09:30 - T, 09:30)
        
        Args:
            df: DataFrame with historical bars
            timeframe_minutes: Timeframe in minutes (5, 10, 15, 30, 60)
            target_date: Target date for "today" calculation (default: latest date in data)
        
        Returns:
            Tuple of (today_volume, avg_10d_volume)
        """
        if df.empty:
            return 0.0, 0.0
        
        # Ensure date column exists
        if 'date' not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                if 'date' not in df.columns:
                    df['date'] = df.index
        
        df['date'] = pd.to_datetime(df['date'])
        if df['date'].dt.tz is None:
            df['date'] = df['date'].dt.tz_localize('US/Eastern')
        else:
            df['date'] = df['date'].dt.tz_convert('US/Eastern')
        
        # Filter to pre-market hours (04:00-09:30)
        pm_df = self.filter_time_range(df, "04:00", "09:30")
        
        if pm_df.empty:
            return 0.0, 0.0
        
        # Determine target date
        if target_date is None:
            target_date = pm_df['date'].max().date()
        elif isinstance(target_date, datetime):
            if target_date.tzinfo is None:
                target_date = pytz.timezone('US/Eastern').localize(target_date)
            target_date = target_date.date()
        
        # Calculate window: [09:30 - T, 09:30) on target_date
        target_datetime = datetime.combine(target_date, time(9, 30))
        target_datetime = pytz.timezone('US/Eastern').localize(target_datetime)
        window_start = target_datetime - timedelta(minutes=timeframe_minutes)
        
        # Filter to today's window
        today_mask = (pm_df['date'] >= window_start) & (pm_df['date'] < target_datetime)
        today_df = pm_df[today_mask]
        today_vol = today_df['volume'].sum() if 'volume' in today_df.columns else 0.0
        
        # Calculate 10-day average
        # Get unique dates in pre-market data
        pm_df['date_only'] = pm_df['date'].dt.date
        unique_dates = sorted(pm_df['date_only'].unique(), reverse=True)[:self.lookback_days]
        
        avg_volumes = []
        for date_val in unique_dates:
            date_dt = datetime.combine(date_val, time(9, 30))
            date_dt = pytz.timezone('US/Eastern').localize(date_dt)
            window_start_dt = date_dt - timedelta(minutes=timeframe_minutes)
            
            day_mask = (pm_df['date'] >= window_start_dt) & (pm_df['date'] < date_dt)
            day_df = pm_df[day_mask]
            day_vol = day_df['volume'].sum() if 'volume' in day_df.columns else 0.0
            if day_vol > 0:  # Only include days with data
                avg_volumes.append(day_vol)
        
        avg_10d_vol = sum(avg_volumes) / len(avg_volumes) if avg_volumes else 0.0
        
        return today_vol, avg_10d_vol
    
    def calculate_rth_volume(
        self,
        df: pd.DataFrame,
        timeframe_minutes: int,
        target_date: Optional[datetime] = None
    ) -> Tuple[float, float]:
        """
        Calculate RTH volume for a specific timeframe
        
        RTH window: 09:30-16:00 ET
        For timeframe T: volume in [09:30, 09:30 + T)
        
        Args:
            df: DataFrame with historical bars
            timeframe_minutes: Timeframe in minutes (5, 10, 15, 30, 60)
            target_date: Target date for "today" calculation (default: latest date in data)
        
        Returns:
            Tuple of (today_volume, avg_10d_volume)
        """
        if df.empty:
            return 0.0, 0.0
        
        # Ensure date column exists
        if 'date' not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                if 'date' not in df.columns:
                    df['date'] = df.index
        
        df['date'] = pd.to_datetime(df['date'])
        if df['date'].dt.tz is None:
            df['date'] = df['date'].dt.tz_localize('US/Eastern')
        else:
            df['date'] = df['date'].dt.tz_convert('US/Eastern')
        
        # Filter to RTH hours (09:30-16:00)
        rth_df = self.filter_time_range(df, "09:30", "16:00")
        
        if rth_df.empty:
            return 0.0, 0.0
        
        # Determine target date
        if target_date is None:
            target_date = rth_df['date'].max().date()
        elif isinstance(target_date, datetime):
            if target_date.tzinfo is None:
                target_date = pytz.timezone('US/Eastern').localize(target_date)
            target_date = target_date.date()
        
        # Calculate window: [09:30, 09:30 + T) on target_date
        target_datetime = datetime.combine(target_date, time(9, 30))
        target_datetime = pytz.timezone('US/Eastern').localize(target_datetime)
        window_end = target_datetime + timedelta(minutes=timeframe_minutes)
        
        # Filter to today's window
        today_mask = (rth_df['date'] >= target_datetime) & (rth_df['date'] < window_end)
        today_df = rth_df[today_mask]
        today_vol = today_df['volume'].sum() if 'volume' in today_df.columns else 0.0
        
        # Calculate 10-day average
        rth_df['date_only'] = rth_df['date'].dt.date
        unique_dates = sorted(rth_df['date_only'].unique(), reverse=True)[:self.lookback_days]
        
        avg_volumes = []
        for date_val in unique_dates:
            date_dt = datetime.combine(date_val, time(9, 30))
            date_dt = pytz.timezone('US/Eastern').localize(date_dt)
            window_end_dt = date_dt + timedelta(minutes=timeframe_minutes)
            
            day_mask = (rth_df['date'] >= date_dt) & (rth_df['date'] < window_end_dt)
            day_df = rth_df[day_mask]
            day_vol = day_df['volume'].sum() if 'volume' in day_df.columns else 0.0
            if day_vol > 0:  # Only include days with data
                avg_volumes.append(day_vol)
        
        avg_10d_vol = sum(avg_volumes) / len(avg_volumes) if avg_volumes else 0.0
        
        return today_vol, avg_10d_vol
    
    @staticmethod
    def calculate_relative_volume(today_vol: float, avg_vol: float) -> float:
        """Calculate relative volume (today_vol / avg_vol)"""
        if avg_vol == 0:
            return 0.0
        return today_vol / avg_vol
    
    @staticmethod
    def calculate_percent_difference(today_vol: float, avg_vol: float) -> float:
        """Calculate percentage difference ((today_vol - avg_vol) / avg_vol) * 100"""
        if avg_vol == 0:
            return 0.0
        return ((today_vol - avg_vol) / avg_vol) * 100

