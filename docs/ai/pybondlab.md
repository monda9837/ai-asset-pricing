# PyBondLab Workflow

PyBondLab is the portfolio-formation engine in this repo. WRDS querying and
data cleaning stay outside the package unless an example explicitly needs them.

## Install and Environment

- Use the Python interpreter recorded in `LOCAL_ENV.md`.
- Install repo utilities with `python -m pip install -e .`
- Install PyBondLab with `python -m pip install -e ".[performance]"` from `packages/PyBondLab/`

## Routing

- Package/API semantics -> `packages/PyBondLab/docs/API_REFERENCE.md`
- Methodology and workflow -> `packages/PyBondLab/docs/AI_GUIDE.md`
- User-facing narrative/examples -> `packages/PyBondLab/docs/HUMAN_GUIDE.md`
- Code changes inside the package -> `packages/PyBondLab/AGENTS.md`

## Repo Boundary

- Data fetching is not the package's job.
- Reuse package docs and baseline references before inventing new behavior.
- When a task mixes WRDS conventions and package behavior, read both this file and `docs/ai/wrds.md`.
