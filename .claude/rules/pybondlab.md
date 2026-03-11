---
description: PyBondLab API constraints, parameter gotchas, column mapping, and fast path conditions
paths:
  - "packages/PyBondLab/**/*.py"
  - "projects/**/code/**/*.py"
  - "projects/**/scripts/**/*.py"
---

# PyBondLab Rules

## Quick Reference

- `banding_threshold` = float (0-1), e.g. `1/5` for quintiles. NOT int.
- Results indexed by return date (t+1), not formation date (t)
- `get_returns()` returns single DataFrame, NOT tuple — use `get_ptf()` for (ew, vw)
- `sort_var` must use POST-mapping names (e.g., `'RATING_NUM'` not `'spc_rat'`)
- Full API reference: `packages/PyBondLab/docs/AI_GUIDE.md`

## Key Constraints

| Constraint | Rule |
|-----------|------|
| `banding_threshold` | Float 0-1 (e.g. `1/nport`). NOT int. |
| `WithinFirmSort` | Only `holding_period=1` (HP>1 raises ValueError) |
| `get_long_short_ex_post()` | Raises exception if no filters applied |
| `DoubleSort` LS | `get_long_short()` extracts LS on `sort_var2` (secondary), averaged across `sort_var` (primary). `sort_var`=control, `sort_var2`=factor. |
| `firm_id_col` | Takes **raw** column name (e.g., `'permno'`). Never put PERMNO in `columns=` dict. |
| `rebalance_frequency` | Goes in **Strategy** constructor (or `BatchStrategyFormation` directly), NOT in `StrategyFormation`. |
| `rebalance_month=7` | PBL timing: month 7 = June formation. NOT `rebalance_month=6`. |

## Filter System

**Universe filters** (pre-formation): `rating='IG'/'NIG'/(min,max)/None`, `subset_filter={'col': (min, max)}`. Excluded bonds get signal→NaN.

**Return adjustment filters** (ex-post): `filters={'adj': 'trim', 'level': 0.2}` in StrategyFormation, or `filters={'trim': [0.2, 0.5]}` in DUA. `get_long_short_ex_post()` only available with filters.

## Column Mapping

Two APIs with **different syntax, same semantics**:

| API | Convention | Example |
|-----|-----------|---------|
| `sf.fit(IDvar=...)` | `PBLvar='user_col'` | `fit(IDvar='cusip')` |
| `Batch(columns=...)` | `{pbl_name: user_name}` | `columns={'ID': 'cusip'}` |

**WRONG**: `columns={'cusip': 'ID'}` (reversed)
**CORRECT**: `columns={'ID': 'cusip', 'ret': 'ret_vw', 'VW': 'mcap_e', 'RATING_NUM': 'spc_rat'}`

**`fit()` only accepts**: IDvar, DATEvar, RETvar, RATINGvar, VWvar, PRICEvar. No PERMNOvar — use `WithinFirmSort(firm_id_col=...)`.

## Parameter Names (WRONG → CORRECT)

| WRONG | CORRECT | Notes |
|-------|---------|-------|
| `banding=1` | `banding_threshold=0.2` | Float 0-1, not int |
| `cond_sort_var='x'` | `sort_var2='x'` | DoubleSort second variable |
| `cond_num_portfolios=3` | `num_portfolios2=3` | DoubleSort second dimension |
| `conditional=True` | `how='conditional'` | DoubleSort method |
| `SingleSort(signal='x')` | `SingleSort(sort_var='x')` | Param is `sort_var` |
| `SingleSort(n_portfolios=5)` | `SingleSort(num_portfolios=5)` | |
| `sf.fit(turnover=True)` | `StrategyFormation(..., turnover=True).fit()` | Config in constructor |
| `sf.fit(PERMNOvar='permno')` | `WithinFirmSort(firm_id_col='permno')` | fit() takes column mapping only |
| `DoubleSort(sort_var2='spc_rat')` | `DoubleSort(sort_var2='RATING_NUM')` | Post-mapping names |
| `BatchWFS(columns={'PERMNO': 'permno'})` | `BatchWFS(firm_id_col='permno')` | Don't put PERMNO in columns= |

## Result Methods (WRONG → CORRECT)

| WRONG | CORRECT | Why |
|-------|---------|-----|
| `ew, vw = result.get_returns()` | `ew, vw = result.get_ptf()` | `get_returns()` = single DataFrame |
| `results.ew_ea` | `results.ew_ex_ante` | DUA uses full name |
| `result.get_long_short(sign_correct=True)` | `result.get_long_short(naming=NamingConfig(sign_correct=True))` | sign_correct is NamingConfig field |

## DoubleSort Variable Ordering

**`get_long_short()` extracts LS on sort_var2, averaged across sort_var groups.**

- **WRONG**: `DoubleSort(sort_var='cs', sort_var2='RATING_NUM')` → extracts rating LS
- **CORRECT**: `DoubleSort(sort_var='RATING_NUM', sort_var2='cs')` → extracts CS LS within rating

Rule: **sort_var = control, sort_var2 = factor** (LS extracted on sort_var2).

## VWvar Column Consumption

`VWvar='me'` renames `me`→`VW` internally. If `me` is also a signal: column disappears.
**Fix**: `data['size'] = data['me'].copy()` before fitting, then `sort_var='size'`.

## NamingConfig & Sign Correction

- `NamingConfig(sign_correct=True)` flips negative factors, appends `*` to name
- EW and VW flipped independently — `'str*'` EW but `'str'` VW is possible
- `extract_panel(results, naming=NamingConfig(sign_correct=True))` for tidy output

## Real Data Gotchas

| Issue | Fix |
|-------|-----|
| Nullable `IntegerArray` in `spc_rat` | `data['spc_rat'] = data['spc_rat'].astype('float64')` |
| DoubleSort date coverage mismatch | `auto_match_signals=True` in DoubleSort() |
| Sort vars must use post-mapping names | `sort_var2='RATING_NUM'` not `'spc_rat'` |
| `get_ptf()` UPPERCASES column names | `c.startswith('SZE1')` not `c.startswith('sze1')` |

## Fast Path Conditions

Ultra-fast numba: ALL must be true: `turnover=False`, `chars=None`, `banding_threshold=None`, SingleSort, monthly rebalancing, no filters.
Otherwise: slow path (pandas with numba kernels). Results identical. `verbose=True` to check.
