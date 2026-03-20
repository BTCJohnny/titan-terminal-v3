# Stage: 01_outcomes — Pull Closed Trades + Match to Archives

## Purpose

Gather all closed trades since the last review and match each one to its original pipeline run archive. Produces a side-by-side: "what the system predicted vs what actually happened."

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Reference | `_config/thesis.md` | 3 (factory) |

## Process

### Step 1: Pull Closed Trades

```bash
python3 src/trading/analytics.py recent-trades
python3 src/trading/analytics.py summary
```

For each closed trade, extract: token, direction, entry, exit, PnL %, R multiple, setup type, date opened, date closed.

### Step 2: Match to Run Archives

For each closed trade, find the corresponding pipeline run in `runs/`:
- Check `runs/find-setups/[DATE]/` for the session that produced the setup
- Check `runs/token-analysis/[TOKEN]_[DATE]_*/` for the analysis that backed the trade

If no archive exists (trade was entered manually or from v2), note "No pipeline archive — entered outside v3 pipeline."

### Step 3: Build Outcome Table

For each trade, create a comparison:

| Field | System Said | What Happened |
|-------|------------|---------------|
| Direction | Long/Short | Correct/Wrong |
| Entry | $X | Filled at $X |
| Stop | $X | Hit? Y/N |
| T1 | $X | Reached? Y/N |
| T2 | $X | Reached? Y/N |
| T3 | $X | Reached? Y/N |
| Verdict confidence | X% | Outcome: Win/Loss |
| Key signal | [strongest signal from verdict] | Confirmed/Failed |

### Step 4: Aggregate Stats

```bash
python3 src/trading/analytics.py by-strategy
python3 src/trading/analytics.py by-direction
```

Summary: win rate, average R, profit factor, best/worst strategy, LONG vs SHORT performance.

## Scripts Used

- `python3 src/trading/analytics.py recent-trades`
- `python3 src/trading/analytics.py summary`
- `python3 src/trading/analytics.py by-strategy`
- `python3 src/trading/analytics.py by-direction`

## Outputs

| File | Contents |
|------|----------|
| `output/outcomes.md` | Per-trade outcome table, matched to run archives where available, aggregate performance stats |

## Review Gate

- Are all recent closed trades captured?
- Are the run archive matches correct?
- Any trades missing outcome data?
