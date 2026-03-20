# Exchange Flows

## Purpose
Measure tokens leaving exchanges (outflows) as a supply squeeze signal. When significant supply moves off exchanges during a consolidation phase, it reduces available sell-side liquidity and sets up a breakout.

## Tool

```
Tool: mcp__nansen__token_recent_flows_summary
Parameters:
  tokenAddress: "[contract-address]"
  chain: "[chain]"
  lookbackPeriod: "7d"              # Use "7d" for 4-week trend, run multiple times if needed
```

For longer lookback windows, use the granular flow tool:
```
Tool: mcp__nansen__token_flows
Parameters:
  tokenAddress: "[contract-address]"
  chain: "[chain]"
  holder_segment: "exchange"
  dateRange: { from: "30D_AGO", to: "NOW" }
```

## What to Measure

### ⚠️ CRITICAL: Always Check Balance Trend (Not Just Snapshot)

**Lesson learned from SKY (March 2026):** A single-day flow snapshot can be completely misleading. SKY was eliminated as "Distribution" on March 3 based on a 1d/7d snapshot that captured a single noisy inflow day (Feb 25: +54.1M tokens to exchanges). But the 14-day exchange balance was structurally declining — 12 of 14 days had net outflows. Three days later, 229M tokens left exchanges in 48 hours and price ripped +17%.

**Mandatory step:** After checking the flow summary, ALWAYS run the balance trend check:

```
Tool: mcp__nansen__token_flows
Parameters:
  tokenAddress: "[contract-address]"
  chain: "[chain]"
  holder_segment: "exchange"
  dateRange: { from: "14D_AGO", to: "NOW" }
```

**What to look for:**
- Count days with net outflows vs net inflows over 14 days
- If outflow days > inflow days (e.g., 10 of 14), the TREND is accumulation — even if one spike day inflated the average inflow
- Watch for exchange BALANCE declining period-over-period (the absolute level, not just daily flows)
- A single large inflow day surrounded by steady outflow days = noise, not distribution

### Net Exchange Flow

```
Net Flow = Outflows - Inflows

Negative net flow (outflows > inflows) = BULLISH — supply leaving exchanges
Positive net flow (inflows > outflows) = BEARISH — supply entering exchanges
```

### Supply Impact

Calculate outflows as a percentage of circulating supply:

| Outflow % of Supply | Score | Interpretation |
|---------------------|-------|---------------|
| > 3% in 4 weeks | 2 pts | **Strong supply squeeze** — significant removal |
| > 1% in 4 weeks | 1 pt | Moderate outflow — accumulation visible |
| < 1% in 4 weeks | 0 pts | Normal flow — no signal |

### Flow Stability

Consistent outflows over multiple weeks are a stronger signal than a single large withdrawal:
- **4 weeks of steady outflows** → high conviction (supply consistently being absorbed)
- **One large outflow event** → could be a single whale moving to cold storage (lower signal)
- **Outflows then inflows** → mixed signal (accumulation window may be closing)

## Interpretation

### ZRO Case Study
- **-4.1M ZRO** left exchanges over the study period
- This was **5.2% of circulating supply** — a significant squeeze
- Score: 2/2 (>3% supply)
- Combined with insider buy + price at low = breakout followed in 18 days

### SKY Case Study (March 2026 — Missed Opportunity)
- **What we saw (Mar 3):** 1d snapshot showed +$3.2M exchange inflows (2.6x avg). Called it "Distribution."
- **What was actually happening:** Feb 22–24 had steady outflows. Feb 25 had a single-day spike of +54.1M tokens inflow — noise. Feb 26–Mar 3 returned to steady outflows.
- **What happened next (Mar 4-5):** 229M tokens left exchanges in 48 hours. Price moved from $0.070 to $0.077.
- **The fix:** The 14-day balance trend check would have shown outflow days dominated (10+ of 14 days). The single noisy day was a one-off, not a structural shift.
- **Lesson:** Never eliminate a candidate on a single-day flow number. Always check the multi-day balance trajectory.

### What Exchange Outflows DON'T Tell You
- **Who** is withdrawing (could be anyone, not necessarily smart money)
- **Why** they're withdrawing (cold storage, staking, DeFi, or just moving between wallets)
- **When** the squeeze becomes actionable (outflows can continue for weeks before price moves)

Exchange flows are a **supporting signal**, not a primary one. Entity tracking tells you who; exchange flows tell you the aggregate supply picture.

## Limitations

- **Native tokens (BTC, ETH, SOL):** Exchange flow tools often don't work for native tokens. Score this signal as N/A.
- **Low-cap tokens:** May have thin exchange data. Flows at 10x average on a $5M token could be one wallet.
- **DEX-only tokens:** No exchange flow data available for tokens not listed on CEXs.

## Output

Report:
- **Net exchange flow (4 weeks):** -$XM / -X tokens
- **% of circulating supply:** X%
- **Flow pattern:** Steady outflows / Single event / Mixed
- **14d balance trend:** Outflow X of 14 days / Balance declining or flat
- **Score:** X/2

**If snapshot shows inflows but balance trend shows outflows:** Flag as "Snapshot misleading — structural trend is [accumulation/outflows]. Do NOT eliminate on snapshot alone."

---

## DB Logging

After querying exchange flows, log the daily data for future trend analysis:
```bash
python3 src/storage/intelligence.py store-exchange-balance \
    --token [TOKEN] --chain [CHAIN] \
    --data '[{"date": "2026-03-20", "balance": 150000000, "inflows": 5000000, "outflows": 8000000, "net_flow": -3000000, "price": 0.1047}]'
```

On future runs, check stored trends first:
```bash
python3 src/storage/intelligence.py exchange-trend [TOKEN] --days 14
```

This builds longitudinal data that resolves the snapshot-vs-trend problem the SKY case study identified. After 2-3 weeks of regular runs, you'll have your OWN exchange balance time series.
