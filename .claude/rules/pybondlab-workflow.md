---
description: Execution routing for PyBondLab tasks — /run for known workflows, orchestrator for novel ones
paths:
  - "packages/PyBondLab/**/*.py"
  - "projects/**/code/**/*.py"
  - "projects/**/scripts/**/*.py"
---

# PyBondLab Workflow Routing

## Execution Routing

**Known workflows on Dickerson bond data** (batch single sort, batch WFS, single sort):
Use the `/run` skill. No agent spawn needed. Fast, low-token.

**Novel/complex workflows** (new data, DoubleSort, DUA, AssayAnomaly, debugging):
Use the `pybondlab-orchestrator` agent. Keep prompts concise.

## ResultsReporter After Every .fit()

After ANY `.fit()` on StrategyFormation, BatchStrategyFormation, BatchWithinFirmSortFormation, or DataUncertaintyAnalysis:

1. SCRIPT must be captured before execution
2. `ResultsReporter(result, mnemonic, script_text=SCRIPT).generate()` must be called
3. Report path must be shown to the user

No exceptions. Results are ephemeral without saving.

## Always Compute Turnover

Always use `turnover=True` for batch and single runs. Turnover is needed for cumret_turnover plots, turnover_bars, and extract_panel output.

## Summary Table After Every Run

Print an annualized summary table after every run:

```
| Signal | EW Mean | EW t | EW SR | EW Turn | VW Mean | VW t | VW SR | VW Turn |
```

All values annualized (%). Turnover = avg monthly two-way (%), or "—" if not computed.
Follow with 2-3 sentences interpreting key findings.

## Bond Data Reference

When loading Dickerson bond data for PyBondLab, reference the `bond-data` skill for column mapping.
