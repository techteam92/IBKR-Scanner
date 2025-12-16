# Fix: Connection Refused Error

## The Error

```
ConnectionRefusedError: The remote computer refused the network connection
```

This means the scanner **cannot connect** to TWS/Gateway at all.

## Common Causes

1. **TWS/Gateway is not running**
2. **API is not enabled** in TWS/Gateway
3. **Wrong port number** (7497 vs 4001)
4. **Firewall blocking** the connection
5. **TWS/Gateway not listening** on the API port

## Quick Fix Checklist

### Step 1: Check TWS/Gateway is Running

1. **Look for TWS or IB Gateway** in your taskbar/system tray
2. **If not running**: Start TWS or IB Gateway
3. **Make sure you're LOGGED IN**

### Step 2: Enable API in TWS/Gateway

1. **TWS → Configure → API → Settings**
2. ✅ **"Enable ActiveX and Socket Clients"** = **ON** (this is critical!)
3. **"Socket port"**: Should be `7497` (TWS) or `4001` (Gateway)
4. **"Trusted IPs"**: Leave empty or add `127.0.0.1`
5. **Click "OK"**
6. **Restart TWS/Gateway** (important - settings only apply after restart)

### Step 3: Verify Port Number

**For TWS:**
- Paper trading: Port `7497`
- Live trading: Port `7496`

**For IB Gateway:**
- Paper trading: Port `4001`
- Live trading: Port `4002`

**Check your `config.py`:**
```python
port: int = 7497  # Make sure this matches TWS/Gateway port
```

### Step 4: Check Firewall

**Windows Firewall might be blocking:**

1. **Windows Security → Firewall & network protection**
2. **Allow an app through firewall**
3. **Find "Trader Workstation" or "IB Gateway"**
4. ✅ **Check both "Private" and "Public"**
5. **If not listed**: Click "Allow another app" and add TWS/Gateway

### Step 5: Test Connection

```bash
python test_ibkr_connection.py
```

## Detailed Diagnosis

### Check if Port is Listening

**On Windows (PowerShell):**
```powershell
netstat -an | findstr "7497"
```

Should show:
```
TCP    127.0.0.1:7497    0.0.0.0:0    LISTENING
```

If you see nothing, TWS/Gateway is not listening on that port.

### Check TWS/Gateway Status

1. **Look at TWS/Gateway window**
2. **Check connection status** (should be green/connected)
3. **Check if API is enabled** (Configure → API → Settings)

### Try Different Port

If using TWS on port 7497 doesn't work:

1. **Try IB Gateway on port 4001**
2. **Update `config.py`**:
   ```python
   port: int = 4001  # IB Gateway
   ```
3. **Restart and test**

## Step-by-Step Fix

### If TWS is Running:

1. **TWS → Configure → API → Settings**
2. ✅ **Enable "Enable ActiveX and Socket Clients"**
3. **Set port to 7497** (or check what it's set to)
4. **Click OK**
5. **Restart TWS** (close completely and reopen)
6. **Log in**
7. **Wait for connection** (green)
8. **Test**: `python test_ibkr_connection.py`

### If Using IB Gateway:

1. **IB Gateway → Configure → API → Settings**
2. ✅ **Enable "Enable ActiveX and Socket Clients"**
3. **Set port to 4001** (paper) or `4002` (live)
4. **Click OK**
5. **Restart IB Gateway**
6. **Log in**
7. **Update `config.py`** to use port 4001
8. **Test**: `python test_ibkr_connection.py`

## Common Mistakes

❌ **API not enabled** - Most common cause!
❌ **Wrong port** - Using 7497 when Gateway uses 4001
❌ **TWS not restarted** - Settings only apply after restart
❌ **Not logged in** - TWS must be logged in
❌ **Firewall blocking** - Windows Firewall blocking connection

## Success Indicators

After fix, you should see:
```
✓ Connected successfully
```

NOT:
```
✗ Failed to connect
ConnectionRefusedError
```

## Still Not Working?

1. **Check TWS logs**: Help → Logs → Look for API errors
2. **Try IB Gateway** instead of TWS
3. **Check Windows Event Viewer** for firewall blocks
4. **Disable firewall temporarily** to test (re-enable after!)
5. **Contact IBKR support** if issue persists

