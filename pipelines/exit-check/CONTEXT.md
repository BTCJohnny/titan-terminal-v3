# Pipeline: exit-check

> Quick smart money exit signal. Answers: "Is smart money exiting a token I hold? Should I be worried?" Costs 4 Nansen credits.

## Entry Point

- `/nansen-exit [TOKEN] [CHAIN]`

## Flow

```
01_signals → 02_verdict
```

## Design Note

This is the cheapest on-chain check in the toolkit — 4 Nansen credits total. Use it for routine position monitoring, not just when you're worried.
