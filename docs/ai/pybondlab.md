# PyBondLab Workflow

PyBondLab is the portfolio-formation engine in this repo. WRDS querying and
data cleaning stay outside the package unless an example explicitly needs them.

## Install and Environment

- Use the Python interpreter recorded in canonical local state from `tools/bootstrap.py audit`.
- Install repo utilities with `uv pip install --python <python> -e .` (or `python -m pip install -e .`)
- Install PyBondLab with `uv pip install --python <python> -e ".[performance]"` from `packages/PyBondLab/` (or `python -m pip install -e ".[performance]"`)

## Routing

- Package/API semantics -> `packages/PyBondLab/docs/API_REFERENCE.md`
- Methodology and workflow -> `packages/PyBondLab/docs/AI_GUIDE.md`
- User-facing narrative/examples -> `packages/PyBondLab/docs/HUMAN_GUIDE.md`
- Code changes inside the package -> `packages/PyBondLab/AGENTS.md`

## Repo Boundary

- Data fetching is not the package's job.
- Reuse package docs and baseline references before inventing new behavior.
- When a task mixes WRDS conventions and package behavior, read both this file and `docs/ai/wrds.md`.
