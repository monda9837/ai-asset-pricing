"""
__init__.py -- Public API for the visualization sub-package.

Entry points: set_latex(), PerformancePlotter
Dependencies: ._latex, .plotting
"""

from ._latex import set_latex
from .plotting import *