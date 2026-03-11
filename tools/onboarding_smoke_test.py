#!/usr/bin/env python3
"""Smoke-test onboarding in a temporary clone-like workspace."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True

from bootstrap import cleanup_generated_repo_artifacts, force_rmtree

REPO_ROOT = Path(__file__).resolve().parent.parent
PYBONDLAB_ROOT = REPO_ROOT / "packages" / "PyBondLab"


def run_command(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 300) -> str:
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=timeout,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "command failed").strip()
        raise RuntimeError(f"{' '.join(cmd)} failed: {detail}")
    return (proc.stdout or "").strip()


def validate_packaging_layout(clone_root: Path) -> None:
    pyproject_text = (clone_root / "pyproject.toml").read_text(encoding="utf-8")
    required_snippets = (
        "[tool.setuptools.packages.find]",
        'include = ["fintools*"]',
    )
    for snippet in required_snippets:
        if snippet not in pyproject_text:
            raise RuntimeError(f"root pyproject.toml is missing required packaging config: {snippet}")

    if not (clone_root / "fintools" / "__init__.py").exists():
        raise RuntimeError("fintools package is missing from the temp clone")

    pybondlab_pyproject = clone_root / "packages" / "PyBondLab" / "pyproject.toml"
    if not pybondlab_pyproject.exists():
        raise RuntimeError("PyBondLab pyproject.toml is missing from the temp clone")

    if not (clone_root / "packages" / "PyBondLab" / "setup.py").exists():
        raise RuntimeError("PyBondLab setup.py is missing from the temp clone")


def copy_tree(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(
            src,
            dst,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.egg-info", ".tmp-*"),
        )
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def build_temp_repo(temp_root: Path) -> Path:
    clone_root = temp_root / "clone"
    copy_tree(REPO_ROOT / "pyproject.toml", clone_root / "pyproject.toml")
    copy_tree(REPO_ROOT / "README.md", clone_root / "README.md")
    copy_tree(REPO_ROOT / "fintools", clone_root / "fintools")
    copy_tree(REPO_ROOT / "tools" / "bootstrap.py", clone_root / "tools" / "bootstrap.py")
    copy_tree(REPO_ROOT / "tools" / "onboard_probe.py", clone_root / "tools" / "onboard_probe.py")
    copy_tree(PYBONDLAB_ROOT, clone_root / "packages" / "PyBondLab")
    return clone_root


def cleanup_stale_smoke_dirs() -> None:
    failed: list[str] = []
    for path in REPO_ROOT.glob(".tmp-bootstrap-smoke-*"):
        if path.is_dir() and not force_rmtree(path):
            failed.append(str(path))
    if failed:
        raise RuntimeError(f"failed to remove stale smoke workspaces: {', '.join(failed)}")


def main() -> int:
    cleanup_generated_repo_artifacts()
    cleanup_stale_smoke_dirs()
    temp_root = REPO_ROOT / f".tmp-bootstrap-smoke-{uuid.uuid4().hex}"
    temp_root.mkdir(parents=True, exist_ok=False)
    try:
        clone_root = build_temp_repo(temp_root)
        python_path = Path(sys.executable).resolve()

        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        validate_packaging_layout(clone_root)

        audit_output = run_command(
            [str(python_path), "tools/bootstrap.py", "audit", "--skip-wrds-test", "--json"],
            cwd=clone_root,
            env=env,
        )
        audit_payload = json.loads(audit_output)
        if audit_payload.get("mode") != "audit":
            raise RuntimeError("bootstrap audit returned the wrong mode")
        audit_plan = audit_payload.get("bootstrap_plan", {}).get("steps", [])
        audit_plan_ids = {step.get("id") for step in audit_plan}
        required_plan_ids = {"install_fintools", "install_pybondlab", "apply_local_files", "rerun_audit"}
        if not required_plan_ids.issubset(audit_plan_ids):
            raise RuntimeError("bootstrap audit did not emit the expected bootstrap_plan steps for a fresh clone")

        # Smoke-test `tools/bootstrap.py apply` in the temp clone.
        apply_output = run_command(
            [str(python_path), "tools/bootstrap.py", "apply", "--skip-wrds-test", "--json"],
            cwd=clone_root,
            env=env,
        )
        apply_payload = json.loads(apply_output)
        if apply_payload.get("mode") != "apply":
            raise RuntimeError("bootstrap apply returned the wrong mode")

        local_files = apply_payload.get("local_files", [])
        if not local_files or any(item.get("status") != "OK" for item in local_files):
            raise RuntimeError("bootstrap apply did not leave all local files in OK state")
        apply_plan = apply_payload.get("bootstrap_plan", {}).get("steps", [])
        if not any(step.get("id") == "apply_local_files" for step in apply_plan):
            raise RuntimeError("bootstrap apply payload did not preserve bootstrap_plan data")

        written_files = apply_payload.get("written_files", [])
        expected = {"LOCAL_ENV.md", "CLAUDE.local.md", ".claude/settings.local.json"}
        if set(written_files) != expected:
            raise RuntimeError("bootstrap apply did not report the expected written files")

        print("onboarding smoke test passed")
        return 0
    finally:
        cleanup_error = ""
        if temp_root.exists() and not force_rmtree(temp_root):
            cleanup_error = f"failed to remove temporary smoke workspace: {temp_root}"
        cleanup_generated_repo_artifacts()
        cleanup_stale_smoke_dirs()
        if cleanup_error:
            raise RuntimeError(cleanup_error)


if __name__ == "__main__":
    raise SystemExit(main())
