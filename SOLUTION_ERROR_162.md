# 🔴 SOLUTION: Error 162 - IP Address Mismatch

## You Are Seeing This Because:

Your terminal shows:
```
⚠ Timeout (15s) waiting for data
✗ No RTH data returned
```

**This is 100% Error 162: IP Address Mismatch**

## What Error 162 Means:

IBKR detected that:
- Your **TWS/Gateway login** is from one IP address
- Your **API connection** is from a different IP address

IBKR **blocks historical data** when this happens (security feature).

## ✅ THE FIX (Do This Exactly):

### Step 1: Close EVERYTHING
```
1. Close the scanner application (completely exit)
2. Close TWS or IB Gateway (completely exit - not just minimize)
3. Close any other IBKR applications
4. Wait 10 seconds
```

### Step 2: Restart TWS/Gateway
```
1. Open TWS or IB Gateway
2. LOG IN (this is critical!)
3. Wait for FULL connection:
   - All connection indicators GREEN
   - Status shows "Connected"
   - Wait an additional 30 seconds after login
```

### Step 3: Restart Scanner
```
1. Open the scanner application
2. Click "Connect"
3. Should show "Connected" (green)
```

### Step 4: Test
```
1. Run: python test_ibkr_connection.py
2. Should see: "✓ Received X bars for AAPL"
3. NOT: "⚠ Timeout" or "✗ No data"
```

## Why This Happens:

1. **TWS restarted** but scanner didn't → IP changed
2. **Network changed** → IP address changed
3. **Multiple TWS instances** → Confusion about which session
4. **TWS on different machine** → Can't work (must be same machine)

## Prevention:

✅ **Always start TWS/Gateway BEFORE the scanner**
✅ **Don't restart TWS while scanner is connected**
✅ **Keep TWS/Gateway running continuously**
✅ **Use IB Gateway instead of TWS** (more stable for API)

## Alternative: Use IB Gateway

If TWS continues to have issues:

1. **Close TWS completely**
2. **Open IB Gateway** (lighter, fewer issues)
3. **Log in to IB Gateway**
4. **Update port in config.py**:
   - Paper trading: `port = 4001`
   - Live trading: `port = 4002`
5. **Restart scanner and connect**

## Check TWS API Settings:

1. In TWS: **Configure → API → Settings**
2. Enable **"Enable ActiveX and Socket Clients"**
3. Check **"Trusted IPs"** includes `127.0.0.1`
4. **Socket port** should match your config (default: 7497)

## Verify It's Fixed:

After restarting, run:
```bash
python test_ibkr_connection.py
```

You should see:
```
✓ Received 2340 bars for AAPL
✓ DataFrame shape: (2340, 6)
```

NOT:
```
⚠ Timeout (15s)
✗ No data returned
```

## Still Not Working?

If you still get timeouts after restarting:

1. **Check Windows Firewall** - might be blocking
2. **Try different port** - 4001 (Gateway) instead of 7497 (TWS)
3. **Check market data subscription** - ensure you have historical data
4. **Restart computer** - sometimes network stack needs reset

## The Root Cause:

IBKR's security system tracks:
- Where you logged in from (TWS session)
- Where API requests come from (scanner connection)

If these don't match → **Error 162** → **No historical data**

This is **by design** to prevent unauthorized API access.

## Quick Checklist:

- [ ] TWS/Gateway is running
- [ ] You are LOGGED IN to TWS/Gateway
- [ ] TWS shows "Connected" (all green)
- [ ] Scanner shows "Connected" (green)
- [ ] Both started on the same machine
- [ ] No firewall blocking
- [ ] API is enabled in TWS settings

If all checked and still not working, the issue is likely:
- **Error 162** (most common) → Restart TWS/Gateway
- **No market data subscription** → Check IBKR account
- **Market closed** → Run during market hours

