# Position Sizing Rules

**Last Updated:** 2026-03-20

## Core Rules

- **Risk per trade:** 2% of portfolio maximum
- **Minimum R:R:** 3:1 at T3 or reject the trade
- **Position size formula:** `dollar_risk / |entry - stop|`
  - `dollar_risk = portfolio_value × 0.02`

---

## Category Limits (max % of portfolio per position)

| Category | Max % | Example Tokens |
|----------|-------|---------------|
| Blue Chip | 30% | BTC, ETH |
| Large Cap (Top 50) | 15% | SOL, AVAX, LINK, DOGE, XRP |
| Mid Cap (Top 100) | 10% | SUI, SEI, INJ, ARB, OP |
| Small Cap (100+) | 5% | ZRO, AERO, PENDLE |
| Degen / New (<30 days) | 2% | Any token listed <30 days ago |

These are per-position caps. A portfolio can hold multiple positions up to these individual limits.

---

## Regime-Adjusted Sizing

Position sizing changes with the market regime (from `_config/thesis.md`):

| Regime | Long Size | Short Size | Notes |
|--------|-----------|------------|-------|
| Risk-On | 100% of category max | 50% of category max | Longs have regime tailwind |
| Risk-Off | 50% of category max | 100% of category max | Shorts have regime tailwind |
| Chop | 50% of category max | 50% of category max | Reduced conviction both ways |

**Exception:** Accumulation longs in risk-off that meet the full exceptional criteria (3+ funds, >$20M, per thesis) can size at 75% of category max instead of 50%.

---

## Conviction Scaling

Within the category and regime limits, scale by verdict confidence:

| Confidence | Size Multiplier |
|-----------|----------------|
| High Conviction (all pillars aligned) | 1.0× (full allowed size) |
| Moderate Conviction (3/4 pillars agree) | 0.75× |
| Low Conviction (2/4 pillars agree) | 0.5× |
| Watch Only (mixed signals) | 0× — no entry |

---

## Scale-Out Rules

Default scale-out structure (adjustable per trade):

| Target | Action | Remaining |
|--------|--------|-----------|
| T1 hit | Scale out 50% | 50% remaining |
| T2 hit | Scale out 25% | 25% remaining |
| T3 hit | Close remaining | 0% |
| Stop hit | Close all | 0% |

Move stop to breakeven after T1 is hit.

---

## Portfolio-Level Constraints

- **Maximum open positions:** 5 simultaneous
- **Maximum correlated exposure:** No more than 2 positions in the same sector (L1, DeFi, etc.)
- **Maximum directional exposure:** No more than 3 positions in the same direction (all longs or all shorts)
- **Stablecoin floor:** Maintain minimum 30% stablecoin allocation at all times
- **Current stablecoin allocation:** ~65% (per thesis — risk-off positioning)

---

## Paper Trading Specifics

Paper portfolio: $50,000 starting capital.

All sizing rules above apply to paper trading. The paper engine calculates sizes automatically, but Claude should verify sizing in the trade card output matches these rules before suggesting entry.

```bash
# Check current portfolio value
python3 src/trading/paper_engine.py status
```

---

## Quick Reference: Sizing a Trade

1. Get portfolio value from paper engine status
2. Calculate dollar risk: `portfolio × 2% = $X`
3. Calculate stop distance: `|entry - stop| = $Y`
4. Calculate raw position size: `$X / $Y = Z units`
5. Calculate position value: `Z units × entry price = $V`
6. Check category limit: `$V / portfolio ≤ category max %`
7. Apply regime multiplier
8. Apply conviction multiplier
9. Take the smaller of (raw size, category-limited size)
