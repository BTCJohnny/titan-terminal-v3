# Coinglass Fix-Probe — L/S Ratio + Coinbase Premium
**Date:** 2026-03-19 11:50
**Results:** ✅ 4 PASS | ❌ 2 FAIL | ⚠️ 0 ERROR

### ✅ Global L/S Ratio (BTCUSDT)
- Path: `/api/futures/global-long-short-account-ratio/history`
- Params: `{'symbol': 'BTCUSDT', 'exchange': 'Binance', 'interval': '4h', 'limit': '6'}`
- Shape: list of 6 items, keys: ['time', 'global_account_long_percent', 'global_account_short_percent', 'global_account_long_short_ratio']
- Sample: `{"time": 1773835200000, "global_account_long_percent": 49.17, "global_account_short_percent": 50.83, "global_account_long_short_ratio": 0.97}`

### ✅ Top L/S Account Ratio (BTCUSDT)
- Path: `/api/futures/top-long-short-account-ratio/history`
- Params: `{'symbol': 'BTCUSDT', 'exchange': 'Binance', 'interval': '4h', 'limit': '6'}`
- Shape: list of 6 items, keys: ['time', 'top_account_long_percent', 'top_account_short_percent', 'top_account_long_short_ratio']
- Sample: `{"time": 1773835200000, "top_account_long_percent": 51.52, "top_account_short_percent": 48.48, "top_account_long_short_ratio": 1.06}`

### ✅ Top L/S Position Ratio (BTCUSDT)
- Path: `/api/futures/top-long-short-position-ratio/history`
- Params: `{'symbol': 'BTCUSDT', 'exchange': 'Binance', 'interval': '4h', 'limit': '6'}`
- Shape: list of 6 items, keys: ['time', 'top_position_long_percent', 'top_position_short_percent', 'top_position_long_short_ratio']
- Sample: `{"time": 1773835200000, "top_position_long_percent": 50.49, "top_position_short_percent": 49.51, "top_position_long_short_ratio": 1.02}`

### ❌ Coinbase Premium (no params)
- Path: `/api/coinbase-premium-index`
- Params: `{}`
- Code: 500
- Error: Server Error

### ✅ Coinbase Premium (with interval)
- Path: `/api/coinbase-premium-index`
- Params: `{'interval': '4h', 'limit': '6'}`
- Shape: list of 6 items, keys: ['time', 'premium', 'premium_rate']
- Sample: `{"time": 1773835200, "premium": 0.75, "premium_rate": 0.001}`

### ❌ Coinbase Premium (alt path)
- Path: `/api/indicator/coinbase-premium-index`
- Params: `{}`
- Code: 404
- Error: {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coinglass.com/reference/endpoint-overview"}

## Verdict
- L/S Ratio with BTCUSDT: **3/3** working
- Coinbase Premium: **1/3** working