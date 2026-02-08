# Dual Volume Scanner (Pre-Market + Regular Hours)

A comprehensive volume scanning tool with two separate scanning panels for pre-market and regular trading hours analysis.

## Features

### Pre-Market Volume Scanner
- Scans volume during pre-market hours (04:00-09:30 ET)
- Calculates volume for selected timeframes (5, 10, 15, 30, 60 minutes)
- Compares today's volume against 10-day average
- Computes relative volume and percentage difference

### Regular Trading Hours (RTH) Volume Scanner
- Scans volume during regular trading hours (09:30-16:00 ET)
- Independent settings from pre-market scanner
- Same timeframe and calculation options

### Key Capabilities
- **User-provided ticker lists** (.txt or .csv format)
- **Configurable lookback period** (default: 10 days)
- **Multi-timeframe analysis** (5, 10, 15, 30, 60 minutes)
- **Flexible filtering** (minimum relative volume, minimum average volume)
- **Sortable results** by any column (default: RelVol descending)
- **Real-time scanning** with IBKR API integration

## Requirements

- Python 3.8+
- Interactive Brokers TWS or IB Gateway running
- ib_insync library
- pandas, numpy

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Interactive Brokers TWS or IB Gateway:
   - TWS: Port 7497 (paper trading) or 7496 (live)
   - IB Gateway: Port 4001 (paper) or 4002 (live)

3. Configure connection settings in `config.py` if needed (default: localhost:7497)

## Usage

1. Run the application:
```bash
python ui.py
```

2. Connect to IBKR:
   - Click "Connect" button
   - Ensure TWS/Gateway is running and API is enabled

3. Load ticker list:
   - Click "Load Tickers"
   - Select a .txt or .csv file
   - Format: One ticker per line, or CSV with ticker in first column

4. Configure scanners:
   - **Pre-Market Panel**: Select timeframes, set min relative volume, min average volume
   - **RTH Panel**: Configure independently with same options
   - Enable/disable each scanner as needed

5. Run scans:
   - Click "Scan Pre-Market" for pre-market analysis
   - Click "Scan RTH" for regular hours analysis
   - Results appear in respective tables

6. Sort results:
   - Click any column header to sort
   - Click again to reverse sort order
   - Default sort: RelVol (descending)

## Ticker List Format

### Text File (.txt)
```
AAPL
MSFT
GOOGL
TSLA
```

### CSV File (.csv)
```
Ticker,Other,Columns
AAPL,data,here
MSFT,data,here
```

## Output Columns

- **Ticker**: Stock symbol
- **Timeframe**: Selected timeframe (5m, 10m, 15m, 30m, 60m)
- **TodayVol**: Today's volume in the timeframe
- **Avg10DVol**: 10-day average volume for the same timeframe
- **RelVol**: Relative volume (TodayVol / Avg10DVol)
- **PercentDiff**: Percentage difference ((TodayVol - Avg10DVol) / Avg10DVol) * 100
- **Notes**: Additional information or warnings

## Configuration

Edit `config.py` to customize:
- IBKR connection settings (host, port, client_id)
- Default lookback days
- Default timeframes
- Default minimum relative volume
- Default minimum average volume

## File Structure

```
scanner/
├── config.py              # Configuration settings
├── ibkr_client.py         # IBKR API client
├── volume_model.py        # Volume calculation logic
├── scanner_premarket.py   # Pre-market scanner
├── scanner_rth.py         # RTH scanner
├── ui.py                  # Main GUI application
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Notes

- Pre-market scanner uses `useRTH=0` to include pre-market data
- RTH scanner uses `useRTH=1` for regular trading hours only
- All times are in Eastern Time (ET)
- Volume calculations use 1-minute bars aggregated to selected timeframes
- Scans run in background threads to keep UI responsive

## Troubleshooting

**Connection Issues:**
- Ensure TWS/Gateway is running
- Check API settings in TWS/Gateway (Enable ActiveX and Socket Clients)
- Verify port number matches configuration

**No Data:**
- Check if market is open (for RTH) or in pre-market hours
- Verify ticker symbols are correct
- Ensure sufficient historical data is available

**Performance:**
- Large ticker lists may take time to scan
- Consider reducing timeframes or ticker count for faster results

