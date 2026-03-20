# Stage: 01_signals — Gather Exit Signal Data

## Purpose

Pull 4 independent on-chain data points that together reveal whether smart money is exiting a token. All 4 calls are independent — run in parallel.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| User input | Token symbol or contract address + chain (default: ethereum) | — |

## Process

### Step 0: Token Resolution

If the user provided a symbol (not a contract address):
```
mcp__nansen__general_search: query "[TOKEN]"
```
Extract chain and contract address. (0 credits)

### Step 1-4: Run All 4 Queries in Parallel (4 credits total)

**1. Flow Intelligence** (1 credit)
```
mcp__nansen__token_recent_flows_summary: chain "[chain]", contractAddress "[address]"
```
Extract `net_flow_usd` for: smart_trader, whale, exchange, fresh_wallets.

**2. Seller Breakdown** (1 credit)
```
mcp__nansen__token_who_bought_sold: chain "[chain]", contractAddress "[address]", limit 20
```
Identify sellers with smart money labels ("Smart Trader", "Fund", "Smart LP"). Note sold_volume_usd.

**3. Smart Money Netflow Trend** (1 credit)
```
mcp__nansen__token_flows: chain "[chain]", contractAddress "[address]"
```
Derive netflow direction across recent hourly periods.

**4. Recent DEX Trades** (1 credit)
```
mcp__nansen__token_dex_trades: chain "[chain]", contractAddress "[address]", limit 20
```
Scan for SELL actions where trader_address_label contains smart money labels.

## Scripts Used

None — all data via Nansen MCP.

## Outputs

| File | Contents |
|------|----------|
| `output/signals_raw.md` | All 4 data points: flow intelligence, seller breakdown, SM netflow trend, recent DEX trades |

## Review Gate

Data quality check — any of the 4 queries fail? Note which ones and proceed with partial data.
