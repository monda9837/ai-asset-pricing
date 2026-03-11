---
name: onboard
description: "Set up a new user's local environment: discover Python and tool paths, install required Python packages, validate WRDS access, and create machine-local Claude files. Run once per machine or after environment changes."
argument-hint: "[wrds-username (optional)]"
---

# User Onboarding

Goal: a fresh clone should be able to run `/onboard` and end with a usable local environment plus two machine-local files:

- `CLAUDE.local.md`
- `.claude/settings.local.json`

This skill must be safe to re-run, must not assume repo-shared local state, and must not rely on bare `python` or `pip` on Windows.

## Hard Rules

- Print `Scanning your environment...` before discovery.
- Print `Testing WRDS connectivity...` before verification.
- Never assume bare `python` or bare `pip` are valid on Windows. Use the discovered absolute Python path and `"<python>" -m pip`.
- Never rely on shared plugin or MCP config. `/onboard` must work with only the shared `.claude/settings.json`.
- Preserve any existing non-Bash permissions in `.claude/settings.local.json`. Replace only `Bash(...)` entries with the canonical set.
- If an install path requires admin privileges or a missing package manager, stop and give exact instructions instead of half-configuring the machine.
- Treat SSH key setup as optional for basic PostgreSQL access. Missing SSH config/key should be reported, not silently ignored.
- On Windows, Bash support is required. If `uname` is unavailable or the shell is not POSIX-like, stop and tell the user to install Git for Windows / Git Bash and ensure Claude Code can run Bash commands.

## Phase 1: Discover

Run this Bash command first. Its only job is to find a working Python interpreter without touching the repo.

```bash
OS=$(uname -s 2>/dev/null || echo "unknown")
echo "PLATFORM=$OS"

PYTHON=""
if [[ "$OS" == MINGW* || "$OS" == MSYS* ]]; then
  for p in \
    "$HOME/anaconda3/python.exe" \
    "$HOME/miniforge3/python.exe" \
    "$HOME/miniconda3/python.exe" \
    "/c/ProgramData/anaconda3/python.exe" \
    "/c/ProgramData/miniconda3/python.exe"; do
    if [[ -x "$p" ]]; then
      PYTHON="$p"
      break
    fi
  done
  if [[ -z "$PYTHON" ]]; then
    for name in python3 python; do
      CAND=$(which "$name" 2>/dev/null)
      if [[ -n "$CAND" ]] && [[ "$CAND" != *"/WindowsApps/"* ]]; then
        "$CAND" --version >/dev/null 2>&1 && { PYTHON="$CAND"; break; }
      fi
    done
  fi
elif [[ "$OS" == "Darwin" ]]; then
  for p in \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    "$HOME/anaconda3/bin/python" \
    "$HOME/miniforge3/bin/python" \
    "$HOME/miniconda3/bin/python"; do
    if [[ -x "$p" ]]; then
      PYTHON="$p"
      break
    fi
  done
  if [[ -z "$PYTHON" ]]; then
    for name in python3 python; do
      CAND=$(which "$name" 2>/dev/null)
      [[ -n "$CAND" ]] && "$CAND" --version >/dev/null 2>&1 && { PYTHON="$CAND"; break; }
    done
  fi
else
  for name in python3 python; do
    CAND=$(which "$name" 2>/dev/null)
    [[ -n "$CAND" ]] && "$CAND" --version >/dev/null 2>&1 && { PYTHON="$CAND"; break; }
  done
fi

echo "PYTHON=$PYTHON"
[[ -n "$PYTHON" ]] && "$PYTHON" --version 2>&1 | head -1 || true
```

If Python is found, run the repo probe from the project root:

```bash
"<PYTHON>" tools/onboard_probe.py
```

Parse the JSON output and print a short discovery table covering:

- platform
- Python path and version
- `psql`
- `pdflatex`
- `R`
- `git`
- `gh`
- `ssh`
- required Python packages
- WRDS file status

## Phase 2: Fix Missing Components

Only fix what is missing. Before doing so, print a short itemized plan of the missing components and the actions you will take.

### If Python is missing

Ask the user once which distribution they want. Recommend Miniforge.

#### Miniforge (recommended)

Windows:

```bash
curl -L -o /tmp/Miniforge3.exe "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe"
start //wait "" /tmp/Miniforge3.exe /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=$(cygpath -w "$HOME/miniforge3")
```

macOS:

```bash
if [[ "$(uname -m)" == "arm64" ]]; then
  curl -L -o /tmp/Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
else
  curl -L -o /tmp/Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"
fi
bash /tmp/Miniforge3.sh -b -p "$HOME/miniforge3"
```

Linux:

```bash
curl -L -o /tmp/Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
bash /tmp/Miniforge3.sh -b -p "$HOME/miniforge3"
```

After installation, re-run Phase 1 discovery before continuing.

### If required Python packages are missing

Install them with the discovered interpreter:

```bash
"<PYTHON>" -m pip install pandas psycopg2-binary pyarrow numpy matplotlib statsmodels
```

### If the shared repo packages are not installed

Install from the project root using the discovered interpreter:

```bash
"<PYTHON>" -m pip install -e .
```

Then install PyBondLab:

```bash
cd packages/PyBondLab && "<PYTHON>" -m pip install -e ".[performance]"
```

### If `psql` is missing

Windows: install a user-local binary build into `$HOME/tools/pgsql`:

```bash
mkdir -p "$HOME/tools"
curl -L -o /tmp/postgresql.zip "https://get.enterprisedb.com/postgresql/postgresql-17.4-1-windows-x64-binaries.zip"
unzip -q /tmp/postgresql.zip -d "$HOME/tools"
```

macOS:

- If `brew` exists, ask once before running `brew install libpq`.
- If `brew` does not exist, stop and tell the user to install Homebrew first.

Linux:

- If `apt-get` exists, ask once before running `sudo apt-get install -y postgresql-client`.
- If `dnf` exists, ask once before running `sudo dnf install -y postgresql`.
- Otherwise stop and tell the user which package they need.

After installing `psql`, re-run the probe.

### If WRDS files are missing

Create or repair these files:

1. `~/.pg_service.conf`
2. `~/.pgpass`
3. `~/.ssh/config` entry for `Host wrds` (optional for basic PostgreSQL, required for SSH/TAQ)

Use the username from `$ARGUMENTS` if provided; otherwise ask once.
If `~/.pgpass` is missing, ask for the WRDS password and do not echo it back in prose.

`~/.pg_service.conf`

```ini
[wrds]
host=wrds-pgdata.wharton.upenn.edu
port=9737
dbname=wrds
user=THEIR_USERNAME
```

`~/.pgpass`

```text
wrds-pgdata.wharton.upenn.edu:9737:wrds:THEIR_USERNAME:THEIR_PASSWORD
```

Then:

```bash
chmod 600 ~/.pgpass
```

On Windows, also copy both files to `$APPDATA/postgresql/` as:

- `pg_service.conf`
- `pgpass.conf`

### Windows Bash setup

If `psql` is installed under `$HOME/tools/pgsql` and `.bashrc` does not already contain the required lines, append only the missing lines:

```bash
export PATH="$HOME/tools/pgsql/bin:$PATH"
export PGSERVICEFILE="$HOME/.pg_service.conf"
```

Do not duplicate lines on re-run.

### Optional tools

- Missing LaTeX: print install guidance only.
- Missing R: print install guidance only.
- Missing SSH key `~/.ssh/wrds`: report that SSH/TAQ workflows are not yet configured.

## Phase 3: Verify and Write Local Files

Print `Testing WRDS connectivity...` before running checks.

If `psql`, `~/.pg_service.conf`, and the Python interpreter are present, run:

### Test 1: basic connection

```bash
PGSERVICEFILE="<HOME>/.pg_service.conf" "<PSQL>" service=wrds -c "SELECT 1 AS connection_test;"
```

### Test 2: CRSP query

```bash
PGSERVICEFILE="<HOME>/.pg_service.conf" "<PSQL>" service=wrds -c "SELECT COUNT(*) FROM crsp.dsi WHERE date >= '2024-01-01';"
```

### Test 3: full pipeline

```bash
PGSERVICEFILE="<HOME>/.pg_service.conf" "<PSQL>" service=wrds -c "COPY (SELECT date, sprtrn FROM crsp.dsi WHERE date >= '2024-12-01' ORDER BY date LIMIT 5) TO STDOUT WITH CSV HEADER" | "<PYTHON>" -c "import sys,pandas as pd; df = pd.read_csv(sys.stdin); print(f'Pipeline OK: {len(df)} rows, columns: {list(df.columns)}')"
```

If one of these fails, explain exactly which prerequisite is still missing and stop pretending onboarding is complete.

### Write `CLAUDE.local.md`

Write it to the project root. Include:

- tool paths and versions
- WRDS status
- canonical command forms for this machine
- any platform-specific notes

Use this structure:

```markdown
# Local Environment

## Tool Paths
| Tool | Path | Version |
|------|------|---------|
| Python | <path> | <version> |
| psql | <path> | <version> |
| pdflatex | <path or not installed> | <version or blank> |
| R | <path or not installed> | <version or blank> |

## WRDS
- Username: <wrds_user or blank>
- pg_service.conf: OK / MISSING
- pgpass: OK / MISSING
- SSH config: OK / MISSING
- SSH key: OK / MISSING

## Canonical Commands
- Python: `<python_path>`
- pip: `<python_path> -m pip`
- psql: `PGSERVICEFILE="<home>/.pg_service.conf" <psql_path> service=wrds`

## Notes
- Platform: <platform>
- Shell: <shell>
- Re-run `/onboard` after major environment changes.
```

### Write `.claude/settings.local.json`

If the file already exists, preserve non-Bash entries and replace only the `Bash(...)` entries with the canonical set below.

Canonical Bash allow list:

```json
[
  "Bash(<python_path> *)",
  "Bash(<python_path> -m pip *)",
  "Bash(<psql_path> *)",
  "Bash(PGSERVICEFILE=* <psql_path> service=wrds*)"
]
```

Add entries only for tools that were actually found.

## Final Summary

End with a short table:

```text
## Onboarding Complete

| Component | Status |
|-----------|--------|
| Python | OK / FAIL |
| Repo packages | OK / FAIL |
| psql | OK / FAIL |
| WRDS connection | OK (3/3) / PARTIAL / FAIL |
| LaTeX | OK / Not installed |
| R | OK / Not installed |
| SSH key | OK / Not configured |
```

Then list the files written and any remaining manual steps.
