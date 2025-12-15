# Fix for Error 162: "Trading TWS session is connected from a different IP address"

## Quick Fix Steps

### Step 1: Close Everything
1. Close the scanner application
2. Close TWS or IB Gateway completely
3. Wait 10 seconds

### Step 2: Restart TWS/Gateway
1. Open TWS or IB Gateway
2. **Log in** (important!)
3. Wait for TWS to fully connect (all indicators green)
4. Wait an additional 30 seconds for full initialization

### Step 3: Start Scanner
1. Open the scanner application
2. Click "Connect"
3. Should show "Connected" (green)

### Step 4: Test
1. Load tickers
2. Click "Scan RTH"
3. Check console - should NOT see Error 162

## Why This Happens

IBKR security feature:
- TWS login is tracked by IP address
- API connections are also tracked by IP
- If they don't match → Error 162
- This prevents unauthorized API access

## Common Causes

1. **TWS restarted but scanner didn't** - IP changed
2. **Multiple TWS instances** - Confusion about which session
3. **Network change** - IP address changed
4. **TWS on different machine** - Can't work (must be same machine)

## Prevention

- Always start TWS/Gateway **before** the scanner
- Don't restart TWS while scanner is connected
- Use IB Gateway instead of TWS (more stable for API)
- Keep TWS/Gateway running continuously

## Still Getting Error 162?

1. **Check TWS API Settings**:
   - Configure → API → Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Check "Trusted IPs" includes 127.0.0.1

2. **Try IB Gateway**:
   - Often more stable for API connections
   - Port 4001 (paper) or 4002 (live)

3. **Check Firewall**:
   - Windows Firewall might be blocking
   - Allow TWS/Gateway through firewall

4. **Restart Computer**:
   - Sometimes network stack needs reset
   - Last resort solution

## Success Indicators

After fix, you should see:
```
Requesting historical data for AAPL: duration=12 D, bar_size=1 min, useRTH=True
Received 2340 bars for AAPL
DataFrame shape for AAPL: (2340, 6)
```

NOT:
```
Error 162, reqId X: Historical Market Data Service error message:Trading TWS session is connected from a different IP address
No bars returned for AAPL
```

