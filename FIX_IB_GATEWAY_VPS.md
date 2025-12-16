# Fix IB Gateway on VPS - Error 162 Timeout

## Current Status

✅ **Connection successful** - Connected to IB Gateway on port 4001
⚠️ **Error 321** - Read-Only mode (not critical, just informational)
❌ **Timeouts** - Historical data requests timing out (Error 162 - IP mismatch)

## The Problem

You're on a VPS with:
- **Public IP**: `85.208.197.124`
- **IB Gateway login IP**: `85.208.197.124` (when you logged in)
- **API connection IP**: `127.0.0.1` (localhost)
- **IBKR sees different IPs** → Error 162 → Blocks historical data

## Solution: Configure IB Gateway API Settings

### Step 1: Open IB Gateway API Settings

1. **IB Gateway → Configure → API → Settings**
   (or **Settings → API** depending on Gateway version)

### Step 2: Configure Settings

1. ✅ **"Enable ActiveX and Socket Clients"** = **ON**
2. **"Socket port"**: `4001` (should already be set)
3. **"Read-Only API"**: 
   - ✅ Checked = Read-only (safer, but Error 321 is normal)
   - ❌ Unchecked = Full access (if you need trading)
4. **"Trusted IPs"**: **LEAVE EMPTY** (this is critical!)
   - Empty = Allows connections from any IP (including localhost)
   - If you set specific IPs, it might block localhost

### Step 3: Restart IB Gateway

1. **Close IB Gateway completely**
2. **Restart IB Gateway**
3. **Log in**
4. **Wait for full connection** (all indicators green)

### Step 4: Test Again

```bash
python test_ibkr_connection.py
```

## Why "Trusted IPs" Must Be Empty

On a VPS:
- IB Gateway logs in with public IP: `85.208.197.124`
- Scanner connects via localhost: `127.0.0.1`
- If "Trusted IPs" restricts to specific IPs, it might block localhost
- **Empty = Allows all IPs** = Works with IP mismatch

## Alternative: Add Both IPs

If leaving "Trusted IPs" empty doesn't work:

1. **"Trusted IPs"**: Add both:
   - `127.0.0.1` (localhost)
   - `85.208.197.124` (your VPS public IP)
2. **Restart IB Gateway**
3. **Test again**

## About Error 321

**Error 321: "Read-Only mode"** is **NOT blocking** historical data. It just means:
- API is in read-only mode (can't place orders)
- This is normal and safe
- Historical data requests should still work

**If you need full API access:**
- IB Gateway → Configure → API → Settings
- Uncheck "Read-Only API"
- Restart IB Gateway

## Verification

After configuring and restarting:

1. **Run test**:
   ```bash
   python test_ibkr_connection.py
   ```

2. **Should see**:
   ```
   ✓ Connected successfully
   Requesting historical data for TSLA...
   ✓ Received 2340 bars for TSLA
   ```

3. **NOT**:
   ```
   ⚠ TIMEOUT (15s)
   ✗ No data returned
   ```

## Quick Checklist

- [ ] IB Gateway is running
- [ ] You are logged in
- [ ] API Settings → "Enable ActiveX and Socket Clients" = ON
- [ ] API Settings → "Trusted IPs" = **EMPTY** (or includes 127.0.0.1)
- [ ] IB Gateway restarted after changing settings
- [ ] Test: `python test_ibkr_connection.py`

## Still Getting Timeouts?

If timeouts persist after setting "Trusted IPs" to empty:

1. **Check IB Gateway logs**:
   - Look for Error 162 messages
   - Check if IP restrictions are being applied

2. **Try adding both IPs** to "Trusted IPs":
   - `127.0.0.1`
   - `85.208.197.124`

3. **Restart everything**:
   - Close IB Gateway
   - Close scanner/test
   - Restart IB Gateway
   - Log in
   - Wait for connection
   - Test again

4. **Check firewall**:
   - Windows Firewall might be blocking
   - Allow IB Gateway through firewall

## Summary

The key fix is: **"Trusted IPs" = EMPTY** in IB Gateway API settings.

This allows connections from any IP, which resolves the IP mismatch issue on VPS.

