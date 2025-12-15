# Troubleshooting Guide

## Issue: No Data in Table After Scanning

### Problem
When you click "Scan RTH" or "Scan Pre-Market", the table shows no results.

### Common Causes & Solutions

#### 1. **Filters Too Restrictive**
**Symptom**: Scan completes but table is empty

**Solution**: 
- Lower the **Min Rel Vol** value (try 0.0 to see all results)
- Lower the **Min Avg Vol** value (try 0)
- The default Min Rel Vol is 3.0, which means only stocks with 3x average volume will show

**How to fix**:
- In the scanner panel, change "Min Rel Vol" from `3.0` to `0.0` or `1.0`
- Click "Scan" again

#### 2. **Market Not Open**
**Symptom**: All results show "No data available" or errors

**For RTH Scanner**:
- Market must be open: 9:30 AM - 4:00 PM ET
- If market is closed, you won't get today's data

**For Pre-Market Scanner**:
- Must be during pre-market hours: 4:00 AM - 9:30 AM ET
- If outside these hours, you won't get today's data

**Solution**: Run scans during appropriate market hours

#### 3. **No Historical Data**
**Symptom**: Results show "No data available" for all tickers

**Causes**:
- Ticker symbols are incorrect
- Not enough historical data (need at least 10 days)
- IBKR subscription doesn't include historical data for those symbols

**Solution**:
- Verify ticker symbols are correct (e.g., AAPL, not APPL)
- Check IBKR has historical data subscription
- Try a well-known ticker like AAPL or MSFT first

#### 4. **Connection Issues**
**Symptom**: Errors in Notes column or connection fails

**Solution**:
- Ensure TWS or IB Gateway is running
- Check API is enabled in TWS/Gateway settings
- Verify port number (default: 7497 for paper trading)
- Try disconnecting and reconnecting

#### 5. **No Timeframes Selected**
**Symptom**: Warning message appears

**Solution**: 
- Check at least one timeframe checkbox (5m, 10m, 15m, 30m, or 60m)
- Then click Scan again

### Debugging Steps

1. **Check Console Output**
   - If running from command line, check for error messages
   - Look for messages like "X results collected, but all filtered out"

2. **Lower All Filters**
   - Set Min Rel Vol to `0.0`
   - Set Min Avg Vol to `0`
   - This will show ALL results, including errors

3. **Test with Single Ticker**
   - Create a test file with just one ticker: `AAPL`
   - Load and scan
   - If this works, the issue is with your ticker list

4. **Check Notes Column**
   - Even with no visible results, errors should now appear
   - Look for messages like:
     - "Error: ..." (connection or data issues)
     - "No data available" (no historical data)
     - "Below min rel vol threshold" (filtered out)

5. **Verify IBKR Data**
   - In TWS, manually check if you can see historical data for your tickers
   - Ensure you have the right market data subscriptions

### Recent Fixes (v1.1)

- **Errors now visible**: Errors and "No data" results are no longer filtered out
- **Better error messages**: More detailed error information in Notes column
- **Helpful messages**: Popup messages guide you when no results found
- **Debug output**: Console shows when results are filtered

### Still Having Issues?

If you're still seeing no data:

1. **Check the Notes column** - Even empty tables should show a helpful message
2. **Try with Min Rel Vol = 0.0** - This shows everything
3. **Verify market hours** - RTH scanner needs market to be open
4. **Test with AAPL** - Use a well-known ticker to verify setup
5. **Check IBKR connection** - Status should show "Connected" (green)

### Example: Testing Setup

1. Connect to IBKR
2. Load a file with just: `AAPL`
3. Set Min Rel Vol to `0.0`
4. Set Min Avg Vol to `0`
5. Select one timeframe (e.g., 5m)
6. Click "Scan RTH" (during market hours)
7. You should see at least one row, even if it's an error

If this doesn't work, the issue is likely:
- IBKR connection
- Market data subscription
- TWS/Gateway configuration

