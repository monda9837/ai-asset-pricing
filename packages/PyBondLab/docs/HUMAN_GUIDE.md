# PyBondLab User Guide

A progressive tutorial for constructing corporate bond factor portfolios with PyBondLab. Every code example uses `generate_synthetic_data()` and runs out of the box.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Single Sorts](#2-single-sorts)
3. [Double Sorts](#3-double-sorts)
4. [Strategy Objects](#4-strategy-objects)
5. [Rebalancing](#5-rebalancing)
6. [Data Filtering](#6-data-filtering)
7. [Batch Processing](#7-batch-processing)
8. [Data Uncertainty Analysis](#8-data-uncertainty-analysis)
9. [Anomaly Assaying](#9-anomaly-assaying)
10. [Panel Extraction & Naming](#10-panel-extraction--naming)
11. [Additional Tools](#11-additional-tools)
12. [Column Mapping](#12-column-mapping)
13. [Performance Guide](#13-performance-guide)
14. [Troubleshooting](#14-troubleshooting)

Appendices:
- [A: Parameter Reference](#appendix-a-parameter-reference)
- [B: Data Format Specification](#appendix-b-data-format-specification)

---

## 1. Getting Started

### Installation

```bash
cd packages/PyBondLab
uv pip install -e ".[performance]"   # or: pip install -e ".[performance]"
```

### Minimal Example

```python
import PyBondLab as pbl
from PyBondLab.pbl_test import generate_synthetic_data

# Generate test data (60 months, 500 bonds)
data = generate_synthetic_data(n_dates=60, n_bonds=500, seed=42)

# Sort bonds into quintiles by signal1
strategy = pbl.SingleSort(holding_period=1, sort_var='signal1', num_portfolios=5)
sf = pbl.StrategyFormation(data, strategy=strategy, verbose=False)
result = sf.fit()

# Get long-short factor returns
ew_ls, vw_ls = result.get_long_short()
print(f"EW long-short mean: {ew_ls.mean():.6f}")
print(f"VW long-short mean: {vw_ls.mean():.6f}")
```

### Data Requirements

Your DataFrame must have these columns (names are configurable):

| Column | Default Name | Type | Required? |
|--------|-------------|------|-----------|
| Date | `date` | datetime64 | Yes |
| Bond ID | `ID` | object/str | Yes |
| Return | `ret` | float | Yes |
| Value Weight | `VW` | float | Yes (for VW portfolios) |
| Rating | `RATING_NUM` | int | Only for rating filters |
| Price | `PRICE` | float | Only for price filters |
| Signals | user-defined | float | At least one |

The test data generator creates all required columns:

```python
data = generate_synthetic_data(n_dates=60, n_bonds=500, seed=42)
print(data.columns.tolist())
# ['date', 'ID', 'ret', 'RATING_NUM', 'VW', 'PRICE', 'signal1', 'signal2',
#  'char1', 'char2', 'char3']
```

---

## 2. Single Sorts

### Basic Quintile Sort

```python
strategy = pbl.SingleSort(
    holding_period=1,       # Monthly rebalancing
    sort_var='signal1',     # Column to sort on
    num_portfolios=5,       # Quintiles
)
sf = pbl.StrategyFormation(data, strategy=strategy, verbose=False)
result = sf.fit()
```

### Accessing Returns

```python
# Long-short factor (P5 - P1)
ew_ls, vw_ls = result.get_long_short()

# All portfolio returns (EW and VW)
ew_ptf, vw_ptf = result.get_ptf()

# Long leg only (top quintile)
ew_long, vw_long = result.get_long_leg()

# Short leg only (bottom quintile)
ew_short, vw_short = result.get_short_leg()

# Bond counts per portfolio
counts = result.get_bond_count()
```

### Turnover

```python
sf = pbl.StrategyFormation(data, strategy=strategy, turnover=True, verbose=False)
result = sf.fit()

# Portfolio-level turnover (DataFrame: T x 5)
ew_turn, vw_turn = result.get_turnover()
print(f"Average P1 turnover: {ew_turn.iloc[:,0].mean():.2f}")
```

### Characteristics

Track portfolio-level averages of bond characteristics:

```python
sf = pbl.StrategyFormation(
    data, strategy=strategy,
    chars=['char1', 'char2'],   # Columns to aggregate
    verbose=False,
)
result = sf.fit()

ew_chars, vw_chars = result.get_characteristics()
# ew_chars is a dict: {'char1': DataFrame(T, 5), 'char2': DataFrame(T, 5)}
print(f"P5 avg char1: {ew_chars['char1'].iloc[:, -1].mean():.4f}")
```

### Banding

Banding reduces turnover by preventing small rank changes from triggering portfolio reassignment:

```python
sf = pbl.StrategyFormation(
    data, strategy=strategy,
    turnover=True,
    banding_threshold=0.2,    # Float between 0 and 1
    verbose=False,
)
result = sf.fit()

ew_turn, _ = result.get_turnover()
# Turnover is lower with banding
```

### Summary Statistics

```python
result.summary()
# Prints: mean, t-stat, std, Sharpe, min, max for each portfolio and L-S
```

---

## 3. Double Sorts

### Unconditional Double Sort

Independently sort on two variables:

```python
strategy = pbl.DoubleSort(
    holding_period=1,
    sort_var='signal1',         # Primary sort variable
    num_portfolios=5,           # 5 portfolios on primary
    sort_var2='signal2',        # Second sort variable
    num_portfolios2=3,          # 3 groups on second variable
    how='unconditional',        # Independent sorts
)
sf = pbl.StrategyFormation(data, strategy=strategy, turnover=True, verbose=False)
result = sf.fit()

ew_ls, vw_ls = result.get_long_short()
```

### Conditional Double Sort

Sort on second variable within groups of the first:

```python
strategy = pbl.DoubleSort(
    holding_period=1,
    sort_var='signal1',
    num_portfolios=5,
    sort_var2='signal2',
    num_portfolios2=3,
    how='conditional',          # Sort signal1 WITHIN signal2 groups
)
```

---

## 4. Strategy Objects

### Momentum

Cumulative past returns over a lookback window:

```python
mom = pbl.Momentum(
    holding_period=1,
    lookback_period=3,    # 3-month lookback
    skip=1,               # Skip most recent month
    num_portfolios=5,
)
sf = pbl.StrategyFormation(data, strategy=mom, verbose=False)
result = sf.fit()

ew_ls, _ = result.get_long_short()
# Signal = cumulative return from t-3 to t-1
```

### Long-Term Reversal

Average past returns over a longer window:

```python
ltr = pbl.LTreversal(
    holding_period=1,
    lookback_period=12,   # 12-month lookback
    skip=1,               # Skip most recent month
    num_portfolios=5,
)
sf = pbl.StrategyFormation(data, strategy=ltr, verbose=False)
result = sf.fit()
```

### WithinFirmSort

Sort bonds within each firm to isolate within-firm dispersion:

```python
import numpy as np

# Data needs a firm identifier (e.g., PERMNO)
np.random.seed(42)
unique_ids = data['ID'].unique()
firm_map = {bid: f'FIRM_{i % 50}' for i, bid in enumerate(unique_ids)}
data['PERMNO'] = data['ID'].map(firm_map)

strategy = pbl.WithinFirmSort(
    holding_period=1,         # HP=1 only (HP>1 not supported)
    sort_var='signal1',
    firm_id_col='PERMNO',     # Column identifying the firm
)
sf = pbl.StrategyFormation(data, strategy=strategy, verbose=False)
result = sf.fit()

ew_ls, vw_ls = result.get_long_short()
# Only 2 portfolios: HIGH and LOW (within-firm relative positioning)
```

---

## 5. Rebalancing

### Monthly (Default, Staggered)

With `holding_period=1`, portfolios rebalance every month. With `holding_period > 1`, multiple overlapping cohorts are averaged (staggered rebalancing):

```python
# HP=3: Three overlapping cohorts
strategy = pbl.SingleSort(holding_period=3, sort_var='signal1', num_portfolios=5)
sf = pbl.StrategyFormation(data, strategy=strategy, verbose=False)
result = sf.fit()

# Returns are averaged across 3 cohorts at each date:
#   Cohort 0: formed this month
#   Cohort 1: formed last month
#   Cohort 2: formed 2 months ago
```

### Non-Staggered (Quarterly / Annual)

Portfolios formed at fixed intervals, held until next rebalancing:

```python
# Quarterly rebalancing in March, June, September, December
strategy = pbl.SingleSort(
    holding_period=1,
    sort_var='signal1',
    num_portfolios=5,
    rebalance_frequency='quarterly',   # 'quarterly', 'semi-annual', 'annual'
    rebalance_month=3,                 # Rebalance in March, June, Sep, Dec
)
sf = pbl.StrategyFormation(data, strategy=strategy, verbose=False)
result = sf.fit()

ew_ls, _ = result.get_long_short()
# Returns computed EVERY month; ranks fixed between rebalancing dates
```

### dynamic_weights

Controls which date's value weights are used for VW portfolio returns:

```python
from PyBondLab.config import StrategyFormationConfig, FormationConfig, DataConfig

# dynamic_weights=True: Use VW from t (day before return date)
# dynamic_weights=False: Use VW from formation date
config = StrategyFormationConfig(
    data=DataConfig(),
    formation=FormationConfig(dynamic_weights=True),
)
sf = pbl.StrategyFormation(data, strategy=strategy, config=config, verbose=False)
```

For `holding_period=1`, both settings are equivalent. For `holding_period > 1`, `True` uses more recent weights while `False` uses weights from when the cohort was formed.

---

## 6. Data Filtering

Filters adjust returns to handle data quality issues. They create a separate `ret_{adj}` column; the original `ret` is never modified.

### Filter Types

| Filter | What It Does | Example |
|--------|-------------|---------|
| `trim` | Set extreme returns to NaN | `{'adj': 'trim', 'level': 0.2}` |
| `price` | Exclude bonds by price level | `{'adj': 'price', 'level': 50}` |
| `bounce` | Exclude return reversals | `{'adj': 'bounce', 'level': 0.05}` |
| `wins` | Clip extreme returns to percentile thresholds | `{'adj': 'wins', 'level': 99, 'loc': 'both'}` |

### Applying Filters

```python
strategy = pbl.SingleSort(holding_period=1, sort_var='signal1', num_portfolios=5)

# Trim: exclude returns > 20%
sf = pbl.StrategyFormation(
    data, strategy=strategy,
    filters={'adj': 'trim', 'level': 0.2},
    verbose=False,
)
result = sf.fit()
```

### Ex-Ante vs Ex-Post

When filters are applied, two sets of results are available:

- **Ex-Ante (EA)**: Uses original `ret` for portfolio returns. The "what would you have earned" answer.
- **Ex-Post (EP)**: Uses filtered `ret_{adj}` for portfolio returns. The "filtered" answer.

Both use the **same ranking** -- only the return column differs.

```python
ew_ea, vw_ea = result.get_long_short()           # Ex-Ante (raw returns)
ew_ep, vw_ep = result.get_long_short_ex_post()    # Ex-Post (filtered returns)

# EA != EP when filters are applied
print(f"EA mean: {ew_ea.mean():.6f}")
print(f"EP mean: {ew_ep.mean():.6f}")
```

### Winsorization

Winsorization clips extreme returns to historical percentile thresholds (ex-ante, no look-ahead):

```python
sf = pbl.StrategyFormation(
    data, strategy=strategy,
    filters={'adj': 'wins', 'level': 99, 'loc': 'both'},
    verbose=False,
)
result = sf.fit()

# EA: original returns, EP: clipped returns
ew_ea, _ = result.get_long_short()
ew_ep, _ = result.get_long_short_ex_post()
```

The `loc` parameter controls which tails are clipped: `'both'`, `'left'`, or `'right'`.

---

## 7. Batch Processing

### BatchStrategyFormation

Process multiple signals at once:

```python
batch = pbl.BatchStrategyFormation(
    data=data,
    signals=['signal1', 'signal2'],   # Column names
    holding_period=1,
    num_portfolios=5,
    turnover=False,                    # Enables fast numba path
    verbose=False,
)
results = batch.fit()

# Access results by signal name
ew_ls, vw_ls = results['signal1'].get_long_short()
ew_ls2, _ = results['signal2'].get_long_short()
```

### Parallel Processing

```python
batch = pbl.BatchStrategyFormation(
    data=data,
    signals=['signal1', 'signal2'],
    holding_period=1,
    num_portfolios=5,
    turnover=True,          # Requires slow path (uses multiprocessing)
    n_jobs=4,               # Number of parallel workers
    verbose=True,
)
results = batch.fit()
```

### Fast Path

When `turnover=False`, `chars=None`, `banding=None`, and `rating=None`, an ultra-fast numba path processes all signals in vectorized parallel. This is **automatically detected** -- no configuration needed.

### BatchWithinFirmSortFormation

```python
batch = pbl.BatchWithinFirmSortFormation(
    data=data,
    signals=['signal1', 'signal2'],
    firm_id_col='PERMNO',
    turnover=False,
    verbose=False,
)
results = batch.fit()
```

---

## 8. Data Uncertainty Analysis

Test factor robustness across multiple filter configurations and holding periods:

```python
results = pbl.DataUncertaintyAnalysis(
    data=data,
    signals=['signal1'],
    holding_periods=[1, 3],
    filters={
        'trim': [0.2, 0.5],           # Trim at 20% and 50%
        'bounce': [0.05],             # Bounce > 5%
        'wins': [(99, 'both')],       # Winsorize at 99th percentile
    },
    num_portfolios=5,
    include_baseline=True,             # Always include no-filter baseline
    verbose=False,
).fit()
```

### Accessing Results

```python
# Factor panels: DataFrame with dates as index, config columns
ew_ea = results.ew_ex_ante
vw_ea = results.vw_ex_ante
ew_ep = results.ew_ex_post
vw_ep = results.vw_ex_post

# Summary with Newey-West t-statistics
summary = results.summary()
print(summary[['signal', 'hp', 'filter_type', 'ew_ea_mean', 'ew_ea_tstat']])
```

### Rating as a Dimension

Run the analysis across multiple rating categories:

```python
results = pbl.DataUncertaintyAnalysis(
    data=data,
    signals=['signal1'],
    holding_periods=[1],
    ratings=['IG', 'NIG', None],      # IG, high-yield, and all bonds
    verbose=False,
).fit()

# Filter results by rating
ig_results = results.filter(rating='IG')
```

### Filtering Results

```python
# By holding period
hp1 = results.filter(hp=1)

# By filter type
trim_only = results.filter(filter_type='trim')

# By signal
sig1 = results.filter(signal='signal1')
```

---

## 9. Anomaly Assaying

Test a signal across a grid of specifications (portfolios, holding periods, rating subsets):

```python
result = pbl.AssayAnomaly(
    data=data,
    strategy=pbl.SingleSort(holding_period=1, sort_var='signal1', num_portfolios=5),
    nport_list=[3, 5, 10],           # Test with terciles, quintiles, deciles
    hp_list=[1, 3],                   # Test HP=1 and HP=3
    rating_list=['IG', 'NIG', None],  # By rating category
    verbose=False,
)

# result is an AnomalyResults object
summary = result.to_dataframe()
print(summary.head())
```

### Batch Anomaly Assaying

Process multiple signals with the same specification grid:

```python
batch = pbl.BatchAssayAnomaly(
    data=data,
    signals=['signal1', 'signal2'],
    specs={'nport_list': [3, 5], 'hp_list': [1]},
    n_jobs=2,
    verbose=False,
)
results = batch.fit()
```

---

## 10. Panel Extraction & Naming

### NamingConfig

Control how factor names appear in output:

```python
cfg = pbl.NamingConfig(
    lowercase=True,              # 'signal1' not 'SIGNAL1'
    sign_correct=False,          # Don't flip negative factors
    weighting_prefix=False,      # No 'ew_'/'vw_' prefix
)

result = sf.fit()
ew_ls, vw_ls = result.get_long_short(naming=cfg)
print(ew_ls.name)  # 'signal1'

# With sign correction: negative factors get flipped and '*' suffix
cfg2 = pbl.NamingConfig(sign_correct=True, weighting_prefix=True)
ew_ls, vw_ls = result.get_long_short(naming=cfg2)
# If EW mean < 0: ew_ls.name = 'ew_signal1*' (flipped)
# If VW mean > 0: vw_ls.name = 'vw_signal1' (not flipped)
```

### Factor-Level Turnover

```python
# Average of long and short leg turnover
ew_ft, vw_ft = result.get_turnover(level='factor', naming=cfg)
print(f"{ew_ft.name}: {ew_ft.mean():.4f}")
# 'signal1_turnover: 1.6898'
```

### extract_panel

Extract all batch results into a single tidy DataFrame:

```python
batch = pbl.BatchStrategyFormation(
    data=data, signals=['signal1', 'signal2'],
    holding_period=1, num_portfolios=5,
    turnover=True, verbose=False,
)
results = batch.fit()

panel = pbl.extract_panel(results)
# Shape: (720, 8)
# Columns: date, factor, freq, leg, weighting, return, turnover, count
#
# leg: 'ls' (long-short), 'l' (long), 's' (short)
# weighting: 'ew' or 'vw'
```

With sign correction:

```python
panel = pbl.extract_panel(results, naming=pbl.NamingConfig(sign_correct=True))
# Negative factors are flipped, 'l' and 's' legs are swapped
```

---

## 11. Additional Tools

### validate_panel

Check your data for PyBondLab compatibility:

```python
report = pbl.validate_panel(data)
# Prints: "Panel validation: OK (24,939 rows, no duplicates)"
```

### PreAnalysisStats

Compute summary statistics for signals before running strategies:

```python
pas = pbl.PreAnalysisStats(data=data, signals=['signal1', 'signal2'], verbose=False)
result = pas.compute()
```

### RollingBeta

Estimate rolling betas against one or more factors:

```python
rb = pbl.RollingBeta(
    data=data,
    ret_col='ret',
    factor_cols=['signal1'],    # Factor(s) to regress on
    window=36,                  # 36-month rolling window
    min_obs=12,                 # Minimum observations
    id_col='ID',
    date_col='date',
)
betas = rb.fit()
```

### Saving and Loading Results

```python
# Save
result.save('my_results.pkl')

# Load
loaded = pbl.StrategyFormation.load('my_results.pkl')
ew_ls, vw_ls = loaded.get_long_short()
```

---

## 12. Column Mapping

If your data uses different column names than PyBondLab expects, you have two options.

### Option A: fit() Parameters

```python
sf = pbl.StrategyFormation(data, strategy=strategy, verbose=False)
result = sf.fit(
    IDvar='cusip',
    RETvar='ret_vw',
    VWvar='mcap_e',
    RATINGvar='spc_rat',
)
```

### Option B: columns= Dict

Preferred for batch classes:

```python
batch = pbl.BatchStrategyFormation(
    data=data,
    columns={'cusip': 'ID', 'ret_vw': 'ret', 'mcap_e': 'VW', 'spc_rat': 'RATING_NUM'},
    signals=['cs', 'mom3_1'],
    holding_period=1,
    num_portfolios=5,
)
```

### Corner Cases

These are handled automatically:

- **`chars` with mapped columns**: `chars=['spc_rat']` + `RATINGvar='spc_rat'` works -- output uses original name
- **Column already named correctly**: If target column exists and source doesn't, mapping is silently skipped
- **Both source and target exist**: Source takes precedence (target is dropped before renaming)

---

## 13. Performance Guide

### When Does the Fast Path Activate?

PyBondLab automatically selects the fastest available code path:

| Conditions | Path | Speedup |
|------------|------|---------|
| SingleSort, turnover=False, chars=None, no banding, no filters | Ultra-fast numba | 5-100x |
| Non-staggered rebalancing (quarterly/annual) | Non-staggered fast | 20-180x |
| WithinFirmSort, turnover=False, chars=None | WithinFirm fast | 33x |
| BatchStrategyFormation with all fast conditions | Vectorized batch | 20-340x |
| Any feature requiring turnover/chars/banding | Slow (pandas) path | 1x (baseline) |

The slow path produces **numerically identical** results -- it's just slower.

### Timing Reference

| Operation | ~500 bonds, 60 dates | ~10K bonds, 300 dates |
|-----------|---------------------|----------------------|
| SingleSort HP=1, no turnover | 0.2s | ~1s |
| SingleSort HP=1, turnover | 0.6s | ~3s |
| Batch 10 signals, no turnover | 0.5s | ~3s |
| DataUncertaintyAnalysis 20 configs | 0.4s | ~5s |

### Memory Tips for Large Data

```python
batch = pbl.BatchStrategyFormation(
    data=data,
    signals=my_100_signals,
    n_jobs=4,
    signals_per_worker=2,    # Process 2 signals per worker (reduces overhead)
    chunk_size=20,           # Process 20 signals at a time (limits memory)
)
```

---

## 14. Troubleshooting

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Signal columns not found` | Signal name not in DataFrame | Check `data.columns` |
| `EP results not available` | Called `get_long_short_ex_post()` without filters | Add `filters=` parameter |
| `Unknown parameter` | Wrong parameter name | Check valid params in error message |
| `banding_threshold must be between 0 and 1` | Used int instead of float | Use e.g. `0.2`, not `1` |
| `WithinFirmSort only supports holding_period=1` | HP>1 not supported | Use `holding_period=1` |
| `Empty results` | No bonds pass filter criteria | Relax filter thresholds |

### Fast Path Not Activating

Check that **all** conditions are met:
1. `turnover=False`
2. `chars=None` (or not specified)
3. `banding_threshold=None` (or not specified)
4. Strategy is `SingleSort` (not DoubleSort or WithinFirmSort)
5. Monthly rebalancing (not quarterly/annual)
6. No filters applied

Set `verbose=True` to see which path is being used.

### Result Has Fewer Dates Than Expected

- For `holding_period=3`, the first 2 dates may have incomplete cohort coverage
- For non-staggered rebalancing, returns start from the month after the first rebalancing date
- Check `len(ew_ls)` to see actual date count

---

## Appendix A: Parameter Reference

### SingleSort

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `holding_period` | int | required | Number of months to hold (1=monthly) |
| `sort_var` | str | required | Column name to sort on |
| `num_portfolios` | int | 5 | Number of portfolio bins |
| `rebalance_frequency` | str | `'monthly'` | `'monthly'`, `'quarterly'`, `'semi-annual'`, `'annual'` |
| `rebalance_month` | int | 6 | Month of year for non-monthly rebalancing |

### DoubleSort

All SingleSort parameters plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_var2` | str | required | Second sort variable |
| `num_portfolios2` | int | required | Portfolios on second variable |
| `how` | str | `'unconditional'` | `'unconditional'` or `'conditional'` |

### Momentum / LTreversal

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `holding_period` | int | required | Holding period |
| `lookback_period` | int | required | Lookback window (months) |
| `skip` | int | 1 | Months to skip (avoids short-term reversal) |
| `num_portfolios` | int | 5 | Number of portfolio bins |

### WithinFirmSort

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `holding_period` | int | 1 | Must be 1 (HP>1 not supported) |
| `sort_var` | str | required | Column name to sort on |
| `firm_id_col` | str | `'PERMNO'` | Column identifying the firm |
| `rating_bins` | list | `[-inf, 7, 10, inf]` | Rating tercile boundaries |
| `min_bonds_per_firm` | int | 2 | Min bonds per firm-date group |

### StrategyFormation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | DataFrame | required | Bond panel data |
| `strategy` | Strategy | required | Strategy object |
| `turnover` | bool | False | Compute portfolio turnover |
| `chars` | list[str] | None | Characteristics to aggregate |
| `banding_threshold` | float | None | Banding threshold (0-1) |
| `filters` | dict | None | Filter config |
| `rating` | str/tuple | None | `'IG'`, `'NIG'`, or `(min, max)` |
| `subset_filter` | dict | None | `{'col': (min, max)}` |
| `dynamic_weights` | bool | False | VW from d-1 (True) or formation (False) |
| `verbose` | bool | True | Print progress |

### BatchStrategyFormation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | DataFrame | required | Bond panel data |
| `signals` | list[str] | required | Column names to process |
| `holding_period` | int | 1 | Holding period |
| `num_portfolios` | int | 5 | Number of portfolio bins |
| `turnover` | bool | False | Compute turnover |
| `chars` | list[str] | None | Characteristics to aggregate |
| `rating` | str/tuple | None | Rating filter |
| `n_jobs` | int | 1 | Parallel workers |
| `columns` | dict | None | Column name mapping |
| `verbose` | bool | True | Print progress |

### DataUncertaintyAnalysis

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | DataFrame | required | Bond panel data |
| `signals` | list[str] | None | Pre-computed signal columns |
| `strategy` | Strategy | None | Strategy object (alternative to signals) |
| `holding_periods` | list[int] | [1,3,6] | Holding periods to test |
| `num_portfolios` | int | 5 | Portfolio bins |
| `filters` | dict | None | Filter configurations |
| `rating` | str/tuple | None | Single rating filter |
| `ratings` | list | None | Multiple ratings as dimension |
| `columns` | dict | None | Column name mapping |
| `verbose` | bool | True | Print progress |

---

## Appendix B: Data Format Specification

### Required Format

```
date       | ID      | ret      | VW         | RATING_NUM | signal
2020-01-31 | BOND001 | 0.0123   | 1000000.0  | 5          | 0.45
2020-01-31 | BOND002 | -0.0056  | 500000.0   | 12         | -0.12
2020-02-28 | BOND001 | 0.0089   | 1050000.0  | 5          | 0.52
...
```

### Key Constraints

- **One row per (date, ID)** -- no duplicates
- **Sorted by date** -- not strictly required but recommended
- **Monthly frequency** -- dates should be month-end
- **NaN handling** -- NaN returns are preserved (not included in portfolio returns)
- **Rating scale** -- 1 (AAA) to 22 (D); IG = 1-10, HY = 11-22

### Real Data Column Mapping

For the Dickerson TRACE corporate bond dataset:

```python
columns = {
    'cusip': 'ID',
    'ret_vw': 'ret',
    'mcap_e': 'VW',
    'spc_rat': 'RATING_NUM',
}
```

See `.claude/skills/bond-data/SKILL.md` for the full 141-column schema reference.
