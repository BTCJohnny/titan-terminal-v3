---
name: liquidity
description: Quick liquidity check — liquidation activity, options max pain, put/call sentiment, and Liquidity Grab Fade detection for any token.
argument-hint: <TOKEN>
allowed-tools:
  - Read
  - Bash
  - mcp__coinstats
---

# /liquidity $ARGUMENTS

Run a quick liquidity intelligence check for the specified token. This is the fast pre-trade check — no full /analyze needed.

## What This Produces

A liquidity report answering: **"Which side is getting liquidated, where does max pain pull price, and is there a mechanical Liquidity Grab Fade setup?"**

Data sources (Hobbyist plan):
- Per-coin liquidation totals across 24h/12h/4h/1h with long/short breakdown
- Options max pain by expiry (BTC/ETH only)
- Options OI, volume, and put/call ratio (BTC/ETH only)

---

## Execution Plan

### Step 1: Get Current Price

```
mcp__coinstats__get-coin-by-id: coinId "[coinstats-id]"
```

For common tokens: BTC = "bitcoin", ETH = "ethereum", SOL = "solana". For others, use lowercase-hyphenated format.

Extract the current price.

### Step 2: Fetch Coinglass Data

```bash
python3 src/fetchers/coinglass_fetcher.py --token $ARGUMENTS --price [PRICE] --json
```

If COINGLASS_API_KEY is not set, stop and tell the user: "COINGLASS_API_KEY not configured. Add it to .env"

### Step 3: Render Report

Using the JSON output, render this report:

```
# 💧 [TOKEN] — Liquidity Report

**Price:** $X | **Max Pain:** $X (distance%) | **P/C Ratio:** Xx

---

## Liquidation Activity

**24h Total:** $X | **Long:** $X | **Short:** $X
**L/S Ratio:** Xx — [Long pain / Short pain / Balanced]
**Bias:** [Bearish (longs getting wrecked) / Bullish (shorts getting wrecked) / Neutral]

| Period | Total | Long | Short |
|--------|-------|------|-------|
| 24h | $X | $X | $X |
| 12h | $X | $X | $X |
| 4h | $X | $X | $X |
| 1h | $X | $X | $X |

[If 1h acceleration detected: flag it — liquidation cascade may be in progress or exhausting]

---

## Options Max Pain (BTC/ETH only)

**Nearest Expiry:** [date] — **Max Pain:** $X ([distance]% [above/below] current price)
**Magnetic Pull:** [UP/DOWN/AT] — [interpretation of what this means for price direction]

[Top 3-5 expiries with max pain, distance, put/call ratio per expiry]

---

## Options Sentiment (BTC/ETH only)

**OI:** $X | **24h Volume:** $X | **OI Change:** +/-X%
**Put/Call OI Ratio:** Xx — [bearish hedging / bullish positioning / balanced]

---

## Liquidity Grab Fade Detection

[If detected:]
**🟢/🔴 SETUP DETECTED — [LONG/SHORT]**
**Confidence:** [HIGH/MEDIUM]
**Thesis:** [one-sentence mechanical thesis]
**Snap-back Target:** $X
[List of conditions met]

[If not detected:]
⚪ No Liquidity Grab Fade setup. Liquidation bias and max pain do not align for a mechanical snap-back at current levels.
```

---

## Error Handling

- If Coinglass API fails: "Coinglass data unavailable. Check API key and try again."
- If CoinStats fails for price: Try running the fetcher without --price (interpretations will be limited)
- For non-BTC/ETH tokens: skip options sections entirely, report liquidation data only
- Partial data is better than no data — render whatever sections have data

## Personality

Same as all Titan output: verdict first, data second. Bold the key numbers. If there's a setup, be specific about the trade. If there's nothing, say "nothing here, move on."
