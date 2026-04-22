---
description: "Deep dive on one token — full TA + on-chain + derivatives + verdict"
---

Run the /analyze workflow as defined in CONTEXT.md for the specified token.

Read CONTEXT.md for the full workflow. Read _config/signal-hierarchy.md for conflict resolution. Read relevant _config/interpreters/ for data interpretation.

Multi-timeframe TA (W/D/4H/1H) + Nansen on-chain + fresh wallet scan + Coinglass derivatives + CEX flows → synthesize a directional verdict using the signal hierarchy. Verdict first, then evidence.

Include a fresh wallet scan for the token (2 credits): `token_current_top_holders` sorted by `balance_change_30d` desc. Flag unlabeled wallets with >$100K, Sent=0, and 30d accumulation pattern. Score each 0-5 per CLAUDE.md fresh wallet criteria.

After completing the analysis, save the full output to:

`signals/dashboards/analyze_[TOKEN]_YYYYMMDD_HHMM.md`

Use the token name in UPPERCASE and current UTC timestamp (e.g., `analyze_ETH_20260324_1520.md`).

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
| `token_quant_scores` | `nansen_quant_snapshots` | (none) |

Skip wallet-level tools (`address_portfolio`, `address_related_addresses`) — they don't map to token snapshot tables.

## Database Pipeline

After saving the markdown report, log structured data to the intelligence DB:

```bash
python3 src/storage/intelligence.py log-analyze --json '{
  "token": "[TOKEN]",
  "price_usd": [current price],
  "verdict": "[BULLISH/BEARISH/NEUTRAL]",
  "conviction": "[LOW/MEDIUM/HIGH]",
  "direction": "[LONG/SHORT/NONE]",
  "accumulation_score": [0-5 or null],
  "exchange_flows_signal": "[BULLISH/BEARISH/NEUTRAL]",
  "fresh_wallets_signal": "[BULLISH/BEARISH/NEUTRAL]",
  "smart_money_signal": "[BULLISH/BEARISH/NEUTRAL]",
  "top_pnl_signal": "[BULLISH/BEARISH/NEUTRAL]",
  "whale_signal": "[BULLISH/BEARISH/NEUTRAL]",
  "onchain_verdict": "[BULLISH/BEARISH/NEUTRAL]",
  "perps_verdict": "[BULLISH/BEARISH/NEUTRAL]",
  "derivatives_verdict": "[BULLISH/BEARISH/NEUTRAL]",
  "ta_verdict": "[BULLISH/BEARISH/NEUTRAL]",
  "support_levels": [array of price floats],
  "resistance_levels": [array of price floats],
  "ta_weekly_rsi": [float],
  "ta_daily_rsi": [float],
  "ta_4h_rsi": [float],
  "ta_weekly_adx": [float],
  "ta_daily_adx": [float],
  "ta_trend_direction": "[UP/DOWN/CHOP]",
  "funding_rate": [float hourly %],
  "oi_usd": [float],
  "oi_change_24h_pct": [float],
  "ls_global_ratio": [float],
  "ls_crowding": "[EXTREME_LONG/EXTREME_SHORT/BALANCED]",
  "invalidation_criteria": "[text description]",
  "nansen_credits_used": [integer],
  "full_markdown": "[full report text]"
}'
```

Omit fields where data was unavailable (don't include null values — just leave them out of the JSON). Then sync to Cowork:

```bash
python3 src/storage/intelligence.py sync
```

$ARGUMENTS
