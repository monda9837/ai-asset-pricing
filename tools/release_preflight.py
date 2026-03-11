#!/usr/bin/env python3
"""Release preflight checks for clone-and-/onboard readiness."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_FILES = (
    Path("README.md"),
    Path("CLAUDE.md"),
    Path(".claude/settings.json"),
    Path(".claude/skills/onboard/SKILL.md"),
    Path("tools/onboard_probe.py"),
)

REQUIRED_GITIGNORE_ENTRIES = (
    "CLAUDE.local.md",
    ".claude/settings.local.json",
    "*.egg-info/",
    "*.nbc",
    "*.nbi",
)

EXACT_FORBIDDEN_PATHS = (
    Path("CLAUDE.local.md"),
    Path(".claude/settings.local.json"),
    Path(".Rhistory"),
)

FORBIDDEN_DIR_NAMES = {"__pycache__"}
FORBIDDEN_DIR_SUFFIXES = (".egg-info",)
FORBIDDEN_FILE_SUFFIXES = (".pyc", ".pyo", ".pyd", ".nbc", ".nbi")

LOCAL_PATH_PATTERNS = (
    re.compile(r"(?i)c:\\users\\"),
    re.compile(r"(?i)//c/users/"),
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
)

SHARED_TEXT_FILES = (
    Path("README.md"),
    Path("CLAUDE.md"),
    Path(".claude/settings.json"),
    Path(".claude/skills/onboard/SKILL.md"),
)


@dataclass
class Finding:
    level: str
    message: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def collect_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    for rel_path in REQUIRED_FILES:
        if not (root / rel_path).exists():
            findings.append(Finding("FAIL", f"Missing required file: {rel_path.as_posix()}"))

    gitignore_path = root / ".gitignore"
    gitignore_text = read_text(gitignore_path) if gitignore_path.exists() else ""
    for entry in REQUIRED_GITIGNORE_ENTRIES:
        if entry not in gitignore_text:
            findings.append(Finding("FAIL", f".gitignore is missing required entry: {entry}"))

    for rel_path in EXACT_FORBIDDEN_PATHS:
        if (root / rel_path).exists():
            findings.append(Finding("FAIL", f"Release tree contains local/generated file: {rel_path.as_posix()}"))

    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts and ".git" in relative.parts:
            continue

        if path.is_dir():
            if path.name in FORBIDDEN_DIR_NAMES or path.name.endswith(FORBIDDEN_DIR_SUFFIXES):
                findings.append(Finding("FAIL", f"Release tree contains generated directory: {relative.as_posix()}"))
            continue

        if path.suffix in FORBIDDEN_FILE_SUFFIXES:
            findings.append(Finding("FAIL", f"Release tree contains generated file: {relative.as_posix()}"))

    settings_path = root / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(read_text(settings_path))
        except json.JSONDecodeError as exc:
            findings.append(Finding("FAIL", f".claude/settings.json is invalid JSON: {exc}"))
        else:
            if "enabledPlugins" in settings:
                findings.append(Finding("FAIL", ".claude/settings.json should not enable user-local plugins"))
            serialized = json.dumps(settings)
            if "mcp__" in serialized:
                findings.append(Finding("WARN", ".claude/settings.json still contains MCP-specific permissions"))

    for rel_path in SHARED_TEXT_FILES:
        path = root / rel_path
        if not path.exists():
            continue
        text = read_text(path)
        for pattern in LOCAL_PATH_PATTERNS:
            if pattern.search(text):
                findings.append(
                    Finding("FAIL", f"Shared file leaks a user-specific absolute path: {rel_path.as_posix()}")
                )
                break

    readme_path = root / "README.md"
    if readme_path.exists():
        readme = read_text(readme_path)
        if "/onboard" not in readme:
            findings.append(Finding("FAIL", "README.md no longer documents /onboard"))
        if "release_preflight.py" not in readme:
            findings.append(Finding("WARN", "README.md does not mention the release preflight checker"))

    if not (root / ".git").exists():
        findings.append(Finding("WARN", "No .git directory found; validate from an actual clone before release"))

    if not findings:
        findings.append(Finding("PASS", "No release-preflight issues found"))

    return findings


def print_findings(findings: list[Finding]) -> None:
    for finding in findings:
        print(f"[{finding.level}] {finding.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    findings = collect_findings(root)
    print_findings(findings)

    has_fail = any(f.level == "FAIL" for f in findings)
    has_warn = any(f.level == "WARN" for f in findings)
    return 1 if has_fail or (args.strict and has_warn) else 0


if __name__ == "__main__":
    raise SystemExit(main())
