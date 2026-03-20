# Stage: 03_propose — Propose _config/ Improvements

## Purpose

Convert diagnoses into concrete, implementable changes to `_config/` files and stage contracts. These are proposals — the human reviews and decides whether to apply each one.

## Inputs

| Source | File | Layer |
|--------|------|-------|
| Previous stage | `../02_diagnosis/output/diagnosis.md` | 4 (working) |
| Reference | `_config/red-flags.md` | 3 (factory) |
| Reference | `_config/interpreters/` (all files) | 3 (factory) |
| Reference | `_config/signal-hierarchy.md` | 3 (factory) |
| Reference | `_config/thesis.md` | 3 (factory) |

## Process

### Step 1: Group Diagnoses by Fix Type

From `diagnosis.md`, group all fixes by type:
- Threshold adjustments → `_config/interpreters/`
- New red flags → `_config/red-flags.md`
- Signal weight changes → `_config/signal-hierarchy.md`
- Regime updates → `_config/thesis.md`
- Stage process updates → specific stage CONTEXT.md files

### Step 2: Generate Concrete Diffs

For each proposed change, show:
- **File:** which file to change
- **Current:** the relevant section as it exists now
- **Proposed:** the new text
- **Rationale:** which trade(s) this would have caught, and why
- **Risk:** could this change cause false negatives? (rejecting good setups)

### Step 3: Prioritize

Rank proposals by:
1. **Pattern strength** — how many trades were affected by this failure
2. **Fix confidence** — how certain we are this would help
3. **Blast radius** — does this change affect many stages or just one?

### Step 4: Format Proposals

```
## Proposal [N]: [Short title]

**File:** `_config/[file]`
**Trades affected:** [TOKEN1], [TOKEN2]
**Pattern:** [description of recurring failure]

**Current:**
> [relevant section from current file]

**Proposed:**
> [new text]

**Rationale:** [why this fixes the problem]
**Risk:** [potential downside of this change]
**Priority:** [HIGH / MEDIUM / LOW]
```

## Outputs

| File | Contents |
|------|----------|
| `output/proposals.md` | Ranked list of concrete _config/ and stage contract changes, each with current/proposed/rationale/risk |

## Post-Output Actions

The human reviews each proposal and either:
- **Applies:** edit the file, commit with message referencing the proposal
- **Rejects:** note why (may be useful for future reviews)
- **Defers:** adds to a "revisit later" list

Archive the full review run to `runs/review/[YYYY-MM-DD]/`.

## Review Gate

This IS the review gate — the entire point of this stage is human judgment on each proposal.
- Which proposals to apply immediately?
- Which to test on the next few trades before committing?
- Any proposals that feel like overfitting to a small sample?
