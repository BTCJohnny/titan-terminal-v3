# Stage: 03_filter — Red Flag Check + Ranking

## Purpose

Apply automatic rejection criteria, check regime fit, and rank survivors to select 0-3 candidates for deep analysis. This is the quality gate — most tokens get rejected here.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../02_scan/output/ta_hits.md` | 4 (working) |
| Previous stage | `../02_scan/output/deriv_hits.md` | 4 (working) |
| Previous stage | `../02_scan/output/onchain_hits.md` | 4 (working) |
| Previous stage | `../02_scan/output/squeeze_hits.md` | 4 (working) |
| Previous stage | `../01_regime/output/regime.md` | 4 (working) |
| Reference | `_config/red-flags.md` | 3 (factory) |
| Reference | `_config/thesis.md` | 3 (factory) |

## Process

### Step 1: Merge Hits

Combine all 4 scan outputs into a single candidate list. Note which scan(s) each token appeared in — tokens appearing in multiple scans get a cross-signal bonus.

### Step 2: Apply Red Flags

For each candidate, check against `_config/red-flags.md`. Any red flag = automatic rejection. Log the rejection reason.

### Step 3: Check Regime Fit

For each surviving candidate, verify the setup type matches the valid setup types from `regime.md`:
- If regime says "shorts only" and the candidate is a long setup → reject
- If regime says "selective longs" and the candidate lacks exceptional on-chain evidence → reject

### Step 4: Rank Survivors

Score remaining candidates by:
1. **Cross-signal count** — how many sub-scans flagged this token (1-4)
2. **Signal strength** — strongest individual signal rating
3. **Regime alignment** — how well the setup type fits the current regime
4. **Thesis overlap** — does this token already have an active thesis in `_config/thesis.md`? (bonus)

### Step 5: Select Top 0-3

- If 0 candidates survive: output "No setups today" with explanation of what was scanned and why everything was rejected
- If 1-3 survive: rank and pass all to 04_analyze
- If 4+ survive: take top 3 by ranking score

## Outputs

| File | Contents |
|------|----------|
| `output/candidates.md` | 0-3 ranked candidates with: token, setup type, signals found, ranking score, or "No setups today — here's why" |

## Review Gate

Before proceeding to 04_analyze:
- Any candidates you want to override (add/remove)?
- Does "no setups today" feel right given what you see in the market?
- Any tokens you want forced through despite a red flag?
