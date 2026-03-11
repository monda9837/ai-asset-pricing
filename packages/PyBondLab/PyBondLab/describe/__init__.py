"""
__init__.py -- Public API for the describe sub-package.

Entry points: PreAnalysisStats, PreAnalysisResult, CorrelationStats, CorrelationResult
Dependencies: .pre_analysis, .results, .correlations
"""

from .pre_analysis import PreAnalysisStats
from .correlations import CorrelationStats
from .results import PreAnalysisResult, CorrelationResult

__all__ = [
    "PreAnalysisStats",
    "PreAnalysisResult",
    "CorrelationStats",
    "CorrelationResult",
]
