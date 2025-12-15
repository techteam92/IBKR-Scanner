# ⚠️ URGENT FIX: Error 162 - No Data Available

## The Problem
You're seeing:
- ⚠ Timeout (15s) waiting for data
- "No data available from IBKR"
- All volumes = 0

**This is Error 162: IP Address Mismatch**

## Quick Fix (Do This Now)

### Step 1: Close Everything
1. **Close the scanner application** (completely exit)
2. **Close TWS or IB Gateway** (completely exit, not just minimize)
3. Wait 10 seconds

### Step 2: Restart TWS/Gateway
1. **Open TWS or IB Gateway**
2. **Log in** (this is critical - you must log in)
3. **Wait for TWS to fully connect**:
   - All connection indicators should be green
   - Wait an additional 30 seconds after login
   - Make sure you see "Connected" status

### Step 3: Restart Scanner
1. **Open the scanner application**
2. **Click "Connect"**
3. Should show "Connected" (green)

### Step 4: Test Again
1. Load your tickers
2. Click "Scan RTH"
3. You should now see data (not timeouts)

## Why This Happens

IBKR tracks:
- Your TWS login IP address
- Your API connection IP address

If they don't match → Error 162 → No historical data

This is a **security feature** to prevent unauthorized API access.

## Prevention

- Always start TWS/Gateway **BEFORE** the scanner
- Don't restart TWS while scanner is connected
- Keep TWS/Gateway running continuously
- Use IB Gateway instead of TWS (more stable for API)

## Still Not Working?

If you still get timeouts after restarting:

1. **Check TWS API Settings**:
   - Configure → API → Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Check "Trusted IPs" includes 127.0.0.1

2. **Try IB Gateway**:
   - Close TWS
   - Open IB Gateway
   - Log in
   - Update port in scanner to 4001 (paper) or 4002 (live)

3. **Check Firewall**:
   - Windows Firewall might be blocking
   - Allow TWS/Gateway through firewall

4. **Verify Market Data Subscription**:
   - In TWS: Account → Market Data Subscriptions
   - Ensure you have data for the symbols you're testing

## Success Indicators

After fix, you should see:
```
Requesting historical data for TSLA...
  ✓ Received 2340 bars for TSLA
  ✓ DataFrame shape: (2340, 6)
    5m: Today=125,000 | Avg10D=45,000 | RelVol=2.78x
```

NOT:
```
⚠ Timeout (15s) waiting for data
✗ No bars returned
```

