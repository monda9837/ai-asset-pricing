# Empirical Finance Agent Guide

This repository is designed to work well with both Codex and Claude Code.

For Codex, this file is the primary routing layer. For Claude, the `.claude/`
surface remains active, but the shared source of truth for repo-wide behavior
should live in `docs/ai/`.

## Core Contract

- Read `docs/ai/core.md` before making cross-cutting repo decisions.
- When machine-specific paths or tools matter, read `LOCAL_ENV.md` if it exists.
- Treat `LOCAL_ENV.md` as the canonical local environment file.
- Treat `CLAUDE.local.md` as a Claude compatibility mirror, not the source of truth.
- Never commit `LOCAL_ENV.md`, `CLAUDE.local.md`, or `.claude/settings.local.json`.
- Run `tools/release_preflight.py --strict` before a shared release.

## Task Routing

- Setup, onboarding, tool paths, or first-run issues:
  - Read `docs/ai/onboarding.md`
  - Use `tools/bootstrap.py audit`
  - Execute the required commands from the audit report's `bootstrap_plan`
  - Use `tools/bootstrap.py apply`
  - Treat `tools/bootstrap.py repair --write-local-files` as a direct-terminal fallback, not the primary Codex path
  - Treat `tools/onboard_probe.py` as the shared probe implementation, not the user-facing entry point
  - Use `LOCAL_ENV.md` if present
- WRDS, data extraction, or query pipelines:
  - Read `docs/ai/wrds.md`
  - Then read the relevant `.claude/agents/*.md` file for deep domain detail
- PyBondLab package work:
  - Read `docs/ai/pybondlab.md`
  - Then read `packages/PyBondLab/AGENTS.md`
- Writing, LaTeX, referee responses, or decks:
  - Read `docs/ai/writing.md`
  - Then read the relevant `.claude/rules/*.md` or `.claude/skills/*.md`
- Editing `.claude/` files:
  - Keep `docs/ai/` authoritative for shared rules
  - Do not duplicate repo-wide guidance if a shared doc already covers it

## Repo Rules

- Use direct PostgreSQL access for WRDS whenever `psql` can handle the task.
- Use SSH/SAS only for TAQ or remote file-management workflows.
- Save extracted data under `data/<source>_<short_description>/` as Parquet plus `metadata.json`.
- Keep machine-local state out of the shared tree.
- Keep project-specific conventions inside each project's own `CLAUDE.md`.
