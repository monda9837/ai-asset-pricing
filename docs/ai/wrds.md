# WRDS Workflow

Use direct PostgreSQL access for WRDS whenever possible.

## Command Rules

- Prefer `psql service=wrds` for CRSP, Compustat, OptionMetrics, Fama-French, and similar datasets.
- Use SSH/SAS only for TAQ or WRDS-server file operations.
- On Windows, respect the `PGSERVICEFILE` note from the local environment file.

## Output Contract

Every extraction should write:

- `data.parquet`
- `metadata.json`

under a short descriptive folder in `data/`.

`metadata.json` should include, at minimum:

- `description`
- `sql`
- `database`
- `tables`
- `columns`
- `n_obs`
- `fetched_at`
- `output_file`

If identifier lists would be large, store a summary rather than the full list.

## Deep References

For schema- or asset-specific work, use these `.claude/agents/` references:

- `crsp-wrds-expert.md`
- `optionmetrics-wrds-expert.md`
- `bonds-wrds-expert.md`
- `taq-wrds-expert.md`
- `ff-wrds-expert.md`
- `wrds-query-orchestrator.md`

These remain the detailed domain references until more knowledge is extracted into shared docs.

For implementation templates, the `.claude/skills/wrds-psql/SKILL.md` file
remains the best detailed reference for query-to-Parquet pipelines.
