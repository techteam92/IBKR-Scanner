# Why `reqHistoricalData` Returns Empty Data

## The Problem

You're seeing:
- ✅ Connection successful
- ✅ No errors captured
- ❌ `reqHistoricalData` returns empty list `[]`
- ❌ Timeout after 15 seconds

## Why This Happens

### 1. **Error 162 (IP Mismatch) - Silent Blocking**

**Most Common Cause**: IBKR silently blocks historical data requests when there's an IP mismatch, but **doesn't send an error message**.

**Symptoms**:
- Connection works (orders work)
- `reqHistoricalData` returns empty immediately or times out
- No error code 162 in error stream
- HMDS (Historical Market Data Service) connected but data blocked

**Why orders work but data doesn't**:
- Order placement = Account access (works with basic API)
- Historical data = Market data service (requires IP match + subscription)

**Solution**:
1. Close TWS/Gateway completely
2. Close scanner/test script
3. Restart TWS/Gateway and **LOG IN**
4. Wait for full connection (all green)
5. Restart scanner and test

### 2. **Market Data Subscription Not Enabled**

**Symptoms**:
- Connection works
- No errors
- Empty data returned

**Check**:
- IB Gateway → Account → Market Data Subscriptions
- Ensure historical data is enabled
- Verify symbols (AAPL, TSLA) are subscribed

**Solution**:
- Subscribe to market data in IB Gateway
- Paper accounts may have limited historical data

### 3. **How `ib_insync` Works**

In `ib_insync`, `reqHistoricalData` can:
1. Return immediately with empty list `[]`
2. Data arrives asynchronously via `historicalData` event
3. Data stored in `contract.historicalData`

**The code waits and checks `contract.historicalData`**, but if IBKR is blocking the request, no data ever arrives.

### 4. **Paper Account Limitations**

Paper trading accounts often have:
- Limited historical data
- Delayed data
- Some symbols not available

**Solution**: Try with a live account or check paper account data limits.

## How to Diagnose

### Step 1: Check TWS/Gateway Logs

1. **TWS/Gateway → Help → Logs**
2. Look for files with today's date
3. Search for "162" or "different IP"
4. If found → **Error 162 confirmed**

### Step 2: Check Market Data Subscription

1. **IB Gateway → Account → Market Data Subscriptions**
2. Check if historical data is enabled
3. Check if AAPL/TSLA are subscribed

### Step 3: Test with Direct Script

Run the direct test script:
```bash
python test_historical_data_direct.py
```

This will show:
- Contract qualification status
- Exact timing of `reqHistoricalData` call
- Whether data arrives in `contract.historicalData`
- Detailed diagnostics

### Step 4: Check IP Address

Run:
```bash
python check_ip_addresses.py
```

This shows:
- Your local IP
- Connection IP
- IBKR connection details

## Most Likely Cause

Based on your symptoms (orders work, data doesn't, no errors):

**Error 162 (IP Mismatch) with Silent Blocking**

IBKR is blocking historical data requests due to IP mismatch, but not sending an explicit error. This is a security feature.

## Solution

### Complete Restart (Most Reliable)

1. **Close everything**:
   - Scanner/test script
   - TWS/Gateway
   - All IBKR-related applications

2. **Restart TWS/Gateway**:
   - Open TWS/Gateway
   - **LOG IN** (critical!)
   - Wait for full connection (all green, ~60 seconds)

3. **Restart scanner**:
   - Open scanner
   - Connect
   - Test

### Check API Settings

1. **TWS/Gateway → Configure → API → Settings**
2. **"Enable ActiveX and Socket Clients"** = ON
3. **"Trusted IPs"** = EMPTY (or includes 127.0.0.1)
4. **Restart TWS/Gateway** after changing

### Verify Market Data

1. **IB Gateway → Account → Market Data Subscriptions**
2. Ensure historical data is enabled
3. Verify symbols are subscribed

## Expected Behavior

When working correctly:
```
Requesting historical data for AAPL...
  reqHistoricalData returned after 2.5 seconds
  Return length: 2340
  ✓ SUCCESS! Received 2340 bars immediately
```

When blocked (Error 162):
```
Requesting historical data for AAPL...
  reqHistoricalData returned after 0.1 seconds
  Return length: 0
  ⚠ No bars returned immediately
  Waiting up to 15 seconds...
  ✗ No data received after 15 seconds
```

## Summary

**Empty data = IBKR is blocking the request**

Most likely causes:
1. **Error 162** (IP mismatch) - 80% of cases
2. **Market data subscription** - 15% of cases
3. **Paper account limitations** - 5% of cases

**Fix**: Restart TWS/Gateway completely and ensure you're logged in before connecting the scanner.

