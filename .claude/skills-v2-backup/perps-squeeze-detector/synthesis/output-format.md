# Output Format

## Purpose

Standardized report templates for squeeze analysis results. Two formats: `scan-squeeze` (single token) and `hunt-squeezes` (multi-token scan).

---

## scan-squeeze Report Template

```markdown
# [EMOJI] [TOKEN] — Perps Squeeze Analysis

**Date:** YYYY-MM-DD | **Price:** $X,XXX | **Squeeze Score:** X/10 [Rating]

---

## Positioning Summary

**Long:** $X.XM across N traders
**Short:** $X.XM across N traders
**Imbalance:** X:1 [direction]-heavy
**Concentration:** [Distributed/Concentrated]

### Key Positions (Crowded Side)

| Trader | Direction | Size | Entry | Mark | Liq Price | P&L |
|--------|-----------|------|-------|------|-----------|-----|
| [Name] | [L/S] | $X.XM | $X,XXX | $X,XXX | $X,XXX | [+/-X%] |

---

## Liquidation Cascade Map

**Squeeze Direction:** [Short/Long] squeeze
**Trigger Line:** $X,XXX (X.X% from current price)
**Total Cascade Fuel:** $X.XM forced [buying/selling]

| Zone | Price Range | Liquidations | Forced Pressure | Cumulative |
|------|-------------|--------------|-----------------|------------|
| Trigger | $X,XXX-$X,XXX | N positions | $X.XM | $X.XM |
| Acceleration | $X,XXX-$X,XXX | N positions | $X.XM | $X.XM |
| Exhaustion | $X,XXX-$X,XXX | N positions | $X.XM | $X.XM |

**Fuel Gaps:** [Location and size of gaps >5%]

---

## Macro Context

| Factor | Assessment | Detail |
|--------|-----------|--------|
| CEX Flows | [Supportive/Opposing/Neutral] | [Detail] |
| BTC Momentum | [Supportive/Opposing/Neutral] | [Detail] |
| Funding Rate | [Supportive/Opposing/Neutral] | [Rate] |
| Position Trend | [Opening/Closing] | [Detail] |
| Spot Divergence | [Yes/No] | [Detail] |

**Catalyst Score:** X/5

---

## Squeeze Score: X/10 — [Alpha/Strong/Moderate/Weak]

| Signal | Score | Detail |
|--------|-------|--------|
| Position Imbalance | X/3 | [Detail] |
| Liquidation Proximity | X/2 | [Detail] |
| Cascade Density | X/2 | [Detail] |
| Macro Catalyst | X/2 | [Detail] |
| Spot Divergence | X/1 | [Detail] |

---

## Trade Setup

### Primary: [Long/Short] (Squeeze Direction)

| Level | Price | Distance | Rationale |
|-------|-------|----------|-----------|
| Entry | $X,XXX | — | [Before trigger line / at support] |
| Stop | $X,XXX | -X.X% | [Below recent structure] |
| Target 1 | $X,XXX | +X.X% | [First fuel gap / cascade pause] |
| Target 2 | $X,XXX | +X.X% | [Cascade exhaustion] |
| R:R | X.X:1 | — | [Risk-reward ratio] |

### Secondary: Fade After Squeeze

| Level | Price | Distance | Rationale |
|-------|-------|----------|-----------|
| Entry | $X,XXX | — | [Where cascade fuel exhausts] |
| Stop | $X,XXX | +X.X% | [Above next liquidation cluster] |
| Target | $X,XXX | -X.X% | [Pre-squeeze levels] |

### Position Sizing (2% Risk)

[Standard target package calculation — reference playbooks/trading/target-package.md]

---

## Verdict

**[Squeeze Score Rating]** — [1-2 sentence verdict with conviction level and key driver]

[Key risk / what could invalidate the setup]
```

---

## hunt-squeezes Report Template

```markdown
# Perps Squeeze Hunt — YYYY-MM-DD

## Screening Summary

**Tokens Scanned:** N
**Candidates Found:** N (>70% one-sided)
**Full Analysis:** Top 3

---

## Candidate Overview

| Rank | Token | Imbalance | Ratio | Squeeze Score | Direction | Status |
|------|-------|-----------|-------|---------------|-----------|--------|
| 1 | [TOKEN] | [direction] | X:1 | X/10 [Rating] | [Short/Long] squeeze | [Setup/Watch/Pass] |
| 2 | [TOKEN] | [direction] | X:1 | X/10 [Rating] | [Short/Long] squeeze | [Setup/Watch/Pass] |
| 3 | [TOKEN] | [direction] | X:1 | X/10 [Rating] | [Short/Long] squeeze | [Setup/Watch/Pass] |

---

## Detailed Analysis

### #1: [TOKEN] — Squeeze Score X/10

[Abbreviated scan-squeeze report — positioning summary, key cascade levels, trade setup]

### #2: [TOKEN] — Squeeze Score X/10

[Abbreviated scan-squeeze report]

### #3: [TOKEN] — Squeeze Score X/10

[Abbreviated scan-squeeze report]

---

## Eliminated Tokens

| Token | Why Eliminated |
|-------|---------------|
| [TOKEN] | [Balanced positioning / insufficient OI / squeeze already happened] |

---

## Actions

- **Trade setups:** [List tokens with Score 8+]
- **Watchlist adds:** [List tokens with Score 4-7]
- **Next scan:** [Recommended timing for re-scan]
```

---

## Formatting Rules

### DO
- Bold all dollar amounts and ratios
- Use tables for structured cascade data
- Lead with Squeeze Score before breakdown
- Quantify everything — no vague language
- Include both squeeze AND post-squeeze fade setups
- Show R:R for every trade setup

### DON'T
- Use code blocks for data (use tables)
- Hedge with "might" or "could" — be direct
- Include raw API responses
- Skip the macro context — catalyst matters
- Present more than 3 candidates in hunt report

## Auto-Save

Save reports to:
- `results/skill-runs/perps-squeeze-detector/[TOKEN]_[YYYY-MM-DD]_squeeze.md` (scan-squeeze)
- `results/skill-runs/perps-squeeze-detector/HUNT_[YYYY-MM-DD].md` (hunt-squeezes)

Auto-append to quarterly journal at `my-trading/journal/YYYY_QX.md` if Score >= 6. (Journal formatter not yet ported — append manually.)
