# Coinglass v2 Re-Probe — Corrected v4 Paths
**Date:** 2026-03-19 11:44
**Available:** 8/22 | **Blocked:** 14/22 | **Error:** 0/22
**Failure breakdown:** 2 tier-blocked, 7 wrong path, 3 bad params

## BASELINE (re-confirm)
- **PASS** `/api/futures/funding-rate/exchange-list` — Funding Rate Exchange List
  - Shape: list of 1055 items, keys: ['symbol', 'stablecoin_margin_list', 'token_margin_list']
  - Sample: `{"symbol": "BTC", "stablecoin_margin_list": [{"exchange": "Binance", "funding_rate_interval": 8, "funding_rate": -0.001274, "next_funding_time": 1773936000000}, {"exchange": "OKX", "funding_rate_inter`
- **PASS** `/api/futures/liquidation/coin-list` — Liquidation Coin List
  - Shape: list of 557 items, keys: ['symbol', 'liquidation_usd_24h', 'long_liquidation_usd_24h', 'short_liquidation_usd_24h', 'liquidation_usd_12h', 'long_liquidation_usd_12h', 'short_liquidation_usd_12h', 'liquidation_usd_4h', 'long_liquidation_usd_4h', 'short_liquidation_usd_4h', 'liquidation_usd_1h', 'long_liquidation_usd_1h', 'short_liquidation_usd_1h']
  - Sample: `{"symbol": "EDU", "liquidation_usd_24h": 8561.0821283, "long_liquidation_usd_24h": 8530.0751283, "short_liquidation_usd_24h": 31.007, "liquidation_usd_12h": 123.5688, "long_liquidation_usd_12h": 123.5`
- **PASS** `/api/option/max-pain` — Options Max Pain
  - Shape: list of 12 items, keys: ['date', 'call_open_interest_market_value', 'put_open_interest', 'put_open_interest_market_value', 'max_pain_price', 'call_open_interest', 'call_open_interest_notional', 'put_open_interest_notional']
  - Sample: `{"date": "260320", "call_open_interest_market_value": 5545337.9, "put_open_interest": 11772.55, "put_open_interest_market_value": 5047315.15, "max_pain_price": "70000", "call_open_interest": 12510.09,`
- **PASS** `/api/option/info` — Options Info
  - Shape: list of 6 items, keys: ['exchange_name', 'open_interest', 'oi_market_share', 'open_interest_change_24h', 'open_interest_usd', 'volume_usd_24h', 'volume_change_percent_24h']
  - Sample: `{"exchange_name": "All", "open_interest": 615703.12, "oi_market_share": 100, "open_interest_change_24h": 2.98, "open_interest_usd": 43118836112.08054, "volume_usd_24h": 4272923865.94353, "volume_chang`

## PRIORITY — corrected v4 paths
- **PASS** `/api/futures/open-interest/aggregated-history` — #2 OI Aggregated History
  - Shape: list of 6 items, keys: ['time', 'open', 'high', 'low', 'close']
  - Sample: `{"time": 1773835200000, "open": "49671839592", "high": "49691681139", "low": "48820625457", "close": "48970945539"}`
- **FAIL** `/api/futures/global-long-short-account-ratio/history` — #3 Global L/S Account Ratio — The requested pair does not exist on the exchange. Please check the documentation to view supported 
- **FAIL** `/api/futures/aggregated-taker-buy-sell-volume/history` — #4 Taker Buy/Sell Aggregated — The requested interval is not available for your current API plan.
- **PASS** `/api/etf/bitcoin/flow-history` — #5 BTC ETF Flows
  - Shape: list of 564 items, keys: ['timestamp', 'flow_usd', 'price_usd', 'etf_flows']
  - Sample: `{"timestamp": 1704931200000, "flow_usd": 655300000, "price_usd": 46663, "etf_flows": [{"etf_ticker": "GBTC", "flow_usd": -95100000}, {"etf_ticker": "IBIT", "flow_usd": 111700000}, {"etf_ticker": "FBTC`
- **PASS** `/api/index/fear-greed-history` — #6 Fear & Greed Index
  - Shape: dict with keys: ['data_list', 'price_list', 'time_list']
  - Sample: `{"data_list": [30.0, 15.0, 40.0, 24.0, 11.0, 8.0, 36.0, 30.0, 44.0, 54.0, 31.0, 42.0, 35.0, 55.0, 71.0, 67.0, 74.0, 63.0, 67.0, 74.0, 54.0, 44.0, 39.0, 31.0, 33.0, 37.0, 44.0, 41.0, 38.0, 47.0, 56.0, `
- **FAIL** `/api/coinbase-premium-index` — #7 Coinbase Premium — Server Error

## BONUS — additional v4 endpoints
- **PASS** `/api/futures/open-interest/exchange-list` — OI Exchange List
  - Shape: list of 25 items, keys: ['exchange', 'symbol', 'open_interest_usd', 'open_interest_quantity', 'open_interest_by_coin_margin', 'open_interest_by_stable_coin_margin', 'open_interest_quantity_by_coin_margin', 'open_interest_quantity_by_stable_coin_margin', 'open_interest_change_percent_5m', 'open_interest_change_percent_15m', 'open_interest_change_percent_30m', 'open_interest_change_percent_1h', 'open_interest_change_percent_4h', 'open_interest_change_percent_24h']
  - Sample: `{"exchange": "All", "symbol": "BTC", "open_interest_usd": 48396871556.9403, "open_interest_quantity": 691248.7791, "open_interest_by_coin_margin": 5910914270.66, "open_interest_by_stable_coin_margin":`
- **FAIL** `/api/futures/aggregated-liquidation/history` — Coin Liquidation History — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/top-long-short-account-ratio/history` — Top L/S Account Ratio — The requested pair does not exist on the exchange. Please check the documentation to view supported 
- **FAIL** `/api/futures/top-long-short-position-ratio/history` — Top L/S Position Ratio — The requested pair does not exist on the exchange. Please check the documentation to view supported 
- **FAIL** `/api/futures/basis` — Futures Basis — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/aggregated-taker-buy-sell-volume/cvd-history` — Aggregated CVD — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/hyperliquid/whale-alert` — Hyperliquid Whale Alert — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/hyperliquid/whale-position` — Hyperliquid Whale Position — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/exchange/balance-list` — Exchange Balance List — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/token/unlock-list` — Token Unlock List — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/index/bitcoin-dominance` — Bitcoin Dominance — Upgrade plan
- **FAIL** `/api/index/altcoin-season` — Altcoin Season Index — Upgrade plan

## Available Endpoints (Hobbyist)
- `/api/futures/funding-rate/exchange-list` — Funding Rate Exchange List
- `/api/futures/liquidation/coin-list` — Liquidation Coin List
- `/api/option/max-pain` — Options Max Pain
- `/api/option/info` — Options Info
- `/api/futures/open-interest/aggregated-history` — #2 OI Aggregated History
- `/api/etf/bitcoin/flow-history` — #5 BTC ETF Flows
- `/api/index/fear-greed-history` — #6 Fear & Greed Index
- `/api/futures/open-interest/exchange-list` — OI Exchange List