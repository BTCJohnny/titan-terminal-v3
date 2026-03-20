---
name: target-package
description: Calculate position sizing with 2% risk, 3:1 minimum RR, and 3 profit targets for scaling out. Generates a ready-to-execute trade plan.
argument-hint: <TOKEN> [entry $X] [stop $Y] [targets $T1 $T2 $T3]
allowed-tools:
  - Read
  - Bash
  - mcp__coinstats
---

# /target-package $ARGUMENTS

Calculate position sizing and generate a complete trade execution plan with entry, stop, and 3 profit targets.

## What This Produces

A Target Package that answers: "How many units do I buy, where do I stop out, and where do I take profit — with exact dollar amounts?"

---

## Argument Parsing

The command accepts flexible input. Parse what's provided and ask for the rest:

- `/target-package ETH` → Token only. Claude analyzes levels and asks for account balance.
- `/target-package ETH entry $3450 stop $3300` → Token + levels. Claude suggests targets and asks for account balance.
- `/target-package ETH long entry $3450 stop $3300 targets $3600 $3800 $4200 account $50000` → Complete. Generate immediately.
- `/target-package ETH short entry $3450 stop $3600 targets $3200 $3000 $2700 account $50000` → Short setup. Generate immediately.

**Required fields (ask if not provided):**
1. **Account balance** — ALWAYS ask. Never assume.
2. **Entry price** — Use S/R levels from TA if not provided
3. **Stop loss** — Use nearest S/R + 1.5x ATR if not provided
4. **Direction** — Infer from entry/stop relationship (stop below entry = LONG, stop above = SHORT). Ask if ambiguous.

**Optional fields (use defaults):**
- Targets: If not provided, calculate from S/R levels and 1R/2R/3R from entry
- Risk %: Default 2%
- Leverage: Default 1x
- Scale-out: Default 33%/33%/34%

---

## Execution Plan

### Step 1: Gather Missing Data

If entry/stop/targets are not provided, run TA on both 4H (structural context) and 1H (execution precision) to determine levels:

```bash
python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 4h --indicators sr,atr,sma
python3 src/analysis/indicators.py analyze [TOKEN] --timeframe 1h --indicators sr,atr,bb,rsi
```

**Level selection logic:**
- **Entry:** Use the nearest 1H S/R level within the 4H setup zone. For longs, this is 1H support near 4H support. For shorts, 1H resistance near 4H resistance. Ideal entry adds 1H BB band touch + favorable RSI (< 40 for longs, > 60 for shorts).
- **Stop:** Use 1.5-2x 1H ATR beyond the entry-side 1H S/R level, but never inside the 4H structural invalidation point. If the 1H stop is tighter than 4H structure, use 4H.
- **T1:** Nearest 1H S/R level in the profit direction.
- **T2:** Next 4H S/R level beyond T1.
- **T3:** Extended target — Daily S/R or 3R from entry, whichever is farther.

If 1H data is unavailable or indicators.py fails for 1H, fall back to 4H levels only.

If account balance is not provided, ask the user: "What is your current account balance?"

### Step 2: Get Token Rank (for category limits)

```
mcp__coinstats__get-coin-by-id: coinId "[token-id]"
```

Extract the market cap rank. This determines the maximum position size:

| Category | Max % of Account |
|----------|-----------------|
| Blue Chip (BTC, ETH) | 30% |
| Large Cap (Top 50) | 15% |
| Mid Cap (Top 100) | 10% |
| Small Cap (100+) | 5% |
| Degen/New (<30 days) | 2% |

### Step 3: Validate Setup

Before calculating, validate:

1. **Direction consistency** — Stop below entry for LONG, above for SHORT. All targets on the correct side of entry.
2. **Minimum 3:1 RR on T3** — If T3 doesn't provide 3:1 risk:reward, REJECT the setup. Show suggested T3 price for 3R minimum.
3. **Category limit** — If position would exceed the category max %, show a WARNING with the recommended maximum.

If validation fails, show the errors and stop. Do NOT generate a Target Package for an invalid setup.

### Step 4: Generate Target Package

Pass the validated data to the Python formatter:

```bash
python3 src/formatters/target_package.py '{"token": "[TOKEN]", "direction": "[LONG/SHORT]", "account": [BALANCE], "entry": [ENTRY], "stop": [STOP], "targets": [[T1], [T2], [T3]], "risk_pct": 2.0, "leverage": 1.0, "rank": [RANK]}'
```

Display the formatter's output directly.

### Step 5: Auto-Save

Save the Target Package to: `results/trade-cards/[TOKEN]_[YYYY-MM-DD]_target.md`

Append to quarterly journal: `my-trading/journal/YYYY_QN.md` with date header and `---` separator.

---

## Scale-Out Strategy

Default: 33% / 33% / 34% at T1 / T2 / T3

| At Target | Action | Result |
|-----------|--------|--------|
| T1 Hit | Sell 33%, move stop to breakeven | Lock in profit, risk-free trade |
| T2 Hit | Sell 33%, trail stop to T1 | More profit locked |
| T3 Hit | Sell remaining 34% | Full position closed |

---

## The 3R Rule Is Non-Negotiable

If the setup cannot achieve 3:1 risk:reward on T3:
- **REJECT the trade**
- Show the math: "Entry $X, Stop $Y, T3 $Z = X.XR — BELOW the 3R minimum"
- Show suggested T3 for minimum 3R
- The user must find a better entry, tighter stop, or farther target

This is Law 2: Seek Asymmetric Upside. No exceptions.

## Error Handling

- If CoinStats fails for rank, default to "small_cap" category limits (conservative)
- If indicators.py fails for S/R levels, ask the user to provide entry/stop/targets manually
- If the formatter crashes, show the raw calculation in plain text — the user still needs the numbers
