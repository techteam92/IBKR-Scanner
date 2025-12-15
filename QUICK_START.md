# Quick Start Guide

## Step-by-Step Instructions

### 1. Install Dependencies
Open PowerShell or Command Prompt in the scanner folder and run:
```bash
pip install -r requirements.txt
```

### 2. Start Interactive Brokers
- **Option A**: Start **Trader Workstation (TWS)**
  - Paper Trading: Port 7497
  - Live Trading: Port 7496
  
- **Option B**: Start **IB Gateway** (lighter option)
  - Paper Trading: Port 4001
  - Live Trading: Port 4002

**Important**: In TWS/Gateway, enable API access:
- TWS: Configure → API → Settings → Enable "Enable ActiveX and Socket Clients"
- Set "Socket port" to match your port (7497 for paper, 7496 for live)

### 3. Create a Ticker List File
Create a text file (e.g., `tickers.txt`) with one ticker per line:
```
AAPL
MSFT
GOOGL
TSLA
NVDA
```

Or use the provided `example_tickers.txt` file.

### 4. Run the Application
```bash
python ui.py
```

### 5. Connect to IBKR
- Click the **"Connect"** button in the top-left
- Status should change to "Connected" (green)
- If it fails, check:
  - TWS/Gateway is running
  - API is enabled in TWS/Gateway settings
  - Port number matches (default: 7497)

### 6. Load Your Ticker List
- Click **"Load Tickers"** button
- Select your `tickers.txt` file
- You should see "X tickers loaded" message

### 7. Configure Pre-Market Scanner (Left Panel)
- **Enable/Disable**: Check/uncheck "Enable Pre-Market Scanner"
- **Select Timeframes**: Check the timeframes you want (5m, 10m, 15m, 30m, 60m)
- **Min Rel Vol**: Minimum relative volume filter (default: 3.0)
- **Min Avg Vol**: Minimum average volume filter (default: 0)

### 8. Configure RTH Scanner (Right Panel)
- Same options as Pre-Market, but independent settings
- Configure separately for regular trading hours

### 9. Run Scans

**For Pre-Market (before 9:30 AM ET):**
- Click **"Scan Pre-Market"** button
- Wait for scan to complete (status shows "Scanning Pre-Market...")
- Results appear in the left table

**For Regular Hours (9:30 AM - 4:00 PM ET):**
- Click **"Scan RTH"** button
- Wait for scan to complete
- Results appear in the right table

### 10. View and Sort Results
- Results are sorted by **RelVol** (descending) by default
- Click any column header to sort by that column
- Click again to reverse sort order
- Columns:
  - **Ticker**: Stock symbol
  - **Timeframe**: Time window (5m, 10m, etc.)
  - **TodayVol**: Today's volume
  - **Avg10DVol**: 10-day average volume
  - **RelVol**: Relative volume (higher = more unusual)
  - **PercentDiff**: % difference from average
  - **Notes**: Warnings or errors

## Example Workflow

1. **Morning (Pre-Market)**: 
   - Connect to IBKR
   - Load tickers
   - Configure Pre-Market scanner (select 5m, 15m, 30m timeframes)
   - Click "Scan Pre-Market"
   - Look for stocks with high RelVol (>3.0x)

2. **During Market Hours**:
   - Configure RTH scanner
   - Click "Scan RTH" periodically
   - Monitor volume spikes

## Tips

- **High RelVol** (>3.0) = Unusual volume activity
- **Positive PercentDiff** = Volume above average
- **Filter by Min Avg Vol** to avoid low-volume stocks
- Scans run in background - UI stays responsive
- You can run both scanners independently

## Troubleshooting

**"Failed to connect to IBKR"**
- Make sure TWS or IB Gateway is running
- Check API is enabled in TWS/Gateway settings
- Verify port number (default: 7497 for paper trading)

**"No data available"**
- Market might be closed
- Ticker symbol might be incorrect
- Not enough historical data (need at least 10 days)

**Scan takes too long**
- Reduce number of tickers
- Select fewer timeframes
- Check internet connection

