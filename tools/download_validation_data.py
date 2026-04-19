#!/usr/bin/env python3
"""Refresh public validation fixtures from source downloads."""

from __future__ import annotations

import argparse
import io
import json
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.offsets import MonthEnd

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / "fintools" / "datasets" / "validation"
RAW_DIR = VALIDATION_DIR / "_raw"

FRENCH_URLS = {
    "ff3_monthly": (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
        "F-F_Research_Data_Factors_CSV.zip"
    ),
    "ff_industry_10_monthly": (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
        "10_Industry_Portfolios_CSV.zip"
    ),
    "ff25_size_value_monthly": (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
        "25_Portfolios_5x5_CSV.zip"
    ),
}

FRED_URLS = {
    "fred_macro_monthly": "https://fred.stlouisfed.org/graph/fredgraph.csv"
    "?id=UNRATE,CPIAUCSL,INDPRO,PAYEMS,FEDFUNDS",
    "fred_rates_daily": "https://fred.stlouisfed.org/graph/fredgraph.csv"
    "?id=DGS10,DGS2,DTB3,T10Y2Y,T10Y3M",
    "fred_financial_stress_daily": "https://fred.stlouisfed.org/graph/fredgraph.csv"
    "?id=VIXCLS,BAMLH0A0HYM2",
}

SHILLER_URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
WORLD_BANK_COUNTRIES = "USA;CHN;JPN;DEU;GBR;IND;FRA;ITA;CAN;KOR"
WORLD_BANK_GDP_URL = (
    "https://api.worldbank.org/v2/country/"
    f"{WORLD_BANK_COUNTRIES}/indicator/NY.GDP.MKTP.CD"
    "?format=json&per_page=500&date=2010:2024"
)
WORLD_BANK_PANEL_INDICATORS = {
    "gdp_current_usd": "NY.GDP.MKTP.CD",
    "population": "SP.POP.TOTL",
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
}
WORLD_BANK_PANEL_URLS = {
    field: (
        "https://api.worldbank.org/v2/country/"
        f"{WORLD_BANK_COUNTRIES}/indicator/{indicator}"
        "?format=json&per_page=500&date=2010:2024"
    )
    for field, indicator in WORLD_BANK_PANEL_INDICATORS.items()
}

METADATA = {
    "ff3_monthly": {
        "name": "ff3_monthly",
        "description": "Full monthly Fama/French 3-factor validation fixture.",
        "source": "Kenneth French Data Library, Fama/French 3 Factors CSV",
        "source_url": FRENCH_URLS["ff3_monthly"],
        "frequency": "monthly",
        "date_column": "date",
        "sample": "full available monthly sample",
        "return_scale": "percent",
        "units": {
            "Mkt-RF": "percent monthly return",
            "SMB": "percent monthly return",
            "HML": "percent monthly return",
            "RF": "percent monthly return",
        },
    },
    "ff_industry_10_monthly": {
        "name": "ff_industry_10_monthly",
        "description": "Full monthly 10-industry return validation fixture.",
        "source": "Kenneth French Data Library, 10 Industry Portfolios CSV",
        "source_url": FRENCH_URLS["ff_industry_10_monthly"],
        "frequency": "monthly",
        "date_column": "date",
        "sample": "full available monthly sample",
        "return_scale": "percent",
        "units": {
            "NoDur": "percent monthly return",
            "Durbl": "percent monthly return",
            "Manuf": "percent monthly return",
            "Enrgy": "percent monthly return",
            "HiTec": "percent monthly return",
            "Telcm": "percent monthly return",
            "Shops": "percent monthly return",
            "Hlth": "percent monthly return",
            "Utils": "percent monthly return",
            "Other": "percent monthly return",
        },
    },
    "ff25_size_value_monthly": {
        "name": "ff25_size_value_monthly",
        "description": "Full monthly 25 size-value portfolio return validation fixture.",
        "source": (
            "Kenneth French Data Library, 25 Portfolios Formed on Size and "
            "Book-to-Market CSV"
        ),
        "source_url": FRENCH_URLS["ff25_size_value_monthly"],
        "frequency": "monthly",
        "date_column": "date",
        "sample": "full available monthly sample",
        "return_scale": "percent",
        "units": {
            "all_portfolios": "percent monthly return",
        },
    },
    "fred_macro_monthly": {
        "name": "fred_macro_monthly",
        "description": "Long monthly macro validation fixture.",
        "source": "FRED CSV downloads for UNRATE, CPIAUCSL, INDPRO, PAYEMS, and FEDFUNDS",
        "source_url": FRED_URLS["fred_macro_monthly"],
        "frequency": "monthly",
        "date_column": "date",
        "units": {
            "UNRATE": "percent",
            "CPIAUCSL": "index 1982-1984=100",
            "INDPRO": "index 2017=100",
            "PAYEMS": "thousands of persons",
            "FEDFUNDS": "percent",
        },
    },
    "fred_rates_daily": {
        "name": "fred_rates_daily",
        "description": "Long daily Treasury-rate and yield-curve validation fixture.",
        "source": "FRED CSV downloads for DGS10, DGS2, DTB3, T10Y2Y, and T10Y3M",
        "source_url": FRED_URLS["fred_rates_daily"],
        "frequency": "daily",
        "date_column": "date",
        "units": {
            "DGS10": "percent",
            "DGS2": "percent",
            "DTB3": "percent",
            "T10Y2Y": "percentage points",
            "T10Y3M": "percentage points",
        },
    },
    "fred_financial_stress_daily": {
        "name": "fred_financial_stress_daily",
        "description": "Daily financial-stress validation fixture.",
        "source": "FRED CSV downloads for VIXCLS and BAMLH0A0HYM2",
        "source_url": FRED_URLS["fred_financial_stress_daily"],
        "frequency": "daily",
        "date_column": "date",
        "units": {
            "VIXCLS": "index",
            "BAMLH0A0HYM2": "percent",
        },
    },
    "shiller_market_monthly": {
        "name": "shiller_market_monthly",
        "description": "Long monthly Robert Shiller market validation fixture.",
        "source": "Robert Shiller Online Data, U.S. Stock Markets 1871-Present and CAPE",
        "source_url": SHILLER_URL,
        "frequency": "monthly",
        "date_column": "date",
        "units": {
            "price": "S&P composite price index",
            "dividend": "dividend",
            "earnings": "earnings",
            "cpi": "consumer price index",
            "long_rate": "percent",
            "real_price": "inflation-adjusted price index",
            "real_dividend": "inflation-adjusted dividend",
            "real_earnings": "inflation-adjusted earnings",
            "cape": "price divided by 10-year average real earnings",
        },
    },
    "world_bank_gdp_annual": {
        "name": "world_bank_gdp_annual",
        "description": "Annual GDP validation fixture for ranking and slope-chart examples.",
        "source": "World Bank World Development Indicators, NY.GDP.MKTP.CD",
        "source_url": WORLD_BANK_GDP_URL,
        "frequency": "annual",
        "date_column": "date",
        "sample": "2010-2024",
        "units": {
            "gdp_current_usd": "current U.S. dollars",
            "gdp_trillions_usd": "trillions of current U.S. dollars",
        },
    },
    "world_bank_country_panel_annual": {
        "name": "world_bank_country_panel_annual",
        "description": (
            "Annual country panel fixture for GDP, population, and GDP per "
            "capita examples."
        ),
        "source": (
            "World Bank World Development Indicators, NY.GDP.MKTP.CD, "
            "SP.POP.TOTL, and NY.GDP.PCAP.CD"
        ),
        "source_url": WORLD_BANK_PANEL_URLS["gdp_current_usd"],
        "source_urls": WORLD_BANK_PANEL_URLS,
        "frequency": "annual",
        "date_column": "date",
        "sample": "2010-2024",
        "units": {
            "gdp_current_usd": "current U.S. dollars",
            "gdp_trillions_usd": "trillions of current U.S. dollars",
            "population": "persons",
            "population_millions": "millions of persons",
            "gdp_per_capita_usd": "current U.S. dollars per person",
        },
    },
}


def download_bytes(url: str, raw_path: Path) -> bytes:
    """Download a URL and save the raw artifact."""

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    raw_path.write_bytes(data)
    return data


def read_french_monthly_zip(data: bytes) -> pd.DataFrame:
    """Parse a Kenneth French monthly CSV zip into a clean dataframe."""

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        text = archive.read(csv_name).decode("utf-8", errors="replace")

    lines = text.splitlines()
    header_index = next(index for index, line in enumerate(lines) if line.startswith(","))
    selected = [lines[header_index]]
    for line in lines[header_index + 1 :]:
        first_field = line.split(",", 1)[0].strip()
        if not first_field.isdigit():
            break
        if len(first_field) == 6:
            selected.append(line)

    frame = pd.read_csv(io.StringIO("\n".join(selected)))
    frame = frame.rename(columns={frame.columns[0]: "date"})
    frame["date"] = pd.to_datetime(frame["date"].astype(str), format="%Y%m") + MonthEnd(0)
    for column in frame.columns:
        if column != "date":
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def read_fred_csv(data: bytes) -> pd.DataFrame:
    """Parse a FRED graph CSV download into a clean dataframe."""

    if data.startswith(b"PK"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            csv_name = next(name for name in archive.namelist() if name.endswith(".csv"))
            data = archive.read(csv_name)
    frame = pd.read_csv(io.BytesIO(data))
    frame = frame.rename(columns={frame.columns[0]: "date"})
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.replace(".", pd.NA)
    for column in frame.columns:
        if column != "date":
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def read_shiller_xls(data: bytes) -> pd.DataFrame:
    """Parse Robert Shiller's monthly market workbook into a clean dataframe."""

    raw = pd.read_excel(io.BytesIO(data), sheet_name="Data", header=None, engine="xlrd")
    first_column = raw.iloc[:, 0].astype(str).str.strip().str.lower()
    header_row = int(raw.index[first_column == "date"][0])
    column_map = {
        0: "date_raw",
        1: "price",
        2: "dividend",
        3: "earnings",
        4: "cpi",
        6: "long_rate",
        7: "real_price",
        8: "real_dividend",
        9: "real_total_return_price",
        10: "real_earnings",
        12: "cape",
    }
    frame = raw.iloc[header_row + 1 :, list(column_map)].copy()
    frame.columns = [column_map[index] for index in column_map]
    frame = frame[pd.to_numeric(frame["date_raw"], errors="coerce").notna()].copy()
    raw_dates = pd.to_numeric(frame["date_raw"], errors="coerce")
    years = np.floor(raw_dates).astype(int)
    months = np.rint((raw_dates - years) * 100).astype(int).clip(1, 12)
    dates = pd.to_datetime({"year": years.to_numpy(), "month": months.to_numpy(), "day": 1})
    frame["date"] = pd.Series((dates + MonthEnd(0)).to_numpy(), index=frame.index)

    columns = [
        "date",
        "price",
        "dividend",
        "earnings",
        "cpi",
        "long_rate",
        "real_price",
        "real_dividend",
        "real_earnings",
        "cape",
    ]
    frame = frame[[column for column in columns if column in frame.columns]].copy()
    for column in frame.columns:
        if column != "date":
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(how="all", subset=[c for c in frame.columns if c != "date"])


def read_world_bank_gdp(data: bytes) -> pd.DataFrame:
    """Parse World Bank GDP API JSON into a compact annual dataframe."""

    payload = json.loads(data.decode("utf-8"))
    rows = payload[1] if len(payload) > 1 else []
    records = []
    for row in rows:
        value = row.get("value")
        if value is None:
            continue
        records.append(
            {
                "date": pd.Timestamp(year=int(row["date"]), month=12, day=31),
                "country": row["country"]["value"],
                "country_code": row["countryiso3code"],
                "gdp_current_usd": float(value),
                "gdp_trillions_usd": round(float(value) / 1e12, 4),
            }
        )
    frame = pd.DataFrame.from_records(records)
    return frame.sort_values(["country_code", "date"]).reset_index(drop=True)


def read_world_bank_country_panel(downloads: dict[str, bytes]) -> pd.DataFrame:
    """Parse World Bank indicator API downloads into one country-year panel."""

    frames: list[pd.DataFrame] = []
    for field, data in downloads.items():
        payload = json.loads(data.decode("utf-8"))
        rows = payload[1] if len(payload) > 1 else []
        records = []
        for row in rows:
            value = row.get("value")
            if value is None:
                continue
            records.append(
                {
                    "date": pd.Timestamp(year=int(row["date"]), month=12, day=31),
                    "country": row["country"]["value"],
                    "country_code": row["countryiso3code"],
                    field: float(value),
                }
            )
        frames.append(pd.DataFrame.from_records(records))

    panel = frames[0]
    for frame in frames[1:]:
        panel = panel.merge(frame, on=["date", "country", "country_code"], how="outer")
    panel["gdp_trillions_usd"] = (panel["gdp_current_usd"] / 1e12).round(4)
    panel["population_millions"] = (panel["population"] / 1e6).round(4)
    return panel.sort_values(["country_code", "date"]).reset_index(drop=True)


def filter_dates(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Return rows whose date column lies in the inclusive date range."""

    start_date = pd.Timestamp(start)
    end_date = pd.Timestamp(end)
    mask = (frame["date"] >= start_date) & (frame["date"] <= end_date)
    return frame.loc[mask].dropna(how="all", subset=[c for c in frame.columns if c != "date"])


def write_fixture(name: str, frame: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    """Write one validation CSV and its metadata JSON."""

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{name}.csv"
    json_path = output_dir / f"{name}.json"
    frame.to_csv(csv_path, index=False, float_format="%.6g")
    json_path.write_text(json.dumps(METADATA[name], indent=2) + "\n", encoding="utf-8")
    return csv_path, json_path


def refresh_fixtures(args: argparse.Namespace) -> list[Path]:
    """Download source data and refresh validation fixtures."""

    output_dir = Path(args.output).resolve()
    raw_dir = Path(args.raw_dir).resolve()
    written: list[Path] = []

    for name, url in FRENCH_URLS.items():
        data = download_bytes(url, raw_dir / f"{name}.zip")
        frame = read_french_monthly_zip(data)
        if args.compact:
            frame = filter_dates(frame, args.monthly_start, args.monthly_end)
        written.extend(write_fixture(name, frame, output_dir))

    for name, url in FRED_URLS.items():
        data = download_bytes(url, raw_dir / f"{name}.csv")
        frame = read_fred_csv(data)
        if args.compact:
            if name == "fred_macro_monthly":
                frame = filter_dates(frame, args.monthly_start, args.monthly_end)
            else:
                frame = filter_dates(frame, args.daily_start, args.daily_end)
        written.extend(write_fixture(name, frame, output_dir))

    data = download_bytes(SHILLER_URL, raw_dir / "shiller_market_monthly.xls")
    frame = read_shiller_xls(data)
    if args.compact:
        frame = filter_dates(frame, args.shiller_start, args.monthly_end)
    written.extend(write_fixture("shiller_market_monthly", frame, output_dir))

    data = download_bytes(WORLD_BANK_GDP_URL, raw_dir / "world_bank_gdp_annual.json")
    frame = read_world_bank_gdp(data)
    written.extend(write_fixture("world_bank_gdp_annual", frame, output_dir))

    panel_downloads = {
        field: download_bytes(url, raw_dir / f"world_bank_country_panel_annual_{field}.json")
        for field, url in WORLD_BANK_PANEL_URLS.items()
    }
    frame = read_world_bank_country_panel(panel_downloads)
    written.extend(write_fixture("world_bank_country_panel_annual", frame, output_dir))

    return written


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        description="Refresh validation fixtures from public data sources."
    )
    parser.add_argument("--output", default=str(VALIDATION_DIR))
    parser.add_argument("--raw-dir", default=str(RAW_DIR))
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--monthly-start", default="2020-01-01")
    parser.add_argument("--monthly-end", default="2021-12-31")
    parser.add_argument("--daily-start", default="2020-02-18")
    parser.add_argument("--daily-end", default="2020-03-31")
    parser.add_argument("--shiller-start", default="1871-01-01")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Refresh fixtures and print the files written."""

    parser = create_parser()
    args = parser.parse_args(argv)
    written = refresh_fixtures(args)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
