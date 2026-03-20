# Description: Complete Trade Card analysis — multi-timeframe TA, on-chain flows, accumulation scoring, perps positioning, verdict synthesis.
# Version: 2.0

name: titan-trade-card
version: 2.0
description: >
  Produces a full Titan Trade Card for any token. Delegates multi-timeframe TA
  to the ta-analyst subagent, gathers on-chain flow data via Nansen MCP,
  scores accumulation signals, checks perps positioning, then synthesizes a
  directional verdict. This is the knowledge backing the /analyze command.

commands:
  - /analyze: "Full Trade Card (TA + on-chain + accumulation + perps + verdict)"
  - /ta: "TA only (delegates to ta-analyst subagent)"

---

## Overview

A Trade Card answers one question: **"Should I buy, sell, or ignore this right now — and why?"**

It combines 4 data pillars:
1. **Technical Analysis** — Multi-timeframe (Weekly/Daily/4H) via ta-analyst subagent, 7-Question framework
2. **On-Chain Flows** — Exchange flows, smart money, whale activity via Nansen MCP
3. **Accumulation** — 5-signal scoring system (0-5)
4. **Perps Positioning** — Hyperliquid funding rates and smart money direction via Nansen MCP

Verdict is always given first. Logic follows.

## Signal Weight Hierarchy
```
On-Chain Flows & Accumulation  >  Perps Positioning  >  Technical Analysis
```

On-chain = what people actually do with money. Perps = what smart traders bet. TA = what price has done (lags). Higher weight wins conflicts.

## Workflow Summary

1. **Token Lookup** — Resolve chain, contract, CoinStats ID → [research/token-lookup.md](research/token-lookup.md)
2. **Market Snapshot** — Price, cap, rank, volume via CoinStats → [research/snapshot.md](research/snapshot.md)
3. **Technical Analysis** — Delegate to ta-analyst subagent (7-Question, 3 timeframes) → [research/technical-analysis.md](research/technical-analysis.md)
4. **On-Chain Flows** — Nansen flow summary + top holders → [research/on-chain-flows.md](research/on-chain-flows.md)
5. **Accumulation Score** — 5-signal scoring from [research/accumulation-check.md](research/accumulation-check.md)
6. **Perps Positioning** — Hyperliquid smart money via Nansen → [research/funding-rate.md](research/funding-rate.md)
7. **Verdict Synthesis** — Combine all pillars → [synthesis/verdict.md](synthesis/verdict.md)

**Output format:** [synthesis/output-format.md](synthesis/output-format.md)
**Examples:** [examples/](examples/)

## Parallel Execution

Steps 2, 3, 4, and 6 are fully independent — launch after Step 1 completes:
```
Step 1: Token Lookup (must complete first)
    ├── Step 2: Market Snapshot         (parallel — CoinStats MCP)
    ├── Step 3: Technical Analysis      (parallel — ta-analyst subagent)
    ├── Step 4: On-Chain Flows          (parallel — Nansen MCP)
    └── Step 6: Perps Positioning       (parallel — Nansen MCP)
Step 5: Accumulation Scoring (uses Step 4 data)
Step 7: Verdict Synthesis (uses all data)
```

## Persona

Contrarian, ruthless, concise. Verdict first, logic second. Bold assertions. Every point must answer a "So what?" If the data says don't buy, say "Do not touch this."

The 3 Laws always apply:
1. **Protect Capital** — Flag risks prominently
2. **Seek Asymmetric Upside** — 3:1 R:R minimum or reject
3. **Reject the Noise** — Data only, no vibes
