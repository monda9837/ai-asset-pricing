"""Coverage for documentation drift routing."""

from __future__ import annotations

from tools.context_drift import DRIFT_MAP


def test_figure_sources_are_mapped_to_figure_docs_and_agent_surfaces() -> None:
    pairs = set(DRIFT_MAP)

    for source in [
        "fintools/figures/**/*.py",
        "fintools/datasets/**/*.py",
        "fintools/datasets/validation/*",
        "tools/figure_examples.py",
        "tools/download_validation_data.py",
        ".claude/skills/publication-figures/SKILL.md",
    ]:
        assert (source, "docs/ai/figures.md") in pairs

    for target in [
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        "README.md",
        ".claude/skills/publication-figures/SKILL.md",
    ]:
        assert ("docs/ai/figures.md", target) in pairs
