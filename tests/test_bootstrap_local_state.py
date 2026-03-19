"""Bootstrap regression coverage for the local-state refactor."""

from pathlib import Path
import shutil
import uuid

from tools import bootstrap


def test_wrds_smoke_dates_are_fixed():
    assert bootstrap.WRDS_SMOKE_COUNT_START == "2022-01-01"
    assert bootstrap.WRDS_SMOKE_COUNT_END == "2023-01-01"
    assert bootstrap.WRDS_SMOKE_SAMPLE_START == "2022-12-01"


def test_build_actions_warn_for_synced_folder_and_missing_bash(monkeypatch):
    temp_root = Path(".test-tmp-bootstrap-actions") / uuid.uuid4().hex
    temp_root.mkdir(parents=True, exist_ok=False)
    try:
        service_path = temp_root / "pg_service.conf"
        service_path.write_text("[wrds]\n", encoding="utf-8")
        monkeypatch.setattr(bootstrap, "preferred_pg_service_path", lambda probe: service_path)

        report = {
            "probe": {
                "local_state": {
                    "storage_hint": {"kind": "synced_folder_candidate", "provider": "OneDrive"},
                },
                "tools": {
                    "uv": {"path": ""},
                    "bash": {"path": ""},
                    "psql": {"path": "psql"},
                },
                "wrds": {
                    "pgpass": "OK",
                    "ssh_config": "OK",
                    "ssh_key": "OK",
                },
            },
            "bootstrap_plan": {
                "steps": [{"id": "install_fintools"}],
            },
            "compatibility_files": [
                {"status": "MISSING"},
                {"status": "MISSING"},
                {"status": "MISSING"},
            ],
            "wrds_test": {"status": "SKIPPED"},
        }

        actions = bootstrap.build_actions(report)

        assert any("synced folder" in action for action in actions)
        assert any("Bash on PATH" in action for action in actions)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
