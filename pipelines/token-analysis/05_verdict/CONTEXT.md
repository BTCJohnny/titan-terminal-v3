# Stage: 05_verdict — Synthesis + Trade Card

## Purpose

Combine all 4 data pillars into a single directional verdict and formatted trade card. This is the final output — the answer to "buy, sell, or ignore?"

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../01_resolve/output/identity.md` | 4 (working) |
| Previous stage | `../02_technical/output/ta_verdict.md` | 4 (working) |
| Previous stage | `../03_onchain/output/flows.md` | 4 (working) |
| Previous stage | `../03_onchain/output/accumulation.md` | 4 (working) |
| Previous stage | `../04_derivatives/output/derivatives.md` | 4 (working) |
| Previous stage | `../04_derivatives/output/perps.md` | 4 (working) |
| Reference | `_config/thesis.md` | 3 (factory) |
| Reference | `_config/signal-hierarchy.md` | 3 (factory) |
| Reference | `_config/position-sizing.md` | 3 (factory) |
| Reference | `_config/examples/trade-card-example.md` | 3 (factory) |

## Process

### Step 1: Apply Signal Hierarchy

Use the decision rules from `_config/signal-hierarchy.md`:

**When all pillars agree:**
- TA Bullish + Accumulation (4-5) + Perps Long → **Bullish — High Conviction**
- TA Bearish + Distribution (0-1) + Perps Short → **Bearish — High Conviction**
- Mixed across all → **Neutral — No Edge, Wait**

**When on-chain conflicts with TA (on-chain wins):**
- TA Bullish + Distribution (0-1) → **Bearish** — Smart money selling into strength
- TA Bearish + Accumulation (4-5) → **Bullish** — Smart money buying the dip
- TA Neutral + Accumulation (4-5) → **Bullish (Watch)** — Setup building, needs confirmation

**When perps conflict with on-chain (on-chain wins):**
- Accumulation + Perps Short → **Cautious Bullish** — On-chain trumps, smaller size
- Distribution + Perps Long → **Bearish** — Trapped longs add selling pressure

**Derivatives confluence (if available):**
- Extreme funding (>0.03% or <-0.03%): note crowding risk
- OI expanding + extreme L/S: flag cascade risk
- Top trader position diverging from global: note smart vs retail divergence
- Liquidity Grab Fade detected: surface as verdict point with direction

### Step 2: Thesis Alignment Check

Compare the verdict against `_config/thesis.md`:
- If the token has an active thesis: does the analysis confirm or contradict? Flag conflicts explicitly.
- If the token matches a target setup type: note which one (Distribution Short, Accumulation Long, Breakout, Mean Reversion). A token can match multiple types.
- If the token is in a focus sector: note it.

### Step 3: Build Verdict

The verdict must include:
1. **Direction:** Bullish / Bearish / Neutral
2. **One-sentence thesis** — quotable. A trader reads only this and understands the setup.
3. **4-6 verdict points** with descriptive emojis (strongest signal first, risk factor last)
4. **Closing instruction** — specific entry zone + stop level, OR "do not touch" + what would change

### Step 4: Format Trade Card

Follow the format in `_config/examples/trade-card-example.md`. Structure:

```
# [EMOJI] [TOKEN] — Titan Trade Card

## Snapshot
**Price:** $X | **Market Cap:** $X | **Rank:** #X
**Volume:** $X | **FDV:** $X
**24h:** +X% | **7d:** -X%

---

## Price Action: [2-3 Word TA Summary]
[TA interpretation as flowing prose — connect the 7-Question answers into a narrative.
Lead with the most important signal. Reference the ta-analyst's verdict and confidence.
Include key levels, regime, and the "So What?"]

---

## Flow Signals: [Bullish/Bearish/Mixed]
[On-chain interpretation as flowing prose — who is buying, who is selling,
divergences between segments, "So what?" conclusion.]

---

## Accumulation Check: [X]/5 — [Label]
| Signal | Rating | Detail |
|--------|--------|--------|
| Exchange Flows | [Bullish/Bearish/Neutral] | [1-line] |
| Fresh Wallets | [Bullish/Bearish/Neutral] | [1-line] |
| Smart Money | [Bullish/Bearish/Neutral] | [1-line] |
| Top PnL Traders | [Bullish/Bearish/Neutral] | [1-line] |
| Whale Activity | [Bullish/Bearish/Neutral] | [1-line] |

---

## Funding Rate: [Bullish/Bearish/Neutral/Unavailable]
**Smart Money Positioning:** [Net Long/Net Short/Balanced]
**Contrarian Signal:** [Yes/No — explain if yes]
[Interpretation paragraph if data available. Omit section if no perps.]

---

## Derivatives Intelligence: [Bullish/Bearish/Neutral/Unavailable]
[Only include if Coinglass data was available. Full derivatives breakdown:
funding, OI, L/S ratios, liquidation activity, options (BTC/ETH), synthesis paragraph.
If Liquidity Grab Fade detected, flag with direction and snap-back target.]

---

## Verdict
**[Direction] — [One-sentence thesis]**

- [emoji] [Point 1 — strongest signal]
- [emoji] [Point 2]
- [emoji] [Point 3]
- [emoji] [Point 4]
- [emoji] [Point 5 — risk factor or watch condition]

**[Closing instruction — entry zone + stop OR "do not touch" + reversal conditions]**
```

### Formatting rules:
- **Verdict first, logic second** — in every section
- Write interpretation as flowing prose, NOT bullet lists of raw indicators
- Every metric gets a "So what?" — no "it depends" or "could go either way"
- Use specific numbers: "$152.7k short" not "large short position"
- If the data says don't buy, say "Do not touch this."
- Descriptive emojis for verdict points (not just checkmarks)
- Bold key metrics and labels

## Scripts Used

None — this is pure synthesis.

## Outputs

| File | Contents |
|------|----------|
| `output/verdict.md` | Direction, thesis sentence, verdict points, closing instruction, thesis alignment notes |
| `output/trade_card.md` | Full formatted Titan Trade Card (all sections above) |

## Post-Output Actions

1. Save trade card to `results/trade-cards/[TOKEN]_[YYYY-MM-DD].md`
2. Auto-journal: append to `trading/journal/YYYY_QN.md` with date header and `---` separator
3. If called from find-setups/04_analyze: copy outputs to `find-setups/04_analyze/output/[TOKEN]/`

## Review Gate

Final assessment:
- Does the verdict direction match the strongest pillar (on-chain)?
- Is the one-sentence thesis clear and specific?
- Do the key levels have actionable R:R?
- Does this confirm or challenge the active thesis? (conflict should be flagged prominently)
