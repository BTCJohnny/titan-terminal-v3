# Coinglass Backfill Endpoint Probe
**Date:** 2026-03-19
**Results:** 3 PASS | 2 FAIL (param issues, fixed)

## Funding Rate History
- Path: `/api/futures/funding-rate/history`
- **FAIL** without exchange param: `Required String parameter 'exchange' is not present`
- **PASS** with `symbol=BTCUSDT, exchange=Binance, interval=1d, limit=180`
- Shape: list of 180 items, keys: `['time', 'open', 'high', 'low', 'close']`
- Values are OHLC funding rate as percentage strings (e.g., `"0.002418"` = 0.002418%)
- Sample: `{"time": 1758412800000, "open": "-0.005343", "high": "0.006878", "low": "-0.005916", "close": "0.006655"}`
- Range: 2025-09-21 to 2026-03-19

## Liquidation Aggregated History
- Path: `/api/futures/liquidation/aggregated-history`
- **FAIL** without exchange_list: `Required String parameter 'exchange_list' is not present`
- **FAIL** with BTCUSDT pair format: returns 0 items (needs coin symbol, NOT pair)
- **PASS** with `symbol=BTC, exchange_list=Binance, interval=1d, limit=180`
- Shape: list of 180 items, keys: `['time', 'aggregated_long_liquidation_usd', 'aggregated_short_liquidation_usd']`
- Sample: `{"time": 1758412800000, "aggregated_long_liquidation_usd": 2021029.80418, "aggregated_short_liquidation_usd": 1204379.00253}`
- Range: 2025-09-21 to 2026-03-19

## Key Learnings
- Funding Rate History: needs PAIR format (BTCUSDT) + explicit exchange
- Liquidation History: needs COIN format (BTC) + `exchange_list` param (not `exchange`)
- Both support 180-day depth at 1d interval on Hobbyist plan
