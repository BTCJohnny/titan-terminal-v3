# Alpha Score Calculation

## Purpose
Quantify the strength of a pre-breakout accumulation setup with a 0-12 point scoring system. The Alpha Score determines whether to trade, watchlist, or pass.

## The 5 Signals (Max 12 Points)

### Signal 1: Entity Balance Increase (0-3 pts)

**Source:** [research/entity-tracking.md](../research/entity-tracking.md)

Measure the largest entity balance increase over the analysis window (typically 4 weeks):

| Balance Change | Points | Rating |
|----------------|--------|--------|
| +100%+ | 3 | **Alpha** — extreme accumulation (e.g., Wintermute 3x on SOL) |
| +50-100% | 2 | **Strong** — significant position building |
| +25-50% | 1 | **Weak** — moderate interest |
| < +25% | 0 | No signal |

**Notes:**
- Use the **single highest entity change** — one entity going 3x is a stronger signal than three entities up 20%
- Insider buys (founder/CEO) at range lows score 3 regardless of magnitude — information advantage is the signal
- This is the highest-weighted signal (3 points max) because entity-level data has the best predictive track record

**DB logging:** After querying entity positions, log the snapshot:
`python3 src/storage/intelligence.py store-entities --token [TOKEN] --date [YYYY-MM-DD] --chain [CHAIN] --data '[ENTITIES_JSON]'`
On subsequent runs, check stored history first:
`python3 src/storage/intelligence.py entity-diff [TOKEN]`
This gives you week-over-week trends from YOUR OWN data, not just Nansen's sometimes-limited historical view.

### Signal 2: Price at Range Low (0-2 pts)

**Source:** [research/price-positioning.md](../research/price-positioning.md)

| Distance from 30d Low | Points | Rating |
|------------------------|--------|--------|
| Within 10% | 2 | **Prime zone** — maximum discounted |
| Within 20% | 1 | Accumulation zone — still attractive |
| > 20% above low | 0 | Extended — may be too late |

### Signal 3: Volume Contraction (0-2 pts)

**Source:** [research/volume-analysis.md](../research/volume-analysis.md)

| Volume vs 20d Avg | Points | Rating |
|--------------------|--------|--------|
| 20%+ below avg | 2 | **Strong dry-up** — selling exhaustion |
| 10-20% below avg | 1 | Moderate contraction |
| Near or above avg | 0 | No dry-up signal |

### Signal 4: Exchange Outflows (0-2 pts)

**Source:** [research/exchange-flows.md](../research/exchange-flows.md)

| Outflows (% of supply, 4 weeks) | Points | Rating |
|----------------------------------|--------|--------|
| > 3% of circulating supply | 2 | **Strong squeeze** — significant supply removal |
| > 1% of circulating supply | 1 | Moderate outflows |
| < 1% or net inflows | 0 | No signal |

**⚠️ MANDATORY: Use 14-day balance trend, not just snapshot.** Run `token_flows` with `holder_segment: exchange` and `dateRange: 14D_AGO to NOW`. Count outflow days vs inflow days. If the snapshot shows inflows but the balance trend shows decline over 14 days, score based on the TREND, not the snapshot. See [exchange-flows.md — SKY case study](../research/exchange-flows.md) for why this matters.

**DB logging:** After querying exchange flows, log the daily data:
`python3 src/storage/intelligence.py store-exchange-balance --token [TOKEN] --chain [CHAIN] --data '[DAILY_JSON]'`
This builds the longitudinal trend data that makes future runs more accurate.

**N/A for native tokens:** If exchange flow data is unavailable (native tokens like SOL), score this signal out of the available maximum. Adjust the total denominator from 12 to 10.

### Signal 5: Top 100 Holder Increase (0-2 pts)

**Source:** [research/holder-analysis.md](../research/holder-analysis.md)

| Supply Accumulated by Top 100 | Points | Rating |
|-------------------------------|--------|--------|
| +10% supply | 2 | **Strong accumulation** |
| +5% supply | 1 | Moderate accumulation |
| < +5% or net decrease | 0 | No signal |

---

## Scoring Table

| Signal | Max | Source |
|--------|-----|--------|
| Entity Balance Increase | 3 | Entity tracking |
| Price at Range Low | 2 | Price history |
| Volume Contraction | 2 | Volume analysis |
| Exchange Outflows | 2 | Exchange flows |
| Top 100 Holder Increase | 2 | Holder analysis |
| **Total** | **12** | |

---

## Interpretation

| Score | Rating | Action |
|-------|--------|--------|
| **11-12** | Alpha | **High conviction entry** — all signals firing, rare setup |
| **8-10** | Strong | **Consider entry** — strong pattern, standard position size |
| **5-7** | Moderate | **Watchlist only** — pattern forming but needs more confirmation |
| **0-4** | Weak | **Pass** — insufficient signals, no trade |

## Edge Cases

### Adjusted Denominator (Native Tokens)
If exchange flow data is unavailable, the max score becomes 10:
- 9-10 = Alpha
- 7-8 = Strong
- 4-6 = Moderate
- 0-3 = Weak

Note in report: "Alpha Score: 8/10 (exchange flows N/A — native token)"

### Insider Buy Override
A confirmed founder/CEO buy at or near the range low is such a high-conviction signal that it should be scored as 3 points for entity balance PLUS a qualitative flag: **"Insider signal — highest conviction."** This was the lesson from ZRO.

### Single Entity vs Multiple Entities
- **Single entity loading:** Strong signal but concentration risk — one actor's thesis
- **Multiple entities loading:** Higher conviction — convergence of independent information
- **Multiple entities + insider:** Maximum conviction

### Score Conflict with Timing
A token can score 8/12 but be too late if:
- Price has already moved 15%+ from the accumulation zone
- Entities are starting to distribute (not accumulate)
- Volume is expanding (breakout already in progress)

In this case, note: "Alpha Score 8/12 but **breakout may be in progress**. Wait for pullback to re-entry zone or pass."

---

## Output Format

```markdown
## Alpha Score: [X]/12 — [Rating]

| Signal | Score | Evidence |
|--------|-------|----------|
| Entity Balance Increase | X/3 | [Entity name] +X% over [period] |
| Price at Range Low | X/2 | Current price X% above 30d low ($X) |
| Volume Contraction | X/2 | Volume X% below 20d avg |
| Exchange Outflows | X/2 | -X% of supply over 4 weeks |
| Top 100 Holder Increase | X/2 | Net +X% supply accumulated |

**Rating: [Weak/Moderate/Strong/Alpha]**
**Action: [Pass / Watchlist / Consider Entry / High Conviction]**
```

### Derivatives Flags (Qualitative — Does NOT Change Score)

After computing the Alpha Score, check derivatives data via:
```bash
python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --derivatives --json
```

Add qualitative flags to the report:
- Funding rate negative while entities accumulate → "Derivatives aligned — shorts will fuel breakout"
- OI expanding while entities accumulate → "New positions building alongside entity loading"
- L/S ratio shows extreme short crowding → "Contrarian setup — retail short, smart money long"

These flags add conviction context but do NOT modify the numerical score. The Alpha Score is purely on-chain.

### Distributor Exhaustion Analysis

For any entity with a DECLINING balance identified during entity tracking:
1. Note their current remaining position
2. Calculate their weekly sell rate (7d balance change)
3. Estimate weeks of remaining sell pressure: `remaining / weekly_sell_rate`

If sell pressure > 4 weeks: flag "⚠️ [Entity] has ~X weeks of distribution overhead at current rate"

This is critical context. If Entity A is buying $5M/week but Entity B is selling $7M/week, the NET flow is negative — accumulation thesis is compromised regardless of the Alpha Score.

---

## Case Study Scores

**ZRO (7.5/10 adjusted):**
- Entity: 3/3 (CEO insider buy at exact low)
- Price: 2/2 (at 30d low)
- Volume: 2/2 (40% below avg)
- Exchange: 2/2 (5.2% supply outflow)
- Top 100: 1/2 (+7.7M ZRO, estimated ~5% supply)
- **Note:** Originally scored 7.5/10 on v1.0 scale; equivalent to 9/12 on v2.0 scale

**SOL (8/12):**
- Entity: 3/3 (Wintermute 3x position)
- Price: 2/2 (at 30d low)
- Volume: 2/2 (30% below avg)
- Exchange: 0/2 (N/A — native token)
- Top 100: 1/2 (estimated +5%)
