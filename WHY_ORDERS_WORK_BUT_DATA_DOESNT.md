# Why Orders Work But Historical Data Doesn't

## Your Situation

✅ **Orders work** - You can send orders with same account/environment
❌ **Historical data times out** - 15 second timeout, no data returned

## This Means

If orders work, it's **NOT Error 162** (or Error 162 only affects historical data).

## Possible Causes

### 1. **Market Data Subscription Issue** (Most Likely)

**Historical data requires a market data subscription**, but order placement doesn't.

**Check:**
- IB Gateway → Account → Market Data Subscriptions
- Ensure you have historical data enabled
- Paper accounts may have limited historical data

**Solution:**
- Subscribe to market data for the symbols you're testing
- Or use a different data source for historical data

### 2. **Multiple API Connections**

If your other project is connected to the same IB Gateway:
- **Same client_id** → Conflicts
- **Different client_id** → Should be OK, but might cause issues

**Check:**
- Are both projects connected to IB Gateway at the same time?
- Are they using different `client_id` values?

**Solution:**
- Use different `client_id` for each connection (1, 2, 3, etc.)
- Or disconnect the other project when testing

### 3. **Historical Data Permissions**

Historical data might require different permissions than order placement.

**Check:**
- IB Gateway → Account → Permissions
- Ensure historical data access is enabled

### 4. **Market Data Farm Connection**

Notice in your output:
```
⚠ IBKR Warning 2107: HMDS data farm connection is inactive
```

**HMDS** = Historical Market Data Service

This suggests historical data service might not be fully connected.

**Solution:**
- Wait longer for all data farms to connect
- Check if HMDS connection becomes active

### 5. **Paper Account Limitations**

Paper trading accounts often have:
- Limited historical data
- Delayed data
- Some symbols not available

**Check:**
- Are you using paper or live account?
- Try a well-known symbol like AAPL
- Try during market hours

## Quick Diagnostic

### Test 1: Check Other Project Connection

1. **Disconnect your other project** from IB Gateway
2. **Wait 10 seconds**
3. **Test historical data again**

If it works → **Multiple connection conflict**

### Test 2: Check Market Data Subscription

1. **IB Gateway → Account → Market Data Subscriptions**
2. **Check if you have historical data enabled**
3. **Check if TSLA (or your test symbol) is subscribed**

If not subscribed → **Subscription issue**

### Test 3: Try Different Symbol

1. **Test with AAPL** (most reliable):
   ```bash
   python test_ibkr_connection.py
   ```
   (Change test_ticker to "AAPL" in the script)

If AAPL works but TSLA doesn't → **Symbol-specific subscription issue**

### Test 4: Check Client ID

1. **Check your other project's client_id**
2. **Make sure scanner uses different client_id**

In `config.py`:
```python
client_id: int = 2  # Change from 1 to 2 (or any unique number)
```

## Most Likely Cause

Based on your situation (orders work, data doesn't):

**Market Data Subscription** - Historical data requires a subscription that you might not have, or it's not enabled for the symbols you're testing.

## Solution

### Step 1: Check Market Data Subscription

1. **IB Gateway → Account → Market Data Subscriptions**
2. **Verify you have historical data enabled**
3. **Check if your test symbols (TSLA, etc.) are subscribed**

### Step 2: Try Well-Known Symbol

Test with AAPL instead of TSLA to see if it's symbol-specific.

### Step 3: Check Other Project

1. **Disconnect other project** from IB Gateway
2. **Test again**

### Step 4: Use Different Client ID

Update `config.py`:
```python
client_id: int = 2  # Use different ID than other project
```

## Why Orders Work But Data Doesn't

- **Order placement** = Account access (works with basic API)
- **Historical data** = Market data subscription (requires additional subscription)

These are **different services** with **different requirements**.

## Next Steps

1. **Check market data subscriptions** in IB Gateway
2. **Disconnect other project** and test
3. **Try AAPL** instead of TSLA
4. **Use different client_id** if both projects running

