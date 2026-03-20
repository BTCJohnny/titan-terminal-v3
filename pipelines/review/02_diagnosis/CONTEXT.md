# Stage: 02_diagnosis — Trace Failures to Specific Stages

## Purpose

For each losing trade (or trade that underperformed), trace the failure back through the pipeline to identify which stage produced the error. This is the "semantic debugging" step.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../01_outcomes/output/outcomes.md` | 4 (working) |
| Run archives | `runs/find-setups/[DATE]/` | 4 (working) |
| Run archives | `runs/token-analysis/[TOKEN]_[DATE]_*/` | 4 (working) |
| Reference | `_config/signal-hierarchy.md` | 3 (factory) |
| Reference | `_config/thesis.md` | 3 (factory) |

## Process

For each losing or underperforming trade:

### Step 1: Identify Failure Type

| Failure Type | Description |
|-------------|-------------|
| **Direction wrong** | Went long, should have been short (or vice versa) |
| **Timing wrong** | Direction was right, but entry was too early/late |
| **Stop too tight** | Direction right, eventually hit target, but stopped out first |
| **Stop too loose** | Lost more than expected before stopping |
| **Target too ambitious** | Direction right, missed realistic exit, gave back gains |
| **Signal failure** | The strongest signal in the verdict was wrong |
| **Red flag missed** | A disqualifying condition existed but wasn't caught |
| **Regime mismatch** | Setup was valid in a different regime than what prevailed |

### Step 2: Trace Back Through Pipeline

Open the archived run outputs for the trade and walk backward:

1. Read `05_setup/output/setups.md` (or `05_verdict/output/verdict.md`) — what was the verdict?
2. Read `03_filter/output/candidates.md` — should this token have been filtered out?
3. Read `02_scan/output/` — which scan flagged it? Was the signal real?
4. Read `01_regime/output/regime.md` — was the regime assessment correct?
5. Check `_config/` files referenced by each stage — were the rules adequate?

### Step 3: Assign Root Cause

For each failure, identify:
- **Which stage** produced the error (regime, scan, filter, analysis, or setup)
- **Which specific input or rule** was wrong (a _config/ threshold, a missing red flag, a bad interpretation)
- **Whether this is a one-off or pattern** (check if similar failures occurred in other trades)

### Step 4: Classify Fix Type

| Fix Type | Where to Change |
|----------|----------------|
| Threshold adjustment | `_config/interpreters/` files |
| New red flag | `_config/red-flags.md` |
| Signal weight change | `_config/signal-hierarchy.md` |
| Regime signal update | `_config/thesis.md` |
| Stage process update | Stage CONTEXT.md process section |
| No fix (market risk) | Log but no change — some trades lose even with correct process |

## Outputs

| File | Contents |
|------|----------|
| `output/diagnosis.md` | Per-trade root cause: failure type, stage responsible, specific input/rule that failed, fix type, pattern vs one-off |

## Review Gate

- Do the root causes make sense? Any misattributed?
- Are any "pattern" failures that should definitely be fixed?
- Any failures you'd classify as "correct process, unlucky outcome" (no fix needed)?
