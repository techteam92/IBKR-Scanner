"""
Configuration settings for the Dual Volume Scanner
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ScannerConfig:
    """Base configuration for volume scanners"""
    lookback_days: int = 10
    timeframes: List[int] = None  # [5, 10, 15, 30, 60] in minutes
    min_relative_volume: float = 3.0
    min_avg_volume: int = 0
    enabled: bool = True
    
    def __post_init__(self):
        if self.timeframes is None:
            self.timeframes = [5, 10, 15, 30, 60]


@dataclass
class PreMarketConfig(ScannerConfig):
    """Pre-market scanner configuration"""
    start_time: str = "04:00"  # ET
    end_time: str = "09:30"  # ET
    use_rth: bool = False  # Pre-market uses useRTH=0


@dataclass
class RTHConfig(ScannerConfig):
    """Regular Trading Hours scanner configuration"""
    start_time: str = "09:30"  # ET
    end_time: str = "16:00"  # ET
    use_rth: bool = True  # RTH uses useRTH=1


@dataclass
class IBKRConfig:
    """IBKR connection configuration"""
    host: str = "127.0.0.1"
    port: int = 7497  # TWS: 7497, IB Gateway: 4001
    client_id: int = 1
    timeout: int = 30


# Default configurations
DEFAULT_PREMARKET_CONFIG = PreMarketConfig()
DEFAULT_RTH_CONFIG = RTHConfig()
DEFAULT_IBKR_CONFIG = IBKRConfig()

