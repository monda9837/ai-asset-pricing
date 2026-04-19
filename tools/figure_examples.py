#!/usr/bin/env python3
# mypy: ignore-errors
"""Generate publication-quality validation figure examples."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


class FigureExampleError(RuntimeError):
    """Raised when validation figure generation cannot complete cleanly."""


WorkflowError = FigureExampleError


def repo_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[1]


def resolve_path(cwd: Path, target_path: Path) -> Path:
    """Resolve an absolute or cwd-relative path."""

    if target_path.is_absolute():
        return target_path.resolve()
    return (cwd / target_path).resolve()


def ensure_within_repo(path: Path, root: Path) -> Path:
    """Ensure a generated output path stays within the repository."""

    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise FigureExampleError(f"path is outside the repo: {resolved}") from exc
    return resolved


def dataset_sample_label(data_index: object) -> str:
    """Return a compact sample-period label for a datetime-like index."""

    try:
        start = data_index.min()
        end = data_index.max()
    except AttributeError:
        return ""
    if hasattr(start, "strftime") and hasattr(end, "strftime"):
        return f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
    return ""


def build_figure_examples(
    root: Path,
    cwd: Path,
    *,
    output: str | None = None,
    docx: bool = False,
    style: str = "fins",
    ft_background: bool = False,
    plotly_demo: bool = False,
) -> tuple[int, list[str]]:
    """Generate a small set of validation figures with the public toolkit."""

    if style not in {"fins", "ft"}:
        raise WorkflowError("figure style must be one of: fins, ft")

    output_path = resolve_path(cwd, Path(output or "results/figures"))
    output_path = ensure_within_repo(output_path, root)

    try:
        import matplotlib

        matplotlib.use("Agg", force=False)
        import matplotlib.pyplot as plt
        import pandas as pd

        from fintools.datasets import load_validation_dataset
        from fintools.figures import (
            FigureContext,
            WordFigureEntry,
            area_balance_plot,
            bubble_scatter_plot,
            calendar_heatmap,
            correlation_heatmap,
            cumulative_returns_plot,
            distribution_comparison_plot,
            distribution_plot,
            diverging_bar_plot,
            dumbbell_plot,
            ecdf_plot,
            export_figure_bundle,
            export_word_figure,
            indexed_time_series_plot,
            insert_figures_docx,
            lollipop_plot,
            mean_return_bar_plot,
            proportional_stacked_bar_plot,
            rolling_stat_plot,
            scatter_plot,
            slope_chart,
            small_multiples,
            stacked_bar_plot,
            time_series_plot,
            uncertainty_band_plot,
            validate_category_label_count,
            validate_display_labels,
            validate_docx_images_fit_page,
            validate_image_not_blank,
            validate_markers_within_axes,
            validate_no_text_overlap,
            validate_no_tick_label_overlap,
            validate_series_identification,
            validate_unique_series_colors,
            value_heatmap,
        )
    except ImportError as exc:
        raise WorkflowError(
            "figure dependencies are missing; reinstall with the repo interpreter and "
            "-m pip install -r requirements.txt -r requirements-dev.txt"
        ) from exc

    stem_prefix = "validation" if style == "fins" else "ft_validation"
    docx_name = "validation_figures.docx" if style == "fins" else "validation_figures_ft.docx"
    docx_title = (
        "Validation Figure Examples"
        if style == "fins"
        else "FT-Style Validation Figure Examples"
    )

    base_gallery_stems = {
        "factor_stacked_returns",
        "ff25_distribution_by_value",
        "ff25_mean_heatmap",
        "ff3_full_cumulative",
        "ff3_full_returns",
        "industry_correlations",
        "industry_ecdf",
        "industry_excess_diverging",
        "industry_mean_returns",
        "industry_small_multiples",
        "macro_indexed",
        "macro_scatter_fit",
        "market_cumulative",
        "market_return_distribution",
        "shiller_cape",
        "shiller_real_market",
        "stress_calendar_heatmap",
        "stress_rolling",
        "stress_uncertainty_band",
        "treasury_rates",
        "world_bank_bubble",
        "world_bank_gdp_per_capita_dumbbell",
        "world_bank_gdp_share_stacked",
        "yield_spreads",
    }
    if style == "ft":
        base_gallery_stems.update(
            {
                "macro_policy_episode",
                "world_bank_gdp_lollipop",
                "world_bank_gdp_slope",
                "yield_spread_deviation",
            }
        )
    if plotly_demo and style == "ft":
        base_gallery_stems.add("plotly_gdp_bar")

    gallery_stems = {f"{stem_prefix}_{name}" for name in base_gallery_stems}

    def output_stem(name: str) -> str:
        return f"{stem_prefix}_{name}"

    def gallery_stem(path: Path) -> str:
        if path.name.endswith(".caption.md"):
            return path.name.removesuffix(".caption.md")
        return path.stem

    output_path.mkdir(parents=True, exist_ok=True)
    stale_pattern = "validation_*" if style == "fins" else "ft_validation_*"
    for stale_path in output_path.glob(stale_pattern):
        if stale_path.name == docx_name:
            continue
        if stale_path.suffix == ".docx" or gallery_stem(stale_path) not in gallery_stems:
            stale_path.unlink(missing_ok=True)

    generated: list[Path] = []
    docx_entries: list[WordFigureEntry] = []
    notes: list[str] = []

    def emit(
        fig: object,
        stem: str,
        context: FigureContext,
        *,
        spec: str = "full_width",
        pdf: bool = True,
        unique_series_colors: int | None = None,
    ) -> None:
        bundle = export_word_figure(fig, output_path, stem, context=context, spec=spec)
        if pdf:
            bundle.update(export_figure_bundle(fig, output_path, stem, formats=("pdf",)))
        issues = validate_image_not_blank(bundle["png"])
        if issues:
            details = "; ".join(issue.message for issue in issues)
            raise WorkflowError(f"generated figure failed image validation: {stem}: {details}")
        rendered_issues = []
        for axis in getattr(fig, "axes", []):
            rendered_issues.extend(validate_display_labels(axis))
            rendered_issues.extend(validate_markers_within_axes(axis))
            rendered_issues.extend(validate_no_text_overlap(axis))
            rendered_issues.extend(validate_no_tick_label_overlap(axis))
            rendered_issues.extend(validate_no_tick_label_overlap(axis, axis="y"))
            rendered_issues.extend(validate_category_label_count(axis))
            rendered_issues.extend(validate_category_label_count(axis, axis="y"))
            rendered_issues.extend(validate_series_identification(axis))
            if unique_series_colors is not None:
                rendered_issues.extend(
                    validate_unique_series_colors(axis, minimum=unique_series_colors)
                )
        if rendered_issues:
            details = "; ".join(issue.message for issue in rendered_issues)
            raise WorkflowError(f"generated figure failed rendered validation: {stem}: {details}")
        generated.extend(bundle.values())
        if docx:
            docx_entries.append(WordFigureEntry(bundle["png"], context=context, spec=spec))

    ff3 = load_validation_dataset("ff3_monthly")
    ff25 = load_validation_dataset("ff25_size_value_monthly")
    industries = load_validation_dataset("ff_industry_10_monthly")
    macro = load_validation_dataset("fred_macro_monthly")
    rates = load_validation_dataset("fred_rates_daily")
    stress = load_validation_dataset("fred_financial_stress_daily")
    shiller = load_validation_dataset("shiller_market_monthly")
    gdp_panel = load_validation_dataset("world_bank_country_panel_annual")
    gdp = load_validation_dataset("world_bank_gdp_annual") if style == "ft" else None
    plot_kwargs = {"profile": "word_a4", "style": style, "ft_background": ft_background}

    context = FigureContext(
        title="Full-Sample Fama/French Factor Returns",
        note=(
            "Monthly market, size, and value factor returns over the full available"
            " sample. Gray bands denote NBER recessions."
        ),
        source=ff3.source,
        sample=dataset_sample_label(ff3.data.index),
        units="Monthly return (%)",
    )
    fig, _ = time_series_plot(
        ff3.data,
        ["Mkt-RF", "SMB", "HML"],
        title=context.title,
        ylabel="Monthly return (%)",
        **plot_kwargs,
    )
    emit(fig, output_stem("ff3_full_returns"), context)
    plt.close(fig)

    context = FigureContext(
        title="Full-Sample Fama/French Growth Of One Dollar",
        note=(
            "Growth of one dollar from monthly market, size, and value factor"
            " returns, shown on a log scale so all factors remain inspectable."
        ),
        source=ff3.source,
        sample=dataset_sample_label(ff3.data.index),
        units="Growth of one dollar, log scale",
    )
    fig, _ = cumulative_returns_plot(
        ff3.data,
        ["Mkt-RF", "SMB", "HML"],
        returns_are_percent=True,
        wealth_index=True,
        log_scale=True,
        title=context.title,
        **plot_kwargs,
    )
    emit(fig, output_stem("ff3_full_cumulative"), context)
    plt.close(fig)

    context = FigureContext(
        title="Cumulative Market Excess Return",
        note=(
            "Growth of one dollar from monthly Fama/French market excess returns,"
            " shown on a log scale with dollar values on the y-axis."
        ),
        source=ff3.source,
        sample=dataset_sample_label(ff3.data.index),
        units="Growth of one dollar, log scale",
    )
    fig, _ = cumulative_returns_plot(
        ff3.data,
        "Mkt-RF",
        returns_are_percent=True,
        wealth_index=True,
        log_scale=True,
        title=context.title,
        **plot_kwargs,
    )
    emit(fig, output_stem("market_cumulative"), context)
    plt.close(fig)

    context = FigureContext(
        title="Indexed Macro Activity Series",
        note=(
            "Industrial production, payroll employment, and CPI are indexed to each"
            " series' first non-missing observation so different units can be compared."
        ),
        source=macro.source,
        sample=dataset_sample_label(macro.data.index),
        units="Index, first observation = 100",
    )
    fig, _ = indexed_time_series_plot(
        macro.data,
        ["INDPRO", "PAYEMS", "CPIAUCSL"],
        title=context.title,
        ylabel="Index",
        **plot_kwargs,
    )
    emit(fig, output_stem("macro_indexed"), context)
    plt.close(fig)

    context = FigureContext(
        title="Treasury Rates Across Maturities",
        note=(
            "Daily 10-year, 2-year, and 3-month Treasury rates. Missing early"
            " observations are trimmed only when all requested series are missing."
        ),
        source=rates.source,
        sample=dataset_sample_label(rates.data.index),
        units="Percent",
    )
    fig, _ = time_series_plot(
        rates.data,
        ["DGS10", "DGS2", "DTB3"],
        title=context.title,
        ylabel="Percent",
        **plot_kwargs,
    )
    emit(fig, output_stem("treasury_rates"), context)
    plt.close(fig)

    context = FigureContext(
        title="Yield-Curve Spread Validation Series",
        note=(
            "Daily 10-year minus 2-year and 10-year minus 3-month Treasury spreads."
            " The zero line helps identify inversions."
        ),
        source=rates.source,
        sample=dataset_sample_label(rates.data.index),
        units="Percentage points",
    )
    fig, ax = time_series_plot(
        rates.data,
        ["T10Y2Y", "T10Y3M"],
        title=context.title,
        ylabel="Percentage points",
        **plot_kwargs,
    )
    ax.axhline(0, color="#111827", linewidth=0.8)
    emit(fig, output_stem("yield_spreads"), context)
    plt.close(fig)

    context = FigureContext(
        title="Shiller Real Market Fundamentals",
        note=(
            "Inflation-adjusted price, dividend, and earnings series indexed to the"
            " first non-missing observation in Robert Shiller's long market dataset."
        ),
        source=shiller.source,
        sample=dataset_sample_label(shiller.data.index),
        units="Index, first observation = 100",
    )
    fig, _ = indexed_time_series_plot(
        shiller.data,
        ["real_price", "real_dividend", "real_earnings"],
        title=context.title,
        ylabel="Index",
        **plot_kwargs,
    )
    emit(fig, output_stem("shiller_real_market"), context)
    plt.close(fig)

    context = FigureContext(
        title="Shiller CAPE Ratio",
        note="Cyclically adjusted price-earnings ratio from the long Shiller workbook.",
        source=shiller.source,
        sample=dataset_sample_label(shiller.data["cape"].dropna().index),
        units="Price divided by 10-year average real earnings",
    )
    fig, _ = time_series_plot(
        shiller.data,
        "cape",
        title=context.title,
        ylabel="CAPE",
        **plot_kwargs,
    )
    emit(fig, output_stem("shiller_cape"), context)
    plt.close(fig)

    context = FigureContext(
        title="Mean Industry Returns With Standard Errors",
        note=(
            "Mean monthly returns across 10 industry portfolios. Error bars are"
            " standard errors of the monthly mean."
        ),
        source=industries.source,
        sample=dataset_sample_label(industries.data.index),
        units="Mean monthly return (%)",
    )
    fig, _, _ = mean_return_bar_plot(
        industries.data,
        industries.data.columns,
        title=context.title,
        ylabel="Mean monthly return (%)",
        error="se",
        **plot_kwargs,
    )
    emit(fig, output_stem("industry_mean_returns"), context)
    plt.close(fig)

    context = FigureContext(
        title="Fama/French Factor Return Composition",
        note=(
            "Stacked monthly returns for the market, size, and value factors over"
            " the latest 24 months. Positive and negative values are stacked separately."
        ),
        source=ff3.source,
        sample=dataset_sample_label(ff3.data.tail(24).index),
        units="Monthly return (%)",
    )
    fig, _ = stacked_bar_plot(
        ff3.data,
        ["Mkt-RF", "SMB", "HML"],
        title=context.title,
        ylabel="Monthly return (%)",
        max_bars=24,
        **plot_kwargs,
    )
    emit(fig, output_stem("factor_stacked_returns"), context)
    plt.close(fig)

    scatter_frame = macro.data[["FEDFUNDS", "UNRATE"]].dropna()
    context = FigureContext(
        title="Federal Funds Rate And Unemployment",
        note=(
            "Scatter plot with fitted line, slope, R-squared, sample size, and"
            " labels for the most unusual months."
        ),
        source=macro.source,
        sample=dataset_sample_label(scatter_frame.index),
        units="Percent",
    )
    fig, _ = scatter_plot(
        scatter_frame,
        "FEDFUNDS",
        "UNRATE",
        fit=True,
        label_outliers=4,
        stats_location="lower right",
        title=context.title,
        xlabel="Federal funds rate (%)",
        ylabel="Unemployment rate (%)",
        **plot_kwargs,
    )
    emit(fig, output_stem("macro_scatter_fit"), context)
    plt.close(fig)

    context = FigureContext(
        title="Distribution Of Market Excess Returns",
        note="Histogram and kernel density estimate for monthly market excess returns.",
        source=ff3.source,
        sample=dataset_sample_label(ff3.data.index),
        units="Monthly return (%)",
    )
    fig, _ = distribution_plot(
        ff3.data.reset_index(),
        "Mkt-RF",
        title=context.title,
        **plot_kwargs,
    )
    emit(fig, output_stem("market_return_distribution"), context)
    plt.close(fig)

    context = FigureContext(
        title="Industry Return Correlations",
        note="Pairwise correlations across monthly 10-industry portfolio returns.",
        source=industries.source,
        sample=dataset_sample_label(industries.data.index),
        units="Correlation",
    )
    fig, _ = correlation_heatmap(industries.data, title=context.title, **plot_kwargs)
    emit(fig, output_stem("industry_correlations"), context, spec="two_panel")
    plt.close(fig)

    context = FigureContext(
        title="Selected Industry Return Small Multiples",
        note=(
            "Small-multiple time-series view for four industry portfolios. Each"
            " panel uses the same reusable time-series styling rules."
        ),
        source=industries.source,
        sample=dataset_sample_label(industries.data.index),
        units="Monthly return (%)",
    )
    fig, _ = small_multiples(
        industries.data,
        ["NoDur", "Durbl", "HiTec", "Utils"],
        title=context.title,
        ylabel="Return (%)",
        **plot_kwargs,
    )
    emit(fig, output_stem("industry_small_multiples"), context, spec="two_panel")
    plt.close(fig)

    ff25_size_labels = ["Small", "2", "3", "4", "Big"]
    ff25_value_labels = ["Low BM", "2", "3", "4", "High BM"]
    ff25_records = []
    ff25_long_parts = []
    for position, column in enumerate(ff25.data.columns):
        size_label = ff25_size_labels[position // 5]
        value_label = ff25_value_labels[position % 5]
        ff25_records.append(
            {
                "size": size_label,
                "value": value_label,
                "mean_return": float(ff25.data[column].mean()),
            }
        )
        long_part = ff25.data[column].rename("return").reset_index()
        long_part["size"] = size_label
        long_part["value"] = value_label
        long_part["portfolio"] = str(column)
        ff25_long_parts.append(long_part)
    ff25_mean_frame = pd.DataFrame.from_records(ff25_records)
    ff25_long_frame = pd.concat(ff25_long_parts, ignore_index=True)

    context = FigureContext(
        title="Average Returns Across Size-Value Portfolios",
        note=(
            "Heatmap of average monthly returns for the 25 Fama/French portfolios"
            " formed on size and book-to-market."
        ),
        source=ff25.source,
        sample=dataset_sample_label(ff25.data.index),
        units="Mean monthly return (%)",
    )
    fig, _ = value_heatmap(
        ff25_mean_frame,
        "size",
        "value",
        "mean_return",
        title=context.title,
        cbar_label="Mean monthly return (%)",
        fmt=".2f",
        **plot_kwargs,
    )
    emit(fig, output_stem("ff25_mean_heatmap"), context, spec="two_panel")
    plt.close(fig)

    context = FigureContext(
        title="Return Distributions By Value Quintile",
        note=(
            "Distribution comparison for Fama/French 25 portfolios grouped by"
            " book-to-market quintile."
        ),
        source=ff25.source,
        sample=dataset_sample_label(ff25.data.index),
        units="Monthly return (%)",
    )
    fig, _ = distribution_comparison_plot(
        ff25_long_frame,
        "return",
        "value",
        title=context.title,
        ylabel="Monthly return (%)",
        kind="box",
        order=ff25_value_labels,
        **plot_kwargs,
    )
    emit(fig, output_stem("ff25_distribution_by_value"), context)
    plt.close(fig)

    industry_excess = (
        industries.data.mean()
        .sub(float(ff3.data["Mkt-RF"].mean()))
        .rename("excess_mean")
        .reset_index()
        .rename(columns={"index": "industry"})
    )
    context = FigureContext(
        title="Industry Mean Returns Relative To The Market",
        note=(
            "Diverging bar chart of average industry returns relative to the"
            " average Fama/French market excess return."
        ),
        source=f"{industries.source}; {ff3.source}",
        sample=dataset_sample_label(industries.data.index),
        units="Monthly return spread (%)",
    )
    fig, _ = diverging_bar_plot(
        industry_excess,
        "industry",
        "excess_mean",
        title=context.title,
        xlabel="Mean return spread versus market (%)",
        **plot_kwargs,
    )
    emit(fig, output_stem("industry_excess_diverging"), context)
    plt.close(fig)

    context = FigureContext(
        title="Cumulative Distribution Of Selected Industry Returns",
        note=(
            "Empirical cumulative distribution curves for selected monthly"
            " industry portfolio returns."
        ),
        source=industries.source,
        sample=dataset_sample_label(industries.data.index),
        units="Monthly return (%)",
    )
    fig, _ = ecdf_plot(
        industries.data,
        ["NoDur", "HiTec", "Enrgy"],
        title=context.title,
        xlabel="Monthly return (%)",
        **plot_kwargs,
    )
    emit(fig, output_stem("industry_ecdf"), context)
    plt.close(fig)

    gdp_panel_frame = gdp_panel.data.reset_index()
    gdp_panel_frame["year"] = gdp_panel_frame["date"].dt.year
    latest_panel = gdp_panel_frame[gdp_panel_frame["year"] == 2024].copy()

    gdp_per_capita = (
        gdp_panel_frame[gdp_panel_frame["year"].isin([2010, 2024])]
        .pivot(index="country", columns="year", values="gdp_per_capita_usd")
        .reset_index()
        .rename(columns={2010: "gdp_pc_2010", 2024: "gdp_pc_2024"})
    )
    context = FigureContext(
        title="GDP Per Capita Change Across Major Economies",
        note="Dumbbell chart comparing GDP per capita in 2010 and 2024.",
        source=gdp_panel.source,
        sample="2010 to 2024",
        units="Current U.S. dollars per person",
    )
    fig, _ = dumbbell_plot(
        gdp_per_capita,
        "country",
        "gdp_pc_2010",
        "gdp_pc_2024",
        title=context.title,
        xlabel="GDP per capita (current U.S. dollars)",
        start_label="2010",
        end_label="2024",
        limit=8,
        **plot_kwargs,
    )
    emit(fig, output_stem("world_bank_gdp_per_capita_dumbbell"), context)
    plt.close(fig)

    top_share_countries = (
        latest_panel.sort_values("gdp_current_usd", ascending=False)
        .head(6)["country"]
        .tolist()
    )
    share_frame = gdp_panel_frame[
        gdp_panel_frame["year"].isin([2010, 2024])
        & gdp_panel_frame["country"].isin(top_share_countries)
    ].copy()
    context = FigureContext(
        title="GDP Share Among Major Economies",
        note=(
            "Proportional stacked bars compare country shares among the six largest"
            " economies in the validation panel."
        ),
        source=gdp_panel.source,
        sample="2010 and 2024",
        units="Share of GDP among selected economies",
    )
    fig, _ = proportional_stacked_bar_plot(
        share_frame,
        "year",
        "country",
        "gdp_current_usd",
        title=context.title,
        ylabel="Share of selected-economy GDP",
        **plot_kwargs,
    )
    emit(fig, output_stem("world_bank_gdp_share_stacked"), context)
    plt.close(fig)

    context = FigureContext(
        title="Population, Income, And GDP Scale",
        note=(
            "Bubble scatterplot using population on the x-axis, GDP per capita on"
            " the y-axis, and total GDP as bubble size. Labels identify the largest"
            " economies by total GDP in the plotted year."
        ),
        source=gdp_panel.source,
        sample="2024",
        units="Population, GDP per capita, and GDP",
    )
    fig, _ = bubble_scatter_plot(
        latest_panel,
        "population_millions",
        "gdp_per_capita_usd",
        "gdp_trillions_usd",
        label="country",
        label_top=4,
        title=context.title,
        xlabel="Population (millions)",
        ylabel="GDP per capita (current U.S. dollars)",
        size_label="GDP (trillions of current U.S. dollars)",
        **plot_kwargs,
    )
    emit(fig, output_stem("world_bank_bubble"), context)
    plt.close(fig)

    stress_frame = stress.data.dropna(how="all")
    context = FigureContext(
        title="Daily VIX Calendar Heatmap During 2020",
        note="Calendar heatmap showing daily VIX levels during the 2020 stress episode.",
        source=stress.source,
        sample="2020",
        units="VIX index",
    )
    fig, _ = calendar_heatmap(
        stress_frame,
        "VIXCLS",
        year=2020,
        title=context.title,
        cbar_label="VIX index",
        **plot_kwargs,
    )
    emit(fig, output_stem("stress_calendar_heatmap"), context, spec="two_panel")
    plt.close(fig)

    context = FigureContext(
        title="Rolling Financial Stress Volatility",
        note="Rolling 21-trading-day volatility of daily VIX levels.",
        source=stress.source,
        sample=dataset_sample_label(stress_frame["VIXCLS"].dropna().index),
        units="VIX index points",
    )
    fig, _ = rolling_stat_plot(
        stress_frame,
        "VIXCLS",
        window=21,
        statistic="volatility",
        title=context.title,
        ylabel="21-day rolling standard deviation",
        **plot_kwargs,
    )
    emit(fig, output_stem("stress_rolling"), context)
    plt.close(fig)

    vix = stress_frame["VIXCLS"].dropna()
    rolling_mean = vix.rolling(window=63, min_periods=21).mean()
    rolling_std = vix.rolling(window=63, min_periods=21).std()
    band_frame = pd.DataFrame(
        {
            "rolling_mean": rolling_mean,
            "lower": (rolling_mean - rolling_std).clip(lower=0),
            "upper": rolling_mean + rolling_std,
        }
    ).dropna()
    context = FigureContext(
        title="VIX Rolling Mean With Uncertainty Band",
        note=(
            "Rolling 63-trading-day mean with a one-standard-deviation band,"
            " using daily VIX observations."
        ),
        source=stress.source,
        sample=dataset_sample_label(band_frame.index),
        units="VIX index",
    )
    fig, _ = uncertainty_band_plot(
        band_frame,
        "rolling_mean",
        "lower",
        "upper",
        title=context.title,
        ylabel="VIX index",
        **plot_kwargs,
    )
    emit(fig, output_stem("stress_uncertainty_band"), context)
    plt.close(fig)

    if style == "ft" and gdp is not None:
        gdp_frame = gdp.data.reset_index()
        gdp_frame["year"] = gdp_frame["date"].dt.year
        latest_gdp = gdp_frame[gdp_frame["year"] == 2024].copy()

        context = FigureContext(
            title="Largest Economies In Current U.S. Dollars",
            note=(
                "Ranked lollipop chart using World Bank annual GDP data. The United"
                " States, China, and India are highlighted; other economies are muted"
                " comparison points."
            ),
            source=gdp.source,
            sample="2024",
            units="Trillions of current U.S. dollars",
        )
        fig, _ = lollipop_plot(
            latest_gdp,
            "country",
            "gdp_trillions_usd",
            title=context.title,
            xlabel="GDP (trillions of current U.S. dollars)",
            ylabel="Country",
            limit=10,
            highlight=["United States", "China", "India"],
            **plot_kwargs,
        )
        emit(fig, output_stem("world_bank_gdp_lollipop"), context)
        plt.close(fig)

        slope_frame = (
            gdp_frame.pivot(index="country", columns="year", values="gdp_trillions_usd")
            .reset_index()
            .rename(columns={2010: "gdp_2010", 2024: "gdp_2024"})
        )
        context = FigureContext(
            title="GDP Rankings Shifted Over The 2010s And 2020s",
            note=(
                "Slope chart comparing 2010 and 2024 GDP for the eight largest"
                " economies in the validation fixture by 2024 GDP."
            ),
            source=gdp.source,
            sample="2010 to 2024",
            units="Trillions of current U.S. dollars",
        )
        fig, _ = slope_chart(
            slope_frame,
            "country",
            "gdp_2010",
            "gdp_2024",
            title=context.title,
            ylabel="GDP (trillions of current U.S. dollars)",
            start_label="2010",
            end_label="2024",
            limit=8,
            **plot_kwargs,
        )
        emit(
            fig,
            output_stem("world_bank_gdp_slope"),
            context,
            spec="portrait_tall",
            unique_series_colors=8,
        )
        plt.close(fig)

        policy_frame = macro.data[["FEDFUNDS", "UNRATE"]].dropna().loc["2007":"2012"]
        context = FigureContext(
            title="Policy Rates And Unemployment During The Financial Crisis",
            note=(
                "Monthly time-series view of the federal funds rate and unemployment"
                " during and after the 2007-2009 financial crisis. Gray bands denote"
                " NBER recessions."
            ),
            source=macro.source,
            sample=dataset_sample_label(policy_frame.index),
            units="Percent",
        )
        fig, _ = time_series_plot(
            policy_frame,
            ["FEDFUNDS", "UNRATE"],
            title=context.title,
            ylabel="Percent",
            **plot_kwargs,
        )
        emit(fig, output_stem("macro_policy_episode"), context)
        plt.close(fig)

        spread_frame = rates.data[["T10Y2Y"]].dropna()
        context = FigureContext(
            title="Yield-Curve Inversions Against Zero",
            note=(
                "Deviation-style area chart for the 10-year minus 2-year Treasury"
                " spread. Values below zero indicate inversions."
            ),
            source=rates.source,
            sample=dataset_sample_label(spread_frame.index),
            units="Percentage points",
        )
        fig, _ = area_balance_plot(
            spread_frame,
            "T10Y2Y",
            title=context.title,
            ylabel="Percentage points",
            **plot_kwargs,
        )
        emit(fig, output_stem("yield_spread_deviation"), context)
        plt.close(fig)

        if plotly_demo:
            context = FigureContext(
                title="Plotly FT-Style GDP Bar Demo",
                note=(
                    "Optional Plotly export example using the same World Bank GDP"
                    " fixture. This is skipped when Plotly, Kaleido, or Chrome is"
                    " unavailable."
                ),
                source=gdp.source,
                sample="2024",
                units="Trillions of current U.S. dollars",
            )
            try:
                import plotly.express as px

                from fintools.figures import apply_ft_plotly_layout, export_plotly_image

                plotly_frame = latest_gdp.sort_values(
                    "gdp_trillions_usd",
                    ascending=False,
                ).head(8)
                plotly_fig = px.bar(
                    plotly_frame,
                    x="country",
                    y="gdp_trillions_usd",
                    color="country",
                    labels={"gdp_trillions_usd": "GDP, current US$ trillions"},
                )
                apply_ft_plotly_layout(
                    plotly_fig,
                    title=context.title,
                    ft_background=ft_background,
                    showlegend=False,
                )
                plotly_path = export_plotly_image(
                    plotly_fig,
                    output_path / f"{output_stem('plotly_gdp_bar')}.png",
                )
                issues = validate_image_not_blank(plotly_path)
                if issues:
                    details = "; ".join(issue.message for issue in issues)
                    raise WorkflowError(
                        f"generated Plotly figure failed image validation: {details}"
                    )
                generated.append(plotly_path)
                if docx:
                    docx_entries.append(WordFigureEntry(plotly_path, context=context))
            except Exception as exc:
                notes.append(f"Skipped optional Plotly demo: {exc}")

    if docx:
        docx_path = insert_figures_docx(
            docx_entries,
            output_path / docx_name,
            title=docx_title,
        )
        issues = validate_docx_images_fit_page(docx_path)
        if issues:
            details = "; ".join(issue.message for issue in issues)
            raise WorkflowError(f"generated Word proof pack failed validation: {details}")
        generated.append(docx_path)

    lines = [f"Generated {style} validation figures in: {output_path.relative_to(root)}"]
    lines.extend(notes)
    lines.append("Files:")
    lines.extend(f"- {path.relative_to(root)}" for path in generated)
    return 0, lines


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate validation figures with the public fintools toolkit.",
    )
    parser.add_argument("--output", default="results/figures")
    parser.add_argument("--docx", action="store_true")
    parser.add_argument("--style", choices=["fins", "ft"], default="ft")
    parser.add_argument("--ft-background", action="store_true")
    parser.add_argument("--plotly-demo", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the gallery generator."""

    args = parse_args(argv)
    root = repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        status, lines = build_figure_examples(
            root,
            root,
            output=args.output,
            docx=args.docx,
            style=args.style,
            ft_background=args.ft_background,
            plotly_demo=args.plotly_demo,
        )
    except FigureExampleError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
