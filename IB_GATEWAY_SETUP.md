# IB Gateway Setup Guide

## Port Configuration

**IB Gateway uses different ports than TWS:**

- **Paper Trading**: Port `4001`
- **Live Trading**: Port `4002`

**TWS uses:**
- Paper: `7497`
- Live: `7496`

## Quick Setup

### Step 1: Configure IB Gateway API

1. **Open IB Gateway**
2. **Log in** (important!)
3. **Configure → API → Settings** (or Settings → API)
4. **Enable these settings**:
   - ✅ **"Enable ActiveX and Socket Clients"** = ON
   - **"Socket port"**: 
     - `4001` for paper trading
     - `4002` for live trading
   - **"Trusted IPs"**: Leave **EMPTY** (allows all, including localhost)
5. **Click "OK"**
6. **Restart IB Gateway** (settings only apply after restart)

### Step 2: Update Scanner Config

The `config.py` file has been updated to use port `4001` by default (IB Gateway paper trading).

If you're using **live trading**, change it to `4002`:

```python
port: int = 4002  # IB Gateway live trading
```

### Step 3: Verify Connection

1. **Make sure IB Gateway is running**
2. **Make sure you're logged in**
3. **Run test**:
   ```bash
   python test_ibkr_connection.py
   ```

Should see:
```
✓ Connected successfully
```

## Common Issues

### Connection Refused

**Cause**: API not enabled or wrong port

**Fix**:
1. IB Gateway → Configure → API → Settings
2. ✅ Enable "Enable ActiveX and Socket Clients"
3. Set port to `4001` (paper) or `4002` (live)
4. **Restart IB Gateway**
5. Test again

### Error 162 (IP Mismatch)

**Cause**: IP address mismatch

**Fix**:
1. Close IB Gateway completely
2. Close scanner
3. Restart IB Gateway and log in
4. Wait for full connection
5. Restart scanner and connect

### Wrong Port

**Symptoms**: Connection refused even though API is enabled

**Fix**: 
- Check IB Gateway shows port `4001` (paper) or `4002` (live)
- Make sure `config.py` matches:
  ```python
  port: int = 4001  # Must match IB Gateway port
  ```

## Advantages of IB Gateway

✅ **Lighter** - Uses less resources than TWS
✅ **Better for API** - Designed for automated trading
✅ **More stable** - Fewer connection issues
✅ **Server-friendly** - Works better on VPS/servers

## Verification Checklist

- [ ] IB Gateway is running
- [ ] You are logged in to IB Gateway
- [ ] API is enabled (Configure → API → Settings)
- [ ] Port is set to `4001` (paper) or `4002` (live)
- [ ] `config.py` port matches IB Gateway port
- [ ] IB Gateway restarted after enabling API
- [ ] Connection test succeeds

## Current Configuration

Your `config.py` is now set to:
```python
port: int = 4001  # IB Gateway paper trading
```

If you need live trading, change to `4002`.

