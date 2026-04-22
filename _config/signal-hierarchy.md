# Signal Hierarchy — Conflict Resolution Rules

**Last Updated:** 2026-03-20

## Pecking Order

```
On-Chain Flows & Accumulation  >  Perps Positioning  >  Derivatives Intelligence  >  Technical Analysis
```

**Why this order:** On-chain shows what people actually do with real money (highest signal). Perps shows what smart leveraged traders bet (strong signal). Derivatives shows crowd behavior across exchanges — funding, OI, L/S ratios (confirmatory). TA shows what price has done — it lags by definition (supporting).

Higher weight wins conflicts. Always.

---

## Decision Matrix: When Signals Conflict

### All Pillars Agree

| On-Chain | Perps | TA | Verdict |
|----------|-------|-----|---------|
| Accumulation (4-5/5) | Smart money long | Bullish | **Bullish — High Conviction** |
| Distribution (0-1/5) | Smart money short | Bearish | **Bearish — High Conviction** |
| Mixed (2-3/5) | Mixed | Mixed | **Neutral — No Edge, Wait** |

### On-Chain Conflicts with TA (On-Chain Wins)

| On-Chain | TA | Verdict | Reasoning |
|----------|-----|---------|-----------|
| Distribution (0-1/5) | Bullish | **Bearish** | Smart money selling into strength. TA rally is a trap. |
| Accumulation (4-5/5) | Bearish | **Bullish** | Smart money buying the dip. TA weakness is opportunity. |
| Accumulation (4-5/5) | Neutral | **Bullish (Watch)** | Setup building but needs TA confirmation to time entry. |
| Distribution (0-1/5) | Neutral | **Bearish (Watch)** | Smart money exiting but no TA trigger yet. |

### Perps Conflicts with On-Chain (On-Chain Wins)

| On-Chain | Perps | Verdict | Reasoning |
|----------|-------|---------|-----------|
| Accumulation | Smart money short | **Cautious Bullish** | On-chain trumps, but reduce size. Perps divergence = timing risk. |
| Distribution | Smart money long | **Bearish** | Trapped longs will add selling pressure when they capitulate. |

### Derivatives Confirm or Contradict

Derivatives data (funding, OI, L/S) sits between perps and TA. It doesn't override on-chain or perps — it adds or subtracts conviction.

| Derivatives Signal | Effect on Verdict |
|-------------------|-------------------|
| Extreme funding >0.03% (longs paying) | +conviction on SHORT. Mechanical pressure to resolve via liquidation. |
| Extreme funding <-0.03% (shorts paying) | +conviction on LONG. Squeeze fuel building. |
| OI expanding + extreme L/S | Flag cascade risk. More fuel for forced liquidation in the majority direction. |
| Top trader position diverges from global L/S | Note smart vs retail divergence. Follow the smart money lean. |
| OI diverges from price (OI up, price down) | New shorts entering. Bearish continuation signal. |
| Liquidity Grab Fade detected | Surface as a verdict point. These are mechanical and time-sensitive. |

---

## Accumulation Score Scale (5-signal system)

| Score | Label | What It Means |
|-------|-------|--------------|
| 5/5 | Strong Accumulation | All 5 on-chain signals bullish. Highest conviction buy signal. |
| 4/5 | Accumulation | Clear accumulation pattern. Strong buy unless regime prohibits. |
| 3/5 | Mild Accumulation | Leaning bullish but mixed. Watchlist, not entry. |
| 2/5 | Mixed | No edge. Conflicting signals. Wait. |
| 1/5 | Distribution | Clear selling pattern. Supports short thesis. |
| 0/5 | Strong Distribution | All 5 signals bearish. Strongest sell/short signal. |

---

## Regime Modifier

The signal hierarchy operates within the current regime from `_config/thesis.md`:

- **Risk-On regime:** Long signals get full weight. Short signals need extra confirmation (on-chain distribution required, not just TA overbought).
- **Risk-Off regime:** Short signals get full weight. Long signals require exceptional on-chain evidence (3+ funds, >$20M, per accumulation long criteria in thesis).
- **Chop regime:** All signals get reduced conviction. Smaller position sizes. Tighter stops.

---

## Edge Cases

**When on-chain data is unavailable** (Nansen down, credits exhausted):
- Verdict relies on Perps > Derivatives > TA only
- Explicitly state: "Reduced confidence — on-chain data unavailable"
- Reduce position size by 50%

**When a token has no perps market:**
- Skip perps pillar entirely
- On-Chain > Derivatives > TA
- Note the gap in the verdict

**When derivatives data is unavailable** (Coinglass key missing):
- On-Chain > Perps > TA
- No derivatives confluence check
- Note: "Derivatives unavailable — no funding/OI/L/S data"
