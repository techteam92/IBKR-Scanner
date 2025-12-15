# Diagnostic Guide: "No Data Available" Issue

## Quick Test

Run this to diagnose the issue:

```bash
python test_ibkr_connection.py
```

This will test:
1. IBKR connection
2. Data retrieval for AAPL
3. Both RTH and Pre-market data

## ⚠️ ERROR 162: "Trading TWS session is connected from a different IP address"

**This is the most common issue!**

### What it means:
IBKR detected that your TWS/Gateway login and API connection are from different IP addresses, which blocks historical data requests for security reasons.

### Solutions (try in order):

#### Solution 1: Restart TWS/Gateway
1. **Close TWS or IB Gateway completely**
2. **Close the scanner application**
3. **Restart TWS/Gateway** (make sure you log in)
4. **Wait for TWS to fully load** (all market data connected)
5. **Then start the scanner and connect**

#### Solution 2: Check for Multiple TWS Sessions
1. Check if you have **multiple TWS windows** open
2. Check if **IB Gateway is also running** (close it if TWS is open)
3. **Only one should be running** at a time

#### Solution 3: Verify Same Machine
- TWS/Gateway and the scanner **must run on the same computer**
- If TWS is on a different machine, this error will occur
- API connections must be from `127.0.0.1` (localhost)

#### Solution 4: Check TWS API Settings
1. In TWS: **Configure → API → Settings**
2. Make sure **"Enable ActiveX and Socket Clients"** is checked
3. **"Read-Only API"** should be unchecked (if you want full access)
4. **Socket port** should match your config (default: 7497)
5. **"Trusted IPs"** - if set, make sure `127.0.0.1` is included

#### Solution 5: Re-login to TWS
1. **Log out** of TWS completely
2. **Close TWS**
3. **Restart TWS** and log back in
4. **Wait for full connection** (all green indicators)
5. **Then connect the scanner**

#### Solution 6: Use IB Gateway Instead
If TWS continues to have issues:
1. **Close TWS**
2. **Start IB Gateway** (lighter, fewer issues)
3. **Log in to IB Gateway**
4. **Update port in config.py** to `4001` (paper) or `4002` (live)
5. **Connect scanner**

### How to Verify It's Fixed:
After applying a solution, run the test again:
```bash
python test_ibkr_connection.py
```

You should see:
- ✓ Connected successfully
- Received X bars for AAPL (not "No bars returned")
- DataFrame shape: (X, Y) where X > 0

If you still see Error 162, try the next solution.

## Common Issues & Solutions

### Issue 1: Contract Not Qualified

**Symptom**: "No bars returned" in console

**Solution**: The contract needs to be qualified first. The code now does this automatically, but if it fails:

1. Check ticker symbol is correct (e.g., "AAPL" not "APPL")
2. Verify you have market data subscription for that symbol
3. Try a well-known ticker like "AAPL" or "MSFT" first

### Issue 2: Historical Data Subscription

**Symptom**: Connection works but no data returned

**Solution**: 
- IBKR requires a market data subscription for historical data
- Paper trading accounts may have limited historical data
- Check in TWS: Market Data Subscriptions

### Issue 3: Market Hours

**Symptom**: No data for "today"

**For RTH Scanner**:
- Market must be open: 9:30 AM - 4:00 PM ET
- If market is closed, you'll only get historical data (yesterday and earlier)

**For Pre-Market Scanner**:
- Must be during pre-market: 4:00 AM - 9:30 AM ET
- Outside these hours, no "today" pre-market data

**Solution**: 
- For testing, use historical dates (yesterday or earlier)
- Or run during appropriate market hours

### Issue 4: Bar Size Format

**Symptom**: Request succeeds but returns empty

**Solution**: The bar size "1 min" should work, but IBKR might need:
- "1 min" (with space) - current format ✓
- "1min" (no space) - try if above fails
- "60 secs" - alternative format

### Issue 5: Duration Format

**Symptom**: Request fails or returns wrong data

**Current format**: "12 D" (12 days)
**Alternative formats to try**:
- "12 D" (current) ✓
- "2 W" (2 weeks)
- "1 M" (1 month)

### Issue 6: useRTH Parameter

**Symptom**: RTH scanner gets no data, but Pre-market does (or vice versa)

**Solution**:
- RTH scanner uses `useRTH=True` (regular hours only)
- Pre-market uses `useRTH=False` (includes pre/post market)
- Make sure you're testing during appropriate hours

## Step-by-Step Debugging

### Step 1: Test Connection
```python
from ibkr_client import IBKRClient
client = IBKRClient()
if client.connect_sync():
    print("Connected!")
else:
    print("Connection failed")
```

### Step 2: Test Contract Qualification
```python
from ib_insync import Stock
contract = Stock("AAPL", "SMART", "USD")
qualified = client.ib.qualifyContracts(contract)
print(f"Qualified: {qualified}")
```

### Step 3: Test Historical Data Request
```python
bars = client.ib.reqHistoricalData(
    contract,
    endDateTime="",
    durationStr="12 D",
    barSizeSetting="1 min",
    whatToShow="TRADES",
    useRTH=True,
    formatDate=1
)
print(f"Bars received: {len(bars) if bars else 0}")
```

### Step 4: Check DataFrame
```python
if bars:
    df = util.df(bars)
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(df.head())
```

## Console Output to Look For

When you run a scan, check the console for:

1. **"Requesting historical data for..."** - Shows the request is being made
2. **"Received X bars for..."** - Shows data was received
3. **"DataFrame shape: ..."** - Shows the data structure
4. **"No bars returned for..."** - Indicates no data from IBKR
5. **"Error fetching historical data..."** - Shows an exception

## What the Test Script Shows

The `test_ibkr_connection.py` script will show:

1. ✓/✗ Connection status
2. DataFrame shape and columns
3. Date range of data
4. Sample data rows
5. Any errors with full traceback

## If Test Script Works But Scanner Doesn't

If the test script gets data but the scanner doesn't:

1. **Check ticker list** - Make sure tickers are valid
2. **Check filters** - Lower Min Rel Vol to 0.0
3. **Check timeframes** - Make sure at least one is selected
4. **Check market hours** - Run during appropriate hours

## Still Not Working?

1. **Check TWS/Gateway Logs**:
   - Look for API request logs
   - Check for error messages
   - Verify API is enabled

2. **Verify Market Data Subscription**:
   - In TWS: Account → Market Data Subscriptions
   - Ensure you have data for the symbols you're testing

3. **Try Different Ticker**:
   - Start with "AAPL" (most reliable)
   - Then try "MSFT", "GOOGL"
   - Avoid low-volume or exotic symbols

4. **Check IBKR API Settings**:
   - TWS: Configure → API → Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Check "Read-Only API" is appropriate
   - Verify port number matches

5. **Paper vs Live Account**:
   - Paper trading: Port 7497 (TWS) or 4001 (Gateway)
   - Live trading: Port 7496 (TWS) or 4002 (Gateway)
   - Paper accounts may have limited historical data

## Expected Console Output (Success)

```
Requesting historical data for AAPL: duration=12 D, bar_size=1 min, useRTH=True
Received 2340 bars for AAPL
DataFrame shape for AAPL: (2340, 6), columns: ['date', 'open', 'high', 'low', 'close', 'volume']
```

## Expected Console Output (Failure)

```
Requesting historical data for AAPL: duration=12 D, bar_size=1 min, useRTH=True
No bars returned for AAPL
Contract: Stock(symbol='AAPL', exchange='SMART', currency='USD')
```

If you see the failure output, the issue is with:
- IBKR connection
- Market data subscription
- Contract qualification
- Historical data permissions

