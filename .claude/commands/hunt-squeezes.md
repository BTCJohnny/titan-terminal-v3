---
name: hunt-squeezes
description: Scan across tokens for extreme perps positioning imbalances on Hyperliquid. Finds mechanical squeeze setups where smart money is crowded one side 5:1+.
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - mcp__nansen
  - mcp__coinstats
---

# /hunt-squeezes

Scan across tokens for extreme positioning imbalances on Hyperliquid perpetuals. Identifies mechanical squeeze opportunities where forced liquidation cascades create predictable price movements.

## What This Produces

A ranked list of tokens with extreme perps positioning, with full squeeze analysis on the top candidates.

---

## Execution

This command delegates to the **perps-squeeze-detector** skill's `hunt-squeezes` workflow. Load the skill from `.claude/skills/perps-squeeze-detector/SKILL.md` and follow its hunt-squeezes workflow exactly.

### Quick Summary of the Workflow

1. **Candidate Screening** — Pull `mcp__nansen__smart_traders_and_funds_perp_trades` for recent activity. Group by token, count long vs short trades, filter for >70% one-sided activity. See `.claude/skills/perps-squeeze-detector/research/candidate-screening.md` for full screening criteria.

2. **Deep Scan Top 3** — For the top 3 candidates by one-sided percentage and dollar amount, run the full `scan-squeeze` analysis:
   - Positioning scan (long $ vs short $, imbalance ratio)
   - Liquidation map (cascade clusters, forced pressure zones)
   - Macro context (CEX flows, BTC momentum)
   - Squeeze score (0-10)
   - See research/ and synthesis/ sub-files in the skill for detailed methodology

3. **Hunt Report** — Summary table of all candidates screened + detailed analysis of top 3

3. **Derivatives Confirmation** — For each candidate that scores 4+ from the skill, run:
   ```bash
   python3 src/fetchers/coinglass_fetcher.py --token [CANDIDATE] --derivatives --json
   ```
   Add confirmation signals to the squeeze score:
   - Funding rate > 0.03% for the token → +1 (extreme long crowding = short squeeze DOWN fuel)
   - Funding rate < -0.03% → +1 (extreme short crowding = long squeeze UP fuel)
   - OI expanding (>5% 24h) while Nansen shows one-sided positioning → +1 (new positions = more liquidation fuel)
   - Global L/S ratio > 2.5 or < 0.4 → +1 (extreme retail crowd positioning)

   Maximum +3 from derivatives confirmation. These boost conviction but don't generate candidates on their own.

4. **Hunt Report** — Summary table of all candidates screened + detailed analysis of top 3

### Key Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Squeeze Score 8-10 | Alpha — high conviction | Flag for immediate /analyze |
| Squeeze Score 6-7 | Strong — consider entry | Add to watchlist |
| Squeeze Score 4-5 | Moderate | Monitor only |
| Squeeze Score 0-3 | Weak | No setup |
| Imbalance 5:1+ | Extreme positioning | Always run full scan |
| First liquidation <5% from price | Imminent trigger | Highest urgency |
| Coinglass derivatives | +1 per signal (max +3) | Boosts conviction of Nansen-sourced candidates |

### Auto-Save

Save the hunt report to: `results/skill-runs/perps-squeeze-detector/hunt_[YYYY-MM-DD].md`

If any token scores 6+, suggest: "Run `/analyze [TOKEN]` for the full Trade Card before entering."

---

## Error Handling

- If Nansen perp data is unavailable for the broad scan, try scanning watchlist tokens individually as fallback
- If fewer than 3 candidates qualify, analyze whatever qualifies — 1 good candidate beats 3 forced ones
- Note which tokens had data issues so the user knows the scan was partial

## Formatting Rules

- Verdict first — lead with the best candidate and its score
- Quantify everything — dollar amounts, ratios, distances to liquidation
- Use the skill's persona: contrarian, mechanical, no hedging
- Bold all squeeze scores and imbalance ratios
