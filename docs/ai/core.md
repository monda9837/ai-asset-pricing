# Shared AI Context Core

This repository supports empirical asset pricing workflows across WRDS data
extraction, PyBondLab factor construction, and academic writing.

## Operating Model

- Shared repo-wide AI guidance lives in `docs/ai/`.
- Claude Code uses `CLAUDE.md` and `.claude/`, but they should point back to this shared layer for repo-wide rules.
- Codex uses `AGENTS.md` plus these shared docs.

## Local State

These files are machine-local and must never be committed:

- `LOCAL_ENV.md` - canonical local environment note for both Codex and Claude
- `CLAUDE.local.md` - Claude compatibility mirror
- `.claude/settings.local.json` - Claude-only local permissions

## Project Structure

- `fintools/` - shared Python utilities used across research code
- `packages/PyBondLab/` - portfolio construction package
- `data/` - extracted datasets, always local/output state
- `.claude/` - Claude-specific adapters, rules, agents, and skills
- `tools/` - probe and release-preflight utilities

Research projects should live under `projects/<name>/` with production code,
tests/investigations, results, and writing artifacts separated cleanly.

## Shared Conventions

- Prefer Parquet plus `metadata.json` for extracted datasets.
- Use short lowercase data folder names such as `crsp_monthly_sp500`.
- Keep data global and project code local; do not copy datasets into project folders.
- Use `tools/release_preflight.py --strict` before publishing shared changes.
- When absolute paths matter, use the paths recorded in `LOCAL_ENV.md`.
