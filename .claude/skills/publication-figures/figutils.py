"""
Publication-quality figure utilities for empirical finance & economics.

Reference module — Claude copies relevant functions into project code/ as needed.
Not meant to be imported directly from this path.

Usage (after copying to project):
    from figutils import setup_style, set_size, savefig, plot_decile_bars
    setup_style()
    fig, ax = plt.subplots(figsize=set_size('single'))
    ...
    savefig(fig, 'results/figures/my_figure')
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path

# ============================================================
# Color Palettes
# ============================================================

# Okabe-Ito colorblind-safe (default cycle)
PALETTE = ['#377EB8', '#E41A1C', '#4DAF4A', '#984EA3',
           '#FF7F00', '#A65628', '#F781BF', '#999999']

# Two-series: long vs short, treatment vs control
BLUE_RED = ['#377EB8', '#E41A1C']

# Grayscale-safe (combine with linestyles for print)
GRAYSCALE = ['#000000', '#555555', '#999999', '#CCCCCC']


# ============================================================
# Style Setup
# ============================================================

def setup_style():
    """Apply publication-ready style for finance/economics figures."""
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'STIXGeneral', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 9,
        'axes.labelsize': 9,
        'axes.titlesize': 10,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'axes.linewidth': 0.6,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': False,
        'axes.axisbelow': True,
        'lines.linewidth': 1.2,
        'lines.markersize': 4,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.size': 4,
        'ytick.major.size': 4,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'legend.frameon': False,
        'figure.dpi': 150,
        'savefig.dpi': 600,
        'savefig.format': 'pdf',
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
        'axes.prop_cycle': plt.cycler('color', PALETTE),
    })


def set_size(width='single', ratio='golden'):
    """Return (width, height) tuple in inches for figure sizing.

    Parameters
    ----------
    width : str or float
        'single' (3.5"), 'onehalf' (5.25"), 'double' (7.0"),
        'slide' (10.0"), or a float in inches.
    ratio : str or float
        'golden' (1.618), 'square' (1.0), 'wide' (2.0), or a float.

    Returns
    -------
    tuple of (width, height) in inches.
    """
    widths = {'single': 3.5, 'onehalf': 5.25, 'double': 7.0, 'slide': 10.0}
    ratios = {'golden': 1.618, 'square': 1.0, 'wide': 2.0}
    w = widths.get(width, width) if isinstance(width, str) else width
    r = ratios.get(ratio, ratio) if isinstance(ratio, str) else ratio
    return (w, w / r)


def savefig(fig, name, formats=('pdf',), dpi=600, preview=True):
    """Save figure with publication settings.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
    name : str
        Output path without extension (e.g., 'results/figures/hml_deciles').
    formats : tuple of str
        File formats to save ('pdf', 'png', 'eps', 'tif').
    dpi : int
        Resolution for raster formats.
    preview : bool
        If True, also save a low-res PNG for quick viewing.
    """
    path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        fig.savefig(f'{name}.{fmt}', bbox_inches='tight', dpi=dpi)
    if preview and 'png' not in formats:
        fig.savefig(f'{name}.png', bbox_inches='tight', dpi=150)


# ============================================================
# Statistical Utilities
# ============================================================

def newey_west_se(x, lag=None):
    """Newey-West HAC standard error of the mean.

    Parameters
    ----------
    x : array-like
        Time series of observations.
    lag : int, optional
        Number of lags. Defaults to floor(T^0.25).

    Returns
    -------
    float
        Newey-West standard error of the mean.
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    T = len(x)
    if T < 2:
        return np.nan
    if lag is None:
        lag = int(np.floor(T ** 0.25))
    xbar = x.mean()
    e = x - xbar
    # Variance term (lag 0)
    gamma0 = np.dot(e, e) / T
    # Autocovariance terms with Bartlett weights
    nw_var = gamma0
    for j in range(1, lag + 1):
        gamma_j = np.dot(e[j:], e[:-j]) / T
        nw_var += 2 * (1 - j / (lag + 1)) * gamma_j
    return np.sqrt(nw_var / T)


# ============================================================
# Finance-Specific Plot Types
# ============================================================

def plot_cumulative_returns(ax, returns_dict, start_value=1.0, log_scale=False):
    """Plot cumulative wealth paths for multiple strategies/portfolios.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    returns_dict : dict
        {'Strategy Name': pd.Series of returns, ...}
    start_value : float
        Starting portfolio value (default 1.0 = growth of $1).
    log_scale : bool
        If True, use log scale on y-axis.
    """
    for i, (label, ret) in enumerate(returns_dict.items()):
        cumret = start_value * (1 + ret).cumprod()
        ax.plot(cumret.index, cumret.values, label=label)
    ax.axhline(start_value, color='grey', linewidth=0.4, linestyle='-', zorder=0)
    if log_scale:
        ax.set_yscale('log')
    ax.set_ylabel(f'Growth of ${start_value:.0f}')
    ax.legend()


def plot_decile_bars(ax, means, labels=None, highlight_extremes=True,
                     ylabel='Mean Return (% monthly)', spread_label=True):
    """Bar chart of decile (or quantile) portfolio means.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    means : array-like
        Mean returns for each portfolio (low to high signal).
    labels : list of str, optional
        X-axis labels. Defaults to 1, 2, ..., N.
    highlight_extremes : bool
        Color the short (low) and long (high) legs differently.
    ylabel : str
    spread_label : bool
        Annotate the long-short spread above the bars.
    """
    n = len(means)
    if labels is None:
        labels = [str(i + 1) for i in range(n)]
    x = np.arange(n)

    colors = [PALETTE[0]] * n
    if highlight_extremes:
        colors[0] = PALETTE[1]       # Short leg = red
        colors[-1] = PALETTE[2]      # Long leg = green

    ax.bar(x, means, color=colors, edgecolor='white', linewidth=0.5, width=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel('Portfolio')
    ax.set_ylabel(ylabel)
    ax.axhline(0, color='grey', linewidth=0.4, zorder=0)

    if spread_label and n >= 2:
        spread = means[-1] - means[0]
        ymax = max(means) * 1.15
        ax.text(n - 1, ymax, f'L-S: {spread:.2f}',
                ha='center', fontsize=7, style='italic')


def plot_portfolio_bars(ax, returns_df, labels=None, highlight_extremes=True,
                        ylabel='Mean Return (% monthly)', show_ls=True,
                        ls_label='10-1', scale=100, lag=None):
    """Bar chart of portfolio means with Newey-West 95% CI error bars.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    returns_df : pd.DataFrame
        Columns are portfolios (0, 1, ..., N-1), rows are time periods.
        Each column is the return time series for that portfolio.
    labels : list of str, optional
        X-axis labels for portfolios. Defaults to 1, 2, ..., N.
    highlight_extremes : bool
        Color the short (low) and long (high) legs differently.
    ylabel : str
    show_ls : bool
        If True, append a long-short (last - first) bar.
    ls_label : str
        Label for the long-short bar.
    scale : float
        Multiply returns by this (default 100 for percent).
    lag : int, optional
        Newey-West lag. Defaults to floor(T^0.25).
    """
    port_cols = [c for c in returns_df.columns if c != 'hml']
    n = len(port_cols)
    if labels is None:
        labels = [str(i + 1) for i in range(n)]

    means = [returns_df[c].mean() * scale for c in port_cols]
    ses = [newey_west_se(returns_df[c].values, lag=lag) * scale for c in port_cols]

    if show_ls:
        ls_series = returns_df[port_cols[-1]] - returns_df[port_cols[0]]
        ls_mean = ls_series.mean() * scale
        ls_se = newey_west_se(ls_series.values, lag=lag) * scale
        means.append(ls_mean)
        ses.append(ls_se)
        labels.append(ls_label)

    n_bars = len(means)
    x = np.arange(n_bars)
    ci95 = [1.96 * s for s in ses]

    colors = [PALETTE[0]] * n
    if highlight_extremes:
        colors[0] = PALETTE[1]       # Short leg = red
        colors[-1] = PALETTE[2]      # Long leg = green
    if show_ls:
        colors.append(PALETTE[3])    # L-S = purple

    ax.bar(x, means, color=colors, edgecolor='white', linewidth=0.5, width=0.7,
           yerr=ci95, error_kw=dict(capsize=3, linewidth=0.8, color='black'))
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel('Portfolio')
    ax.set_ylabel(ylabel)
    ax.axhline(0, color='grey', linewidth=0.4, zorder=0)

    # Annotate L-S with t-stat
    if show_ls:
        t_stat = means[-1] / ses[-1] if ses[-1] > 0 else np.nan
        y_pos = means[-1] + ci95[-1] if means[-1] >= 0 else means[-1] - ci95[-1]
        va = 'bottom' if means[-1] >= 0 else 'top'
        ax.text(x[-1], y_pos, f't = {t_stat:.2f}',
                ha='center', va=va, fontsize=7, style='italic')


def plot_coefficient(ax, coefs, ci_low, ci_high, names, horizontal=True):
    """Coefficient plot (forest plot) with confidence intervals.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    coefs : array-like
        Point estimates.
    ci_low, ci_high : array-like
        Lower and upper confidence interval bounds.
    names : list of str
        Variable names.
    horizontal : bool
        If True (default), variables on y-axis, coefficients on x-axis.
    """
    coefs = np.asarray(coefs)
    ci_low = np.asarray(ci_low)
    ci_high = np.asarray(ci_high)
    pos = np.arange(len(coefs))

    if horizontal:
        ax.errorbar(coefs, pos, xerr=[coefs - ci_low, ci_high - coefs],
                     fmt='o', color=PALETTE[0], capsize=3, markersize=4,
                     linewidth=1.0)
        ax.axvline(0, color='grey', linewidth=0.5, linestyle='--')
        ax.set_yticks(pos)
        ax.set_yticklabels(names)
        ax.invert_yaxis()
    else:
        ax.errorbar(pos, coefs, yerr=[coefs - ci_low, ci_high - coefs],
                     fmt='o', color=PALETTE[0], capsize=3, markersize=4,
                     linewidth=1.0)
        ax.axhline(0, color='grey', linewidth=0.5, linestyle='--')
        ax.set_xticks(pos)
        ax.set_xticklabels(names, rotation=45, ha='right')


def plot_event_study(ax, car, ci_low=None, ci_high=None, event_window=(-10, 10)):
    """Event study cumulative abnormal return plot.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    car : array-like
        Cumulative abnormal returns for each day in the event window.
    ci_low, ci_high : array-like, optional
        Confidence interval bounds.
    event_window : tuple
        (start_day, end_day) relative to event.
    """
    days = np.arange(event_window[0], event_window[1] + 1)
    ax.plot(days, car, color=PALETTE[0], linewidth=1.2)
    if ci_low is not None and ci_high is not None:
        ax.fill_between(days, ci_low, ci_high, alpha=0.2, color=PALETTE[0])
    ax.axvline(0, color='grey', linewidth=0.5, linestyle='--')
    ax.axhline(0, color='grey', linewidth=0.4)
    ax.set_xlabel('Days Relative to Event')
    ax.set_ylabel('CAR (%)')


def plot_time_series(ax, series_dict, zero_line=False):
    """Multi-series time series plot.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    series_dict : dict
        {'Series Name': pd.Series with DatetimeIndex, ...}
    zero_line : bool
        If True, add a horizontal line at y=0.
    """
    for label, s in series_dict.items():
        ax.plot(s.index, s.values, label=label)
    if zero_line:
        ax.axhline(0, color='grey', linewidth=0.4, zorder=0)
    if len(series_dict) > 1:
        ax.legend()


def add_recession_bands(ax, recessions=None):
    """Add NBER recession shading to a time series axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    recessions : list of (start, end) tuples, optional
        If None, uses NBER recessions from 2001 onward.
    """
    import pandas as pd
    if recessions is None:
        recessions = [
            ('2001-03-01', '2001-11-01'),
            ('2007-12-01', '2009-06-01'),
            ('2020-02-01', '2020-04-01'),
        ]
    for start, end in recessions:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end),
                    alpha=0.08, color='grey', zorder=0)


def label_panels(axes, labels=None, x=-0.1, y=1.05, fontweight='bold'):
    """Label multi-panel figures with (a), (b), (c), etc.

    Parameters
    ----------
    axes : array-like of matplotlib.axes.Axes
    labels : list of str, optional
        Custom labels. Defaults to (a), (b), (c), ...
    """
    axes_flat = np.atleast_1d(axes).flat
    if labels is None:
        labels = [f'({chr(97 + i)})' for i in range(len(list(axes_flat)))]
        axes_flat = np.atleast_1d(axes).flat  # reset iterator
    for ax, lbl in zip(axes_flat, labels):
        ax.text(x, y, lbl, transform=ax.transAxes,
                fontsize=10, fontweight=fontweight, va='top')


def format_pct_axis(ax, axis='y', decimals=1):
    """Format axis tick labels as percentages.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    axis : str
        'x' or 'y'
    decimals : int
        Number of decimal places.
    """
    fmt = mticker.FuncFormatter(lambda x, _: f'{x:.{decimals}f}%')
    if axis == 'y':
        ax.yaxis.set_major_formatter(fmt)
    else:
        ax.xaxis.set_major_formatter(fmt)
