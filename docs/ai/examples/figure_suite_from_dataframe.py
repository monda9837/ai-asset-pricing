"""PyCharm-friendly example for generating an FT-style figure suite.

Use this after you already have a pandas dataframe named ``df``. In PyCharm,
paste the relevant block into your script or Python console and change only the
output folder, source, or title prefix as needed.
"""

from __future__ import annotations

from fintools.figures import create_figure_suite, plan_figure_suite, profile_dataframe


def make_ft_figure_suite_from_dataframe(df):
    """Create a validated FT-style figure suite from a pandas dataframe."""

    profile = profile_dataframe(df)
    plan = plan_figure_suite(df, title_prefix="My Dataset", max_figures=8, narrative=True)
    print(profile)
    print("Planned figures:")
    for item in plan:
        print(f"- {item.kind}: {item.title}")

    result = create_figure_suite(
        df,
        output="results/figures",
        style="ft",
        docx=True,
        source="",
        title_prefix="My Dataset",
        max_figures=8,
        narrative=True,
    )

    print("Generated files:")
    for path in result.generated_paths:
        print(path)
    if result.skipped:
        print("Skipped figures:")
        for message in result.skipped:
            print(f"- {message}")
    return result


# Example use inside PyCharm after creating a dataframe:
# result = make_ft_figure_suite_from_dataframe(df)
