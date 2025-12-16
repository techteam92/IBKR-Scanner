# Quick Fix for VPS IP Mismatch (Error 162)

## The Issue
- TWS login IP: `85.208.197.124` (public)
- API connection IP: `127.0.0.1` (localhost)
- **Different IPs → Error 162**

## Fastest Fix (5 minutes)

### Step 1: Configure TWS API (2 min)
1. **TWS → Configure → API → Settings**
2. ✅ **"Enable ActiveX and Socket Clients"** = ON
3. **"Trusted IPs"** = **LEAVE EMPTY** (allows all)
4. Click **OK**

### Step 2: Restart TWS (1 min)
1. **Close TWS completely**
2. **Restart TWS**
3. **Log in**
4. **Wait for connection** (all green)

### Step 3: Test (2 min)
```bash
python test_ibkr_connection.py
```

Should see: `✓ Received 2340 bars for AAPL`

## Alternative: Use IB Gateway

If TWS still has issues:

1. **Install IB Gateway** (lighter, better for VPS)
2. **Configure API** (same as above)
3. **Update `config.py`**:
   ```python
   port: int = 4001  # Gateway paper trading
   ```
4. **Restart and test**

## Why This Works

By setting "Trusted IPs" to empty, TWS accepts connections from ANY IP, including localhost. This makes both TWS login and API connection work regardless of IP mismatch.

**Note**: This is safe on a VPS/server since only localhost can connect (firewall should block external access to port 7497).

