---
name: scan-wyckoff
description: Batch Wyckoff phase scan across all active tokens. Downloads OHLCV, delegates to wyckoff-analyst subagent for each token, persists results to titan_intelligence.db.
allowed-tools:
  - Read
  - Bash
  - mcp__coinstats
---

# /scan-wyckoff

Run a Wyckoff phase classification scan across all active tokens in the token list and persist results to the intelligence database.

## What This Produces

A table showing each token's current Wyckoff phase, confidence, key events detected, and what to watch for — stored in the DB so you can track phase transitions over time.

---

## Execution Plan

### Step 1: Load Token List

```bash
cat config/token_list.json
```

Extract all tokens where `"active": true`. These are the scan targets.

### Step 2: Ensure OHLCV Data is Fresh

For each active token, download daily OHLCV data (the primary Wyckoff timeframe):

```bash
python3 src/data/ohlcv_client.py download [TOKEN] --timeframe 1d
```

If any download fails, note the failure but continue with other tokens. Partial scans are better than no scan.

### Step 3: Run Wyckoff Analysis Per Token

For each active token, delegate to the **wyckoff-analyst** subagent with this task:

> Analyze [TOKEN] for Wyckoff phase classification. Daily timeframe is primary.
> Run indicators if needed: `python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 1d --indicators obv,sr,bb,atr,sma,adx`
> Return your full structured output.

Collect the subagent's output for each token.

### Step 4: Get Current Prices

For each token, get the current price from CoinStats MCP or from the most recent OHLCV candle close.

### Step 5: Parse and Persist Results

From each wyckoff-analyst response, extract these fields into a JSON object:

```json
{
    "token": "ETH",
    "timeframe": "1d",
    "price_at_scan": 3200.50,
    "cycle_type": "accumulation",
    "phase": "C",
    "confidence": 70,
    "spring_detected": true,
    "upthrust_detected": false,
    "sos_detected": false,
    "sow_detected": false,
    "events_detail": [{"event": "Spring", "description": "False break below $2,950 support on low volume, recovered within 2 candles"}],
    "support_level": 2950.0,
    "resistance_level": 3400.0,
    "range_width_pct": 15.2,
    "position_in_range": "mid_range",
    "volume_trend": "declining",
    "obv_divergence": true,
    "volume_confirmation": "confirms",
    "phase_progression": "Spring detected — watching for SOS breakout above $3,400 on high volume",
    "watch_conditions": "Break above $3,400 on 1.5x+ volume = SOS confirmation. Break below $2,850 on high volume = Spring invalidated.",
    "trading_implications": "Phase C accumulation with confirmed Spring is high-conviction setup. Wait for SOS before entry, or aggressive entry now with stop below $2,850."
}
```

Write all results in one batch:

```bash
python3 src/storage/intelligence.py log-wyckoff --date [YYYY-MM-DD] --data '[...JSON array...]'
```

### Step 6: Display Summary

After persisting, show a summary table:

```
WYCKOFF SCAN — [DATE]
Batch: [batch_id] | Tokens scanned: [N]

Token    Cycle           Phase  Conf   Events          Watch For
----------------------------------------------------------------------
BTC      Accumulation    B      55%    None            Break below $82k = Spring
ETH      Accumulation    C      70%    Spring          SOS above $3,400 on 1.5x vol
SOL      Distribution    B      45%    None            Break above $190 on low vol = Upthrust
...

Results saved to titan_intelligence.db (wyckoff_scans table)
```

Then show the high-conviction items (confidence >= 60) with their full watch conditions.

---

## Do NOT

- Do NOT skip tokens that fail OHLCV download — scan what you can, note failures
- Do NOT fabricate Wyckoff events — if the subagent says "None detected", store that honestly
- Do NOT override the subagent's confidence score — store exactly what it returns
- Do NOT run this on timeframes shorter than Daily — Wyckoff phases play out over weeks/months, 4H is too noisy
- Do NOT store results without persisting to the DB — the entire point is persistence
- Do NOT make any Anthropic API calls — all intelligence comes from Claude Code (subscription)

## Error Handling

- If a token's OHLCV download fails: Skip that token, note it in the summary as "[TOKEN] — OHLCV unavailable"
- If the wyckoff-analyst subagent returns an unclear result: Store it with the confidence the subagent gave (it will be low)
- If the DB write fails: Print the full error and the JSON that failed to write, so it can be retried manually
