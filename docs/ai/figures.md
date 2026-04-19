# Publication Figures Workflow

Use this workflow when a user wants to create, improve, validate, or export a
figure for an empirical finance paper, report, deck, or Word proof pack.

## Core Rule

Start with `fintools.figures` before writing custom plotting code. The package
contains FT-style and paper-style themes, reusable chart builders, Word/A4
export helpers, caption context, validation checks, and dataframe-to-figure
suite planning.

## Style Choice

The native toolkit supports both repo figure styles:

- Use `style="fins"` for the house publication style used by the older
  publication-figures skill helpers.
- Use `style="ft"` for FT-style output.
- Keep the legacy `.claude/skills/publication-figures/finance.mplstyle` and
  `figutils.py` assets available for explicitly requested standalone helper
  workflows, but prefer `fintools.figures` for repo-native work.

## Deterministic Commands

Build the FT-style validation gallery:

```bash
python tools/figure_examples.py --style ft --docx --output results/figures
```

Build the non-FT validation gallery:

```bash
python tools/figure_examples.py --style fins --docx --output results/figures
```

Refresh frozen validation fixtures from public sources only when explicitly
maintaining fixtures:

```bash
python tools/download_validation_data.py
```

Raw downloads must stay under `fintools/datasets/validation/_raw/` or
`_refresh/`; those folders are ignored.

## Dataframe Figure Suites

For broad requests such as "make FT-style figures for my dataframe", profile
and plan first:

```python
from fintools.figures import create_figure_suite, plan_figure_suite, profile_dataframe

profile = profile_dataframe(df)
plan = plan_figure_suite(df, title_prefix="My Dataset", narrative=True)
result = create_figure_suite(
    df,
    output="results/figures",
    style="ft",
    docx=True,
    title_prefix="My Dataset",
    narrative=True,
)
```

Inspect `plan`, `result.skipped`, and `result.issues` before presenting the
figures. The suite generator skips rendered figures that fail validation rather
than exporting unreadable charts.

## Plotting Standards

- Always supply title, x label, y label, units, source, and sample period.
- Use `FigureContext` for captions and source notes.
- Use `style="ft"` for FT-inspired colors, ticks, and grids.
- Use `style="fins"` when the user wants the original house publication style
  rather than FT-style output.
- Keep FT background off unless the user explicitly wants the beige background.
- For Word/A4 exports, prefer `profile="word_a4"` and `export_word_figure`.
- Use NBER recession shading for relevant time-series figures.
- Check return scale before compounding returns; Fama/French fixtures are
  percent returns.
- Avoid raw dataframe field names in visible labels.
- Check rendered outputs for overlapping labels, clipped markers, unreadable
  ticks, blank images, and Word page fit.
- Keep generated PNG/PDF/DOCX/caption files under ignored output directories
  such as `results/figures/`.

## Validation Datasets

Use `fintools.datasets.load_validation_dataset` for deterministic examples and
tests. The tracked fixtures include:

- `ff3_monthly`
- `ff_industry_10_monthly`
- `ff25_size_value_monthly`
- `fred_macro_monthly`
- `fred_rates_daily`
- `fred_financial_stress_daily`
- `shiller_market_monthly`
- `world_bank_country_panel_annual`
- `world_bank_gdp_annual`

## Common Helpers

Use these public helpers for most figures:

- `time_series_plot`
- `cumulative_returns_plot`
- `indexed_time_series_plot`
- `drawdown_plot`
- `mean_return_bar_plot`
- `stacked_area_plot`
- `stacked_bar_plot`
- `proportional_stacked_bar_plot`
- `diverging_bar_plot`
- `dumbbell_plot`
- `scatter_plot`
- `bubble_scatter_plot`
- `calendar_heatmap`
- `distribution_plot`
- `distribution_comparison_plot`
- `ecdf_plot`
- `correlation_heatmap`
- `value_heatmap`
- `small_multiples`
- `lollipop_plot`
- `slope_chart`
- `area_balance_plot`
- `rolling_stat_plot`
- `uncertainty_band_plot`
- `export_figure_bundle`
- `export_word_figure`
- `insert_figures_docx`
