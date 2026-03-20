---
name: review
description: Learning loop — trace trade outcomes back to pipeline stages, propose _config improvements.
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
---

# /review

Run the review pipeline. Read `pipelines/review/CONTEXT.md` for the full stage map, then execute stages 01 through 03 in order.

This pipeline improves the factory (_config/ files), not the product. Proposals require human approval before applying.

After completion, archive to `runs/review/[YYYY-MM-DD]/`.
