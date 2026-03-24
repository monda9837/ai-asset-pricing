# Release Procedure

Use this procedure when preparing a public release of this repo.

## Preferred Path

Publish from a fresh working copy, ideally outside Dropbox/OneDrive. A normal
local clone is the safest release environment.

Why:

- local sync clients can leave permission-locked temp directories behind
- repo-root local shims should never be part of a release
- a fresh copy proves the shipped tree works without machine-local residue

## Release Gate

Use the interpreter reported by `tools/bootstrap.py audit`, not bare `python`.

Run:

```bash
<python> -B -m pytest tests/ -v -p no:cacheprovider
<python> -B tools/onboarding_smoke_test.py
<python> -B tools/bootstrap.py audit --skip-wrds-test --json
<python> -B tools/release_preflight.py --strict
```

All four commands should pass.

Strict preflight now also verifies that PyBondLab core imports are live and that
the bundled breakpoint data loads from the shipped package tree.

## Tree Hygiene

Before publishing, confirm the working tree does not contain any repo-root
machine-local or generated files such as:

- `LOCAL_ENV.md`
- `CLAUDE.local.md`
- `.claude/settings.local.json`
- `.tmp-*`
- `.test-tmp-*`
- `__pycache__/`
- `*.pyc`

Also confirm:

```bash
git status --short
```

The release tree should be clean apart from intentional tracked changes.

## If The Active Checkout Is Polluted

If strict preflight fails only because the current working tree contains
permission-locked local residue, do not publish from that checkout.

Use one of these fallback paths:

1. Reboot, remove the locked local residue, and rerun the release gate.
2. Create a fresh sibling copy or clone, rerun the release gate there, and
   publish from that clean copy.

This is especially relevant for Windows checkouts under OneDrive or Dropbox.

## Support Contract Reminder

The public support contract is:

- one working copy per user is fully supported
- shared Dropbox/OneDrive working trees are supported only when canonical local
  state stays external
- Dropbox/OneDrive are not a substitute for Git merge/conflict handling on the
  same tracked code/config files

## Final Check

Do not push or tag until:

- the test suite passes
- onboarding smoke passes
- strict preflight passes
- repo-root local shims are absent
- the release tree is clean
