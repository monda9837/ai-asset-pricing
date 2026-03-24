[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

# Empirical Finance with Claude Code and Codex

This repository supports both Claude Code and Codex for WRDS data work, PyBondLab workflows, and empirical finance research.

The shared design is:

- `AGENTS.md` is the Codex-native routing layer
- `CLAUDE.md` plus `.claude/` are the Claude-native adapters
- `docs/ai/` is the shared source of truth for repo-wide AI guidance

## What's Included

```text
AGENTS.md                              # Codex routing and repo rules
CLAUDE.md                              # Claude adapter and commands
.claude/                               # Claude-specific rules, skills, and agents
docs/ai/                               # Shared cross-tool context
tools/onboard_probe.py                 # Cross-platform environment probe
tools/bootstrap.py                    # Shared onboarding audit/apply engine plus repair fallback
tools/onboarding_smoke_test.py        # Temp-clone onboarding smoke test
tools/context_drift.py                 # Documentation drift detector
tools/release_preflight.py             # Release/readiness checker
fintools/                              # Shared Python utilities
packages/PyBondLab/                    # Portfolio construction package
```

## Prerequisites

- Claude Code with skill support, or Codex with repo-local `AGENTS.md`
- Bash on `PATH` for Claude hook automation and Claude Bash commands
- Windows users running Claude Code should install Git for Windows / Git Bash and ensure `bash` is on `PATH`
- A WRDS account for database access
- Internet access for first-run package installation

## Local Environment Contract

The canonical local state now lives **outside the repo** in a per-user OS-specific
directory reported by `tools/bootstrap.py audit`. This keeps shared
Dropbox/OneDrive working trees from syncing machine-specific paths across users.

Repo-root compatibility shims may still be generated when explicitly requested:

- `LOCAL_ENV.md`
- `CLAUDE.local.md`
- `.claude/settings.local.json`

If you use Claude Code, the repo's hook automation assumes `bash` is available.
The hook scripts no longer depend on `jq` or GNU `grep`.

Mode guidance:

- One clone/copy per user is fully supported.
- A shared Dropbox/OneDrive working tree is supported only when canonical local state stays external.
- Dropbox/OneDrive are not a replacement for Git conflict handling and are not safe for simultaneous edits to the same code/config files.

## First-Time Setup

### Claude Code users

Run `/onboard`. It is a thin wrapper over the shared `tools/bootstrap.py`
engine, which audits the machine state, emits the exact setup commands still
required on that machine, and writes canonical local state outside the repo.

### Codex users

Start from `AGENTS.md`, then follow `docs/ai/onboarding.md`. Codex should use
`tools/bootstrap.py audit`, execute the required commands from its
`bootstrap_plan`, run `tools/bootstrap.py apply`, then rerun
`tools/bootstrap.py audit`.

### Direct local-terminal fallback

If you are not using an agent runtime and want a best-effort convenience path,
you can also try:

```bash
<python> tools/bootstrap.py repair --write-canonical-state
```

On Windows, do not assume bare `python` is usable. If it resolves to the
Windows Store shim or the wrong interpreter, use the exact interpreter path
reported by `tools/bootstrap.py audit`.

### Manual WRDS files

If onboarding has not created them yet, you need:

1. `~/.pg_service.conf`
2. `~/.pgpass`
3. `~/.ssh/config` entry for `Host wrds` if you need SSH/TAQ workflows

Minimal `~/.pg_service.conf`:

```ini
[wrds]
host=wrds-pgdata.wharton.upenn.edu
port=9737
dbname=wrds
user=YOUR_WRDS_USERNAME
```

Minimal `~/.pgpass`:

```text
wrds-pgdata.wharton.upenn.edu:9737:wrds:YOUR_WRDS_USERNAME:YOUR_PASSWORD
```

Then set restrictive permissions:

```bash
chmod 600 ~/.pgpass
```

## Shared Rules

- Prefer direct PostgreSQL access with `psql service=wrds` when possible.
- Use SSH/SAS only for TAQ or remote file-management workflows.
- Save extracted data as Parquet plus `metadata.json` under `data/<source>_<description>/`.
- Keep machine-local state out of the shared tree.
- Keep project-specific conventions inside each project's own `CLAUDE.md`.

## Tool-Specific Entry Points

- Codex: `AGENTS.md`
- Claude Code: `CLAUDE.md`
- WRDS workflow: `docs/ai/wrds.md`
- PyBondLab workflow: `docs/ai/pybondlab.md`
- Writing and LaTeX workflow: `docs/ai/writing.md`

For deeper domain references, both tools can reuse the existing `.claude/agents/*.md`, `.claude/skills/*.md`, and `.claude/rules/*.md` files.

## Data and Reproducibility

This repo is designed for AI-assisted empirical finance research. Most data
workflows require a [WRDS](https://wrds-www.wharton.upenn.edu/) account.

**What works without WRDS:**
- All AI skills, rules, and agents (writing, auditing, LaTeX, project scaffolding)
- `fintools` package (rolling betas, panel lags) — pure Python, no data dependency
- `PyBondLab` package install and import — the API is functional without data
- LaTeX boilerplate and paper setup
- Basic test suite: `<python> -B -m pytest tests/ -v -p no:cacheprovider` (use the interpreter path from `tools/bootstrap.py audit`)

**What requires WRDS access:**
- Data extraction via `psql service=wrds` or SSH
- Running PyBondLab portfolio sorts on real bond data
- WRDS connectivity checks during `/onboard`

Extracted datasets are saved locally under `data/` as Parquet plus
`metadata.json` and are never committed.

## Maintainer Preflight

Before pushing shared changes, run:

```bash
<python> tools/release_preflight.py --strict
```

This should fail if the repo still contains local files, generated caches, onboarding drift, or a broken temp-clone onboarding smoke test.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
