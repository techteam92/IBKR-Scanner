# IBKR API Historical Data Request Fixes

Based on the [IBKR TWS API Documentation](https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#requesting-time-and-sales), here are the issues and fixes:

## Issues Found

### 1. **endDateTime Parameter**

**Problem**: According to IBKR docs, if `endDateTime` is `None`, we should pass an **empty string `""`** instead.

**Fix Applied**: 
```python
end_date_time = "" if end_time is None else end_time
```

### 2. **Contract Qualification**

**Problem**: Contract must be fully qualified (have `conId`) before requesting historical data.

**Fix Applied**: Added explicit contract qualification check before the request.

### 3. **Pacing Violations**

**IBKR Limitations**:
- No identical requests within 15 seconds
- Max 6 requests for same contract/exchange/tick type within 2 seconds
- Max 60 requests within 10 minutes

**Current Issue**: We're making multiple requests quickly, which might violate pacing rules.

### 4. **Data Availability**

**IBKR Restrictions**:
- Bars ≤ 30 seconds: Only available for past 6 months
- Expired futures: Up to 2 years from expiration
- Some data may not be available

### 5. **Asynchronous Nature**

In `ib_insync`, `reqHistoricalData` is asynchronous. The data arrives via the `historicalData` event, not as a direct return value.

## What We Fixed

1. ✅ **endDateTime handling**: Now passes `""` if `None`
2. ✅ **Contract qualification**: Explicitly checks and qualifies before request
3. ✅ **Better logging**: Shows exact parameters being sent

## What Still Needs Attention

1. **Pacing**: Add delays between requests to avoid violations
2. **Error handling**: Check for pacing violation errors
3. **Data availability**: Verify requested data is actually available

## Testing

Run the test again:
```bash
python test_ibkr_connection.py
```

The enhanced logging will show:
- Exact parameters being sent
- Contract qualification status
- Response details

## References

- [IBKR TWS API Documentation](https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#requesting-time-and-sales)
- [Historical Data Limitations](https://interactivebrokers.github.io/tws-api/historical_limitations.html)

