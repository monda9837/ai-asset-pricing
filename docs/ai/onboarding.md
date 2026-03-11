# Shared Onboarding

This repo has one repo-local onboarding engine for both Claude Code and Codex:
`tools/bootstrap.py`.

## Canonical Local File

Use `LOCAL_ENV.md` as the shared local environment note. It should contain:

- platform and shell
- Python path and version
- canonical `python -m pip` command
- `psql` path and version
- WRDS config status
- any platform-specific notes

`tools/bootstrap.py apply` writes or refreshes:

- `LOCAL_ENV.md`
- `CLAUDE.local.md`
- `.claude/settings.local.json`

`CLAUDE.local.md` may still exist, but only as a compatibility mirror for Claude.

## Shared Bootstrap Flow

1. Find a working Python interpreter.
2. Run `<python> tools/bootstrap.py audit`.
3. Execute the required shell-specific commands listed in the audit report's `bootstrap_plan`.
4. Run `<python> tools/bootstrap.py apply`.
5. Re-run `<python> tools/bootstrap.py audit`.
6. Treat `<python> tools/bootstrap.py repair --write-local-files` as an optional convenience for direct local terminals, not the primary agent path.

## Tool-Specific Entry Points

- Claude Code users: clone the repo, run `/onboard`, and let the skill wrap the shared bootstrap `audit` -> execute bootstrap plan -> `apply` -> `audit` flow.
- Codex users: clone the repo, ask Codex to set up the repo, and have it run the same shared bootstrap `audit` -> execute bootstrap plan -> `apply` -> `audit` flow.

## Underlying Probe

`tools/onboard_probe.py` is the reusable probe library and CLI used by
`tools/bootstrap.py`. It remains part of the contract, but it is not the
primary onboarding entry point.

## Bootstrap Plan Contract

`tools/bootstrap.py audit` is the source of truth for what still needs to run.
If the repo is not ready yet, the audit report should emit a `bootstrap_plan`
with exact PowerShell/native and Bash commands for:

- missing Python packages
- missing or external repo package installs
- refreshing `LOCAL_ENV.md`, `CLAUDE.local.md`, and `.claude/settings.local.json`
- rerunning the audit at the end

Agents should prefer executing those commands directly, because that allows the
agent runtime to request any needed approvals for package installation.

## Rules

- Never assume bare `python` or `pip` are safe on Windows.
- Prefer a discovered absolute Python path plus `-m pip`.
- If `LOCAL_ENV.md` is missing, create it before relying on machine-specific commands.
- Prefer `tools/bootstrap.py audit`, its emitted `bootstrap_plan`, and `tools/bootstrap.py apply` over ad hoc local file generation.
- Keep `tools/bootstrap.py repair --write-local-files` as a convenience fallback for unsandboxed local terminals.
- If WRDS access is missing, record the missing pieces explicitly instead of pretending onboarding is complete.
