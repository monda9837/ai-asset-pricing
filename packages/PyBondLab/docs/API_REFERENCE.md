# PyBondLab API Reference

All publicly exported classes and functions. Signatures extracted from source code via `inspect.signature()`.

---

## Strategy Classes

### SingleSort

1-dimensional portfolio sorting by a single signal.

```python
SingleSort(
    sort_var: str,                                    # Column name of sorting signal
    holding_period: Optional[int] = None,             # Months to hold (1=monthly, 3=quarterly cohorts)
    num_portfolios: Optional[int] = None,             # Number of bins (e.g., 5=quintiles)
    breakpoints: Optional[List[float]] = None,        # Custom breakpoints (overrides num_portfolios)
    lookback_period: Optional[int] = None,            # For derived signals (not used for SingleSort)
    skip: Optional[int] = None,                       # Months to skip between signal and formation
    rebalance_frequency: Union[str, int] = 'monthly', # 'monthly'|'quarterly'|'semi-annual'|'annual'|int
    rebalance_month: Union[int, List[int]] = 6,       # Month(s) for non-monthly rebalancing
    breakpoint_universe_func: Optional[Union[str, Callable]] = None,  # Custom breakpoint function
    verbose: bool = False,
)
```

### DoubleSort

2-dimensional portfolio sorting by two signals (unconditional or conditional).

```python
DoubleSort(
    holding_period: int,                              # Months to hold
    sort_var: str,                                    # Primary sorting signal
    sort_var2: str,                                   # Secondary sorting signal
    num_portfolios: Optional[int] = None,             # Bins for primary signal
    num_portfolios2: Optional[int] = None,            # Bins for secondary signal
    breakpoints: Optional[List[float]] = None,        # Custom breakpoints for primary
    breakpoints2: Optional[List[float]] = None,       # Custom breakpoints for secondary
    how: str = 'unconditional',                       # 'unconditional' or 'conditional'
    lookback_period: Optional[int] = None,
    skip: Optional[int] = None,
    rebalance_frequency: Union[str, int] = 'monthly',
    rebalance_month: Union[int, List[int]] = 6,
    breakpoint_universe_func: Optional[Union[str, Callable]] = None,
    breakpoint_universe_func2: Optional[Union[str, Callable]] = None,
    auto_match_signals: bool = False,                 # Auto-match signal column names
    verbose: bool = False,
)
```

### Momentum

Momentum factor: cumulative log returns over lookback window, skipping recent months.

```python
Momentum(
    lookback_period: Optional[int] = None,  # Months of past returns to cumulate
    skip: int = 1,                          # Months to skip (avoids short-term reversal)
    no_gap: bool = False,                   # Don't require contiguous returns
    fill_na: bool = False,                  # Forward-fill missing returns
    drop_na: bool = False,                  # Drop NaN signals
    enforce_contiguous: bool = False,       # Require full lookback window
    holding_period: Optional[int] = None,
    num_portfolios: Optional[int] = None,
    rebalance_frequency: Union[str, int] = 'monthly',
    rebalance_month: Union[int, List[int]] = 6,
    verbose: bool = False,
    # Legacy aliases:
    K: Optional[int] = None,               # Alias for holding_period
    nport: Optional[int] = None,           # Alias for num_portfolios
    J: Optional[int] = None,               # Alias for lookback_period
)
```

### LTreversal

Long-term reversal factor: mean of log returns over lookback window.

```python
LTreversal(
    lookback_period: Optional[int] = None,  # Months of past returns to average
    skip: Optional[int] = None,             # Months to skip
    no_gap: bool = False,
    fill_na: bool = False,
    drop_na: bool = False,
    enforce_contiguous: bool = False,
    holding_period: Optional[int] = None,
    num_portfolios: Optional[int] = None,
    rebalance_frequency: Union[str, int] = 'monthly',
    rebalance_month: Union[int, List[int]] = 6,
    verbose: bool = False,
)
```

### WithinFirmSort

Sort bonds within each firm (isolates within-firm dispersion from cross-firm differences).

```python
WithinFirmSort(
    sort_var: str,                              # Column name of sorting signal
    holding_period: int = 1,                    # MUST be 1 (HP>1 disabled)
    firm_id_col: str = 'PERMNO',                # Column identifying the firm
    min_bonds_per_firm: int = 2,                # Minimum bonds per firm-date-rating group
    rating_bins: Optional[List[float]] = None,  # Rating tercile edges (default: [-inf, 7, 10, inf])
    num_portfolios: int = 2,                    # Always 2 (HIGH/LOW)
    skip: Optional[int] = None,
    rebalance_frequency: Union[str, int] = 'monthly',
    rebalance_month: Union[int, List[int]] = 6,
    verbose: bool = False,
)
```

---

## Portfolio Formation

### StrategyFormation

Main entry point for portfolio formation. Combines data + strategy -> results.

```python
StrategyFormation(
    data: pd.DataFrame,                                      # Bond panel data
    strategy: Strategy,                                       # Strategy object (SingleSort, DoubleSort, etc.)
    config: Optional[StrategyFormationConfig] = None,         # Full config (overrides kwargs)
    # kwargs (used if config is None):
    turnover: bool = False,                # Compute portfolio turnover
    chars: Optional[List[str]] = None,     # Characteristics to track at portfolio level
    banding_threshold: Optional[int] = None,  # Banding threshold (int: 1 or 2)
    rating: Optional[Union[str, tuple]] = None,  # 'IG', 'NIG', or (min, max) tuple
    subset_filter: Optional[Dict[str, Tuple]] = None,  # {'col': (min, max)}
    dynamic_weights: bool = True,          # VW from d-1 (True) or formation date (False)
    verbose: bool = True,
)
```

**`.fit()` method:**

```python
StrategyFormation.fit(
    IDvar: Optional[str] = None,       # Column name for bond ID (renames to 'ID')
    DATEvar: Optional[str] = None,     # Column name for date (renames to 'date')
    RETvar: Optional[str] = None,      # Column name for return (renames to 'ret')
    RATINGvar: Optional[str] = None,   # Column name for rating (renames to 'RATING_NUM')
    VWvar: Optional[str] = None,       # Column name for value weight (renames to 'VW')
    PRICEvar: Optional[str] = None,    # Column name for price (renames to 'PRICE')
) -> FormationResults
```

### load_breakpoints_WRDS

```python
load_breakpoints_WRDS() -> pd.DataFrame
```

Load historical breakpoints (rolling percentiles) from WRDS data files.

---

## Result Objects

### FormationResults

Main output from `StrategyFormation.fit()`. Contains EA (ex-ante) and optionally EP (ex-post) results.

| Method | Signature | Returns | Notes |
|--------|-----------|---------|-------|
| `get_long_short()` | `(strategy='ea', naming=None)` | `(ew_series, vw_series)` | Long-short factor returns |
| `get_long_short_ex_post()` | `(naming=None)` | `(ew_series, vw_series)` | Only when filters applied |
| `get_long_leg()` | `(strategy='ea', naming=None)` | `(ew_series, vw_series)` | Long portfolio returns |
| `get_short_leg()` | `(strategy='ea', naming=None)` | `(ew_series, vw_series)` | Short portfolio returns |
| `get_turnover()` | `(strategy='ea', level='portfolio', naming=None)` | `(ew_df, vw_df)` or `(ew_series, vw_series)` | `level='factor'` returns (L+S)/2 |
| `get_characteristics()` | `(strategy='ea', naming=None)` | `(ew_dict, vw_dict)` | Dict: char_name -> DataFrame |
| `get_bond_count()` | `(strategy='ea')` | `(ew_df, vw_df)` | Bonds per portfolio |
| `get_ptf()` | `(strategy='ea', weight_type='ew')` | `pd.DataFrame` | Individual portfolio returns |
| `get_ptf_ex_post()` | `(weight_type='ew')` | `pd.DataFrame` | EP portfolio returns |
| `get_returns()` | `(strategy='ea')` | `PortfolioReturns` | Raw returns object |
| `get_ptf_bins()` | `(strategy='ea')` | `dict` | Portfolio breakpoints |
| `get_ptf_counts()` | `(strategy='ea')` | `dict` | Bond counts per portfolio |
| `get_ptf_turnover()` | `(strategy='ea')` | `dict` | Portfolio-level turnover |
| `summary()` | `(periods_per_year=12)` | `dict` | Summary statistics |
| `save()` | `(filepath: str)` | `None` | Save to pickle |
| `load()` | `(filepath: str)` classmethod | `FormationResults` | Load from pickle |

**Properties:** `has_ep`, `has_bond_counts`, `ea`, `ep`, `port_idx`

### DataUncertaintyResults

Output from `DataUncertaintyAnalysis.fit()`. Contains factor returns across all filter configurations.

| Method/Property | Signature | Returns |
|-----------------|-----------|---------|
| `ew_ea` | property | `pd.DataFrame` -- EW ex-ante long-short factors (dates x configs) |
| `vw_ea` | property | `pd.DataFrame` -- VW ex-ante |
| `ew_ep` | property | `pd.DataFrame` -- EW ex-post |
| `vw_ep` | property | `pd.DataFrame` -- VW ex-post |
| `configs` | property | `pd.DataFrame` -- metadata for all configurations |
| `summary()` | `(aggregate_by=None)` | `pd.DataFrame` -- means, NW t-stats, Sharpe ratios |
| `filter()` | `(signal=None, hp=None, filter_type=None, location=None, rating=None)` | `DataUncertaintyResults` -- filtered subset |
| `to_excel()` | `(path: str)` | `None` |

### BatchResults

Output from `BatchStrategyFormation.fit()`. Dict-like container: signal_name -> FormationResults.

| Method | Returns |
|--------|---------|
| `results['signal_name']` | `FormationResults` for that signal |
| `results.keys()` | Signal names |
| `results.values()` | FormationResults objects |
| `results.items()` | (name, result) pairs |
| `results.to_panel()` | `pd.DataFrame` -- panel format |
| `results.save(filepath)` | Save to pickle |
| `BatchResults.load(filepath)` | Load from pickle |

---

## Batch Processing

### BatchStrategyFormation

Process multiple signals in parallel using multiprocessing or numba fast path.

```python
BatchStrategyFormation(
    data: pd.DataFrame,                                 # Bond panel data
    signals: List[str],                                  # Signal column names
    holding_period: int = 1,                             # Months to hold
    num_portfolios: int = 5,                             # Number of bins
    turnover: bool = True,                               # Compute turnover
    chars: Optional[List[str]] = None,                   # Characteristics to track
    rating: Optional[Union[str, tuple]] = None,          # 'IG', 'NIG', or (min, max)
    subset_filter: Optional[Dict[str, Tuple]] = None,    # {'col': (min, max)}
    banding: Optional[int] = None,                       # Banding threshold (1 or 2)
    dynamic_weights: bool = True,                        # VW from d-1
    rebalance_frequency: Union[str, int] = 'monthly',
    rebalance_month: Union[int, List[int]] = 6,
    columns: Optional[Dict[str, str]] = None,            # Column name mapping
    n_jobs: int = 1,                                     # Parallel workers
    signals_per_worker: int = 1,                         # Signal batching
    chunk_size: Optional[Union[int, str]] = None,        # Memory control
    verbose: bool = True,
)
```

**Fast path**: Automatically used when `turnover=False`, `chars=None`, `banding=None`. Processes all signals via numba.

**`.fit()` returns**: `BatchResults`

### BatchWithinFirmSortFormation

Batch processing for WithinFirmSort with multiple signals.

```python
BatchWithinFirmSortFormation(
    data: pd.DataFrame,
    signals: List[str],
    firm_id_col: str = 'PERMNO',
    rating_bins: Optional[List[float]] = None,
    min_bonds_per_firm: int = 2,
    turnover: bool = False,
    chars: Optional[List[str]] = None,
    rating: Optional[Union[str, Tuple[int, int]]] = None,
    subset_filter: Optional[Dict[str, Tuple]] = None,
    columns: Optional[Dict[str, str]] = None,
    n_jobs: int = 1,
    signals_per_worker: int = 1,
    chunk_size: Optional[Union[int, str]] = None,
    verbose: bool = True,
)
```

**`.fit()` returns**: `BatchResults` (dict-like, signal_name -> FormationResults)

### batch_single_sort

Convenience function wrapping `BatchStrategyFormation`.

```python
batch_single_sort(
    data: pd.DataFrame,
    signals: List[str],
    holding_period: int = 1,
    num_portfolios: int = 5,
    turnover: bool = True,
    n_jobs: int = -1,         # -1 = all CPUs
    **kwargs,
) -> BatchResults
```

---

## Data Uncertainty Analysis

### DataUncertaintyAnalysis

Test robustness of factor returns across multiple filter configurations, holding periods, and ratings.

```python
DataUncertaintyAnalysis(
    data: pd.DataFrame,
    signals: Optional[List[str]] = None,                    # Pre-computed signal columns (fast path)
    strategy: Optional[Strategy] = None,                    # OR strategy object (Momentum, LTreversal)
    holding_periods: Optional[List[int]] = None,            # e.g., [1, 3, 6]
    num_portfolios: int = 5,
    dynamic_weights: bool = True,
    filters: Optional[Dict[str, List]] = None,              # See filter format below
    include_baseline: bool = True,                          # Always include no-filter baseline
    rating: Optional[Union[str, Tuple[int, int]]] = None,   # Single rating filter
    ratings: Optional[List] = None,                          # Rating as dimension: ['IG', 'NIG', None]
    subset_filter: Optional[Dict[str, Tuple]] = None,
    rebalance_frequency: Union[str, int] = 'monthly',
    rebalance_month: Union[int, List[int]] = 6,
    n_jobs: int = 1,
    verbose: bool = True,
    use_fast_path: bool = True,                              # Set False to force slow path
)
```

**Filter format:**
```python
filters = {
    'trim': [0.2, 0.5, -0.3, [-0.3, 0.3]],             # positive=right, negative=left, list=both
    'price': [[1, 2, 5], [125, 150, 200]],               # [[left_levels], [right_levels]]
    'bounce': [0.05, -0.05, [-0.05, 0.05]],
    'wins': [(99, 'both'), (95, 'left'), (99, 'right')], # (percentile, location)
}
```

**`.fit()` returns**: `DataUncertaintyResults`

---

## Anomaly Assaying

### AssayAnomaly

Build and run anomaly assay grid across holding periods, portfolio counts, and ratings.

```python
AssayAnomaly(
    data: pd.DataFrame,
    sort_var: str,                                    # Signal column name
    IDvar: Optional[str] = None,                      # Bond ID column
    DATEvar: Optional[str] = None,
    RETvar: Union[str, List[str], None] = None,       # Return column(s)
    PRICEvar: Optional[str] = None,
    RATINGvar: Optional[str] = None,
    Wvar: Optional[str] = None,                       # Value weight column
    subset_filter: Optional[Dict[str, Tuple]] = None,
    holding_periods: Optional[List[int]] = None,      # e.g., [1, 3, 6, 12]
    nport: Optional[List[int]] = None,                # e.g., [5, 10]
    ratings: Optional[List] = None,                   # e.g., ['IG', 'NIG', None]
    dynamic_weights: bool = True,
    turnover: bool = True,
    save_idx: bool = True,
    breakpoint_universe_func: Optional[Callable] = None,
    verbose: bool = True,
) -> AnomalyResults
```

### assay_anomaly_fast

Numba-optimized anomaly assaying. Much faster for large specification grids.

```python
assay_anomaly_fast(
    data: pd.DataFrame,
    signal: str,                       # Signal column name
    specs: Dict[str, Any],             # Specification grid
    holding_period: int = 1,
    dynamic_weights: bool = True,
    validate: bool = False,            # Cross-validate against slow path
    validate_sample_size: int = 3,
    skip_invalid: bool = True,
    verbose: bool = True,
    IDvar: str = None,
    DATEvar: str = None,
    RETvar: str = None,
    VWvar: str = None,
    RATINGvar: str = None,
) -> AnomalyAssayResult
```

### BatchAssayAnomaly

Batch anomaly assaying for multiple signals.

```python
BatchAssayAnomaly(
    data: pd.DataFrame,
    sort_vars: List[str],              # Signal column names
    **kwargs,                          # Same kwargs as AssayAnomaly
)
```

**`.fit()` returns**: `BatchAssayResults`

### batch_assay_anomaly

Convenience function for batch anomaly assaying.

```python
batch_assay_anomaly(
    data: pd.DataFrame,
    sort_vars: List[str],
    **kwargs,
) -> Dict[str, AnomalyResults]
```

---

## Configuration

### StrategyFormationConfig

```python
@dataclass
class StrategyFormationConfig:
    data: DataConfig = DataConfig()
    formation: FormationConfig = FormationConfig()
    filters: FilterConfig = FilterConfig()
```

### NamingConfig

Controls factor naming conventions for output.

```python
@dataclass
class NamingConfig:
    lowercase: bool = True              # 'cs' not 'CS'
    sign_correct: bool = False          # Flip negative factors, add '*' suffix
    use_signal_name: bool = True        # Use signal column name as base
    weighting_prefix: bool = False      # Add 'ew_'/'vw_' prefix
    include_rating_suffix: bool = True  # Add '_ig'/'_hy' suffix
    include_wf_suffix: bool = True      # Add '_wf' for WithinFirmSort
    doublesort_sep: str = '_'           # Separator for DoubleSort names
```

---

## Utilities

### extract_panel

Extract unified panel DataFrame from batch results.

```python
extract_panel(
    results: Union[BatchResults, BatchWithinFirmResults],
    naming: Optional[NamingConfig] = None,
) -> pd.DataFrame
```

Returns DataFrame with columns: `date`, `factor`, `freq`, `leg`, `weighting`, `return`, `turnover`, `{chars...}`.

### validate_panel

Validate panel data structure and handle duplicates.

```python
validate_panel(
    data: pd.DataFrame,
    id_col: str = 'ID',
    date_col: str = 'date',
    handle_duplicates: Literal['error', 'warn', 'drop'] = 'warn',
    keep: Literal['first', 'last'] = 'first',
    verbose: bool = True,
    IDvar: Optional[str] = None,
    DATEvar: Optional[str] = None,
) -> pd.DataFrame
```

### check_duplicates

Check for duplicate (date, ID) rows.

```python
check_duplicates(
    data: pd.DataFrame,
    id_col: str = 'ID',
    date_col: str = 'date',
    IDvar: Optional[str] = None,
    DATEvar: Optional[str] = None,
) -> Tuple[bool, int]   # (has_duplicates, count)
```

---

## Specification Validation

### validate_specs

```python
validate_specs(specs: Dict[str, Any], spec_type: str = 'formation') -> bool
```

### generate_spec_list

```python
generate_spec_list(
    sort_vars: List[str],
    holding_periods: List[int],
    num_portfolios: List[int],
    **kwargs,
) -> List[Dict[str, Any]]
```

### get_valid_spec_list

```python
get_valid_spec_list(spec_type: str = 'formation') -> List[Dict[str, Any]]
```

### filter_spec_list

```python
filter_spec_list(
    specs: List[Dict[str, Any]],
    filter_dict: Dict[str, Any],
) -> List[Dict[str, Any]]
```

### SpecificationValidator

```python
SpecificationValidator(strict: bool = False, verbose: bool = True)
```

---

## Summary Statistics

### PreAnalysisStats

Pre-analysis summary statistics for bond panel data.

```python
PreAnalysisStats(
    data: pd.DataFrame,
    groupby: Optional[Union[str, List[str]]] = None,
    verbose: bool = True,
)
```

### RollingBeta

Rolling window beta estimation for bonds.

```python
RollingBeta(
    data: pd.DataFrame,
    factor_returns: pd.Series,
    window: int = 60,
    min_periods: Optional[int] = None,
)
```

---

## Data Requirements

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `date` | datetime | Yes | End-of-month date |
| `ID` | str/int | Yes | Unique bond identifier |
| `ret` | float | Yes | Monthly return (decimal, not %) |
| `VW` | float | Yes | Market value weight (positive) |
| `RATING_NUM` | int | Yes | Numeric rating (1-22; 1-10=IG, 11-22=NIG) |
| `PRICE` | float | No | Bond price (only for price filters) |
| `PERMNO` | int/float | No | Firm identifier (only for WithinFirmSort) |
| Signal columns | float | Yes | One or more signal columns for sorting |
| Char columns | float | No | Characteristics for portfolio-level tracking |

**Column mapping**: If your data uses different names, use `fit(IDvar='cusip', RETvar='ret_vw', ...)` or `columns={'ID': 'cusip', 'ret': 'ret_vw', ...}`.
