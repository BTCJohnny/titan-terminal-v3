# Nansen MCP Tool Reference

Access: MCP server (`mcp__nansen__*`) | Session budget: 200 credits (guardrail, not conservation target)

All 34 tools verified available. 8 are stored to `titan_intelligence.db`, 26 available on-demand. Credit costs per tool in parentheses.

See `_config/nansen-budget.md` for full budget rules, cache TTLs, and cost-saving tips.

---

## Stored Tools (8)

These tools feed into `/hunt` and `/analyze` workflows. Results are persisted for trend tracking and historical comparison.

### Token Flows — `flow_snapshots` table

On-chain flow intelligence. Signal hierarchy #1 — shows what people do with real money.

| Tool | Credits | Description | Key Params |
|------|---------|-------------|------------|
| `token_recent_flows_summary` | 2 | Aggregated flows by segment: Public Figures, Top PnL, Whales, Smart Traders, Exchanges, Fresh Wallets | `chain`, `tokenAddress`, `lookbackPeriod` (5m/1h/6h/12h/1d/7d) |
| `token_flows` | 2 | Hourly granular flows by holder segment over a date range | `tokenAddress`, `chain`, `holder_segment`, `dateRange` |
| `token_current_top_holders` | 3 | Top holders with balance changes (on-chain or HL perps) | `tokenAddress`, `chain`, `labelType` (whale/smart_money/top_100/exchange), `mode` (onchain_tokens/perps) |

Cache TTL: Flow summaries 6h, holders 12h (on-chain) / 1h (perps).

### Smart Money Positioning — stored per snapshot

Broad smart money activity across all tokens and chains.

| Tool | Credits | Description | Key Params |
|------|---------|-------------|------------|
| `smart_traders_and_funds_token_balances` | 5 | Aggregated SM + fund holdings across chains | `chains`, `includeSmartMoneyLabels` |
| `smart_traders_and_funds_perp_trades` | 5 | Recent SM + fund perp trades on Hyperliquid | `action`, `side`, `includeSmartMoneyLabels` |

Labels: `30D Smart Trader`, `90D Smart Trader`, `180D Smart Trader`, `All Time Smart Trader`, `Fund`, `Smart HL Perps Trader`, `Any Smart Money`.

### Token Discovery — stored per scan

Screening tools for `/hunt` alpha scanning.

| Tool | Credits | Description | Key Params |
|------|---------|-------------|------------|
| `token_discovery_screener` | 5 | Live token screening by volume, liquidity, SM activity, sectors, token age | `chains`, `timeframe`, `sectors`, `orderBy`, filters |
| `nansen_score_top_tokens` | 5 | Pre-scored buy recommendations (Performance Score >= 15) | `marketCapGroup` (lowcap/midcap/largecap) |

### Hyperliquid Leaderboard — stored per snapshot

| Tool | Credits | Description | Key Params |
|------|---------|-------------|------------|
| `hyperliquid_leaderboard` | 3 | HL trader rankings by PnL, ROI, account value | `date`, `order_by`, `accountValue`, `totalPnl` |

---

## On-Demand Tools (26)

Available for ad-hoc queries during `/analyze`, research, or wallet investigation. Not persisted.

### Token Deep Dive (6 tools)

| Tool | Credits | Description | When to Use |
|------|---------|-------------|-------------|
| `general_search` | 1 | Search tokens, entities, addresses | First step — resolve symbol to chain + address |
| `token_ohlcv` | 2 | Token OHLCV price data (EVM + Solana) | Price history, NOT for Hyperliquid |
| `token_transfers` | 2 | Token transfer history with SM filter | Large transfer investigation |
| `token_dex_trades` | 5 | DEX trade history (on-chain or HL perps) | Trade-level drill-down |
| `token_who_bought_sold` | 3 | Aggregated DEX buyers/sellers | "Who is buying/selling X?" |
| `token_pnl_leaderboard` | 3 | Top PnL traders for a token | Smart money performance on a token |
| `token_quant_scores` | 3 | Nansen Score risk/reward indicators | Per-token risk assessment |

### Address Investigation (7 tools)

| Tool | Credits | Description | When to Use |
|------|---------|-------------|-------------|
| `address_portfolio` | 2 | Wallet portfolio (balances + DeFi + HL positions) | Wallet overview, includes HL liquidation prices |
| `address_transactions` | 1 | 20 most recent transactions | Recent wallet activity |
| `address_counterparties` | 2 | Top interaction partners by netflow | "Who does this wallet trade with?" |
| `address_historical_balances` | 2 | Historical token balances (1d to 2yr lookback) | Position tracking over time |
| `address_related_addresses` | 2 | Linked addresses (funder, signer, deployer) | Wallet cluster discovery |
| `wallet_pnl_summary` | 3 | Aggregate realized PnL for wallet | Overall trader performance |
| `wallet_pnl_for_token` | 3 | Wallet PnL on specific token | "How did this wallet do on X?" |

### Prediction Markets — Polymarket (10 tools)

| Tool | Credits | Description | When to Use |
|------|---------|-------------|-------------|
| `prediction_market_lookup` | 1 | Search events/markets by name or URL | Resolve market name to marketId |
| `prediction_market_screener` | 2 | Browse/sort markets by volume, liquidity, OI | Market discovery |
| `prediction_market_ohlcv` | 2 | Price/odds history candles | Probability trend over time |
| `prediction_market_orderbook` | 2 | Live bid/ask depth | Liquidity analysis |
| `prediction_market_trades` | 2 | Recent trade tape | Latest fills and pricing |
| `prediction_market_top_holders` | 2 | Largest position holders | Concentration risk |
| `prediction_market_pnl_leaderboard` | 2 | PnL rankings for a market | Who is winning? |
| `prediction_market_position_detail` | 2 | Position breakdown with cost basis | Detailed position analysis |
| `prediction_market_address_pnl` | 2 | Wallet-level PM PnL | Wallet PM performance |
| `prediction_market_address_trades` | 2 | Wallet PM trade history | Wallet PM activity |

### Chain & Transaction (2 tools)

| Tool | Credits | Description | When to Use |
|------|---------|-------------|-------------|
| `growth_chain_rank` | 5 | Chain growth rankings (addresses, txns, gas, DEX) | Ecosystem momentum |
| `transaction_lookup` | 1 | Transaction details with transfers | Single tx investigation |

---

## Database Schema

### Storage Tables Used by Nansen

| Table | Stores | Source Tools |
|-------|--------|-------------|
| `flow_snapshots` | On-chain flow intelligence per token per segment | `token_recent_flows_summary`, `token_flows`, `token_current_top_holders` |
| `mcp_queries` | All Nansen MCP query log (tool, params, timestamp) | All tools |
| `mcp_responses` | All Nansen MCP response log (raw responses) | All tools |

### Tool Registry

Query `nansen_tools` table for programmatic lookup:
```sql
SELECT * FROM nansen_tools WHERE storage_mode='store';
SELECT tool_name, credits, description FROM nansen_tools WHERE category='token';
```

---

## Supported Chains

EVM: ethereum, arbitrum, avalanche, base, bnb, optimism, polygon, scroll, zksync, linea, mantle, sei, sonic, ronin, monad, plasma, iotaevm, unichain, tron, ton, near, sui, hyperevm

Non-EVM: solana, bitcoin (limited), hyperliquid (perps only)

**Chain limits per tool:**
- `token_ohlcv`: EVM + Solana only (no Hyperliquid)
- `token_recent_flows_summary`: No Bitcoin, no Hyperliquid
- `token_discovery_screener`: Max 5 chains per request, Hyperliquid returns perps data
- `token_current_top_holders` (perps mode): Hyperliquid only

---

## Smart Money Labels

Used in `includeSmartMoneyLabels` filter across multiple tools:

| Label | Description |
|-------|-------------|
| `30D Smart Trader` | Profitable over last 30 days |
| `90D Smart Trader` | Profitable over last 90 days |
| `180D Smart Trader` | Profitable over last 180 days |
| `All Time Smart Trader` | Historically profitable |
| `Fund` | Known fund/institution |
| `Smart HL Perps Trader` | Profitable Hyperliquid perps trader |
| `Any Smart Money` | Includes all of the above |

---

## Credit Budget Quick Reference

| Tier | Credits | Tools |
|------|---------|-------|
| **1 credit** | 1 | `general_search`, `address_transactions`, `transaction_lookup`, `prediction_market_lookup` |
| **2 credits** | 2 | `token_flows`, `token_recent_flows_summary`, `token_ohlcv`, `token_transfers`, `address_portfolio`, `address_historical_balances`, `address_counterparties`, `address_related_addresses`, all PM tools (except lookup) |
| **3 credits** | 3 | `token_current_top_holders`, `token_who_bought_sold`, `token_pnl_leaderboard`, `token_quant_scores`, `wallet_pnl_*`, `hyperliquid_leaderboard` |
| **5 credits** | 5 | `smart_traders_and_funds_*`, `token_discovery_screener`, `token_dex_trades`, `nansen_score_top_tokens`, `growth_chain_rank` |

**Typical usage:** `/analyze` = 15-20 credits | `/hunt` = 20-40 credits | Quick check = 4-8 credits
