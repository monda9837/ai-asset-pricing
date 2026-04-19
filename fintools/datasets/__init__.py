"""Small validation datasets for coursework examples and tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

VALIDATION_DATA_DIR = Path(__file__).resolve().parent / "validation"


@dataclass(frozen=True)
class ValidationDataset:
    """A compact validation dataset with source and unit metadata."""

    name: str
    data: pd.DataFrame
    metadata: dict[str, object]

    @property
    def source(self) -> str:
        return str(self.metadata.get("source", ""))

    @property
    def units(self) -> dict[str, str]:
        raw_units = self.metadata.get("units", {})
        return raw_units if isinstance(raw_units, dict) else {}


def available_validation_datasets() -> list[str]:
    """Return the public validation dataset names."""

    return sorted(path.stem for path in VALIDATION_DATA_DIR.glob("*.csv"))


def load_validation_dataset(name: str) -> ValidationDataset:
    """Load a compact frozen validation dataset by name."""

    csv_path = VALIDATION_DATA_DIR / f"{name}.csv"
    meta_path = VALIDATION_DATA_DIR / f"{name}.json"
    if not csv_path.exists():
        available = ", ".join(available_validation_datasets())
        raise ValueError(f"unknown validation dataset '{name}'. Available: {available}")

    data = pd.read_csv(csv_path, parse_dates=["date"])
    if "date" in data.columns:
        data = data.set_index("date")

    metadata: dict[str, object] = {}
    if meta_path.exists():
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))

    return ValidationDataset(name=name, data=data, metadata=metadata)
