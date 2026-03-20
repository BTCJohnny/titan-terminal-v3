# Coinglass Hobbyist Tier — Endpoint Probe Results
**Date:** 2026-03-19 11:37
**Plan:** Hobbyist (30 req/min)
**Available:** 6/47 | **Blocked:** 41/47 | **Error:** 0/47

## BASELINE (should all pass)
- **PASS** `/api/futures/liquidation/coin-list` — Liquidation Coin List — list of 557 items, keys: ['symbol', 'liquidation_usd_24h', 'long_liquidation_usd_24h', 'short_liquidation_usd_24h', 'liquidation_usd_12h']
- **PASS** `/api/option/max-pain` — Options Max Pain — list of 12 items, keys: ['date', 'call_open_interest_market_value', 'put_open_interest', 'put_open_interest_market_value', 'max_pain_price']
- **PASS** `/api/option/info` — Options Info — list of 6 items, keys: ['exchange_name', 'open_interest', 'oi_market_share', 'open_interest_change_24h', 'open_interest_usd']

## FUTURES DERIVATIVES
- **PASS** `/api/futures/funding-rate/exchange-list` — Funding Rate Exchange List — list of 1055 items, keys: ['symbol', 'stablecoin_margin_list', 'token_margin_list']
- **FAIL** `/api/futures/open-interest/ohlc-aggregated-history` — OI Aggregated History — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/long-short-ratio/global-account` — Global L/S Account Ratio — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/long-short-ratio/top-account` — Top L/S Account Ratio — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/long-short-ratio/top-position` — Top L/S Position Ratio — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/taker-buy-sell/aggregated-history` — Taker Buy/Sell History (Aggregated) — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/taker-buy-sell/history` — Taker Buy/Sell History (Pair) — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/long-short-ratio/net-position` — Net Long/Short Position — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/taker-buy-sell/cvd-history` — Futures CVD History — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/taker-buy-sell/aggregated-cvd-history` — Futures Aggregated CVD — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla

## OI DETAIL
- **FAIL** `/api/futures/open-interest/ohlc-history` — OI OHLC History (Pair) — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **PASS** `/api/futures/open-interest/exchange-list` — OI Exchange List — list of 25 items, keys: ['exchange', 'symbol', 'open_interest_usd', 'open_interest_quantity', 'open_interest_by_coin_margin']

## LIQUIDATION (expect premium-only)
- **FAIL** `/api/futures/liquidation/map` — Liquidation Map (Pair) — Upgrade plan
- **FAIL** `/api/futures/liquidation/aggregated-map` — Liquidation Map (Aggregated) — Upgrade plan
- **FAIL** `/api/futures/liquidation/order` — Liquidation Order — Upgrade plan
- **FAIL** `/api/futures/liquidation/heatmap` — Liquidation Heatmap Model1 — {"code":"404","msg":"Not Found"}
- **PASS** `/api/futures/liquidation/history` — Liquidation History (Pair) — list of 6 items, keys: ['time', 'long_liquidation_usd', 'short_liquidation_usd']
- **FAIL** `/api/futures/liquidation/aggregated-history` — Liquidation History (Aggregated) — Required String parameter 'exchange_list' is not present
- **FAIL** `/api/futures/liquidation/max-pain` — Liquidation Max Pain — Upgrade plan

## ORDERBOOK
- **FAIL** `/api/futures/orderbook/history` — Orderbook Bid/Ask (Pair) — Upgrade plan
- **FAIL** `/api/futures/orderbook/heatmap` — Orderbook Heatmap — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/orderbook/large-limit-order` — Large Orderbook — Upgrade plan

## HYPERLIQUID
- **FAIL** `/api/futures/hyperliquid/whale-alert` — Hyperliquid Whale Alert — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/hyperliquid/whale-position` — Hyperliquid Whale Position — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/hyperliquid/position` — Hyperliquid Positions by Coin — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/futures/hyperliquid/long-short-account-ratio-history` — Hyperliquid L/S Account Ratio — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla

## ON-CHAIN / EXCHANGE DATA
- **FAIL** `/api/onchain/exchange-balance-list` — Exchange Balance List — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/onchain/exchange-balance-chart` — Exchange Balance Chart — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/onchain/whale-transfer` — Whale Transfer — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/onchain/token-unlock-list` — Token Unlock List — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla

## ETF
- **FAIL** `/api/etf/flows-history` — BTC ETF Flows History — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/etf/bitcoin-list` — BTC ETF List — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/etf/bitcoin-etf-netassets-history` — BTC ETF NetAssets History — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/etf/ethereum-etf-flows-history` — ETH ETF Flows History — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla

## INDICATORS
- **FAIL** `/api/indicator/fear-greed` — Fear & Greed Index — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/indicator/coinbase-premium` — Coinbase Premium — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/indicator/basis` — Futures Basis — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/indicator/futures-rsi-list` — BTC RSI List — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/indicator/altcoin-season-index` — Altcoin Season Index — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla
- **FAIL** `/api/indicator/bitcoin-dominance` — BTC Dominance — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla

## SPOT
- **FAIL** `/api/spot/coins-markets` — Spot Coins Markets — Upgrade plan
- **FAIL** `/api/spot/taker-buy-sell/aggregated-history` — Spot Taker Buy/Sell — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: https://docs.coingla

## MULTI-TIMEFRAME / MARKETS
- **FAIL** `/api/futures/coins-price-change` — Coins Price Change — Upgrade plan
- **FAIL** `/api/futures/coins-markets` — Coins Markets — Upgrade plan

## Priority Endpoints
1. **PASS** Funding Rate Exchange List
2. **FAIL** OI Aggregated History
3. **FAIL** Global L/S Account Ratio
4. **FAIL** Taker Buy/Sell History (Aggregated)
5. **FAIL** BTC ETF Flows History
6. **FAIL** Fear & Greed Index
7. **FAIL** Coinbase Premium

## Available Endpoints
- `/api/futures/liquidation/coin-list`
- `/api/option/max-pain`
- `/api/option/info`
- `/api/futures/funding-rate/exchange-list`
- `/api/futures/open-interest/exchange-list`
- `/api/futures/liquidation/history`

## Blocked Endpoints
- `/api/futures/open-interest/ohlc-aggregated-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/long-short-ratio/global-account` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/long-short-ratio/top-account` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/long-short-ratio/top-position` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/taker-buy-sell/aggregated-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/taker-buy-sell/history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/long-short-ratio/net-position` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/taker-buy-sell/cvd-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/taker-buy-sell/aggregated-cvd-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/open-interest/ohlc-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/liquidation/map` — Upgrade plan
- `/api/futures/liquidation/aggregated-map` — Upgrade plan
- `/api/futures/liquidation/order` — Upgrade plan
- `/api/futures/liquidation/heatmap` — {"code":"404","msg":"Not Found"}
- `/api/futures/liquidation/aggregated-history` — Required String parameter 'exchange_list' is not present
- `/api/futures/liquidation/max-pain` — Upgrade plan
- `/api/futures/orderbook/history` — Upgrade plan
- `/api/futures/orderbook/heatmap` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/orderbook/large-limit-order` — Upgrade plan
- `/api/futures/hyperliquid/whale-alert` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/hyperliquid/whale-position` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/hyperliquid/position` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/hyperliquid/long-short-account-ratio-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/onchain/exchange-balance-list` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/onchain/exchange-balance-chart` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/onchain/whale-transfer` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/onchain/token-unlock-list` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/etf/flows-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/etf/bitcoin-list` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/etf/bitcoin-etf-netassets-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/etf/ethereum-etf-flows-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/indicator/fear-greed` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/indicator/coinbase-premium` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/indicator/basis` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/indicator/futures-rsi-list` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/indicator/altcoin-season-index` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/indicator/bitcoin-dominance` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/spot/coins-markets` — Upgrade plan
- `/api/spot/taker-buy-sell/aggregated-history` — {"code":"404","msg":"Endpoint not found. Please refer to the API documentation: 
- `/api/futures/coins-price-change` — Upgrade plan
- `/api/futures/coins-markets` — Upgrade plan