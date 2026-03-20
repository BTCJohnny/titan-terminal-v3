# Trade Card Output Format

## Section Order (Fixed — Never Varies)

1. Header
2. Snapshot
3. Price Action
4. Flow Signals
5. Accumulation Check
6. Funding Rate (omit if no perps)
7. Verdict
8. Footer

Every Trade Card follows this order. No exceptions.

---

## Template
```markdown
# [EMOJI] [TOKEN] — Titan Trade Card

## Snapshot
**Price:** $X | **Market Cap:** $X | **Rank:** #X
**Volume:** $X | **FDV:** $X | **Supply:** XB / XB
**24h:** +X% | **7d:** -X%

---

## Price Action: [2-3 Word Summary]

**Regime:** [Full bull / Full bear / Transitional] — Price [above/below] SMA 200, [Golden Cross / Death Cross / neither]

[Flowing paragraph — connect key findings across Weekly, Daily, 4H into a narrative.
Lead with the most important signal and which timeframe it comes from.
Tell the story of what the market is doing. End with plain-English "So What?"]

**Timeframe Alignment:** [All aligned / Mostly aligned / Conflicting]
- Weekly: [direction] — [1-line key reason]
- Daily: [direction] — [1-line key reason]
- 4H: [direction] — [1-line key reason]

**Key Levels:** Support $X ([strength]) | Resistance $X ([strength]) | Invalidation $X
**TA Confidence:** [X]%

---

## Flow Signals: [Bullish/Bearish/Mixed]

[Interpretation paragraph — who is buying, who is selling, divergences,
"So what?" conclusion.]

---

## Accumulation Check: [X]/5 — [Label]

| Signal | Rating | Detail |
|--------|--------|--------|
| Exchange Flows | [Rating] | [1-line] |
| Fresh Wallets | [Rating] | [1-line] |
| Smart Money | [Rating] | [1-line] |
| Top PnL Traders | [Rating] | [1-line] |
| Whale Activity | [Rating] | [1-line] |

---

## Funding Rate: [Bullish/Bearish/Neutral]
- **Smart Money Positioning:** [Net Long/Net Short/Balanced]
- **Contrarian Signal:** [Yes/No]

[Interpretation paragraph if data available.]

---

## Verdict

**[Direction] — [One-sentence thesis]**

- [emoji] [Point 1 — strongest signal]
- [emoji] [Point 2]
- [emoji] [Point 3]
- [emoji] [Point 4]
- [emoji] [Point 5 — risk/watch condition]

**[Closing instruction — entry + stop OR "do not touch" + reversal conditions]**

---
*Generated: YYYY-MM-DD — Titan Trade Card v2*
```

---

## Formatting Rules

### DO
- **Bold** key metrics and labels
- Use `---` horizontal rules between every section
- Tables for structured data (accumulation check only)
- Flowing prose for interpretation sections
- Descriptive emojis for verdict points (describe the point, not just checkmarks)
- Specific numbers: "$152.7k short" not "large short"
- Start verdict thesis with the strongest word: "Dead money." / "Accumulation zone."

### DON'T
- ASCII art tables or code blocks for data display
- Bullet lists for interpretation sections (use flowing prose)
- Hedged language ("could go either way", "hard to say")
- Multiple verdict options ("Bullish IF... Bearish IF...")
- Generic conclusions without data backing
- Skip the closing instruction

## Header Emoji Guide

| Verdict | Emoji Style |
|---------|-------------|
| Bullish | Token's emoji, rocket, chart up, green |
| Bearish | Skull, ice, red, chart down |
| Neutral | Hourglass, yellow, magnifying glass |

## Auto-Save

After displaying: save to `results/trade-cards/[TOKEN]_[YYYY-MM-DD].md` and append to `my-trading/journal/YYYY_QN.md` with date header and `---` separator.
