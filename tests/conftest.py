"""Test configuration for deterministic local package imports."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYBONDLAB_SRC = ROOT / "packages" / "PyBondLab"

sys.dont_write_bytecode = True

if str(PYBONDLAB_SRC) not in sys.path:
    sys.path.insert(0, str(PYBONDLAB_SRC))
