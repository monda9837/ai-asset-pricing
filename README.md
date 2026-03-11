# Empirical Finance with Claude Code

This project uses [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with specialized agents and skills for querying [WRDS](https://wrds-www.wharton.upenn.edu/) financial databases (CRSP, OptionMetrics, Compustat, TAQ) directly from your terminal.

The WRDS toolkit is based on [claude-wrds-public](https://github.com/piotrek-orlowski/claude-wrds-public).

## What's included (project-level, shared with all users)

```
CLAUDE.md                              # WRDS instructions for Claude
.claude/
  settings.json                        # Pre-approved WRDS command permissions
  agents/
    crsp-wrds-expert.md                # CRSP stock data + CCM + JKP factors
    optionmetrics-wrds-expert.md       # IvyDB options data specialist
    taq-wrds-expert.md                 # TAQ high-frequency data specialist
    bonds-wrds-expert.md               # Dickerson TRACE corporate bonds
    wrds-query-orchestrator.md         # Multi-database query coordinator
    paper-reader.md                    # Academic paper reader/summarizer
  skills/
    onboard/SKILL.md                   # Environment setup (run /onboard)
    wrds-psql/SKILL.md                 # psql connection patterns
    wrds-ssh/SKILL.md                  # SSH + SAS job submission
    wrds-schema/SKILL.md               # Schema pre-loader
    new-project/SKILL.md               # Project scaffolding (/new-project)
    create-skill/SKILL.md              # Skill creator (/create-skill)
```

All of this is **project-level configuration** — anyone who receives this folder (via Dropbox, Git, etc.) gets the full Claude Code WRDS setup automatically. No need to install anything into `~/.claude/`.

## Prerequisites

- Claude Code with skill support enabled
- A POSIX-capable shell for Claude Code Bash commands
- Windows users: Git for Windows / Git Bash is recommended
- A WRDS account for database access
- Internet access for first-run package installation

`/onboard` is the supported first-run path. It discovers a working Python interpreter, installs missing Python packages, checks for `psql`, validates WRDS config, and writes machine-local files that should never be committed:

- `CLAUDE.local.md`
- `.claude/settings.local.json`

## First-time setup (per user)

You need a [WRDS account](https://wrds-www.wharton.upenn.edu/register/) with SSH key access.

**Recommended:** Run `/onboard` in Claude Code. It is the only path that is expected to be shell-safe across machines, especially on Windows where bare `python` may resolve to a broken WindowsApps stub.

If you prefer manual setup, follow these steps:

### 1. PostgreSQL service file

Create `~/.pg_service.conf`:

```ini
[wrds]
host=wrds-pgdata.wharton.upenn.edu
port=9737
dbname=wrds
user=YOUR_WRDS_USERNAME
```

### 2. PostgreSQL password file

Create `~/.pgpass`:

```
wrds-pgdata.wharton.upenn.edu:9737:wrds:YOUR_WRDS_USERNAME:YOUR_PASSWORD
```

Then restrict permissions:

```bash
chmod 600 ~/.pgpass
```

### 3. SSH config

Add to `~/.ssh/config`:

```
Host wrds
    HostName wrds-cloud-sshkey.wharton.upenn.edu
    User YOUR_WRDS_USERNAME
    IdentityFile ~/.ssh/wrds
    Port 22
```

For SSH connection multiplexing (avoids repeated Duo MFA prompts):

```
Host wrds
    HostName wrds-cloud-sshkey.wharton.upenn.edu
    User YOUR_WRDS_USERNAME
    IdentityFile ~/.ssh/wrds
    Port 22
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 4h
```

Then: `mkdir -p ~/.ssh/sockets`

### 4. WRDS scratch symlink

Run once after SSH is working:

```bash
ssh wrds 'ln -sf /scratch/$(basename $(dirname $HOME))/$(whoami) ~/scratch'
```

### 5. Verify connectivity

```bash
# PostgreSQL
psql service=wrds -c "SELECT COUNT(*) FROM crsp.dsf LIMIT 1;"

# SSH
ssh wrds 'whoami'
```

### 6. (Optional) Local settings

If you need user-specific Claude Code permissions, create `.claude/settings.local.json` (this file is not shared):

```json
{
  "permissions": {
    "allow": [
      "Bash(gh:*)"
    ]
  }
}
```

## Maintainer Preflight

Before pushing this folder to GitHub, run the release checker with a real Python interpreter on your machine:

```bash
<python> tools/release_preflight.py --strict
```

The checker fails the release if the tree still contains machine-local files, generated caches, invalid shared JSON, or other clone-time hazards.

## Usage

Just ask Claude for WRDS data — it delegates to the right specialist automatically:

```
> Get me daily returns for AAPL and MSFT for 2024

> What's the ATM implied volatility for SPY options with 30-day maturity?

> Merge CRSP monthly returns with Compustat annual fundamentals for 2020-2024

> Compute 5-minute realized variance for AAPL from TAQ trade records

> Pull investment-grade bond spreads and returns for 2024
```

Pre-load schema knowledge at the start of a session:

```
> /wrds-schema crsp optionm
```

Create a new research project:

```
> /new-project momentum_replication
```

## Design: extensibility

- **Project-level config**: All shared agents, skills, and settings live inside the project directory. Anyone who gets this folder has the complete shared setup — no global installation needed.
- **User-specific credentials**: WRDS username/password stay in personal home directory files (`~/.pg_service.conf`, `~/.pgpass`, `~/.ssh/config`). No credentials are stored in the project.
- **Pre-approved permissions**: `settings.json` contains only shared-safe permissions. User-specific absolute tool paths are written to `.claude/settings.local.json` by `/onboard`.
- **Cross-platform**: `/onboard` supports Windows, macOS, and Linux, but Windows support assumes Claude Code can execute Bash commands via Git Bash or an equivalent POSIX shell.

**Dropbox users:** `CLAUDE.local.md` and `.claude/settings.local.json` are user-specific and generated by `/onboard`. If sharing this folder via Dropbox, each user should run `/onboard` on their machine to generate these files. They are local state and should not be committed.
