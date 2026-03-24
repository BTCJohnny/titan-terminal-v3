---
description: "S/R levels + position sizing for a specific setup"
---

Run the /targets workflow as defined in CONTEXT.md.

Read CONTEXT.md for the full workflow. Read _config/position-sizing.md for risk rules and category limits.

Calculate support/resistance levels from multi-timeframe analysis, suggest entry/stop/targets, and generate position sizing using 2% risk rule. Minimum 3:1 R:R required.

After completing the analysis, save the full output to:

`signals/dashboards/targets_[TOKEN]_YYYYMMDD_HHMM.md`

Use the token name in UPPERCASE and current UTC timestamp (e.g., `targets_ETH_20260324_1530.md`).

$ARGUMENTS
