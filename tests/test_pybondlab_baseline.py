"""Regression coverage for the bundled PyBondLab baseline artifacts."""

import PyBondLab as pbl

from PyBondLab.pbl_test import (
    generate_synthetic_data,
    load_baseline_results,
    validate_against_baseline,
)


def test_pybondlab_matches_baseline():
    """Current package behavior should match the bundled source-of-truth baseline."""
    data = generate_synthetic_data()
    baseline_results = load_baseline_results()
    assert validate_against_baseline(data, baseline_results, verbose=False)


def test_pybondlab_core_imports_and_bundled_data_are_live():
    """Core imports should be callable and packaged breakpoint data should load."""
    assert pbl.StrategyFormation is not None
    assert pbl.BatchStrategyFormation is not None

    breakpoints = pbl.load_breakpoints_WRDS()
    assert not breakpoints.empty
