---
description: PyBondLab output indexing convention — returns at t+1, not formation date t
paths:
  - "packages/PyBondLab/**/*.py"
  - "projects/**/code/**/*.py"
  - "projects/**/scripts/**/*.py"
---

# Output Timing Convention

All PyBondLab outputs are indexed by **return realization date** (t+1), not formation date (t). At any date in the output, portfolio formation happened one month earlier.

## Timing Table

At any row `datelist[i]`:

| Output | What's stored | Economic event at |
|--------|---------------|-------------------|
| Returns | Return earned during month i | Portfolio formed at datelist[i-1] |
| Turnover | Rebalancing cost | Trading at datelist[i-1] |
| Characteristics | Portfolio-level chars | Measured at datelist[i-1] |
| Weights | Bond-level weights & ranks | Decided at datelist[i-1] |

All four have NaN at `datelist[0]` (no prior formation).

## Concrete Example

```
Formation: 2024-01-31  (signal measured, bonds ranked, portfolios formed)
Output at 2024-02-29:
  returns[2024-02-29]  = return earned during Feb
  turnover[2024-02-29] = rebalancing cost from Jan 31 formation
  chars[2024-02-29]    = portfolio characteristics at Jan 31
```

This enables direct computation: `net_return[t] = return[t] - k * turnover[t]` (no date shifting).

## Common Mistakes

| Mistake | Reality |
|---------|---------|
| "Turnover at date t happened at date t" | Turnover at t was incurred at t-1 (formation) |
| "Chars at date t are measured at date t" | Chars at t were measured at t-1 |
| "First row has data" | First row is always NaN |
