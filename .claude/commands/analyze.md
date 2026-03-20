---
name: analyze
description: Full Titan Trade Card — technical analysis, on-chain flows, accumulation scoring, perps positioning, and verdict synthesis for any token.
argument-hint: <TOKEN>
allowed-tools:
  - Read
  - Bash
  - mcp__nansen
  - mcp__coinstats
---

# /analyze $ARGUMENTS

Run a complete Titan Trade Card analysis for the specified token.

## What This Produces

A Trade Card answers one question: **"Should I buy, sell, or ignore this right now — and why?"**

It combines 4 data pillars, synthesizes a directional verdict, and auto-saves the result.

## Signal Weight Hierarchy
```
On-Chain Flows & Accumulation  >  Perps Positioning  >  Derivatives Intelligence  >  Technical Analysis
```

On-chain shows what people are actually doing with money (highest signal). Perps shows what smart traders are betting (strong signal). Derivatives shows crowd behavior across exchanges — funding, OI, L/S ratios (confirmatory signal). TA shows what price has done — it lags by definition (supporting signal). When signals conflict, higher-weight sources win.

---

## Execution Plan

### Step 0: Cache Check

Before making any Nansen calls, check the cache for each required data point. For each call below, run the cache check first — if it returns `CACHE_HIT`, use the stored response and skip the live Nansen call entirely.

```bash
# Check cache for flows (1d)
python3 src/storage/nansen_cache.py check --tool token_recent_flows_summary \
    --token [TOKEN] --params '{"chain":"[chain]","tokenAddress":"[address]","lookbackPeriod":"1d"}'

# Check cache for flows (7d)
python3 src/storage/nansen_cache.py check --tool token_recent_flows_summary \
    --token [TOKEN] --params '{"chain":"[chain]","tokenAddress":"[address]","lookbackPeriod":"7d"}'

# Check cache for smart money holders
python3 src/storage/nansen_cache.py check --tool token_current_top_holders \
    --token [TOKEN] --params '{"chain":"[chain]","tokenAddress":"[address]","labelType":"smart_money","mode":"onchain_tokens"}'

# Check cache for top 100 holders
python3 src/storage/nansen_cache.py check --tool token_current_top_holders \
    --token [TOKEN] --params '{"chain":"[chain]","tokenAddress":"[address]","labelType":"top_100_holders","mode":"onchain_tokens"}'

# Check cache for perps
python3 src/storage/nansen_cache.py check --tool token_current_top_holders \
    --token [TOKEN] --params '{"tokenAddress":"[TOKEN]","mode":"perps","labelType":"smart_money"}'
```

**Cache TTLs (enforced by the script):**
- Flow summaries: 6h
- On-chain holders (smart money, top 100): 12h
- Perps holders: 1h
- Token identity search: 24h

If all 5 checks return `CACHE_HIT`, skip Steps 1 and 4–5 entirely — 0 Nansen credits used.
If any return `CACHE_MISS`, fetch only those from Nansen and store the results immediately after.

**After each live Nansen call that was a cache miss, store the response:**
```bash
python3 src/storage/nansen_cache.py store --tool [tool_name] \
    --token [TOKEN] --params '[params_json]' --response '[response_json]'
```

---

### Step 1: Resolve Token Identity

Check cache first:
```bash
python3 src/storage/nansen_cache.py check --tool general_search \
    --token [TOKEN] --params '{"query":"[TOKEN]"}'
```

If `CACHE_MISS`, use Nansen to find the token's chain and contract address:
```
mcp__nansen__general_search: query "$ARGUMENTS"
```
Then store:
```bash
python3 src/storage/nansen_cache.py store --tool general_search \
    --token [TOKEN] --params '{"query":"[TOKEN]"}' --response '[response_json]'
```

Extract:
- Token name and symbol
- Chain (ethereum, solana, base, etc.)
- Contract address (needed for subsequent Nansen calls)

Also determine the CoinStats ID (lowercase-hyphenated format: "pyth-network", "chainlink", "ethereum"). For common tokens: BTC = "bitcoin", ETH = "ethereum", SOL = "solana".

If the token cannot be found, stop and tell the user: "Could not resolve [TOKEN]. Check the symbol and try again."

---

### Steps 2-5: Run in Parallel

After Step 1 completes, launch these four steps simultaneously. They have no dependencies on each other.

#### Step 2: Market Snapshot
```
mcp__coinstats__get-coin-by-id: coinId "[coinstats-id]"
```

Extract: price, market cap, rank, 24h volume, FDV, circulating supply, total supply, 24h change %, 7d change %.

#### Step 3: Technical Analysis → Delegate to ta-analyst

Delegate the full multi-timeframe TA to the **ta-analyst** subagent with this task:

> Run a complete 7-Question technical analysis for $ARGUMENTS across Weekly, Daily, and 4H timeframes. Download data, run all 8 indicators (RSI, MACD, ADX+DI, BB, OBV, S/R, SMA 50/200, ATR), interpret results, resolve timeframe conflicts, then drill down to 1H (S/R, ATR, RSI, BB) to refine precise entry, stop, and target levels. Return the structured verdict with 1H-refined key levels, R:R at each target, confidence score, and the "So What?" section. **Explicitly evaluate both long and short setups** — if the data supports a short opportunity (confirmed downtrend, distribution, breakdown structure, crowded longs), flag it directly with 1H-refined entry, stop, and R:R. Do not bias toward longs by default.

The ta-analyst will return a structured TA verdict. Do NOT re-run the analysis — use the subagent's output directly.

#### Step 4: On-Chain Flows

For each call, check cache first (Step 0). Only make the live call on a `CACHE_MISS`, then store.

**4a — Recent flow summary (1d and 7d):**
```
mcp__nansen__token_recent_flows_summary: chain "[chain]", tokenAddress "[address]", lookbackPeriod "1d"
mcp__nansen__token_recent_flows_summary: chain "[chain]", tokenAddress "[address]", lookbackPeriod "7d"
```

**4b — Top holders (smart money + top 100):**
```
mcp__nansen__token_current_top_holders: chain "[chain]", tokenAddress "[address]", labelType "smart_money"
mcp__nansen__token_current_top_holders: chain "[chain]", tokenAddress "[address]", labelType "top_100_holders"
```

Interpret: Who is buying? Who is selling? Are exchange flows showing accumulation (outflows) or distribution (inflows)? Are smart money wallets adding or reducing? What's the "So what?"

#### Step 4c: Derivatives Intelligence (Coinglass)

Runs in parallel with Steps 2-5 — no dependencies.

```bash
python3 src/fetchers/coinglass_fetcher.py --token [TOKEN] --price [PRICE] --derivatives --json
```

If COINGLASS_API_KEY is not set or the call fails, skip this step silently — the trade card is still valid without it.

From the JSON output, extract:
- **Funding rate:** cross-exchange average, bias (crowded long/short/neutral), annualized cost
- **Open Interest:** current OI, 24h change %, trend (rising/falling/flat), exchange momentum
- **Long/Short Ratio:** global account ratio, top trader account + position ratios, smart money lean, contrarian signals
- **Liquidation activity:** 24h totals, long/short breakdown, L/S ratio, directional bias (from existing data)
- **Options max pain:** nearest expiry target, distance from price (BTC/ETH only)
- **Liquidity Grab Fade setup detection** (if conditions align, from existing logic)

This data feeds into the Derivatives Intelligence section of the trade card and informs the verdict synthesis.

#### Step 5: Perps Positioning

Check cache first (Step 0). Only call live on `CACHE_MISS`, then store.

```
mcp__nansen__token_current_top_holders: tokenAddress "[TOKEN]", mode "perps", labelType "smart_money"
```

If the token has no perps market, skip this step and note "No perps data available."

Interpret: What are smart money perps traders doing? Net long or net short? What's the funding rate implying? Is there a contrarian signal (crowded positioning)?

---

### Step 6: Score Accumulation

Using the data from Step 4, score 5 signals as Bullish, Bearish, or Neutral:

| Signal | Source | Bullish | Bearish |
|--------|--------|---------|---------|
| Exchange Flows | flow_summary | Net outflows (leaving CEX) | Net inflows (to CEX) |
| Fresh Wallets | flow_summary | High new wallet inflows | Low/negative |
| Smart Money | top_holders smart_money | Buying/holding | Selling/reducing |
| Top PnL Traders | flow_summary | Net positive flow | Net negative flow |
| Whale Activity | top_holders top_100 | Accumulating | Distributing |

**Scoring:**
- Count bullish signals: 5/5 = Strong Accumulation, 4/5 = Accumulation, 3/5 = Mild Accumulation
- 2/5 = Mixed, 1/5 = Distribution, 0/5 = Strong Distribution

---

### Step 7: Synthesize Verdict

Combine all 4 pillars into a single directional call.

**Verdict Decision Rules:**

When all pillars agree:
- TA Bullish + On-Chain Accumulation (4-5) + Perps Long → **Bullish — High Conviction**
- TA Bearish + On-Chain Distribution (0-1) + Perps Short → **Bearish — High Conviction**
- Mixed across all → **Neutral — No Edge, Wait**

When on-chain conflicts with TA (on-chain wins):
- TA Bullish + Distribution (0-1) → **Bearish** — Smart money selling into strength
- TA Bearish + Accumulation (4-5) → **Bullish** — Smart money buying the dip
- TA Neutral + Accumulation (4-5) → **Bullish (Watch)** — Setup building, wait for TA confirmation

When perps conflict with on-chain (on-chain wins):
- Accumulation + Perps Short → **Cautious Bullish** — On-chain trumps, but smaller size
- Distribution + Perps Long → **Bearish** — Trapped longs will add selling pressure

**Liquidation confluence check (if Coinglass data available):**
- If entry is near a liquidation cluster: flag stop-hunting risk in verdict points
- If targets align with liquidation cascade zones: note mechanical fuel that supports the move
- If a Liquidity Grab Fade setup is detected: surface it as a verdict point with direction and confidence

**Derivatives confluence check (if Coinglass data available):**
- If funding is extreme (>0.03% or <-0.03%): note crowding risk in verdict points — extreme funding is mechanical pressure that resolves through liquidation
- If OI is expanding while L/S ratio is extreme: flag cascade risk — new positions in a crowded market = more fuel for forced liquidations
- If top trader position ratio diverges from global account ratio: note the divergence — smart money sizing often contra to retail account count
- If OI diverges from price direction: flag it (OI up + price down = new shorts entering, bearish continuation)
- Derivatives data ranks between perps positioning and TA in the signal hierarchy: On-Chain > Perps > Derivatives > TA

**Verdict must include:**
1. Direction: Bullish / Bearish / Neutral
2. One-sentence thesis (quotable — a trader reads only this and understands the setup)
3. 4-6 verdict points with descriptive emojis (strongest signal first)
4. Closing instruction (specific entry zone, stop level, or "do not touch")

### Thesis Alignment Check

After forming the verdict, check it against `reference/titan-thesis.md`:

- **If the token has an active thesis:** Does the analysis confirm or contradict it? If the verdict differs from the thesis, flag the conflict explicitly: "⚠️ This analysis CONTRADICTS the active [thesis name]. The thesis says [X], but current data says [Y]. Review the thesis."
- **If the token matches a target setup type:** Note it: "This setup matches the [Distribution Short / Accumulation Long / Breakout / Mean Reversion] pattern from the active framework." A single token can match multiple types (e.g., TAO is both a distribution short and a mean reversion fade).
- **If the token is in a focus sector:** Note it: "[TOKEN] is in the [sector] focus area."

This prevents drift — the system stays aligned with the macro view unless data explicitly contradicts it.

---

### Step 8: Format and Save

#### Output Format

Render the Trade Card using this exact structure:
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
Include key levels, regime, and the "So What?" from the subagent.]

---

## Flow Signals: [Bullish/Bearish/Mixed]

[On-chain interpretation as flowing prose — who is buying, who is selling,
any divergences between segments, and the "So what?" conclusion.]

---

## Accumulation Check: [X]/5 — [Label]

| Signal | Rating | Detail |
|--------|--------|--------|
| Exchange Flows | [Bullish/Bearish/Neutral] | [1-line explanation] |
| Fresh Wallets | [Bullish/Bearish/Neutral] | [1-line explanation] |
| Smart Money | [Bullish/Bearish/Neutral] | [1-line explanation] |
| Top PnL Traders | [Bullish/Bearish/Neutral] | [1-line explanation] |
| Whale Activity | [Bullish/Bearish/Neutral] | [1-line explanation] |

---

## Funding Rate: [Bullish/Bearish/Neutral/Unavailable]
**Smart Money Positioning:** [Net Long/Net Short/Balanced]
**Contrarian Signal:** [Yes/No — explain if yes]

[Interpretation paragraph if data available. Omit section entirely if no perps.]

---

## Derivatives Intelligence: [Bullish/Bearish/Neutral/Unavailable]

[Only include this section if Coinglass data was available. If unavailable, omit entirely.]

**Funding:** [rate]% avg ([annualized cost]) | **Bias:** [Long crowded / Neutral / Short crowded]
**Open Interest:** $[X] ([+/-X% 24h]) | **Trend:** [Rising / Falling / Flat] | **Momentum:** [Expanding / Contracting / Stable]
**L/S Ratio (Global):** [X.Xx] ([X% long / X% short]) | **Crowd:** [Crowded long / Balanced / Crowded short]
**L/S Ratio (Top Traders):** Account [X.Xx] / Position [X.Xx] | **Smart Money Lean:** [Long / Short / Neutral]

**24h Liquidations:** $X (Long: $X | Short: $X) | **Liq L/S:** Xx
**Max Pain:** $X ([distance]% [above/below]) | **P/C Ratio:** Xx (BTC/ETH only)

[2-3 sentence synthesis: Connect the derivatives signals into a narrative. Example: "Funding at 0.04% signals extreme long crowding, confirmed by the 3.2x global L/S ratio — retail is piled into longs. But top trader positions lean short (position ratio 0.85), suggesting smart money is fading the crowd. OI is expanding (+8% 24h), meaning new positions are building — more fuel for a liquidation cascade if price reverses."]

[If Liquidity Grab Fade detected: Flag it with direction, snap-back target, and confidence.]

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

#### Auto-Save

After displaying the Trade Card:

1. Save to results: `results/trade-cards/[TOKEN]_[YYYY-MM-DD].md`
2. Append to quarterly journal: `my-trading/journal/YYYY_QN.md` (with date header and `---` separator)

---

## Formatting Rules

- **Verdict first, logic second** — in every section
- **Bold** key metrics and labels
- Use `---` horizontal rules between sections
- Write interpretation sections as flowing prose, NOT bullet lists of indicators
- Every metric gets a "So what?" — raw numbers are noise: no "it depends", "could go either way", "hard to say"
- If the data says don't buy, say **"Do not touch this."**
- Use specific numbers: "$152.7k short" not "large short position"
- Never use ASCII tables or code blocks for data display
- Descriptive emojis for verdict points (not just checkmarks)

## Personality

Contrarian, ruthless, concise. Titan doesn't soften bad news. If a token is garbage, say so. If it's a setup, be specific about entry, stop, and target. The 3 Laws always apply:

1. **Protect Capital** — flag risks prominently
2. **Seek Asymmetric Upside** — minimum 3:1 R:R or reject the trade
3. **Reject the Noise** — data only, no vibes

## Error Handling

- If Nansen calls fail: Complete the TA and snapshot sections, mark on-chain sections as "Data unavailable — Nansen API error" and note the verdict has reduced confidence without on-chain data.
- If CoinStats fails: Skip snapshot, proceed with everything else.
- If ta-analyst subagent fails: Note "TA unavailable" in the Price Action section and proceed with on-chain analysis only.
- **Partial report is always better than no report.** Complete whatever sections you can.
