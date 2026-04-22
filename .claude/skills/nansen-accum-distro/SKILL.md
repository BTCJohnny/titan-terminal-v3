---
name: nansen-accum-distro
description: >
  Multi-layer accumulation/distribution analysis using Nansen MCP. Use when asked to
  analyze token accumulation, distribution, smart money flows, CEX flows, fresh wallet
  activity, stealth buying, or "who's accumulating/selling" for any token.
---

# Nansen Accumulation/Distribution Analysis

Chains multiple Nansen MCP tools to detect token accumulation or distribution across three layers: CEX flows, smart money flows, and fresh wallet detection.

## Usage

```
/nansen-accum-distro [TOKEN] [CHAIN] [TOKEN_ADDRESS]
```

## Credit Budget

| Layer | Tools | Credits |
|-------|-------|---------|
| Layer 1 — CEX Flows | `token_recent_flows_summary`, `token_flows` | 2 |
| Layer 2 — Smart Money | `smart_traders_and_funds_token_balances`, `token_who_bought_sold`, `token_dex_trades` | 6-7 |
| Layer 3 — Fresh Wallets | `token_current_top_holders`, `address_portfolio` (×2-3), `address_related_addresses` (×2-3) | 5-7 |
| **Total** | | **13-16** |

## Layer 1 — CEX Flows (2 credits)

Determine net exchange flow direction and segment breakdown.

### Step 1: Net flow direction
```
tool: token_recent_flows_summary
params: {"request": {"tokenAddress": "<ADDRESS>", "chain": "<CHAIN>"}}
```
Read: `netFlow` (positive = outflow/accumulation, negative = inflow/distribution), `totalInflow`, `totalOutflow`.

### Step 2: Hourly flow detail
```
tool: token_flows
params: {"request": {"tokenAddress": "<ADDRESS>", "chain": "<CHAIN>", "dateRange": {"from": "<7D_AGO>", "to": "<TODAY>"}}}
```
Read: hourly flow segments, identify acceleration or deceleration patterns.

**Layer 1 Verdict:** ACCUMULATION if net outflow from CEX. DISTRIBUTION if net inflow to CEX. NEUTRAL if balanced.

---

## Layer 2 — Smart Money (6-7 credits)

Track institutional and smart trader positioning.

### Step 3: Smart money balances
```
tool: smart_traders_and_funds_token_balances
params: {"request": {"chain": "<CHAIN>", "smFilter": ["Fund", "Smart Trader", "180D Smart Trader"]}}
```
Find the target token in results. Read: `balancePctChange24H`, `nofHolders`, `totalBalance`. Rising holders + rising balance = accumulation.

### Step 4: Top buyers and sellers
```
tool: token_who_bought_sold
params: {"request": {"tokenAddress": "<ADDRESS>", "chain": "<CHAIN>", "dateRange": {"from": "<7D_AGO>", "to": "<TODAY>"}}}
```
Read: buyer vs seller count, net volume direction, labeled entity names.

### Step 5: Individual trade sizes
```
tool: token_dex_trades
params: {"request": {"tokenAddress": "<ADDRESS>", "chain": "<CHAIN>", "dateRange": {"from": "<3D_AGO>", "to": "<TODAY>"}}}
```
Read: trade size clustering (many large buys = institutional accumulation), trade frequency patterns.

**Layer 2 Verdict:** ACCUMULATION if smart money adding, buyers > sellers by volume, large clustered buys. DISTRIBUTION if opposite. NEUTRAL if mixed.

---

## Layer 3 — Fresh Wallet Detection (5-7 credits)

Identify stealth accumulation via unlabeled wallets.

### Step 6: Find unlabeled top holders
```
tool: token_current_top_holders
params: {"request": {"tokenAddress": "<ADDRESS>", "chain": "<CHAIN>"}}
```
Filter: large holders (>$100K value) with NO Nansen label. These are suspicious — labeled wallets are known entities.

### Step 7: Check war chest (per suspicious wallet, max 2-3)
```
tool: address_portfolio
params: {"request": {"wallet_address": "<WALLET_ADDRESS>"}}
```
Check stablecoin holdings (USDC, USDT, DAI). A wallet with $500K+ stables AND a large token position = war chest for continued buying.

### Step 8: Check wallet provenance (per suspicious wallet, max 2-3)
```
tool: address_related_addresses
params: {"request": {"addresses": ["<WALLET_ADDRESS>"]}}
```
Check: wallet age, first funder, connected addresses. Recently created wallets funded from exchanges or unlabeled sources = stealth buying.

### Fresh Wallet Scoring (0-5 per wallet)

| Signal | Points |
|--------|--------|
| Created in last 30 days | +1 |
| >$100K stablecoins (war chest) | +1 |
| Single-purpose portfolio (1-3 tokens) | +1 |
| Funded from exchange or unlabeled wallet | +1 |
| Related wallets also hold target token | +1 |

**Score interpretation:** 4-5 = high-confidence stealth accumulation. 3 = suspicious. 0-2 = likely organic holder.

**Layer 3 Verdict:** STEALTH ACCUMULATION if 2+ wallets score 3+. NORMAL if all score ≤2.

---

## Final Verdict

Combine all three layers:

| Scenario | Verdict |
|----------|---------|
| All 3 layers show accumulation | **STRONG ACCUMULATION** — high conviction |
| 2 of 3 layers show accumulation | **ACCUMULATION** — moderate conviction |
| Mixed signals | **NEUTRAL** — no clear direction |
| 2 of 3 layers show distribution | **DISTRIBUTION** — moderate conviction |
| All 3 layers show distribution | **STRONG DISTRIBUTION** — high conviction |

## Tool Parameter Reference

### Wrapper patterns
- `general_search`, `transaction_lookup` — flat args (no `request` wrapper)
- All other tools — wrap in `{"request": {...}}`

### Address parameter naming
- Most wallet tools: `addresses: ["0x..."]` (plural, array)
- `wallet_pnl_for_token`, `wallet_pnl_summary`: `address: "0x..."` (singular)
- `address_portfolio`: `wallet_address: "0x..."` (unique name)

### Enum values
- Case-sensitive: `"BUY"` / `"SELL"` (not lowercase)

### Date ranges
- Format: `{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}`

## Chain Coverage Notes

- **Ethereum, Base, Arbitrum, Optimism, Polygon, BNB**: Full coverage across all 3 layers
- **Solana**: Full coverage but address format differs (base58)
- **Hyperliquid**: Limited — Token God Mode tools may return empty. Use `hyperliquid_leaderboard` as fallback for perps positioning data
- **Sui, Sei, other L1s**: Partial coverage — test before relying on results

## Output Format

Save reports as markdown with sections:
```
# [TOKEN] Accumulation/Distribution Analysis
## Date & Parameters
## Layer 1: CEX Flows
## Layer 2: Smart Money
## Layer 3: Fresh Wallets
## Suspicious Wallet Details (if any)
## Final Verdict
## Credit Usage
```

Save to: `signals/dashboards/accum_distro_[TOKEN]_YYYYMMDD_HHMM.md`

## Nansen Snapshot Pipeline

After completing analysis, store each raw Nansen MCP response to the intelligence DB. For every Nansen tool called during this analysis, run:

```bash
python3 src/storage/intelligence.py log-nansen --json '{
  "table": "<table>",
  "token": "[TOKEN]",
  "tool_name": "<mcp_tool_name>",
  "data": <raw MCP response JSON>,
  ...extra fields from mapping below...
}'
```

| Nansen Tool | table | Extra Fields |
|-------------|-------|--------------|
| `token_recent_flows_summary` | `nansen_flow_snapshots` | `"holder_segment": "all"`, `"lookback_period": "<period>"` |
| `token_flows` | `nansen_flow_snapshots` | `"holder_segment": "<segment>"`, `"lookback_period": "<period>"` |
| `token_who_bought_sold` | `nansen_flow_snapshots` | `"lookback_period": "7d"` |
| `token_dex_trades` | `nansen_flow_snapshots` | `"lookback_period": "3d"` |
| `smart_traders_and_funds_token_balances` | `nansen_holder_snapshots` | `"chain": "<chain>"`, `"label_type": "<filter>"`, `"mode": "onchain"` |
| `token_current_top_holders` | `nansen_holder_snapshots` | `"chain": "<chain>"`, `"label_type": "<filter>"`, `"mode": "<mode>"` |
| `smart_traders_and_funds_perp_trades` | `nansen_perp_snapshots` | (none) |

Skip wallet-level tools (`address_portfolio`, `address_related_addresses`) — they don't map to token snapshot tables.

## Database Pipeline

After saving the markdown report, log structured data to the intelligence DB:

```bash
python3 src/storage/intelligence.py log-accum-distro --json '{
  "token": "[TOKEN]",
  "chain": "[CHAIN]",
  "token_address": "[ADDRESS]",
  "price_usd": [current price],
  "layer1_verdict": "[ACCUMULATION/DISTRIBUTION/NEUTRAL]",
  "layer2_verdict": "[ACCUMULATION/DISTRIBUTION/NEUTRAL/MILD ACCUMULATION]",
  "layer3_verdict": "[STEALTH ACCUMULATION/NORMAL/NEUTRAL]",
  "cex_net_flow_usd": [positive = outflow/bullish],
  "cex_flow_vs_avg": [multiplier],
  "sm_holders_count": [integer],
  "sm_balance_usd": [float],
  "sm_balance_change_24h_pct": [float],
  "sm_net_buy_volume_usd": [buyers minus sellers 7d],
  "sm_buyer_count": [integer],
  "sm_seller_count": [integer],
  "fresh_wallet_count": [wallets scoring 3+],
  "fresh_wallet_max_score": [0-5],
  "fresh_wallet_total_usd": [total USD in fresh wallets],
  "final_verdict": "[STRONG ACCUMULATION/ACCUMULATION/NEUTRAL/DISTRIBUTION/STRONG DISTRIBUTION]",
  "conviction": "[HIGH/MODERATE/LOW]",
  "nansen_credits_used": [integer],
  "full_markdown": "[full report text]"
}'
```

Omit fields where data was unavailable. Then sync to Cowork:

```bash
python3 src/storage/intelligence.py sync
```
