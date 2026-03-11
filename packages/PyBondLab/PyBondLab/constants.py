# -*- coding: utf-8 -*-
"""
constants.py -- Centralized magic numbers, column names, and enum-like classes.

Entry points: get_rating_bounds(), get_portfolio_labels(),
              get_signal_based_labels(), get_adjusted_return_column()
Internal: RatingBounds, Defaults, RebalanceFrequency, FilterType,
          DoubleSortMethod, ColumnNames, ResultSuffix, NumericConstants,
          ValidationMessages, FilePatterns, Performance
Dependencies: (none -- leaf module)

Naming conventions
------------------
- Class-level constants: UPPER_SNAKE_CASE (e.g., IG_MIN, VALID_TYPES)
- Column name constants mirror the exact DataFrame column strings
  (e.g., ColumnNames.RETURN = 'ret', ColumnNames.ID = 'ID')
- Helper functions use lower_snake_case
"""

from typing import List


# =============================================================================
# Rating Constants
# =============================================================================
# @internal
class RatingBounds:
    """Bond rating numeric boundaries.

    Maps S&P-style letter ratings to integers:
    1 (AAA) through 10 (BBB-) = IG, 11 (BB+) through 22 (D) = NIG/HY.
    """

    # Investment Grade: 1=AAA ... 10=BBB-
    IG_MIN = 1
    IG_MAX = 10

    # Non-Investment Grade (High Yield): 11=BB+ ... 22=D
    NIG_MIN = 11
    NIG_MAX = 22

    # Valid rating categories accepted by DataConfig
    VALID_CATEGORIES = ["IG", "NIG", None]


# =============================================================================
# Default Values
# =============================================================================
# @internal
class Defaults:
    """Default parameter values used when user omits optional arguments.

    Monthly (staggered) rebalancing is the default strategy mode.
    """

    # Rebalancing -- 'monthly' enables staggered cohorts when hp > 1
    REBALANCE_FREQUENCY = 'monthly'
    REBALANCE_MONTH = 6  # June, used only for non-staggered rebalancing

    # Strategy parameters
    SKIP_PERIOD = 1       # Months between signal measurement and portfolio formation
    NUM_PORTFOLIOS = 10   # Decile portfolios by default

    # Price filtering -- bonds below this price are excluded by the price filter
    PRICE_THRESHOLD = 25

    # Minimum columns that must exist in the input DataFrame
    REQUIRED_COLUMNS = ["date", "ID", "ret", "RATING_NUM", "VW"]

    # Display
    VERBOSE = True


# =============================================================================
# Rebalancing Frequencies
# =============================================================================
# @internal
class RebalanceFrequency:
    """Valid rebalancing frequency options."""
    
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    SEMI_ANNUAL = 'semi-annual'
    ANNUAL = 'annual'
    
    VALID_FREQUENCIES = [MONTHLY, QUARTERLY, SEMI_ANNUAL, ANNUAL]
    
    @classmethod
    def is_valid(cls, freq: str) -> bool:
        """Check if frequency is valid."""
        return freq in cls.VALID_FREQUENCIES


# =============================================================================
# Filter Types
# =============================================================================
# @internal
class FilterType:
    """Valid filter/adjustment types for ex-post return adjustments."""
    
    TRIM = 'trim'
    WINS = 'wins'
    PRICE = 'price'
    BOUNCE = 'bounce'
    
    VALID_TYPES = [TRIM, WINS, PRICE, BOUNCE]
    
    @classmethod
    def is_valid(cls, filter_type: str) -> bool:
        """Check if filter type is valid."""
        return filter_type in cls.VALID_TYPES


# =============================================================================
# Double Sort Methods
# =============================================================================
# @internal
class DoubleSortMethod:
    """Valid double sorting methods.

    Conditional: breakpoints computed within each group of the second sort.
    Unconditional: breakpoints computed over the full cross-section.
    """
    
    CONDITIONAL = 'conditional'
    UNCONDITIONAL = 'unconditional'
    
    VALID_METHODS = [CONDITIONAL, UNCONDITIONAL]
    
    @classmethod
    def is_valid(cls, method: str) -> bool:
        """Check if method is valid."""
        return method in cls.VALID_METHODS


# =============================================================================
# Column Names
# =============================================================================
# @internal
class ColumnNames:
    """Standard column names used throughout PyBondLab.

    Values match the exact strings expected in input/output DataFrames.
    Users can remap their own column names via the ``columns`` mapping
    in StrategyFormation or BatchStrategyFormation.
    """

    # Core input columns (must exist or be mapped)
    INDEX = 'index'
    DATE = 'date'
    ID = 'ID'              # Bond identifier (e.g., CUSIP)
    RETURN = 'ret'          # Monthly bond return
    RATING = 'RATING_NUM'  # Numeric credit rating (1=AAA ... 22=D)
    VALUE_WEIGHT = 'VW'    # Market-cap-based value weight
    PRICE = 'PRICE'        # End-of-month price (used by price filter only)

    # Derived columns created during portfolio formation
    PORTFOLIO_RANK = 'ptf_rank'  # Integer portfolio assignment (1..N)
    WEIGHTS = 'weights'
    EQ_WEIGHTS = 'eweights'      # Normalized equal weights (1/n per portfolio)
    VAL_WEIGHTS = 'vweights'     # Normalized value weights (VW_i / sum(VW))
    COUNT = 'count'              # Bond count per portfolio
    SIGNAL = 'signal'            # Generic signal column for fast path
    LOG_RETURN = 'logret'        # log(1+ret), used by Momentum/LTreversal

    # Required core columns (checked during input validation)
    REQUIRED = [DATE, ID, RETURN, RATING, VALUE_WEIGHT]


# =============================================================================
# Result Suffixes
# =============================================================================
# @internal
class ResultSuffix:
    """Suffixes appended to result column names to distinguish output types.

    EA = ex-ante (raw returns), EP = ex-post (filtered returns).
    """

    # Strategy types
    EX_ANTE = '_ea'
    EX_POST = '_ep'

    # Weighting types
    EQUAL_WEIGHT = 'ew'
    VALUE_WEIGHT = 'vw'

    # Components
    LONG = '_long'
    SHORT = '_short'
    LONG_SHORT = 'ls'


# =============================================================================
# Numeric Constants
# =============================================================================
# @internal
class NumericConstants:
    """Numeric constants used in calculations."""
    
    # Portfolio numbering
    MIN_PORTFOLIO_RANK = 1
    
    # Percentiles
    PERCENTILE_MIN = 0
    PERCENTILE_MAX = 100
    
    # Infinity values for thresholds
    NEG_INF = float('-inf')
    POS_INF = float('inf')


# =============================================================================
# Validation Messages
# =============================================================================
# @internal
class ValidationMessages:
    """Standard validation error messages (f-string templates with named placeholders)."""
    
    INVALID_RATING = (
        "Invalid rating: {rating}. "
        "Valid options are None, 'IG', 'NIG', or a 2-tuple (min, max)."
    )
    
    INVALID_BOUNDS = (
        "Invalid bounds for column '{col}': "
        "lower bound ({low}) must be <= upper bound ({high})"
    )
    
    INVALID_FILTER = (
        "Invalid filtering option: {adj}. "
        "Valid options are {valid_options}"
    )
    
    INVALID_REBALANCE_FREQ = (
        "rebalance_frequency must be one of {valid_frequencies} or an integer. "
        "Got '{freq}'"
    )
    
    MISSING_COLUMN = (
        "Column '{col}' not found in data. "
        "Available columns: {available}"
    )
    
    EMPTY_DATA = (
        "No bonds matched between time {time_t} and {time_t1}. "
        "Setting return to nan and going to next period."
    )


# =============================================================================
# File Naming Patterns
# =============================================================================
# @internal
class FilePatterns:
    """Patterns for result file naming and portfolio labels."""
    
    # Portfolio labels
    PORTFOLIO_PREFIX = 'Q'  # Q1, Q2, Q3, etc.
    
    # Long/short labels
    LONG_LABEL = 'LONG_{weight}{strategy}_{name}'
    SHORT_LABEL = 'SHORT_{weight}{strategy}_{name}'
    LS_LABEL = '{weight}{strategy}_{name}'


# =============================================================================
# Performance Constants
# =============================================================================
# @internal
class Performance:
    """Performance-related constants for caching and chunking thresholds."""
    
    # Caching
    MAX_CACHE_SIZE = 128
    
    # Chunking for large operations
    CHUNK_SIZE = 10000
    
    # Minimum rows for pd.eval optimization
    MIN_ROWS_FOR_EVAL = 100000


# =============================================================================
# Helper Functions for Constants
# =============================================================================
# @entrypoint
# @called-by:DataConfig._validate_rating, StrategyFormation._apply_rating_filter
def get_rating_bounds(rating: str) -> tuple:
    """
    Get numeric bounds for a rating category.
    
    Parameters
    ----------
    rating : str
        Rating category ('IG', 'NIG', or None)
    
    Returns
    -------
    tuple
        (min_rating, max_rating)
    
    Examples
    --------
    >>> get_rating_bounds('IG')
    (1, 10)
    >>> get_rating_bounds('NIG')
    (11, 22)
    """
    if rating == "IG":
        return (RatingBounds.IG_MIN, RatingBounds.IG_MAX)
    elif rating == "NIG":
        return (RatingBounds.NIG_MIN, RatingBounds.NIG_MAX)
    elif rating is None:
        # No rating filter -- return (-inf, +inf) so all bonds pass
        return (NumericConstants.NEG_INF, NumericConstants.POS_INF)
    else:
        raise ValueError(ValidationMessages.INVALID_RATING.format(rating=rating))


# @entrypoint
def get_portfolio_labels(num_portfolios: int) -> List[str]:
    """
    Generate portfolio labels (Q1, Q2, ..., Qn).
    
    Parameters
    ----------
    num_portfolios : int
        Number of portfolios
    
    Returns
    -------
    list of str
        Portfolio labels
    
    Examples
    --------
    >>> get_portfolio_labels(5)
    ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
    """
    return [f"{FilePatterns.PORTFOLIO_PREFIX}{i}" 
            for i in range(1, num_portfolios + 1)]


# @entrypoint
def get_signal_based_labels(
    signal_name: str,
    num_portfolios: int,
    signal_name2: str = None,
    num_portfolios2: int = None
) -> List[str]:
    """
    Generate signal-based portfolio labels.
    
    For single sorts: ['SIGNAL1', 'SIGNAL2', ..., 'SIGNALn']
    For double sorts: ['SIG1_1_SIG2_1', 'SIG1_1_SIG2_2', ..., 'SIG1_n_SIG2_m']
    
    Parameters
    ----------
    signal_name : str
        Primary signal variable name (e.g., 'ret_mom')
    num_portfolios : int
        Number of portfolios for primary sort
    signal_name2 : str, optional
        Secondary signal variable name for double sorts
    num_portfolios2 : int, optional
        Number of portfolios for secondary sort
    
    Returns
    -------
    list of str
        Portfolio labels with signal names
    
    Examples
    --------
    >>> get_signal_based_labels('ret_mom', 5)
    ['RET_MOM1', 'RET_MOM2', 'RET_MOM3', 'RET_MOM4', 'RET_MOM5']
    
    >>> get_signal_based_labels('ret_mom', 3, 'size', 5)
    ['RET_MOM1_SIZE1', 'RET_MOM1_SIZE2', ..., 'RET_MOM3_SIZE5']
    """
    # Labels always uppercase to match legacy output conventions
    sig1 = signal_name.upper()
    
    if signal_name2 is not None and num_portfolios2 is not None:
        # Double sort
        sig2 = signal_name2.upper()
        labels = [
            f'{sig1}{i}_{sig2}{j}'
            for i in range(1, num_portfolios + 1)
            for j in range(1, num_portfolios2 + 1)
        ]
    else:
        # Single sort
        labels = [f'{sig1}{i}' for i in range(1, num_portfolios + 1)]
    
    return labels


# @entrypoint
def get_adjusted_return_column(base_column: str, adjustment: str) -> str:
    """
    Get the adjusted return column name.
    
    Parameters
    ----------
    base_column : str
        Base column name (e.g., 'ret')
    adjustment : str
        Adjustment type (e.g., 'trim', 'wins')
    
    Returns
    -------
    str
        Adjusted column name (e.g., 'ret_trim')
    
    Examples
    --------
    >>> get_adjusted_return_column('ret', 'trim')
    'ret_trim'
    """
    return f"{base_column}_{adjustment}"