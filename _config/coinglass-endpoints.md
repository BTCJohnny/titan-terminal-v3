# Coinglass API Endpoint Reference

API: `https://open-api-v4.coinglass.com` | Plan: Hobbyist ($29/mo) | Rate limit: 30 req/min | Auth header: `CG-API-KEY`

All 157 endpoints verified reachable. 44 are stored to `titan_intelligence.db`, 113 available on-demand.

---

## Stored Endpoints (44)

These endpoints are persisted to the intelligence database on a recurring basis. Data compounds over time and feeds into `/hunt`, `/analyze`, and `/targets`.

### Derivatives — `derivatives_snapshots` table

Already integrated into the fetcher (`coinglass_fetcher.py`). Per-token and market-level snapshots.

| Endpoint | Path | Params |
|----------|------|--------|
| Funding Rate Exchange List | `/api/futures/funding-rate/exchange-list` | `symbol` |
| Funding Rate OI Weight History | `/api/futures/funding-rate/oi-weight-history` | `symbol`, `interval` |
| Funding Rate Vol Weight History | `/api/futures/funding-rate/vol-weight-history` | `symbol`, `interval` |
| Cumulative Funding Rate | `/api/futures/funding-rate/accumulated-exchange-list` | `symbol`, `range` |
| OI Aggregated History | `/api/futures/open-interest/aggregated-history` | `symbol`, `interval` |
| OI Stablecoin Margin History | `/api/futures/open-interest/aggregated-stablecoin-history` | `symbol`, `interval` |
| OI Coin Margin History | `/api/futures/open-interest/aggregated-coin-margin-history` | `symbol`, `interval` |
| OI Exchange List | `/api/futures/open-interest/exchange-list` | `symbol` |
| Global L/S Account Ratio | `/api/futures/global-long-short-account-ratio/history` | `symbol`, `interval` |
| Top L/S Account Ratio | `/api/futures/top-long-short-account-ratio/history` | `symbol`, `interval` |
| Top L/S Position Ratio | `/api/futures/top-long-short-position-ratio/history` | `symbol`, `interval` |
| Taker Buy/Sell Exchange List | `/api/futures/taker-buy-sell-volume/exchange-list` | `symbol`, `range` |
| Net Long/Short Position | `/api/futures/net-position/history` | `symbol`, `interval` |
| Coin Liquidation History | `/api/futures/liquidation/aggregated-history` | `symbol`, `interval` |
| Liquidation Coin List | `/api/futures/liquidation/coin-list` | — |
| Pair Liquidation Map | `/api/futures/liquidation/map` | `symbol`, `exchange` |
| Coin Liquidation Map | `/api/futures/liquidation/aggregated-map` | `symbol`, `range` |
| Liquidation Max Pain | `/api/futures/liquidation/max-pain` | `symbol` |
| Option Max Pain | `/api/option/max-pain` | `symbol`, `exchange` |
| Options Info | `/api/option/info` | `symbol` |
| Fear & Greed Index | `/api/index/fear-greed-history` | — |
| Coinbase Premium Index | `/api/coinbase-premium-index` | `symbol`, `interval` |

### Hyperliquid Whales — `hl_whale_snapshots` table

Whale positioning on Hyperliquid perps. High signal weight per the signal hierarchy.

| Endpoint | Path | Params |
|----------|------|--------|
| Whale Alert | `/api/hyperliquid/whale-alert` | — |
| Whale Position | `/api/hyperliquid/whale-position` | `symbol` |
| Wallet Position Distribution | `/api/hyperliquid/wallet/position-distribution` | `symbol` |
| Wallet PNL Distribution | `/api/hyperliquid/wallet/pnl-distribution` | `symbol` |
| HL L/S Ratio (Accounts) | `/api/hyperliquid/global-long-short-account-ratio/history` | `symbol`, `interval` |

### ETF Flows — `etf_flow_snapshots` table

Institutional flow tracking across BTC, ETH, SOL, XRP ETFs.

| Endpoint | Path | Params |
|----------|------|--------|
| BTC ETF Flows | `/api/etf/bitcoin/flow-history` | — |
| ETH ETF Flows | `/api/etf/ethereum/flow-history` | — |
| SOL ETF Flows | `/api/etf/solana/flow-history` | — |
| XRP ETF Flows | `/api/etf/xrp/flow-history` | — |

### Macro Indicators — `macro_snapshots` table

Market regime context. Checked during `/hunt` scans.

| Endpoint | Path | Params |
|----------|------|--------|
| Fear & Greed Index | `/api/index/fear-greed-history` | — |
| Altcoin Season Index | `/api/index/altcoin-season` | — |
| Bitcoin Dominance | `/api/index/bitcoin-dominance` | — |
| StableCoin MarketCap | `/api/index/stableCoin-marketCap-history` | — |
| BTC vs Global M2 | `/api/index/bitcoin-vs-global-m2-growth` | — |
| BTC vs US M2 | `/api/index/bitcoin-vs-us-m2-growth` | — |
| Coinbase Premium | `/api/coinbase-premium-index` | `symbol`, `interval` |

### Taker Flows — `taker_flow_snapshots` table

Aggressor-side volume and cumulative volume delta.

| Endpoint | Path | Params |
|----------|------|--------|
| Coin Taker Buy/Sell | `/api/futures/aggregated-taker-buy-sell-volume/history` | `symbol`, `interval` |
| Aggregated CVD | `/api/futures/aggregated-cvd/history` | `symbol`, `interval` |
| Coin NetFlow List | `/api/futures/netflow-list` | `symbol` |

### On-Chain Exchange Balances — `cg_exchange_balances` table

Exchange reserve tracking from Coinglass on-chain data.

| Endpoint | Path | Params |
|----------|------|--------|
| Exchange Balance List | `/api/exchange/balance/list` | `symbol` |
| Exchange Balance Chart | `/api/exchange/balance/chart` | `symbol` |

### Whale Transfers — `whale_transfers` table

Large on-chain transfers ($10M+ minimum).

| Endpoint | Path | Params |
|----------|------|--------|
| Whale Transfer | `/api/chain/v2/whale-transfer` | — |

### Token Unlocks — `token_unlocks` table

Upcoming supply events.

| Endpoint | Path | Params |
|----------|------|--------|
| Token Unlock List | `/api/coin/unlock-list` | — |
| Token Vesting | `/api/coin/vesting` | `symbol` |

---

## On-Demand Endpoints (113)

Available for ad-hoc queries during `/analyze` or research. Not persisted — call when needed.

### Futures — Market Reference

| Endpoint | Path | Use Case |
|----------|------|----------|
| Supported Coins | `/api/futures/supported-coins` | List available coins |
| Supported Exchanges | `/api/futures/supported-exchanges` | List exchanges |
| Supported Exchange Pairs | `/api/futures/supported-exchange-pairs` | Pair lookup |
| Coins Markets | `/api/futures/coins-markets` | Market overview |
| Pairs Markets | `/api/futures/pairs-markets` | Pair-level data |
| Coins Price Change | `/api/futures/coins-price-change` | Price change scanner |
| Price History (OHLC) | `/api/futures/price/history` | Futures price candles |
| Delisted Pairs | `/api/futures/delisted-exchange-pairs` | Historical reference |
| Exchange Rank | `/api/futures/exchange-rank` | Exchange volume ranking |

### Futures — Deep Dive

| Endpoint | Path | Use Case |
|----------|------|----------|
| OI Per-Pair History | `/api/futures/open-interest/history` | Single pair OI drill-down |
| OI Exchange History Chart | `/api/futures/open-interest/exchange-history-chart` | OI by exchange over time |
| Funding Rate Per-Pair | `/api/futures/funding-rate/history` | Single pair funding history |
| Funding Rate Arbitrage | `/api/futures/funding-rate/arbitrage` | Cross-exchange arb scanner |
| Net L/S Position v2 | `/api/futures/v2/net-position/history` | Alternative net position data |
| Pair Liquidation History | `/api/futures/liquidation/history` | Per-pair liq history |
| Liquidation Exchange List | `/api/futures/liquidation/exchange-list` | Liq by exchange |
| Liquidation Order | `/api/futures/liquidation/order` | Individual liq events |
| Pair Liq Heatmap Model 1 | `/api/futures/liquidation/heatmap/model1` | Liq heatmap visualization |
| Pair Liq Heatmap Model 2 | `/api/futures/liquidation/heatmap/model2` | Liq heatmap (alt model) |
| Pair Liq Heatmap Model 3 | `/api/futures/liquidation/heatmap/model3` | Liq heatmap (alt model) |
| Coin Liq Heatmap Model 1 | `/api/futures/liquidation/aggregated-heatmap/model1` | Aggregated liq heatmap |
| Coin Liq Heatmap Model 2 | `/api/futures/liquidation/aggregated-heatmap/model2` | Aggregated liq heatmap |
| Coin Liq Heatmap Model 3 | `/api/futures/liquidation/aggregated-heatmap/model3` | Aggregated liq heatmap |

### Futures — Order Book

| Endpoint | Path | Use Case |
|----------|------|----------|
| Pair Orderbook Bid/Ask | `/api/futures/orderbook/history` | Depth + heatmap data |
| Aggregated Orderbook | `/api/futures/orderbook/aggregated-ask-bids-history` | Coin-level depth |
| Large Open Orders | `/api/futures/orderbook/large-limit-order` | Whale limit orders |
| Large Open Orders History | `/api/futures/orderbook/large-limit-order-history` | Historical whale orders |

### Futures — Taker (per-pair)

| Endpoint | Path | Use Case |
|----------|------|----------|
| Pair Taker Buy/Sell | `/api/futures/v2/taker-buy-sell-volume/history` | Pair aggression |
| Footprint History | `/api/futures/volume/footprint-history` | Footprint chart data |
| Pair CVD History | `/api/futures/cvd/history` | Single pair CVD |
| Coin NetFlow | `/api/futures/coin/netflow` | Per-coin flow detail |

### Hyperliquid — Lookup

| Endpoint | Path | Use Case |
|----------|------|----------|
| Positions by Coin | `/api/hyperliquid/position` | HL positions for a coin |
| Positions by Address | `/api/hyperliquid/user-position` | Wallet-level HL positions |

### Spots

| Endpoint | Path | Use Case |
|----------|------|----------|
| Spot Supported Coins | `/api/spot/supported-coins` | List spot coins |
| Spot Exchange Pairs | `/api/spot/supported-exchange-pairs` | Spot pair list |
| Spot Coins Markets | `/api/spot/coins-markets` | Spot market overview |
| Spot Pairs Markets | `/api/spot/pairs-markets` | Pair-level spot data |
| Spot Price OHLC | `/api/spot/price/history` | Spot price candles |
| Spot Orderbook | `/api/spot/orderbook/history` | Spot depth data |
| Spot Aggregated Orderbook | `/api/spot/orderbook/aggregated-ask-bids-history` | Coin-level spot depth |
| Spot Large Orders | `/api/spot/orderbook/large-limit-order` | Spot whale orders |
| Spot Large Orders History | `/api/spot/orderbook/large-limit-order-history` | Historical spot whales |
| Spot Taker Buy/Sell | `/api/spot/taker-buy-sell-volume/history` | Spot taker aggression |
| Spot Agg Taker Buy/Sell | `/api/spot/aggregated-taker-buy-sell-volume/history` | Coin-level spot taker |
| Spot Footprint | `/api/spot/volume/footprint-history` | Spot footprint |
| Spot CVD | `/api/spot/cvd/history` | Spot CVD |
| Spot Aggregated CVD | `/api/spot/aggregated-cvd/history` | Coin-level spot CVD |
| Spot NetFlow List | `/api/spot/netflow-list` | Spot netflow overview |
| Spot Coin NetFlow | `/api/spot/coin/netflow` | Per-coin spot flow |

### Options — Deep Dive

| Endpoint | Path | Use Case |
|----------|------|----------|
| Options Exchange OI History | `/api/option/exchange-oi-history` | Options OI by exchange |
| Options Exchange Vol History | `/api/option/exchange-vol-history` | Options volume by exchange |

### On-Chain — Lookup

| Endpoint | Path | Use Case |
|----------|------|----------|
| Exchange Assets | `/api/exchange/assets` | Per-exchange asset holdings |
| Exchange Transfers (ERC-20) | `/api/exchange/chain/tx/list` | On-chain transfer log |

### ETF — Detail

| Endpoint | Path | Use Case |
|----------|------|----------|
| Bitcoin ETF List | `/api/etf/bitcoin/list` | ETF fund list |
| BTC ETF NetAssets | `/api/etf/bitcoin/net-assets/history` | AUM over time |
| BTC ETF Premium/Discount | `/api/etf/bitcoin/premium-discount/history` | NAV divergence |
| BTC ETF History | `/api/etf/bitcoin/history` | Per-ticker history |
| BTC ETF Price OHLC | `/api/etf/bitcoin/price/history` | ETF price candles |
| BTC ETF Detail | `/api/etf/bitcoin/detail` | Per-ticker detail |
| BTC ETF AUM | `/api/etf/bitcoin/aum` | Current AUM |
| HK BTC ETF Flows | `/api/hk-etf/bitcoin/flow-history` | Hong Kong ETF flows |
| Ethereum ETF List | `/api/etf/ethereum/list` | ETH ETF fund list |
| ETH ETF NetAssets | `/api/etf/ethereum/net-assets/history` | ETH ETF AUM |
| Grayscale Holdings | `/api/grayscale/holdings-list` | Grayscale fund holdings |
| Grayscale Premium | `/api/grayscale/premium-history` | Grayscale NAV premium |

### Indicators — Futures TA (computed locally, API available as fallback)

| Endpoint | Path | Use Case |
|----------|------|----------|
| Coin RSI List | `/api/futures/rsi/list` | RSI scanner |
| Pair RSI | `/api/futures/indicators/rsi` | Single pair RSI |
| Pair MA | `/api/futures/indicators/ma` | Moving average |
| Coin MA List | `/api/futures/ma/list` | MA scanner |
| Pair EMA | `/api/futures/indicators/ema` | Exponential MA |
| Coin EMA List | `/api/futures/ema/list` | EMA scanner |
| Pair BOLL | `/api/futures/indicators/boll` | Bollinger Bands |
| Pair MACD | `/api/futures/indicators/macd` | MACD |
| Coin MACD List | `/api/futures/macd/list` | MACD scanner |
| Futures Basis | `/api/futures/basis/history` | Spot-perp basis |
| Whale Index | `/api/futures/whale-index/history` | Whale activity |
| CGDI Index | `/api/futures/cgdi-index/history` | Derivatives index |
| CDRI Index | `/api/futures/cdri-index/history` | DeFi risk index |
| Pair ATR | `/api/futures/indicators/avg-true-range` | ATR |
| Coin ATR List | `/api/futures/avg-true-range/list` | ATR scanner |

### Indicators — Spots

| Endpoint | Path | Use Case |
|----------|------|----------|
| Bitfinex Margin L/S | `/api/bitfinex-margin-long-short` | Bitfinex margin positioning |
| Borrow Interest Rate | `/api/borrow-interest-rate/history` | Cross-exchange borrow rates |

### Indicators — BTC Macro (check when needed)

| Endpoint | Path | Use Case |
|----------|------|----------|
| AHR999 | `/api/index/ahr999` | BTC valuation |
| Bull Market Peak | `/api/bull-market-peak-indicator` | Cycle top signals |
| Puell Multiple | `/api/index/puell-multiple` | Mining profitability |
| Stock-to-Flow | `/api/index/stock-flow` | S2F model |
| Pi Cycle Top | `/api/index/pi-cycle-indicator` | Cycle top indicator |
| Golden Ratio Multiplier | `/api/index/golden-ratio-multiplier` | BTC valuation bands |
| Bitcoin Profitable Days | `/api/index/bitcoin/profitable-days` | % profitable days |
| Bitcoin Rainbow Chart | `/api/index/bitcoin/rainbow-chart` | Rainbow valuation |
| Bitcoin Bubble Index | `/api/index/bitcoin/bubble-index` | Bubble metric |
| 2-Year MA Multiplier | `/api/index/2-year-ma-multiplier` | Long-term MA bands |
| 200-Week MA Heatmap | `/api/index/200-week-moving-average-heatmap` | 200w MA heatmap |
| BTC STH SOPR | `/api/index/bitcoin-sth-sopr` | Short-term holder SOPR |
| BTC LTH SOPR | `/api/index/bitcoin-lth-sopr` | Long-term holder SOPR |
| BTC STH Realized Price | `/api/index/bitcoin-sth-realized-price` | STH cost basis |
| BTC LTH Realized Price | `/api/index/bitcoin-lth-realized-price` | LTH cost basis |
| BTC STH Supply | `/api/index/bitcoin-short-term-holder-supply` | STH supply |
| BTC LTH Supply | `/api/index/bitcoin-long-term-holder-supply` | LTH supply |
| BTC RHODL Ratio | `/api/index/bitcoin-rhodl-ratio` | Realized HODL ratio |
| BTC Reserve Risk | `/api/index/bitcoin-reserve-risk` | Reserve risk |
| BTC Active Addresses | `/api/index/bitcoin-active-addresses` | Network activity |
| BTC New Addresses | `/api/index/bitcoin-new-addresses` | New adoption |
| BTC NUPL | `/api/index/bitcoin-net-unrealized-profit-loss` | Net unrealized P/L |
| BTC Correlations | `/api/index/bitcoin-correlation` | BTC vs GLD/SPY/QQQ/TLT |
| Bitcoin Macro Oscillator | `/api/index/bitcoin-macro-oscillator` | BMO composite |
| Options/Futures OI Ratio | `/api/index/option-vs-futures-oi-ratio` | Options vs futures OI |
| BTC vs Global M2 | `/api/index/bitcoin-vs-global-m2-growth` | Liquidity correlation |
| BTC vs US M2 | `/api/index/bitcoin-vs-us-m2-growth` | US liquidity correlation |
| Exchanges Transparency | `/api/exchange_assets_transparency/list` | Proof of reserves |
| Futures/Spot Volume Ratio | `/api/futures_spot_volume_ratio` | Speculation ratio |

### Other

| Endpoint | Path | Use Case |
|----------|------|----------|
| Economic Calendar | `/api/calendar/economic-data` | Macro event context |
| News | `/api/article/list` | Crypto news feed |

---

## Database Schema

### Storage Tables

| Table | Stores | Source Endpoints |
|-------|--------|-----------------|
| `derivatives_snapshots` | Funding, OI, L/S, liquidation, options, market pulse | 22 endpoints |
| `hl_whale_snapshots` | Hyperliquid whale alerts, positions, distributions | 5 endpoints |
| `etf_flow_snapshots` | BTC/ETH/SOL/XRP ETF daily flows | 4 endpoints |
| `macro_snapshots` | Fear & Greed, altcoin season, BTC dominance, stablecoin mcap, M2, premium | 7 endpoints |
| `taker_flow_snapshots` | Taker buy/sell volume, CVD, netflow | 3 endpoints |
| `cg_exchange_balances` | Exchange reserve balances by coin | 2 endpoints |
| `whale_transfers` | Large on-chain transfers ($10M+) | 1 endpoint |
| `token_unlocks` | Upcoming token unlock schedules | 2 endpoints |

### Existing Tables (unchanged)

| Table | Purpose |
|-------|---------|
| `cex_snapshots` | CEX flow snapshots (from `cex_monitor.py`) |
| `exchange_balance_daily` | Daily exchange balances (from Nansen) |
| `flow_snapshots` | On-chain flow snapshots (from Nansen) |
| `signal_watchlist` | Active watchlist entries |
| `mcp_queries` / `mcp_responses` | Nansen MCP query log |
| `coinglass_endpoints` | This endpoint registry (meta) |

---

## API Notes

- **Rate limit**: 30 requests/minute. The fetcher tracks this automatically.
- **Auth**: `CG-API-KEY` header on every request.
- **Common params**: `symbol` (e.g. BTC, ETH), `interval` (e.g. h1, h4, 1d), `range` (e.g. 1h, 4h, 12h, 24h).
- **Response format**: `{"code": "0", "msg": "success", "data": ...}` — code 0 = success.
- **Endpoint registry**: Query `coinglass_endpoints` table for programmatic lookup: `SELECT * FROM coinglass_endpoints WHERE storage_mode='store'`.
