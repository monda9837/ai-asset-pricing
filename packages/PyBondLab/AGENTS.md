# PyBondLab Agent Guide

This file applies to everything under `packages/PyBondLab/`.

## Read First

- `docs/ai/pybondlab.md`
- `packages/PyBondLab/docs/AI_GUIDE.md`
- `packages/PyBondLab/docs/API_REFERENCE.md`

Use `packages/PyBondLab/PyBondLab/pbl_test.py` and the bundled baseline results
as the first regression reference when behavior changes are suspected.

## Package Rules

- Preserve the boundary between data acquisition and portfolio formation.
- Keep WRDS-specific fetching logic outside the core package except for examples.
- Prefer existing package docs and test/baseline fixtures over rediscovering behavior from scratch.
- When changing public behavior, update the package docs or examples that define that behavior.
- When editing code in this subtree, do not assume repo-wide finance conventions if the package docs say otherwise.

## Workflow Notes

- For API questions or result semantics, read `docs/API_REFERENCE.md` before changing code.
- For methodology questions, read `docs/AI_GUIDE.md` and `docs/HUMAN_GUIDE.md`.
- For factor-construction tasks that depend on WRDS data conventions, cross-check `docs/ai/wrds.md`.
