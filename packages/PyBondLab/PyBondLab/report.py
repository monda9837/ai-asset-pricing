"""
report.py -- Automated results reporting for PyBondLab portfolio formation.

Generates structured output directories with tables, figures, and metadata
after each StrategyFormation or Batch run.

Entry points: ResultsReporter.generate()
Internal: _single_report(), _batch_report(), _plot_*(), _write_*()
Dependencies: matplotlib, numpy, pandas, describe.utils, visualization._latex
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Dict, Any

import matplotlib
matplotlib.use('Agg')  # non-interactive backend for file output
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from PyBondLab.describe.utils import compute_nw_tstat
from PyBondLab.extract import extract_panel
from PyBondLab.naming import NamingConfig
from PyBondLab.visualization._latex import set_latex

# ---------------------------------------------------------------------------
# NBER recession peak-to-trough dates (embedded, no external dependency)
# ---------------------------------------------------------------------------
NBER_RECESSIONS = [
    ("1973-11-01", "1975-03-01"),
    ("1980-01-01", "1980-07-01"),
    ("1981-07-01", "1982-11-01"),
    ("1990-07-01", "1991-03-01"),
    ("2001-03-01", "2001-11-01"),
    ("2007-12-01", "2009-06-01"),
    ("2020-02-01", "2020-04-01"),
]

# Palette
_BLUE = '#3182bd'
_RED = '#de2d26'
_GRAY = '#bdbdbd'
_VW_BLUE = '#6baed6'

# Double-sort group colors (up to 10 levels)
_GROUP_COLORS = [
    '#3182bd', '#e6550d', '#31a354', '#756bb1', '#636363',
    '#843c39', '#7b4173', '#a55194', '#ce6dbd', '#de9ed6',
]


# Map __strategy_name__ values to clean identifiers
_STRATEGY_TYPE_MAP = {
    'Single Sorting': 'SingleSort',
    'Double Sorting': 'DoubleSort',
    'MOMENTUM': 'Momentum',
    'LT-REVERSAL': 'LTreversal',
    'Within-Firm Sort': 'WithinFirmSort',
}


def _normalize_strategy_type(raw: str) -> str:
    """Normalize __strategy_name__ to a clean identifier."""
    return _STRATEGY_TYPE_MAP.get(raw, raw)


# Smart display names for common variables (case-insensitive)
_DEFAULT_LABELS = {
    'rating_num': 'Rating',
    'cs': 'Credit Spread',
    'bbtm': 'Book-to-Market',
    'btm': 'Book-to-Market',
    'tmat': 'Maturity',
    'me': 'Size',
    'mom': 'Momentum',
    'rev': 'Reversal',
    'oas': 'Option-Adj. Spread',
    'duration': 'Duration',
    'ret_vw': 'Return',
    'mcap': 'Market Cap',
    'eff_yld': 'Yield',
    'amt_out': 'Amount Outstanding',
    'age': 'Age',
    'illiq': 'Illiquidity',
}


def _display_name(var: str, labels: Optional[Dict[str, str]] = None) -> str:
    """Convert a variable name to a human-readable display name.

    Lookup order: user labels dict -> built-in defaults -> smart fallback.
    """
    if not var:
        return ''
    # User override (case-insensitive)
    if labels:
        for k, v in labels.items():
            if k.lower() == var.lower():
                return v
    # Built-in defaults (case-insensitive)
    hit = _DEFAULT_LABELS.get(var.lower())
    if hit:
        return hit
    # Smart fallback: strip _NUM suffix, title-case, replace underscores
    import re
    clean = re.sub(r'_NUM$', '', var, flags=re.IGNORECASE)
    clean = clean.replace('_', ' ').strip()
    if clean.isupper() and len(clean) <= 5:
        return clean  # Keep short acronyms like "CS", "OAS"
    return clean.title()


def _nw_stats(series: pd.Series, annualize: bool = True):
    """Compute mean, NW t-stat, SE, and 95% CI for a return series."""
    valid = series.dropna()
    T = len(valid)
    if T < 2:
        return np.nan, np.nan, np.nan, (np.nan, np.nan)
    nw_lag = int(T ** 0.25)
    mean = valid.mean()
    t_stat, _ = compute_nw_tstat(valid, nw_lag=nw_lag)
    se = abs(mean / t_stat) if abs(t_stat) > 1e-12 else np.nan
    scale = 12.0 if annualize else 1.0
    ann_mean = mean * scale
    ann_se = se * scale
    ci = (ann_mean - 1.96 * ann_se, ann_mean + 1.96 * ann_se)
    return ann_mean, t_stat, ann_se, ci


class ResultsReporter:
    """
    Generates structured report folders after PyBondLab runs.

    Parameters
    ----------
    result : FormationResults or BatchResults
        The output from StrategyFormation.fit() or BatchStrategyFormation.fit().
    mnemonic : str
        Short identifier for this run (e.g., 'cs_single_5').
    script_text : str
        The Python code that generated this result (saved as script.py).
    output_dir : str or Path
        Root directory for reports. Default 'results'.
    script_path : str or Path, optional
        Path to a .py file whose contents will be saved as script.py.
        Takes precedence over script_text if both are provided.
    show_recessions : bool, default True
        Whether to add NBER recession shading to cumulative return plots.
    labels : dict, optional
        Custom display names for variables, e.g. ``{'cs': 'Credit Spread'}``.
        Built-in defaults cover common bond/equity variables. User labels
        take precedence.
    custom_factors : dict, optional
        User-constructed factor returns as ``{name: (ew_series, vw_series)}``.
        Example: ``{'SMB': (ew_smb, vw_smb), 'HML': (ew_hml, vw_hml)}``.
        When provided, all factor-level outputs (cumret, factor bars,
        factor_returns.csv, headline stats) use these instead of the
        default ``get_long_short()`` extraction.
    custom_factor_legs : dict, optional
        Portfolio composition for each custom factor:
        ``{name: (long_cols, short_cols)}``.
        Example: ``{'SMB': (['ME1_BTM1', ...], ['ME2_BTM1', ...])}``.
        Required for per-factor turnover computation.
    """

    def __init__(
        self,
        result,
        mnemonic: str,
        script_text: str = "",
        output_dir: Union[str, Path] = "results",
        *,
        script_path: Optional[Union[str, Path]] = None,
        show_recessions: bool = True,
        labels: Optional[Dict[str, str]] = None,
        custom_factors: Optional[Dict[str, tuple]] = None,
        custom_factor_legs: Optional[Dict[str, tuple]] = None,
    ):
        self.result = result
        self.mnemonic = mnemonic
        self.output_dir = Path(output_dir)
        self.show_recessions = show_recessions
        self.labels = labels or {}
        self.custom_factors = custom_factors
        self.custom_factor_legs = custom_factor_legs or {}
        self._is_batch = hasattr(result, 'results') and hasattr(result, 'signals')

        # Resolve script text: script_path takes precedence
        if script_path is not None:
            sp = Path(script_path)
            if sp.is_file():
                self.script_text = sp.read_text(encoding="utf-8")
            else:
                self.script_text = script_text
        else:
            self.script_text = script_text

    def generate(self) -> str:
        """Generate the full report and return the report folder path."""
        set_latex(use_tex=False)
        date_str = datetime.now().strftime("%Y_%m_%d")
        folder = self.output_dir / f"{self.mnemonic}_{date_str}"
        folder.mkdir(parents=True, exist_ok=True)

        # Save script
        (folder / "script.py").write_text(self.script_text, encoding="utf-8")

        if self._is_batch:
            self._batch_report(folder)
        else:
            self._single_report(self.result, folder)

        print(f"Report saved to: {folder}")
        return str(folder)

    # ------------------------------------------------------------------
    # Single-strategy report
    # ------------------------------------------------------------------
    def _single_report(self, result, folder: Path, signal_name: str = ""):
        """Generate tables and figures for a single FormationResults."""
        tables_dir = folder / "tables"
        figs_dir = folder / "figures"
        tables_dir.mkdir(exist_ok=True)
        figs_dir.mkdir(exist_ok=True)

        # Detect strategy type from result
        strategy_type = self._detect_strategy_type(result)
        has_turnover = self._has_turnover(result)
        is_double = strategy_type == "DoubleSort"

        # Build descriptive label for figure titles
        title_label = self._build_title_label(result, signal_name)

        # --- Tables ---
        self._write_summary_table(result, tables_dir, has_turnover, is_double)
        self._write_factor_returns(result, tables_dir)
        self._write_factor_turnover(result, tables_dir, has_turnover)

        # --- Figures ---
        if is_double:
            self._plot_portfolio_premia_double(result, figs_dir, title_label)
        else:
            self._plot_portfolio_premia(result, figs_dir, title_label)

        self._plot_factor_bars(result, figs_dir, title_label)
        self._plot_cumret_turnover(result, figs_dir, has_turnover, title_label)
        self._plot_turnover_bars(result, figs_dir, has_turnover, title_label)

        # --- Meta ---
        self._write_meta(result, folder, signal_name, strategy_type)

    # ------------------------------------------------------------------
    # Batch report
    # ------------------------------------------------------------------
    def _batch_report(self, folder: Path):
        """Generate per-signal reports + summary for BatchResults."""
        batch = self.result
        summary_dir = folder / "summary"
        summary_dir.mkdir(exist_ok=True)

        # Per-signal reports
        for signal, sig_result in batch.results.items():
            sig_folder = folder / signal
            sig_folder.mkdir(exist_ok=True)
            self._single_report(sig_result, sig_folder, signal_name=signal)

        # Summary table
        self._write_batch_summary(batch, summary_dir)

        # Batch factor exports
        self._write_batch_factor_returns(batch, summary_dir)

        # Summary factor comparison chart
        self._plot_factor_comparison(batch, summary_dir)

        # Extract panel with sign correction -> parquet
        self._write_extract_panel(batch, summary_dir)

        # Meta
        self._write_meta(batch, folder, strategy_type="Batch")

    # ------------------------------------------------------------------
    # Summary statistics table
    # ------------------------------------------------------------------
    def _write_summary_table(self, result, tables_dir: Path,
                             has_turnover: bool, is_double: bool):
        """Write summary_stats.csv with portfolio-level statistics."""
        rows = []
        for weight_label, weight_type in [("EW", "ew"), ("VW", "vw")]:
            try:
                ew_df, vw_df = result.get_ptf()
                ptf_df = ew_df if weight_type == "ew" else vw_df
            except Exception:
                continue

            # Turnover data
            turn_df = None
            if has_turnover:
                try:
                    ew_turn, vw_turn = result.get_turnover()
                    turn_df = ew_turn if weight_type == "ew" else vw_turn
                except Exception:
                    pass

            for col in ptf_df.columns:
                series = ptf_df[col]
                ann_mean, t_stat, ann_se, ci = _nw_stats(series)
                valid = series.dropna()
                std_ann = valid.std() * np.sqrt(12) * 100 if len(valid) > 1 else np.nan
                sr = (valid.mean() / valid.std() * np.sqrt(12)) if len(valid) > 1 and valid.std() > 0 else np.nan
                row = {
                    'Weight': weight_label,
                    'Portfolio': col,
                    'Mean(%)': round(ann_mean * 100, 3) if not np.isnan(ann_mean) else np.nan,
                    't-stat(NW)': round(t_stat, 2) if not np.isnan(t_stat) else np.nan,
                    'SR': round(sr, 3) if not np.isnan(sr) else np.nan,
                    'Std(%)': round(std_ann, 3) if not np.isnan(std_ann) else np.nan,
                }
                if has_turnover and turn_df is not None and col in turn_df.columns:
                    row['Turnover(%)'] = round(turn_df[col].mean() * 100, 3)
                elif has_turnover:
                    row['Turnover(%)'] = np.nan
                row['N'] = int(series.notna().sum())
                rows.append(row)

            # Long-short row
            try:
                ew_ls, vw_ls = result.get_long_short()
                ls_series = ew_ls if weight_type == "ew" else vw_ls
                ann_mean, t_stat, ann_se, ci = _nw_stats(ls_series)
                valid = ls_series.dropna()
                std_ann = valid.std() * np.sqrt(12) * 100 if len(valid) > 1 else np.nan
                sr = (valid.mean() / valid.std() * np.sqrt(12)) if len(valid) > 1 and valid.std() > 0 else np.nan
                row = {
                    'Weight': weight_label,
                    'Portfolio': 'LS',
                    'Mean(%)': round(ann_mean * 100, 3) if not np.isnan(ann_mean) else np.nan,
                    't-stat(NW)': round(t_stat, 2) if not np.isnan(t_stat) else np.nan,
                    'SR': round(sr, 3) if not np.isnan(sr) else np.nan,
                    'Std(%)': round(std_ann, 3) if not np.isnan(std_ann) else np.nan,
                }
                if has_turnover:
                    # Factor-level turnover: average of long + short leg
                    try:
                        ew_ft, vw_ft = result.get_turnover(level='factor')
                        ft_series = ew_ft if weight_type == "ew" else vw_ft
                        row['Turnover(%)'] = round(ft_series.mean() * 100, 3)
                    except Exception:
                        row['Turnover(%)'] = 'N/A'
                row['N'] = int(ls_series.notna().sum())
                rows.append(row)
            except Exception:
                pass

        # Custom factor rows: EW and VW per factor
        if self.custom_factors is not None:
            # Get portfolio-level turnover DataFrames for per-factor computation
            ew_turn_df, vw_turn_df = None, None
            if has_turnover:
                try:
                    ew_turn_df, vw_turn_df = result.get_turnover()
                except Exception:
                    pass

            for factor_name, (ew_series, vw_series) in self.custom_factors.items():
                for weight_label, series in [('EW', ew_series), ('VW', vw_series)]:
                    ann_mean, t_stat, ann_se, ci = _nw_stats(series)
                    valid = series.dropna()
                    std_ann = valid.std() * np.sqrt(12) * 100 if len(valid) > 1 else np.nan
                    sr = (valid.mean() / valid.std() * np.sqrt(12)) if len(valid) > 1 and valid.std() > 0 else np.nan
                    row = {
                        'Weight': weight_label,
                        'Portfolio': factor_name,
                        'Mean(%)': round(ann_mean * 100, 3) if not np.isnan(ann_mean) else np.nan,
                        't-stat(NW)': round(t_stat, 2) if not np.isnan(t_stat) else np.nan,
                        'SR': round(sr, 3) if not np.isnan(sr) else np.nan,
                        'Std(%)': round(std_ann, 3) if not np.isnan(std_ann) else np.nan,
                    }
                    if has_turnover:
                        turn_val = self._compute_factor_turnover(
                            factor_name, weight_label,
                            ew_turn_df, vw_turn_df)
                        row['Turnover(%)'] = round(turn_val, 3) if turn_val is not None else 'N/A'
                    row['N'] = int(valid.notna().sum())
                    rows.append(row)

        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(tables_dir / "summary_stats.csv", index=False)

    # ------------------------------------------------------------------
    # Factor returns CSV (single strategy)
    # ------------------------------------------------------------------
    def _write_factor_returns(self, result, tables_dir: Path):
        """Save long-short factor returns as CSV (decimal, not %)."""
        # Custom factors: interleaved EW/VW columns per factor
        if self.custom_factors is not None:
            cols = {}
            for name, (ew, vw) in self.custom_factors.items():
                cols[f'{name}_ew'] = ew
                cols[f'{name}_vw'] = vw
            df = pd.DataFrame(cols)
            df.index.name = 'date'
            df.to_csv(tables_dir / "factor_returns.csv")
            return
        try:
            ew_ls, vw_ls = result.get_long_short()
        except Exception:
            return
        df = pd.DataFrame({'ew_ls': ew_ls, 'vw_ls': vw_ls})
        df.index.name = 'date'
        df.to_csv(tables_dir / "factor_returns.csv")

    # ------------------------------------------------------------------
    # Factor turnover CSV (single strategy)
    # ------------------------------------------------------------------
    def _write_factor_turnover(self, result, tables_dir: Path, has_turnover: bool):
        """Save factor-level turnover time series as CSV (decimal, not %)."""
        if not has_turnover:
            return
        try:
            ew_turn, vw_turn = result.get_turnover()
        except Exception:
            return
        cols = {}
        # Custom factor turnover from long/short legs
        if self.custom_factors is not None and self.custom_factor_legs:
            for fname in self.custom_factors:
                ew_series = self._compute_factor_turnover_series(fname, ew_turn)
                vw_series = self._compute_factor_turnover_series(fname, vw_turn)
                if ew_series is not None:
                    cols[f'{fname}_ew'] = ew_series
                if vw_series is not None:
                    cols[f'{fname}_vw'] = vw_series
        # Built-in LS factor turnover
        try:
            ew_ft, vw_ft = result.get_turnover(level='factor')
            cols['LS_ew'] = ew_ft
            cols['LS_vw'] = vw_ft
        except Exception:
            pass
        if cols:
            df = pd.DataFrame(cols)
            df.index.name = 'date'
            df.to_csv(tables_dir / "factor_turnover.csv")

    # ------------------------------------------------------------------
    # Portfolio premia bars (SingleSort / WithinFirmSort)
    # ------------------------------------------------------------------
    def _plot_portfolio_premia(self, result, figs_dir: Path, title_label: str = ""):
        """Bar chart of annualized portfolio mean returns with NW CIs."""
        try:
            ew_df, vw_df = result.get_ptf()
        except Exception:
            return

        fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

        for ax, (label, ptf_df) in zip(axes, [("EW", ew_df), ("VW", vw_df)]):
            means, errs = [], []
            cols = list(ptf_df.columns)
            n_ptf = len(cols)
            for col in cols:
                ann_mean, t_stat, ann_se, ci = _nw_stats(ptf_df[col])
                means.append(ann_mean * 100)
                errs.append(1.96 * ann_se * 100 if not np.isnan(ann_se) else 0)

            # Blue gradient: lightest for Q1, darkest for Q_last
            cmap = plt.cm.Blues
            # Map portfolio indices to 0.3-0.8 range (avoid extremes)
            ptf_colors = [cmap(0.3 + 0.5 * i / max(n_ptf - 1, 1)) for i in range(n_ptf)]

            # Add LS bar
            try:
                ew_ls, vw_ls = result.get_long_short()
                ls = ew_ls if label == "EW" else vw_ls
                ann_mean, t_stat, ann_se, ci = _nw_stats(ls)
                means.append(ann_mean * 100)
                errs.append(1.96 * ann_se * 100 if not np.isnan(ann_se) else 0)
                ptf_colors.append(_RED)
                cols.append("LS")
            except Exception:
                pass

            x = np.arange(len(cols))
            ax.bar(x, means, yerr=errs, color=ptf_colors, capsize=3, edgecolor='black',
                   linewidth=0.5, alpha=0.85)
            ax.set_xticks(x)
            ax.set_xticklabels(cols, fontsize=9, rotation=45, ha='right')
            ax.set_title(label, fontsize=12)
            ax.set_ylabel("Annualized Mean (%)" if label == "EW" else "")
            ax.axhline(0, color='black', linewidth=0.5, linestyle='--')

        fig.suptitle(f"Portfolio Premia: {title_label}" if title_label else "Portfolio Premia",
                     fontsize=13, y=1.02)
        fig.tight_layout()
        fig.savefig(figs_dir / "portfolio_premia.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

    # ------------------------------------------------------------------
    # Portfolio premia bars (DoubleSort — grouped)
    # ------------------------------------------------------------------
    def _plot_portfolio_premia_double(self, result, figs_dir: Path, title_label: str = ""):
        """Grouped bar chart for DoubleSort: groups by first-sort, bars by second-sort."""
        try:
            ew_df, vw_df = result.get_ptf()
        except Exception:
            return

        cols = list(ew_df.columns)
        ncols = len(cols)

        # Parse column names to detect groups
        # Columns follow pattern: VAR1_VAR2 (e.g., RATING_NUM1_CS1)
        import re
        groups = {}  # {group_prefix: [col_names]}
        for col in cols:
            match = re.match(r'^([A-Za-z_]+\d+)_([A-Za-z_]+\d+)$', str(col))
            if match:
                grp = match.group(1)
                groups.setdefault(grp, []).append(col)

        if not groups:
            # Fallback: try to infer dimensions from column count
            for n1 in range(2, 11):
                if ncols % n1 == 0:
                    n2 = ncols // n1
                    groups = {f"G{i+1}": cols[i*n2:(i+1)*n2] for i in range(n1)}
                    break
            else:
                self._plot_portfolio_premia(result, figs_dir)
                return

        group_names = list(groups.keys())
        n_groups = len(group_names)
        n_within = len(next(iter(groups.values())))

        # Extract clean labels for within-group bars (just the second-sort part)
        first_group_cols = groups[group_names[0]]
        within_labels = []
        for col in first_group_cols:
            match = re.match(r'^[A-Za-z_]+\d+_([A-Za-z_]+)(\d+)$', str(col))
            if match:
                # e.g., "CS 1", "CS 2" — clean short label
                within_labels.append(f"{match.group(1)} {match.group(2)}")
            else:
                within_labels.append(str(col))

        # Clean group labels: strip trailing digits for display, keep number
        display_group_names = []
        for grp in group_names:
            match = re.match(r'^([A-Za-z_]+?)(\d+)$', grp)
            if match:
                display_group_names.append(f"{match.group(1)} {match.group(2)}")
            else:
                display_group_names.append(grp)

        fig, axes = plt.subplots(1, 2, figsize=(max(10, n_groups * 2.5), 5.5), sharey=True)

        for ax, (label, ptf_df) in zip(axes, [("EW", ew_df), ("VW", vw_df)]):
            bar_width = 0.8 / n_within
            for j in range(n_within):
                means, errs = [], []
                for grp_name in group_names:
                    grp_cols = groups[grp_name]
                    if j < len(grp_cols):
                        series = ptf_df[grp_cols[j]]
                        ann_mean, t_stat, ann_se, ci = _nw_stats(series)
                        means.append(ann_mean * 100)
                        errs.append(1.96 * ann_se * 100 if not np.isnan(ann_se) else 0)
                    else:
                        means.append(0)
                        errs.append(0)

                x_pos = np.arange(n_groups) + j * bar_width
                color = _GROUP_COLORS[j % len(_GROUP_COLORS)]
                ax.bar(x_pos, means, width=bar_width, yerr=errs, color=color,
                       capsize=2, edgecolor='black', linewidth=0.3, alpha=0.85,
                       label=within_labels[j] if label == "EW" else "")

            ax.set_xticks(np.arange(n_groups) + bar_width * (n_within - 1) / 2)
            ax.set_xticklabels(display_group_names, fontsize=9, rotation=45, ha='right')
            ax.set_title(label, fontsize=12)
            ax.set_ylabel("Annualized Mean (%)" if label == "EW" else "")
            ax.axhline(0, color='black', linewidth=0.5, linestyle='--')

        axes[0].legend(fontsize=8, loc='best', title="Second Sort")
        fig.suptitle(f"Portfolio Premia: {title_label}" if title_label else "Portfolio Premia (Double Sort)",
                     fontsize=13, y=1.02)
        fig.tight_layout()
        fig.savefig(figs_dir / "portfolio_premia.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

    # ------------------------------------------------------------------
    # Factor bars (LS EW & VW)
    # ------------------------------------------------------------------
    def _plot_factor_bars(self, result, figs_dir: Path, title_label: str = ""):
        """Bar chart: EW and VW long-short mean with NW CIs and t-stat annotations."""
        # Dispatch to custom factors if provided
        if self.custom_factors is not None:
            self._plot_factor_bars_custom(figs_dir, title_label)
            return

        try:
            ew_ls, vw_ls = result.get_long_short()
        except Exception:
            return

        fig, ax = plt.subplots(figsize=(5, 5))
        labels = ["EW", "VW"]
        means, errs, tstats = [], [], []

        for series in [ew_ls, vw_ls]:
            ann_mean, t_stat, ann_se, ci = _nw_stats(series)
            means.append(ann_mean * 100)
            errs.append(1.96 * ann_se * 100 if not np.isnan(ann_se) else 0)
            tstats.append(t_stat)

        x = np.arange(2)
        bars = ax.bar(x, means, yerr=errs, color=[_BLUE, _VW_BLUE], capsize=4,
                      edgecolor='black', linewidth=0.5, alpha=0.85, width=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=11)
        ax.set_ylabel("Annualized Mean (%)", fontsize=11)
        ax.set_title(f"Long-Short Factor: {title_label}" if title_label else "Long-Short Factor Returns",
                     fontsize=12)
        ax.axhline(0, color='black', linewidth=0.5, linestyle='--')

        # Annotate t-stats
        for i, (bar, t) in enumerate(zip(bars, tstats)):
            if not np.isnan(t):
                y_pos = bar.get_height()
                offset = -0.15 if y_pos >= 0 else 0.05
                ax.text(bar.get_x() + bar.get_width() / 2, y_pos + offset,
                        f"t={t:.2f}", ha='center', va='top' if y_pos >= 0 else 'bottom',
                        fontsize=9, color='black')

        fig.tight_layout()
        fig.savefig(figs_dir / "factor_bars.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

    def _plot_factor_bars_custom(self, figs_dir: Path, title_label: str = ""):
        """Grouped bar chart for custom factors: EW + VW bars per factor."""
        factor_names = list(self.custom_factors.keys())
        n = len(factor_names)
        fig, ax = plt.subplots(figsize=(max(6, n * 2.5), 5))
        bar_width = 0.35
        x = np.arange(n)

        for offset, (wt_label, wt_idx, color) in enumerate([
            ("EW", 0, _BLUE), ("VW", 1, _VW_BLUE)
        ]):
            means, errs, tstats = [], [], []
            for name in factor_names:
                series = self.custom_factors[name][wt_idx]
                ann_mean, t_stat, ann_se, ci = _nw_stats(series)
                means.append(ann_mean * 100)
                errs.append(1.96 * ann_se * 100 if not np.isnan(ann_se) else 0)
                tstats.append(t_stat)

            pos = x + (offset - 0.5) * bar_width
            bars = ax.bar(pos, means, width=bar_width, yerr=errs, color=color,
                          capsize=3, edgecolor='black', linewidth=0.5, alpha=0.85,
                          label=wt_label)
            # Annotate t-stats
            for bar, t in zip(bars, tstats):
                if not np.isnan(t):
                    y_pos = bar.get_height()
                    va = 'top' if y_pos >= 0 else 'bottom'
                    y_off = -0.1 if y_pos >= 0 else 0.05
                    ax.text(bar.get_x() + bar.get_width() / 2, y_pos + y_off,
                            f"t={t:.2f}", ha='center', va=va, fontsize=8, color='black')

        ax.set_xticks(x)
        ax.set_xticklabels(factor_names, fontsize=11)
        ax.set_ylabel("Annualized Mean (%)", fontsize=11)
        ax.set_title(f"Factor Returns: {title_label}" if title_label else "Factor Returns",
                     fontsize=12)
        ax.axhline(0, color='black', linewidth=0.5, linestyle='--')
        ax.legend(fontsize=10)

        fig.tight_layout()
        fig.savefig(figs_dir / "factor_bars.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

    # ------------------------------------------------------------------
    # Cumulative returns + turnover panel
    # ------------------------------------------------------------------
    def _plot_cumret_turnover(self, result, figs_dir: Path, has_turnover: bool,
                              title_label: str = ""):
        """Two-panel plot: (A) cumulative log returns, (B) turnover time series."""
        # Dispatch to custom factors if provided
        if self.custom_factors is not None:
            self._plot_cumret_turnover_custom(result, figs_dir, has_turnover, title_label)
            return

        try:
            ew_ls, vw_ls = result.get_long_short()
        except Exception:
            return

        n_panels = 2 if has_turnover else 1
        fig, axes = plt.subplots(n_panels, 1, figsize=(12, 4 * n_panels), sharex=True)
        if n_panels == 1:
            axes = [axes]

        # Panel A: Cumulative log returns
        ax = axes[0]
        for series, label, style, color in [
            (ew_ls, "EW", '-', _BLUE), (vw_ls, "VW", '--', _VW_BLUE)
        ]:
            valid = series.dropna()
            cum_ret = np.log1p(valid).cumsum()
            ax.plot(cum_ret.index, cum_ret.values, label=label,
                    linestyle=style, color=color, linewidth=1.2)

        if self.show_recessions:
            self._add_nber_shading(ax)
        ax.set_ylabel("Cumulative Log Return", fontsize=11)
        ax.set_title(f"Cumulative Returns: {title_label}" if title_label else "Cumulative Returns",
                     fontsize=12)
        ax.legend(fontsize=9)
        ax.axhline(0, color='black', linewidth=0.3)

        # Panel B: Turnover
        if has_turnover:
            ax2 = axes[1]
            try:
                ew_turn, vw_turn = result.get_turnover()
                # Average turnover across portfolios
                ew_avg = ew_turn.mean(axis=1).dropna()
                vw_avg = vw_turn.mean(axis=1).dropna()
                ax2.plot(ew_avg.index, ew_avg.values * 100, label="EW",
                         color=_BLUE, linewidth=0.8)
                ax2.plot(vw_avg.index, vw_avg.values * 100, label="VW",
                         color=_VW_BLUE, linewidth=0.8, linestyle='--')
                if self.show_recessions:
                    self._add_nber_shading(ax2)
                ax2.set_ylabel("Avg. Turnover (%)", fontsize=11)
                ax2.set_title(f"Portfolio Turnover: {title_label}" if title_label else "Portfolio Turnover",
                              fontsize=12)
                ax2.legend(fontsize=9)
            except Exception:
                ax2.text(0.5, 0.5, "Turnover data unavailable",
                         transform=ax2.transAxes, ha='center')

        # Format x-axis dates
        axes[-1].xaxis.set_major_locator(mdates.YearLocator(5))
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45)

        fig.tight_layout()
        fig.savefig(figs_dir / "cumret_turnover.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

    def _plot_cumret_turnover_custom(self, result, figs_dir: Path,
                                     has_turnover: bool, title_label: str = ""):
        """Multi-panel cumret plot: one panel per custom factor with EW + VW lines."""
        factor_names = list(self.custom_factors.keys())
        n_panels = len(factor_names)

        fig, axes = plt.subplots(n_panels, 1, figsize=(12, 3.5 * n_panels), sharex=True)
        if n_panels == 1:
            axes = [axes]

        for i, fname in enumerate(factor_names):
            ax = axes[i]
            ew_series, vw_series = self.custom_factors[fname]

            for series, label, style, color in [
                (ew_series, "EW", '-', _BLUE), (vw_series, "VW", '--', _VW_BLUE)
            ]:
                valid = series.dropna()
                cum_ret = np.log1p(valid).cumsum()
                ax.plot(cum_ret.index, cum_ret.values, label=label,
                        linestyle=style, color=color, linewidth=1.2)

            if self.show_recessions:
                self._add_nber_shading(ax)
            ax.set_ylabel("Cum. Log Return", fontsize=10)
            ax.set_title(fname, fontsize=11)
            ax.legend(fontsize=9)
            ax.axhline(0, color='black', linewidth=0.3)

        # Format x-axis dates
        axes[-1].xaxis.set_major_locator(mdates.YearLocator(5))
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45)

        fig.suptitle(f"Cumulative Returns: {title_label}" if title_label else "Cumulative Returns",
                     fontsize=13, y=1.01)
        fig.tight_layout()
        fig.savefig(figs_dir / "cumret_turnover.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

        # Separate factor turnover figure
        if has_turnover and self.custom_factor_legs:
            self._plot_factor_turnover_custom(result, figs_dir, title_label)

    def _plot_factor_turnover_custom(self, result, figs_dir: Path,
                                     title_label: str = ""):
        """Per-factor turnover plot: one panel per custom factor."""
        try:
            ew_turn, vw_turn = result.get_turnover()
        except Exception:
            return

        factor_names = [f for f in self.custom_factors if f in self.custom_factor_legs]
        if not factor_names:
            return

        n_panels = len(factor_names)
        fig, axes = plt.subplots(n_panels, 1, figsize=(12, 2.5 * n_panels), sharex=True)
        if n_panels == 1:
            axes = [axes]

        for i, fname in enumerate(factor_names):
            ax = axes[i]
            ew_series = self._compute_factor_turnover_series(fname, ew_turn)
            vw_series = self._compute_factor_turnover_series(fname, vw_turn)

            if ew_series is not None:
                valid = ew_series.dropna()
                ax.plot(valid.index, valid.values * 100, label="EW",
                        color=_BLUE, linewidth=0.8)
            if vw_series is not None:
                valid = vw_series.dropna()
                ax.plot(valid.index, valid.values * 100, label="VW",
                        color=_VW_BLUE, linewidth=0.8, linestyle='--')

            if self.show_recessions:
                self._add_nber_shading(ax)
            ax.set_ylabel("Turnover (%)", fontsize=10)
            ax.set_title(f"{fname} Turnover", fontsize=11)
            ax.legend(fontsize=9)

        axes[-1].xaxis.set_major_locator(mdates.YearLocator(5))
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45)

        fig.suptitle(f"Factor Turnover: {title_label}" if title_label else "Factor Turnover",
                     fontsize=13, y=1.01)
        fig.tight_layout()
        fig.savefig(figs_dir / "factor_turnover.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

    # ------------------------------------------------------------------
    # Turnover bar chart (Long, Short, Long-Short legs)
    # ------------------------------------------------------------------
    def _plot_turnover_bars(self, result, figs_dir: Path, has_turnover: bool,
                            title_label: str = ""):
        """Bar chart showing average turnover (%) for Long, Short, LS legs."""
        if not has_turnover:
            return

        try:
            ew_turn, vw_turn = result.get_turnover()
            if ew_turn is None or ew_turn.empty:
                return
        except Exception:
            return

        try:
            ew_df, vw_df = result.get_ptf()
        except Exception:
            return

        cols = list(ew_df.columns)
        n_ptf = len(cols)

        fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)

        for ax, (wt_label, turn_df) in zip(axes, [("EW", ew_turn), ("VW", vw_turn)]):
            # Identify long and short leg columns
            long_col = cols[-1] if n_ptf >= 2 else cols[0]
            short_col = cols[0] if n_ptf >= 2 else cols[0]

            leg_means = {}
            for leg_label, col in [("Long", long_col), ("Short", short_col)]:
                if col in turn_df.columns:
                    leg_means[leg_label] = turn_df[col].mean() * 100

            # LS turnover = average of long + short
            if "Long" in leg_means and "Short" in leg_means:
                leg_means["L-S"] = (leg_means["Long"] + leg_means["Short"]) / 2

            if not leg_means:
                continue

            labels = list(leg_means.keys())
            vals = list(leg_means.values())
            colors = [_BLUE, _VW_BLUE, _RED][:len(labels)]

            ax.bar(range(len(labels)), vals, color=colors, edgecolor='black',
                   linewidth=0.5, alpha=0.85, width=0.5)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, fontsize=11)
            ax.set_title(wt_label, fontsize=12)
            ax.set_ylabel("Avg. Monthly Turnover (%)" if wt_label == "EW" else "")

            # Annotate values
            for i, v in enumerate(vals):
                ax.text(i, v + 0.3, f"{v:.1f}%", ha='center', va='bottom', fontsize=9)

        fig.suptitle(f"Turnover by Leg: {title_label}" if title_label else "Turnover by Leg",
                     fontsize=13, y=1.02)
        fig.tight_layout()
        fig.savefig(figs_dir / "turnover_bars.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

    # ------------------------------------------------------------------
    # Batch: factor comparison chart
    # ------------------------------------------------------------------
    def _plot_factor_comparison(self, batch, summary_dir: Path,
                                max_per_plot: int = 10):
        """Grouped bar chart comparing LS means across all signals.

        When there are more than ``max_per_plot`` signals, splits into
        multiple pages (e.g., factor_comparison_1_10.png,
        factor_comparison_11_20.png, ...).
        """
        signals = list(batch.results.keys())
        if not signals:
            return

        n = len(signals)
        if n <= max_per_plot:
            chunks = [(0, n)]
        else:
            chunks = []
            for start in range(0, n, max_per_plot):
                end = min(start + max_per_plot, n)
                chunks.append((start, end))

        for start, end in chunks:
            chunk_signals = signals[start:end]
            n_chunk = len(chunk_signals)

            fig, ax = plt.subplots(figsize=(max(6, n_chunk * 1.5), 5))
            bar_width = 0.35
            x = np.arange(n_chunk)

            for offset, (label, color) in enumerate([("EW", _BLUE), ("VW", _VW_BLUE)]):
                means, errs = [], []
                for sig in chunk_signals:
                    try:
                        ew_ls, vw_ls = batch.results[sig].get_long_short()
                        series = ew_ls if label == "EW" else vw_ls
                        ann_mean, t_stat, ann_se, ci = _nw_stats(series)
                        means.append(ann_mean * 100)
                        errs.append(1.96 * ann_se * 100 if not np.isnan(ann_se) else 0)
                    except Exception:
                        means.append(0)
                        errs.append(0)

                pos = x + (offset - 0.5) * bar_width
                ax.bar(pos, means, width=bar_width, yerr=errs, color=color,
                       capsize=3, edgecolor='black', linewidth=0.5, alpha=0.85, label=label)

            ax.set_xticks(x)
            ax.set_xticklabels(chunk_signals, fontsize=10, rotation=45, ha='right')
            ax.set_ylabel("Annualized LS Mean (%)", fontsize=11)
            ax.set_title(f"Factor Comparison: {self.mnemonic}", fontsize=12)
            ax.legend(fontsize=10)
            ax.axhline(0, color='black', linewidth=0.5, linestyle='--')

            fig.tight_layout()

            if len(chunks) == 1:
                fname = "factor_comparison.png"
            else:
                fname = f"factor_comparison_{start + 1}_{end}.png"
            fig.savefig(summary_dir / fname, dpi=150, bbox_inches='tight')
            plt.close(fig)

    # ------------------------------------------------------------------
    # Batch: summary stats CSV
    # ------------------------------------------------------------------
    def _write_batch_summary(self, batch, summary_dir: Path):
        """One-row-per-signal summary CSV."""
        rows = []
        for signal, result in batch.results.items():
            for weight_label, wt in [("EW", "ew"), ("VW", "vw")]:
                try:
                    ew_ls, vw_ls = result.get_long_short()
                    ls = ew_ls if wt == "ew" else vw_ls
                    ann_mean, t_stat, ann_se, ci = _nw_stats(ls)
                    valid = ls.dropna()
                    std_ann = valid.std() * np.sqrt(12) * 100 if len(valid) > 1 else np.nan
                    sr = (valid.mean() / valid.std() * np.sqrt(12)) if len(valid) > 1 and valid.std() > 0 else np.nan
                    row = {
                        'Signal': signal,
                        'Weight': weight_label,
                        'Mean(%)': round(ann_mean * 100, 3),
                        't-stat(NW)': round(t_stat, 2),
                        'SR': round(sr, 3),
                        'Std(%)': round(std_ann, 3) if not np.isnan(std_ann) else np.nan,
                        'N': int(valid.notna().sum()),
                    }
                    # Turnover if available
                    try:
                        ew_turn, vw_turn = result.get_turnover()
                        turn = ew_turn if wt == "ew" else vw_turn
                        row['Turnover(%)'] = round(turn.mean().mean() * 100, 3)
                    except Exception:
                        pass
                    rows.append(row)
                except Exception:
                    pass

        if rows:
            pd.DataFrame(rows).to_csv(summary_dir / "summary_stats.csv", index=False)

    # ------------------------------------------------------------------
    # Batch: factor returns CSV (wide-form)
    # ------------------------------------------------------------------
    def _write_batch_factor_returns(self, batch, summary_dir: Path):
        """Save all signals' LS returns in wide-form CSV (dates x signals)."""
        try:
            ew_factors = batch.get_factor_returns('ew')
            vw_factors = batch.get_factor_returns('vw')
        except Exception:
            return

        # Merge with suffixes
        merged = ew_factors.add_suffix('_ew').join(
            vw_factors.add_suffix('_vw'), how='outer'
        )
        # Interleave columns: signal1_ew, signal1_vw, signal2_ew, ...
        signals = list(batch.results.keys())
        ordered_cols = []
        for sig in signals:
            for suffix in ['_ew', '_vw']:
                col = f"{sig}{suffix}"
                if col in merged.columns:
                    ordered_cols.append(col)
        merged = merged[[c for c in ordered_cols if c in merged.columns]]
        merged.index.name = 'date'
        merged.to_csv(summary_dir / "factor_returns.csv")

    # ------------------------------------------------------------------
    # Batch: factor correlation matrices
    # ------------------------------------------------------------------
    def _write_batch_correlations(self, batch, summary_dir: Path):
        """Save EW and VW correlation matrices + heatmap figure."""
        for wt, suffix in [('ew', 'ew'), ('vw', 'vw')]:
            try:
                factors = batch.get_factor_returns(wt)
                if factors.shape[1] < 2:
                    continue
                corr = factors.corr()
                corr.to_csv(summary_dir / f"factor_correlations_{suffix}.csv")
            except Exception:
                pass

        # Heatmap figure (EW only for simplicity)
        try:
            ew_factors = batch.get_factor_returns('ew')
            if ew_factors.shape[1] < 2:
                return
            corr = ew_factors.corr()
            n = len(corr)
            fig, ax = plt.subplots(figsize=(max(5, n * 0.8), max(4, n * 0.7)))
            im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='equal')
            ax.set_xticks(range(n))
            ax.set_yticks(range(n))
            ax.set_xticklabels(corr.columns, fontsize=9, rotation=45, ha='right')
            ax.set_yticklabels(corr.index, fontsize=9)
            # Annotate cells
            for i in range(n):
                for j in range(n):
                    val = corr.iloc[i, j]
                    color = 'white' if abs(val) > 0.6 else 'black'
                    ax.text(j, i, f"{val:.2f}", ha='center', va='center',
                            fontsize=8, color=color)
            fig.colorbar(im, ax=ax, shrink=0.8)
            ax.set_title(f"Factor Correlations (EW): {self.mnemonic}", fontsize=12)
            fig.tight_layout()
            fig.savefig(summary_dir / "factor_correlations.png", dpi=150, bbox_inches='tight')
            plt.close(fig)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Batch: extract_panel with sign correction -> parquet
    # ------------------------------------------------------------------
    def _write_extract_panel(self, batch, summary_dir: Path):
        """Save sign-corrected extract_panel() output as parquet.

        Uses full extract_panel() when available (turnover=True or
        WithinFirmSort). Falls back to LS-only panel from
        get_factor_returns() when extract_panel requires full leg data.
        """
        naming = NamingConfig(sign_correct=True)
        try:
            panel = extract_panel(batch, naming=naming)
            panel.to_parquet(summary_dir / "factor_panel.parquet", index=False)
            return
        except ValueError:
            # Fast-path batch: no individual legs available, build LS-only panel
            pass
        except Exception:
            return

        # Fallback: LS-only panel from get_factor_returns()
        try:
            frames = []
            for wt in ['ew', 'vw']:
                factors = batch.get_factor_returns(wt)
                for col in factors.columns:
                    sign = -1 if factors[col].mean() < 0 else 1
                    name = f"{col}*" if sign < 0 else col
                    df = pd.DataFrame({
                        'date': factors.index,
                        'factor': name,
                        'freq': 1,
                        'leg': 'ls',
                        'weighting': wt,
                        'return': factors[col].values * sign,
                    })
                    frames.append(df)
            if frames:
                panel = pd.concat(frames, ignore_index=True)
                panel.to_parquet(summary_dir / "factor_panel.parquet", index=False)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Meta JSON
    # ------------------------------------------------------------------
    def _write_meta(self, result, folder: Path, signal_name: str = "",
                    strategy_type: str = ""):
        """Write meta.json with run configuration."""
        try:
            import PyBondLab
            version = getattr(PyBondLab, '__version__', 'unknown')
        except Exception:
            version = 'unknown'

        meta: Dict[str, Any] = {
            "mnemonic": self.mnemonic,
            "date_generated": datetime.now().isoformat(),
            "pybondlab_version": version,
        }

        if signal_name:
            meta["signal"] = signal_name

        # Extract config from result
        config = getattr(result, 'config', None)

        # --- Strategy section ---
        strategy_meta: Dict[str, Any] = {"type": strategy_type}
        if config and isinstance(config, dict):
            # Normalize strategy_type from __strategy_name__ to clean identifier
            raw_type = config.get('strategy_type', '')
            normalized = _normalize_strategy_type(raw_type)
            if normalized:
                strategy_meta['type'] = normalized
            for key in ['sort_var', 'num_portfolios', 'holding_period',
                        'rebalance_frequency', 'rebalance_month',
                        'turnover', 'chars', 'banding_threshold',
                        'dynamic_weights', 'breakpoints', 'breakpoint_filter']:
                if key in config and config[key] is not None:
                    strategy_meta[key] = config[key]
            # DoubleSort-specific
            if config.get('sort_var2') is not None:
                for key in ['sort_var2', 'num_portfolios2', 'how', 'breakpoints2']:
                    if key in config and config[key] is not None:
                        strategy_meta[key] = config[key]
                # Factor definition
                sv = config.get('sort_var', '?')
                sv2 = config.get('sort_var2', '?')
                strategy_meta['factor_definition'] = (
                    f"LS on {sv2} (sort_var2), averaged across {sv} groups (sort_var)"
                )
            # WithinFirmSort-specific
            if config.get('firm_id_col') is not None:
                strategy_meta['firm_id_col'] = config['firm_id_col']
            # Override type from config if available (already normalized above)
        meta["strategy"] = strategy_meta

        # --- Filters section ---
        filters_meta: Dict[str, Any] = {}
        if config and isinstance(config, dict):
            if 'rating' in config:
                filters_meta['rating'] = config['rating']
            filters_meta['applied'] = config.get('filters', False)
            if config.get('banding_threshold') is not None:
                filters_meta['banding_threshold'] = config['banding_threshold']
        meta["filters"] = filters_meta

        # --- Sample section ---
        sample_meta: Dict[str, Any] = {}
        # Data range: prefer custom_factors index, fallback to get_long_short()
        try:
            if self.custom_factors is not None:
                # Get index from first factor's EW series
                first_ew = next(iter(self.custom_factors.values()))[0]
                idx = first_ew.dropna().index
            elif self._is_batch:
                first_result = next(iter(result.results.values()))
                ew_ls, _ = first_result.get_long_short()
                idx = ew_ls.dropna().index
            else:
                ew_ls, _ = result.get_long_short()
                idx = ew_ls.dropna().index
            if len(idx) > 0:
                sample_meta["data_range"] = f"{idx[0].strftime('%Y-%m')} to {idx[-1].strftime('%Y-%m')}"
                sample_meta["n_dates"] = len(idx)
        except Exception:
            pass
        # Sample stats from metadata
        metadata = getattr(result, 'metadata', None)
        if metadata and isinstance(metadata, dict):
            if 'avg_bonds_per_date' in metadata:
                sample_meta['avg_bonds_per_date'] = metadata['avg_bonds_per_date']
            if 'signal_coverage_pct' in metadata:
                sample_meta['signal_coverage_pct'] = metadata['signal_coverage_pct']
        meta["sample"] = sample_meta

        # --- Headline stats section ---
        headline: Dict[str, Any] = {}
        if self.custom_factors is not None:
            # Per-factor headline stats with EW/VW
            for factor_name, (ew_series, vw_series) in self.custom_factors.items():
                factor_stats = {}
                for prefix, series in [('ew', ew_series), ('vw', vw_series)]:
                    ann_mean, t_stat, ann_se, ci = _nw_stats(series)
                    valid = series.dropna()
                    sr = (valid.mean() / valid.std() * np.sqrt(12)) if len(valid) > 1 and valid.std() > 0 else np.nan
                    factor_stats[f'{prefix}_mean_ann_pct'] = round(ann_mean * 100, 3) if not np.isnan(ann_mean) else None
                    factor_stats[f'{prefix}_tstat'] = round(t_stat, 2) if not np.isnan(t_stat) else None
                    factor_stats[f'{prefix}_sharpe'] = round(sr, 3) if not np.isnan(sr) else None
                headline[factor_name] = factor_stats
        else:
            try:
                if self._is_batch:
                    first_result = next(iter(result.results.values()))
                    ew_ls, vw_ls = first_result.get_long_short()
                else:
                    ew_ls, vw_ls = result.get_long_short()
                for prefix, series in [('ew', ew_ls), ('vw', vw_ls)]:
                    ann_mean, t_stat, ann_se, ci = _nw_stats(series)
                    valid = series.dropna()
                    sr = (valid.mean() / valid.std() * np.sqrt(12)) if len(valid) > 1 and valid.std() > 0 else np.nan
                    headline[f'{prefix}_mean_ann_pct'] = round(ann_mean * 100, 3) if not np.isnan(ann_mean) else None
                    headline[f'{prefix}_tstat'] = round(t_stat, 2) if not np.isnan(t_stat) else None
                    headline[f'{prefix}_sharpe'] = round(sr, 3) if not np.isnan(sr) else None
            except Exception:
                pass
        meta["headline"] = headline

        # --- Batch-specific ---
        if self._is_batch and hasattr(result, 'signals'):
            meta["signals"] = list(result.signals)

        with open(folder / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _add_nber_shading(ax):
        """Add gray recession shading to a matplotlib axes.

        Only draws recessions that overlap the current data range so that
        the x-axis limits are not extended beyond the plotted data.
        """
        xlim = ax.get_xlim()
        # num2date returns tz-aware datetimes; strip tz for comparison with naive Timestamps
        xmin = mdates.num2date(xlim[0]).replace(tzinfo=None)
        xmax = mdates.num2date(xlim[1]).replace(tzinfo=None)
        for start, end in NBER_RECESSIONS:
            s, e = pd.Timestamp(start), pd.Timestamp(end)
            if e < xmin or s > xmax:
                continue
            ax.axvspan(s, e, alpha=0.15, color='gray', zorder=0)
        # Restore original xlim (axvspan can extend it)
        ax.set_xlim(xlim)

    @staticmethod
    def _detect_strategy_type(result) -> str:
        """Best-effort detection of strategy type from a FormationResults."""
        config = getattr(result, 'config', None) or {}
        stype = config.get('strategy_type', '')
        if stype:
            return _normalize_strategy_type(stype)
        # Heuristic from portfolio column names
        try:
            ew_df, _ = result.get_ptf()
            cols = list(ew_df.columns)
            # DoubleSort columns contain '_' separating two variable names (e.g., CS1_RATING_NUM1)
            # But be careful: column names like 'RATING_NUM1' also have underscores
            # Key pattern: DoubleSort has more columns than any standard single sort
            # and columns follow pattern VAR1_VAR2 where both parts end in digits
            if len(cols) >= 4:
                # DoubleSort columns: VAR1_VAR2 where both parts have letters+digits
                # e.g., RATING_NUM1_CS1. Must have >1 distinct first-sort group.
                # Avoids false match on signals like mom3_1 -> MOM3_11 (no letters in "11")
                import re
                double_pattern = re.compile(r'^([A-Za-z_]+\d+)_([A-Za-z_]+\d+)$')
                matches = [double_pattern.match(str(c)) for c in cols]
                if all(matches):
                    groups = set(m.group(1) for m in matches)
                    if len(groups) > 1:
                        return 'DoubleSort'
            # WithinFirmSort: exactly 2 portfolios named LOW/HIGH
            if set(cols) == {'LOW', 'HIGH'}:
                return 'WithinFirmSort'
        except Exception:
            pass
        return 'SingleSort'

    @staticmethod
    def _has_turnover(result) -> bool:
        """Check if turnover data is available."""
        try:
            ew_turn, _ = result.get_turnover()
            return ew_turn is not None and not ew_turn.empty
        except Exception:
            return False

    def _compute_factor_turnover(self, factor_name, weight_label,
                                 ew_turn_df, vw_turn_df):
        """Compute turnover for a custom factor from its long/short leg composition.

        Returns turnover as a percentage, or None if unavailable.
        Factor turnover = (avg long-leg turnover + avg short-leg turnover) / 2.
        """
        if factor_name not in self.custom_factor_legs:
            return None
        turn_df = ew_turn_df if weight_label == 'EW' else vw_turn_df
        if turn_df is None:
            return None
        long_cols, short_cols = self.custom_factor_legs[factor_name]
        # Filter to columns that actually exist in turnover data
        long_valid = [c for c in long_cols if c in turn_df.columns]
        short_valid = [c for c in short_cols if c in turn_df.columns]
        if not long_valid or not short_valid:
            return None
        long_avg = turn_df[long_valid].mean(axis=1).mean()
        short_avg = turn_df[short_valid].mean(axis=1).mean()
        return (long_avg + short_avg) / 2 * 100

    def _compute_factor_turnover_series(self, factor_name, turn_df):
        """Compute per-period turnover time series for a custom factor.

        Returns a Series, or None if unavailable.
        """
        if factor_name not in self.custom_factor_legs:
            return None
        if turn_df is None:
            return None
        long_cols, short_cols = self.custom_factor_legs[factor_name]
        long_valid = [c for c in long_cols if c in turn_df.columns]
        short_valid = [c for c in short_cols if c in turn_df.columns]
        if not long_valid or not short_valid:
            return None
        return (turn_df[long_valid].mean(axis=1) + turn_df[short_valid].mean(axis=1)) / 2

    def _build_title_label(self, result, signal_name: str = "") -> str:
        """Build a descriptive label for figure titles from result config."""
        config = getattr(result, 'config', None) or {}
        labels = self.labels
        strategy_type = _normalize_strategy_type(config.get('strategy_type', ''))

        # Signal display name
        sort_var = config.get('sort_var', '')
        sort_var2 = config.get('sort_var2', '')
        if signal_name:
            signal_display = _display_name(signal_name, labels)
        elif sort_var:
            signal_display = _display_name(sort_var, labels)
        else:
            signal_display = self.mnemonic

        # DoubleSort: "Signal2 x Signal1" (factor x control)
        if sort_var2:
            sv2_display = _display_name(sort_var2, labels)
            signal_display = f"{sv2_display} \u00d7 {signal_display}"

        # Build details list
        details = []

        # Portfolio grid
        nport = config.get('num_portfolios')
        nport2 = config.get('num_portfolios2')
        if nport2:
            details.append(f"{nport}\u00d7{nport2}")
        elif nport:
            details.append(f"{nport} ptf")

        # DoubleSort how
        if sort_var2 and config.get('how'):
            details.append(config['how'])

        # Within-firm
        if strategy_type == 'WithinFirmSort':
            details.append('within-firm')

        # Rating filter
        rating = config.get('rating')
        if rating and rating not in (None, 'ALL', 'all', 'All'):
            details.append(str(rating))

        # Rebalance frequency (skip monthly since it's default)
        rebal = config.get('rebalance_frequency', 'monthly')
        rebal_month = config.get('rebalance_month')
        if rebal and rebal != 'monthly':
            month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May',
                           6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct',
                           11: 'Nov', 12: 'Dec'}
            rebal_str = str(rebal)
            if rebal_month and isinstance(rebal_month, int):
                rebal_str += f" {month_names.get(rebal_month, str(rebal_month))}"
            details.append(rebal_str)

        if details:
            return f"{signal_display} ({', '.join(details)})"
        return signal_display
