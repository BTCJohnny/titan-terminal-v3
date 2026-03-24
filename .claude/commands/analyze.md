---
description: "Deep dive on one token — full TA + on-chain + derivatives + verdict"
---

Run the /analyze workflow as defined in CONTEXT.md for the specified token.

Read CONTEXT.md for the full workflow. Read _config/signal-hierarchy.md for conflict resolution. Read relevant _config/interpreters/ for data interpretation.

Multi-timeframe TA (W/D/4H/1H) + Nansen on-chain + Coinglass derivatives + CEX flows → synthesize a directional verdict using the signal hierarchy. Verdict first, then evidence.

After completing the analysis, save the full output to:

`signals/dashboards/analyze_[TOKEN]_YYYYMMDD_HHMM.md`

Use the token name in UPPERCASE and current UTC timestamp (e.g., `analyze_ETH_20260324_1520.md`).

$ARGUMENTS
