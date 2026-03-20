---
name: check-signals
description: Fetch and validate recent MarketInsights trading signals against Titan's technical analysis and on-chain data. Produces VALID/INVALID/NEEDS_CONFIRMATION for each signal.
argument-hint: <TOKEN or hours:N>
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
  - mcp__coinstats
---

# /check-signals $ARGUMENTS

Fetch recent external trading signals from MarketInsights and validate each one against Titan's data-driven analysis.

## What This Produces

For each signal: a VALID / INVALID / NEEDS_CONFIRMATION recommendation based on TA alignment + on-chain evidence.

---

## Argument Parsing

- No argument → fetch signals from last 72 hours (default)
- Token name (e.g., `ETH`) → fetch signals for that specific token
- `hours:N` (e.g., `hours:24`) → fetch signals from last N hours

---

## Execution Plan

### Step 1: Fetch Signals

```bash
# Default: last 72 hours
python3 src/fetchers/signals_fetcher.py recent --hours 72

# If specific token:
python3 src/fetchers/signals_fetcher.py token --token [TOKEN]
```

If no signals found, report: "No MarketInsights signals found in the specified window." and stop.

Display a summary table:

```
| ID | Token | Direction | Date | Chart |
|----|-------|-----------|------|-------|
| 258 | CVX | LONG | 2026-01-23 | Yes |
```

### Step 2: Validate Each Signal

For each signal, run a two-layer validation:

#### Layer 1: TA Assessment (delegate to signal-validator subagent)

Delegate to the **signal-validator** subagent with this task:

> Validate MarketInsights signal [ID] for [TOKEN]. Fetch the signal details from the database using `python3 src/fetchers/signals_fetcher.py show --id [ID]`. Run multi-timeframe TA, read the chart image if available, and produce your preliminary alignment assessment (ALIGNED/CONDITIONAL/CONFLICTING) with suggested levels.

The signal-validator returns: direction inferred from signal text, TA verdict, preliminary assessment, and suggested trade levels.

#### Layer 2: On-Chain Validation (orchestrator handles directly)

For each signal where the signal-validator returned ALIGNED or CONDITIONAL, run on-chain analysis via Nansen MCP:

First, resolve the token's chain and contract address:
```
mcp__nansen__general_search: query "[TOKEN]"
```

Then run the accumulation check:
```
mcp__nansen__token_recent_flows_summary: chain "[chain]", contractAddress "[address]", lookbackWindow "7d"
mcp__nansen__token_current_top_holders: chain "[chain]", contractAddress "[address]", labelType "smart_money"
```

Score the 5 accumulation signals (Exchange Flows, Fresh Wallets, Smart Money, Top PnL Traders, Whale Activity) as described in the /analyze command.

Skip on-chain for CONFLICTING signals — if TA already opposes the signal, on-chain rarely overrides.

### Step 3: Final Recommendation

Combine the signal-validator's TA assessment with on-chain evidence using this decision table:

| TA Assessment | Accumulation Score | Final Recommendation |
|--------------|-------------------|---------------------|
| ALIGNED | 4-5 (Strong Accum) | **VALID — Full Size** |
| ALIGNED | 3 (Mild Accum) | **VALID — Reduced Size** |
| ALIGNED | 0-2 (Mixed/Distrib) | **NEEDS_CONFIRMATION** — TA supports but on-chain doesn't |
| CONDITIONAL | 4-5 | **VALID — Reduced Size** — On-chain compensates for neutral TA |
| CONDITIONAL | 0-3 | **NEEDS_CONFIRMATION** — Neither TA nor on-chain is strong |
| CONFLICTING | Any | **INVALID** — TA opposes the signal direction |

### Step 4: Output

If multiple signals, show a summary table first:

```
## Signal Validation Summary

| ID | Token | Signal | TA | On-Chain | Recommendation |
|----|-------|--------|-----|---------|----------------|
| 258 | CVX | LONG | ALIGNED | 4/5 | VALID — Full Size |
| 259 | AVAX | LONG | CONFLICTING | — | INVALID |
```

Then for each signal, show the detailed validation:

```
## Signal [ID]: [TOKEN] [DIRECTION]

**MarketInsights:** [2-sentence summary]

**TA Assessment:** [ALIGNED/CONDITIONAL/CONFLICTING]
[Key TA findings from signal-validator — trend, momentum, volume, regime]

**On-Chain:** [Accumulation Score]/5 — [Label]
[Key on-chain findings — exchange flows, smart money direction]

**Recommendation: [VALID/INVALID/NEEDS_CONFIRMATION]**
[1-sentence reason]

**Suggested Levels** (if VALID or NEEDS_CONFIRMATION):
Entry: $X,XXX | Stop: $X,XXX | Target: $X,XXX | R:R: X.X:1
[Flag if R:R < 3:1: "BELOW 3R minimum — setup does not qualify"]
```

### Step 5: Auto-Actions

For VALID signals:
- Suggest: "Run `/target-package [TOKEN]` to size this trade"
- If the token is not on the watchlist, suggest adding it

For NEEDS_CONFIRMATION signals:
- Suggest: "Add to watchlist with `python3 src/storage/intelligence.py watchlist-add --symbol [TOKEN] --type confirmation --thesis '[reason]'`"

For INVALID signals:
- No action needed. Move on.

---

## Formatting Rules

- Summary table first, then details — the user should see all results at a glance before diving in
- Bold all recommendations (VALID, INVALID, NEEDS_CONFIRMATION)
- Flag any signal older than 7 days prominently
- Bold the R:R ratio and explicitly state whether it meets the 3R minimum
- If on-chain data is unavailable, note reduced confidence but still make a call based on TA alone
- Partial validation is better than no validation

## Error Handling

- If signals_fetcher.py fails, report the error and suggest checking the external signals database path
- If signal-validator subagent fails for a specific signal, skip that signal and note the error
- If Nansen fails for on-chain, make the recommendation based on TA assessment alone (with reduced confidence noted)
- Complete as many signals as possible — don't let one failure block the batch
