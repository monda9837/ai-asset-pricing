## Project Scope

This is a broad **empirical asset pricing** research environment. Work includes but is not limited to: constructing and testing cross-sectional factors, building stock/bond/option panels, running regressions (Fama-MacBeth, panel, IV), event studies, risk model estimation, portfolio optimization, and any quantitative analysis using CRSP, Compustat, OptionMetrics, TAQ, or other financial data. Not all tasks involve portfolio sorts — treat every session as general empirical finance research.

## Local Environment

User-specific tool paths and WRDS credentials are in `CLAUDE.local.md` (local to each machine, never shared). New users should run `/onboard` to auto-discover their environment and create this file.

When running Python, psql, LaTeX, R, or other tools, check `CLAUDE.local.md` for the correct paths on this machine.

Never commit `CLAUDE.local.md` or `.claude/settings.local.json`. They are generated local state.

## Shared Python Package

Reusable Python code lives in the `fintools/` package at the project root. Install once:

```bash
<python-from-CLAUDE.local.md> -m pip install -e .
```

Import in any script: `from fintools import ...`

**Rules:**
- Import from `fintools` in scripts — never copy-paste utilities between projects.
- Add new modules and functions as needed. Keep functions stateless.

## PyBondLab

PyBondLab is a Numba-optimized package for constructing long-short factor portfolios from any panel data (bonds, equities). Source in `packages/PyBondLab/`. Install once:

```bash
cd packages/PyBondLab && <python-from-CLAUDE.local.md> -m pip install -e ".[performance]"
```

Import: `import PyBondLab as pbl`

**Rules:**
- PBL handles portfolio formation. WRDS agents handle data fetching. They are separate concerns.
- Bond data from `bonds-wrds-expert` needs column mapping: `fit(IDvar='cusip', RETvar='ret_vw', VWvar='mcap_e', RATINGvar='spc_rat')`. Cast `spc_rat` to float64 first.
- Equity data needs synthetic rating: `data['RATING_NUM'] = 1`, use `rating=None`.
- Docs: `packages/PyBondLab/docs/` (AI_GUIDE.md, HUMAN_GUIDE.md, API_REFERENCE.md)
- Examples: `packages/PyBondLab/examples/`

## WRDS Setup (one-time per user)

New users must configure these files before WRDS access works:

1. **`~/.pg_service.conf`** — PostgreSQL connection (host, port, database, user)
2. **`~/.pgpass`** — PostgreSQL password (chmod 600)
3. **`~/.ssh/config`** — SSH host alias for WRDS cloud:
   ```
   Host wrds
       HostName wrds-cloud-sshkey.wharton.upenn.edu
       User <your-wrds-username>
       IdentityFile ~/.ssh/wrds
       Port 22
   ```
4. **WRDS scratch symlink** — run once after SSH is configured:
   ```bash
   ssh wrds 'ln -sf /scratch/$(basename $(dirname $HOME))/$(whoami) ~/scratch'
   ```

## Data Output Conventions

All query results are saved under `data/` in a short, descriptive subfolder that includes the database name:

```
data/
  crsp_daily_jan24/
    data.parquet           ← query results (default format, snappy compression)
    metadata.json          ← query record: SQL, row count, date range, columns, timestamp
  optionm_spy_iv_2024/
    data.parquet
    metadata.json
```

**Rules:**
- **Default format is Parquet** (snappy compression). Never save as CSV unless the user explicitly asks.
- **Subfolder naming:** `{database}_{short_description}`, lowercase, underscores. Keep it short (2-4 words). Examples: `crsp_monthly_sp500`, `optionm_atm_iv`, `merged_crsp_compustat`.
- **Every extraction must produce a `metadata.json`** alongside the data file. This is the permanent record of what was fetched.

**metadata.json structure:**
```json
{
  "description": "Brief human-readable description of the data",
  "sql": "The exact SQL query that produced this data",
  "database": "crsp",
  "tables": ["crsp.dsf"],
  "columns": ["permno", "date", "ret", "prc"],
  "n_obs": 84,
  "date_range": ["2024-01-02", "2024-01-31"],
  "identifiers": {"permno": [10107, 14593, 84398, 93436]},
  "filters": "US common stocks, major exchanges",
  "fetched_at": "2026-03-07T10:30:00",
  "output_file": "data.parquet",
  "compression": "snappy"
}
```

Fields `description`, `sql`, `database`, `tables`, `columns`, `n_obs`, `fetched_at`, and `output_file` are required. All other fields are included when applicable.

**Bloat protection:** If an `identifiers` field (e.g., permno list, ticker list) would contain more than 50 entries, do NOT store the full list. Instead store a summary: `{"permno": {"count": 2847, "sample": [10107, 14593, 84398], "description": "all NYSE common stocks"}}`. This keeps metadata files small and readable.

## Skills & Rules

Skills are invoked with `/skill-name`. Auto-apply skills trigger automatically when their description matches the task. Rules auto-trigger on matching file paths.

### Data & WRDS (user-invocable)
- `/onboard` — Set up local environment, discover tools, create CLAUDE.local.md
- `/wrds-psql` — PostgreSQL query → Parquet pipeline with metadata.json
- `/wrds-schema` — Pre-load WRDS schema knowledge (dispatches specialist agents)
- `/wrds-ssh` — SSH to WRDS cloud, SAS job submission, file transfer

### Factor Construction (auto-apply)
- `factor-construction` — LAB prevention checklist, portfolio sorts, rebalancing conventions
- `panel-data-rules` — Safe lagging, gap checks, CCM linking, book equity, winsorization

### PyBondLab (user-invocable + auto-apply)
- `/run` — **Fast batch/single portfolio sort on bond data. No agent spawn.** E.g., `/run batch cs ytm bbtm`, `/run single cs --nport 10`
- `bond-data` — Dickerson bond dataset reference: WRDS↔PyBondLab column mapping, rating encoding, signal clusters (auto-apply)
- `pybondlab-report` — Results persistence after PyBondLab runs (auto-apply)
- `pybondlab` — PyBondLab API constraints, parameter gotchas, column mapping, fast path conditions (auto-apply rule)
- `pybondlab-timing` — Output indexing convention (returns at t+1, not formation date t) (auto-apply rule)
- `pybondlab-workflow` — Execution routing: `/run` for known workflows, orchestrator for novel ones (auto-apply rule)

### Figures (auto-apply)
- `publication-figures` — Matplotlib styling, Okabe-Ito palette, Newey-West bar charts, export settings (600 DPI PDF)

### Writing & LaTeX (user-invocable)
- `/write-section` — Write a paper section following academic writing rules
- `/style-check` — 13-category writing analysis (banned words, AI tells, passive voice, vague claims)
- `/proofread` — Mechanical error scan (typos, LaTeX formatting, spacing, equation punctuation)
- `/build-paper` — Compile LaTeX (pdflatex + bibtex cycle)
- `/build-deck` — Create Beamer presentations with the Rhetoric of Decks philosophy
- `/respond-to-referee` — Draft referee response letters (single-point or full-reply mode)
- `/latex-doctor` — Clean and fix .tex files (comments, markers, compilation)
- `/submission-prep` — Pre-submission checklist for JF/RFS/JFE

### Project Management (user-invocable)
- `/new-project` — Create `projects/<name>/` scaffold with README, CLAUDE.md, .gitignore
- `/create-skill` — Create or audit skills, auto-apply skills, and rules (`/create-skill audit all` for fleet audit)
- `/rule-create` — Create a new `.claude/rules/` file (guided workflow) or audit an existing rule (`/rule-create audit`)
- `/create-audit-agent` — Create new agents or audit existing ones in `.claude/agents/` (17-point checklist with PASS/WARN/FAIL)

### Rules (auto-trigger on `**/*.tex`, `**/*.bib`)
- `academic-writing` — 85+ banned words, AI-tell detection, Cochrane writing principles, referee reply guidelines
- `latex-conventions` — Figures, tables, equations, bibliography hygiene, section markers, cross-references
- `latex-citations` — Citation verification protocol (Perplexity-based, never cite from memory)
- `latex-compile` — Auto-compile after every `.tex` edit
- `presentation-rules` — Rhetoric of Decks framework, Beamer conventions, visual style

### Exemplars
- `cochrane_writing_tips.md` — John Cochrane's "Writing Tips for Ph.D. Students" (foundational reference)
- `agents_best_practices.md` — Subagent & agent team configuration reference (Anthropic docs)

Project-specific conventions (terminology, section keys, target journal) belong in each project's `CLAUDE.md`.

## Project Structure

Research projects live under `projects/`, each with a standard layout. Create new projects with `/new-project <name>`.

```
projects/<project_name>/
  README.md          ← purpose, data dependencies, status
  CLAUDE.md          ← project-level instructions for Claude
  latex/             ← LaTeX writeup
  code/              ← production code (clean, reusable)
  scripts/tests/     ← exploratory investigations, each in its own subfolder
    {test_name}/
      output/        ← figures, tables, logs from this test
  results/           ← publication-ready final outputs
    figures/
    tables/
  literature/        ← reference papers
  guidance/          ← methodology notes
  _misc/             ← catch-all
```

**Rules:**
- **Project naming:** lowercase, underscores, 2-50 chars, starts with a letter.
- **Data stays global.** Projects reference datasets in `data/` — never copy data into a project folder.
- **Test naming:** Each investigation gets `scripts/tests/{test_name}/` with an `output/` subfolder. Name descriptively — any empirical exercise: `summary_stats`, `fmb_regressions`, `event_study`, `data_quality_check`, etc.
- **Final outputs** go in `results/figures/` and `results/tables/`. LaTeX references these via relative paths.
- **Production code** in `code/`. Scripts import from `code/`, never the reverse.

## WRDS Database Access

**NEVER use SSH for database queries that psql can handle locally.** Use direct PostgreSQL connections via `psql service=wrds`. SSH is only for TAQ data (which requires SAS on WRDS cloud) and for managing files on the WRDS server.

**PostgreSQL connection:**
```bash
psql service=wrds
```

**Windows users:** libpq does not find `~/.pg_service.conf` automatically. Set the env var first:
```bash
export PGSERVICEFILE="$HOME/.pg_service.conf"
```
The onboard skill handles this — see `CLAUDE.local.md` for your platform-specific notes.

## Maintainer Release Check

Before publishing this folder, run:

```bash
<python> tools/release_preflight.py --strict
```

Fix every `FAIL` and `WARN` before pushing the shared tree.

**CRSP versions:** v1 is frozen (ends Dec 2024). Prefer v2 (`dsf_v2`, `msf_v2`) for new research. Key differences: v2 includes delisting returns in `mthret`/`dlyret`, SHROUT is actual shares (not thousands in v1).

**Compustat required filters:** Every `comp.funda`/`comp.fundq` query MUST include `indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'` to avoid duplicate gvkey-datadate rows.

**Standard access pattern** (CRSP, OptionMetrics, Compustat, etc.):
```bash
psql service=wrds -c "COPY (SELECT ... FROM schema.table WHERE ...) TO STDOUT WITH CSV HEADER" \
  | python -c "import sys,json,os,pandas as pd; ..."
```
This pipes query results directly into Python, which saves as Parquet + `metadata.json` in `data/{db}_{description}/`. See the `wrds-psql` skill for the full template. **Never save as CSV unless the user explicitly asks.**

**Exception — TAQ only:** NYSE TAQ data is too large for direct SQL. Use SSH + SAS on WRDS cloud for TAQ. Access: `ssh wrds`.

**TAQ workflow:**
1. **Always prototype first** — test SAS program on a small subset (one week) before submitting the full job.
2. **Mirror local directory structure on WRDS.** If SAS files live in `data/taq-iv/` locally, create `~/scratch/taq-iv/` on WRDS and upload there.
3. **Submit:** `scp data/taq-iv/prog.sas wrds:~/scratch/taq-iv/` then `ssh wrds 'qsas ~/scratch/taq-iv/prog.sas'`
4. **Logs go to `~/prog.log`** (home dir), not `/scratch/`. CSV output goes wherever the SAS program specifies.
5. **Monitor:** `ssh wrds 'qstat -u $(whoami)'`

**Never use the `wrds` Python library** — it has interactive prompts that don't work in non-interactive contexts. Use `psql` directly or `sqlalchemy`/`psycopg2` with the `.pgpass` credentials.

**Always delegate WRDS queries to specialist agents.** Never write WRDS SQL directly — the expert agents know the correct table names, schemas, and conventions.
- **Multi-schema or ambiguous requests** → use `wrds-query-orchestrator` first. It will coordinate the right specialists and compose merged queries. Use this when the prompt mentions multiple databases (e.g., CRSP + OptionMetrics), or when it's unclear which schema to query.
- **Single-schema requests** → delegate directly to the appropriate expert:
  - `crsp-wrds-expert` — CRSP returns, prices, adjustments, delisting, identifiers, CCM linking (PERMNO↔GVKEY), Compustat fundamentals
  - `jkp-wrds-expert` — JKP/Global Factor Data (`contrib.global_factor` — 443 pre-computed stock characteristics, 93 countries, pre-linked permno/gvkey)
  - `optionmetrics-wrds-expert` — option prices, IVs, Greeks, volatility surfaces
  - `taq-wrds-expert` — TAQ high-frequency trades, quotes, NBBO (SSH + SAS)
  - `bonds-wrds-expert` — corporate bond returns, spreads, duration, ratings, liquidity, factor betas (Dickerson cleaned TRACE data)
  - `ff-wrds-expert` — Fama-French 5 factors + momentum (daily and monthly)
- **Academic papers** → use `paper-reader` to read, summarize, or analyze PDFs of research papers in finance, economics, statistics, or econometrics
  - `pybondlab-expert` — PyBondLab API: parameter semantics, result types, strategy concepts, troubleshooting
  - `pybondlab-orchestrator` — Multi-step PyBondLab workflows: data onboarding → factor construction → batch analysis → results
  - `ff-pybondlab-expert` — Fama-French style factor construction with PyBondLab: custom breakpoints, annual rebalancing, independent sorts
- **Factor construction with PyBondLab** → use `pybondlab-orchestrator`. It coordinates data fetching (via WRDS agents) and PBL execution.
- **FF-style factors** → use `ff-pybondlab-expert` for methodology + `pybondlab-orchestrator` for execution.
- **PyBondLab API questions** → delegate to `pybondlab-expert` directly.
