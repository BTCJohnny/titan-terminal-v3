---
description: "Daily alpha scan — pull all data sources, reason through them, surface 0-5 opportunity cards"
---

Run the /hunt workflow as defined in CONTEXT.md.

Read CONTEXT.md for the full workflow. Read _config/thesis.md for the current regime and hunting priorities. Read _config/signal-hierarchy.md for conflict resolution rules.

Open the floodgates — pull data from every source (Nansen, Coinglass, Hyperliquid, CEX monitor, indicators, fresh wallet scan), reason through it all, and surface 0-5 opportunities ranked by conviction. Show your reasoning.

The hunt includes a full `/fresh-wallets all` scan (15 tokens, 30 credits). Fresh wallet accumulation is an independent evidence type — it catches buying before Nansen labels are applied.

"Nothing today" is always a valid outcome. Do not force-find setups.

After completing the analysis, save the full output (regime assessment, thesis updates, opportunity cards, smart money activity, scan rejections, and credits used) to:

`signals/dashboards/hunt_YYYYMMDD_HHMM.md`

Use the current UTC timestamp for the filename (e.g., `hunt_20260324_1340.md`). This enables multiple hunts per day with distinct filenames.

## MANDATORY: Database Pipeline (run ALL of these after the analysis)

These storage steps are **required** — they are not optional cleanup. Run them immediately after writing the markdown report. The hunt is not complete until all four sections below have executed.

### 1. Store Hunt Results

Log each surfaced opportunity card (or an empty array for "Nothing today"):

```bash
python3 src/storage/intelligence.py store-hunt --date YYYY-MM-DD --data '[
  {
    "token": "AAVE",
    "chain": "ethereum",
    "price_at_hunt": 147.0,
    "alpha_score": 4,
    "entity_convergence_score": 3,
    "exchange_flow_score": 4,
    "volume_dry_up_score": 2,
    "perps_score": 3,
    "exchange_net_flow_usd": -5200000,
    "exchange_flow_ratio": 0.85,
    "num_entities_buying": 5,
    "num_entities_selling": 2,
    "top_entity": "Fund A",
    "top_entity_change": "+$2.1M",
    "verdict": "BULLISH",
    "verdict_reason": "SM accumulation + CEX outflows + funding negative"
  }
]'
```

Use an empty array `[]` if no opportunities were surfaced ("Nothing today" hunts still get logged). This is critical for tracking hit rates over time.

### 2. Store Nansen Snapshots

For every Nansen tool called during this hunt, run:

```bash
python3 src/storage/intelligence.py log-nansen --json '{
  "table": "<table>",
  "token": "<TOKEN>",
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
| `token_discovery_screener` | `nansen_flow_snapshots` | `"holder_segment": "screener"`, `"lookback_period": "7d"` |

For screener calls that return multiple tokens, use the token `"_SCREENER"` as the token field.

### 3. Verify Coinglass Storage

Coinglass data auto-stores to `derivatives_snapshots` when the fetcher runs via Bash (unless `--no-save` is passed). Ensure you ran these during the hunt — they store automatically:

- `python3 src/fetchers/coinglass_fetcher.py --market --json` → stores BTC+ETH to `derivatives_snapshots`
- `python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --price [PRICE] --json` → stores per-token to `derivatives_snapshots`
- `python3 src/fetchers/coinglass_fetcher.py --scan` → stores to `liquidation_heatmap_snapshots` (via cron only)

**Do NOT pass `--no-save`.** If you skipped the Coinglass calls earlier (e.g., used cached data), re-run them now to ensure DB storage.

### 4. Sync to Cowork

```bash
python3 src/storage/intelligence.py sync
```
