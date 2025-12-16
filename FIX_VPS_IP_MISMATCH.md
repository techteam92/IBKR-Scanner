# Fix IP Mismatch on VPS/Server (Error 162)

## The Problem

On a VPS/server:
- **TWS login IP**: `85.208.197.124` (public IP)
- **API connection IP**: `127.0.0.1` (localhost)
- **IBKR sees different IPs** → Error 162 → No historical data

## Solution 1: Configure TWS API to Accept Localhost (Easiest)

### Step 1: Configure TWS API Settings

1. **Open TWS**
2. **Configure → API → Settings**
3. **Enable these settings**:
   - ✅ **"Enable ActiveX and Socket Clients"**
   - ✅ **"Read-Only API"** (uncheck if you need full access)
   - **"Socket port"**: `7497` (or your configured port)
   - **"Trusted IPs"**: 
     - Option A: Leave **EMPTY** (allows all IPs)
     - Option B: Add `127.0.0.1` and `85.208.197.124`
4. **Click "OK"**
5. **Restart TWS**

### Step 2: Restart TWS

1. **Close TWS completely**
2. **Restart TWS**
3. **Log in**
4. **Wait for full connection** (all green)

### Step 3: Test

```bash
python test_ibkr_connection.py
```

## Solution 2: Use IB Gateway (More Reliable on VPS)

IB Gateway is lighter and often works better on servers:

### Step 1: Download IB Gateway

1. Download from IBKR website
2. Install on your VPS

### Step 2: Configure IB Gateway

1. **Open IB Gateway**
2. **Log in**
3. **Configure → API → Settings**:
   - ✅ **"Enable ActiveX and Socket Clients"**
   - **"Socket port"**: `4001` (paper) or `4002` (live)
   - **"Trusted IPs"**: Leave empty or add `127.0.0.1`

### Step 3: Update Scanner Config

Edit `config.py`:
```python
@dataclass
class IBKRConfig:
    host: str = "127.0.0.1"
    port: int = 4001  # Changed from 7497 to 4001 (Gateway)
    client_id: int = 1
    timeout: int = 30
```

### Step 4: Test

```bash
python test_ibkr_connection.py
```

## Solution 3: Force TWS to Bind to Localhost

### Method A: Windows Hosts File (If on Windows VPS)

1. **Edit hosts file** (as Administrator):
   ```
   C:\Windows\System32\drivers\etc\hosts
   ```
2. **Add this line**:
   ```
   127.0.0.1 localhost
   ```
3. **Save and restart TWS**

### Method B: Configure Network Binding

1. **In TWS → Configure → API → Settings**
2. **Set "Trusted IPs" to**: `127.0.0.1`
3. **Restart TWS**

## Solution 4: Use SSH Tunneling (If Accessing Remotely)

If you're accessing the VPS remotely via SSH:

### On Your Local Machine:

```bash
ssh -L 7497:localhost:7497 user@85.208.197.124
```

This creates a tunnel so:
- Your local machine connects to `localhost:7497`
- Tunnel forwards to VPS `localhost:7497`
- Both use same IP context

### Then Connect Scanner:

- Scanner connects to `127.0.0.1:7497` (local)
- Tunnel forwards to VPS
- TWS on VPS sees localhost connection

## Solution 5: Configure TWS to Only Accept Localhost

### In TWS API Settings:

1. **Configure → API → Settings**
2. **"Trusted IPs"**: Enter only `127.0.0.1`
3. **This forces TWS to only accept localhost connections**
4. **Restart TWS**

## Solution 6: Use Docker/Container (Advanced)

If TWS is in a container:

1. **Bind TWS to localhost in container**
2. **Map port**: `127.0.0.1:7497:7497`
3. **Ensure container network uses host mode or bridge correctly**

## Recommended Approach for VPS

**Best Solution**: Use **IB Gateway** with **localhost binding**

1. **Install IB Gateway** (lighter than TWS)
2. **Configure API to accept localhost** (`127.0.0.1`)
3. **Update scanner port to 4001** (Gateway)
4. **Restart everything**

## Verification Steps

After applying a solution:

1. **Run diagnostic**:
   ```bash
   python check_ip_addresses.py
   ```

2. **Check TWS/Gateway API settings**:
   - Should show "Enable ActiveX and Socket Clients" = ON
   - "Trusted IPs" should include `127.0.0.1` or be empty

3. **Test connection**:
   ```bash
   python test_ibkr_connection.py
   ```

4. **Should see**:
   ```
   ✓ Received 2340 bars for AAPL
   ```
   NOT:
   ```
   ⚠ TIMEOUT (15s)
   ```

## Troubleshooting

### Still Getting Timeouts?

1. **Check TWS logs**:
   - TWS → Help → Logs
   - Look for Error 162 messages

2. **Verify API is enabled**:
   - TWS → Configure → API → Settings
   - Must show "Enable ActiveX and Socket Clients" = ON

3. **Check firewall**:
   - Windows Firewall might block localhost connections
   - Allow TWS/Gateway through firewall

4. **Try different port**:
   - Gateway port 4001 instead of TWS port 7497
   - Sometimes Gateway works better on VPS

## Quick Fix Checklist

- [ ] TWS API Settings → "Enable ActiveX and Socket Clients" = ON
- [ ] TWS API Settings → "Trusted IPs" = empty OR includes `127.0.0.1`
- [ ] Restart TWS completely
- [ ] Log in to TWS
- [ ] Wait for full connection (all green)
- [ ] Scanner connects to `127.0.0.1:7497`
- [ ] Test: `python test_ibkr_connection.py`

## Why This Happens on VPS

VPS/servers have:
- **Public IP**: `85.208.197.124` (what internet sees)
- **Localhost**: `127.0.0.1` (internal)

When TWS logs in, it might use the public IP. When API connects via localhost, IBKR sees different IPs → Error 162.

**Solution**: Make both use `127.0.0.1` (localhost) by configuring TWS API settings.

