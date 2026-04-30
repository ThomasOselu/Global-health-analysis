"""
data_loader.py
==============
Data ingestion, validation, and loading utilities for the
Global Health Analytics project.

Supports WHO GHO API, CSV flat files, and Excel sources.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Union, List, Dict

import numpy as np
import pandas as pd
import requests
import yaml
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(config_path: str = "config.yaml") -> dict:
    """Load project YAML configuration."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


CONFIG = load_config()


# ---------------------------------------------------------------------------
# Pydantic Schemas (Data Validation)
# ---------------------------------------------------------------------------

class HealthRecord(BaseModel):
    """Validated health indicator record."""
    country_code: str = Field(..., min_length=2, max_length=3)
    country_name: str
    region: str
    year: int = Field(..., ge=1990, le=2030)
    indicator: str
    value: Optional[float]
    unit: Optional[str]
    source: str = "WHO"

    @validator("year")
    def year_in_range(cls, v):
        if not (1990 <= v <= 2030):
            raise ValueError(f"Year {v} out of valid range 1990–2030")
        return v

    @validator("value")
    def value_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError(f"Health indicator value cannot be negative: {v}")
        return v


class DatasetSummary(BaseModel):
    """Summary statistics for a loaded dataset."""
    dataset_name: str
    n_rows: int
    n_countries: int
    n_indicators: int
    year_range: tuple
    missing_pct: float
    load_timestamp: str


# ---------------------------------------------------------------------------
# WHO GHO API Client
# ---------------------------------------------------------------------------

class WHOGHOClient:
    """
    Client for the WHO Global Health Observatory REST API.
    Documentation: https://www.who.int/data/gho/info/gho-odata-api
    """

    BASE_URL = CONFIG["data"]["sources"]["who_gho_base_url"]
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request with retry logic."""
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(self.RETRY_ATTEMPTS):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.RETRY_ATTEMPTS - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
        raise ConnectionError(f"Failed to fetch {url} after {self.RETRY_ATTEMPTS} attempts")

    def get_indicator(
        self,
        indicator_code: str,
        countries: List[str] = None,
        start_year: int = 2000,
        end_year: int = 2025,
    ) -> pd.DataFrame:
        """
        Fetch a specific health indicator from WHO GHO API.

        Args:
            indicator_code: WHO indicator code (e.g. 'WHOSIS_000001')
            countries: ISO3 country codes; None = all
            start_year: Start of data range
            end_year: End of data range

        Returns:
            DataFrame with standardized columns
        """
        logger.info(f"Fetching indicator: {indicator_code} ({start_year}–{end_year})")

        params = {
            "$filter": f"TimeDim ge {start_year} and TimeDim le {end_year}",
            "$select": "SpatialDim,SpatialDimType,TimeDim,NumericValue,Low,High,Comments",
        }

        if countries:
            country_filter = " or ".join([f"SpatialDim eq '{c}'" for c in countries])
            params["$filter"] += f" and ({country_filter})"

        raw = self._get(f"{indicator_code}", params=params)
        records = raw.get("value", [])

        if not records:
            logger.warning(f"No data returned for indicator {indicator_code}")
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df = df.rename(columns={
            "SpatialDim": "country_code",
            "TimeDim": "year",
            "NumericValue": "value",
            "Low": "lower_bound",
            "High": "upper_bound",
        })
        df["indicator"] = indicator_code
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        return df[["country_code", "year", "indicator", "value", "lower_bound", "upper_bound"]]

    def list_indicators(self) -> pd.DataFrame:
        """Return catalog of all available indicators."""
        raw = self._get("Indicator")
        records = raw.get("value", [])
        return pd.DataFrame(records)[["IndicatorCode", "IndicatorName", "Language"]]


# ---------------------------------------------------------------------------
# CSV / Excel Loaders
# ---------------------------------------------------------------------------

class HealthDataLoader:
    """
    Unified loader for health data from multiple file sources.
    Handles CSV, Excel, JSON, and WHO API.
    """

    REQUIRED_COLUMNS = {"country_code", "year", "value"}

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_csv(self, filename: str, **kwargs) -> pd.DataFrame:
        """Load and basic-validate a CSV file."""
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        df = pd.read_csv(path, **kwargs)
        self._validate_columns(df, filename)
        logger.info(f"Loaded {len(df):,} rows from {filename}")
        return df

    def load_excel(self, filename: str, sheet_name: Union[str, int] = 0, **kwargs) -> pd.DataFrame:
        """Load and basic-validate an Excel file."""
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        df = pd.read_excel(path, sheet_name=sheet_name, **kwargs)
        self._validate_columns(df, filename)
        logger.info(f"Loaded {len(df):,} rows from {filename} (sheet: {sheet_name})")
        return df

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files in the data directory."""
        datasets = {}
        for csv_path in self.data_dir.glob("*.csv"):
            try:
                datasets[csv_path.stem] = self.load_csv(csv_path.name)
            except Exception as e:
                logger.error(f"Failed to load {csv_path.name}: {e}")
        return datasets

    def _validate_columns(self, df: pd.DataFrame, source: str) -> None:
        """Ensure required columns are present."""
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"[{source}] Missing required columns: {missing}")


# ---------------------------------------------------------------------------
# Synthetic Data Generator (for demo / testing)
# ---------------------------------------------------------------------------

def generate_synthetic_health_data(seed: int = 42) -> Dict[str, pd.DataFrame]:
    """
    Generate realistic synthetic health datasets for demonstration.
    Based on WHO World Health Statistics 2024/2025 reported ranges.

    Returns:
        Dictionary of DataFrames keyed by indicator name.
    """
    rng = np.random.default_rng(seed)

    COUNTRIES = {
        "AFR": [("NGA", "Nigeria"), ("ETH", "Ethiopia"), ("ZAF", "South Africa"),
                ("KEN", "Kenya"), ("GHA", "Ghana"), ("UGA", "Uganda")],
        "AMR": [("USA", "United States"), ("BRA", "Brazil"), ("MEX", "Mexico"),
                ("COL", "Colombia"), ("ARG", "Argentina"), ("CAN", "Canada")],
        "SEAR": [("IND", "India"), ("BGD", "Bangladesh"), ("IDN", "Indonesia"),
                 ("THA", "Thailand"), ("NPL", "Nepal"), ("MMR", "Myanmar")],
        "EUR": [("GBR", "United Kingdom"), ("DEU", "Germany"), ("FRA", "France"),
                ("SWE", "Sweden"), ("ROU", "Romania"), ("UKR", "Ukraine")],
        "EMR": [("EGY", "Egypt"), ("IRN", "Iran"), ("PAK", "Pakistan"),
                ("IRQ", "Iraq"), ("MAR", "Morocco"), ("SDN", "Sudan")],
        "WPR": [("CHN", "China"), ("JPN", "Japan"), ("AUS", "Australia"),
                ("PHL", "Philippines"), ("VNM", "Viet Nam"), ("KOR", "Republic of Korea")],
    }

    YEARS = list(range(2000, 2026))

    # Regional baseline life expectancy (years)
    LE_BASELINES = {"AFR": 52, "AMR": 74, "SEAR": 65, "EUR": 76, "EMR": 68, "WPR": 74}
    LE_GROWTH = 0.28  # years gained per year

    # UHC index baselines (0–100 scale)
    UHC_BASELINES = {"AFR": 32, "AMR": 68, "SEAR": 52, "EUR": 75, "EMR": 55, "WPR": 71}

    records_le, records_uhc, records_u5m, records_tb, records_imm = [], [], [], [], []

    for region, countries in COUNTRIES.items():
        for iso3, name in countries:
            le_base = LE_BASELINES[region] + rng.uniform(-3, 3)
            uhc_base = UHC_BASELINES[region] + rng.uniform(-5, 5)

            for year in YEARS:
                t = year - 2000

                # Life expectancy: upward trend with COVID-19 dip in 2020-2021
                covid_shock = -1.8 if year == 2020 else (-0.5 if year == 2021 else 0)
                noise = rng.normal(0, 0.3)
                le = le_base + LE_GROWTH * t + covid_shock + noise
                records_le.append({
                    "country_code": iso3, "country_name": name, "region": region,
                    "year": year, "indicator": "life_expectancy", "value": round(le, 2),
                    "lower_bound": round(le - 1.2, 2), "upper_bound": round(le + 1.2, 2)
                })

                # UHC index: improving but slowdown post-COVID
                uhc_growth = 0.9 if year <= 2019 else 0.4
                uhc = min(95, uhc_base + uhc_growth * t + rng.normal(0, 0.8))
                records_uhc.append({
                    "country_code": iso3, "country_name": name, "region": region,
                    "year": year, "indicator": "uhc_index", "value": round(uhc, 1)
                })

                # Under-5 mortality (per 1000 live births): declining
                u5_base = {"AFR": 145, "AMR": 25, "SEAR": 75, "EUR": 12,
                           "EMR": 60, "WPR": 22}[region] + rng.uniform(-10, 10)
                u5 = max(2, u5_base - 3.2 * t + rng.normal(0, 1.5))
                records_u5m.append({
                    "country_code": iso3, "country_name": name, "region": region,
                    "year": year, "indicator": "under5_mortality", "value": round(u5, 1)
                })

                # TB incidence (per 100,000): declining
                tb_base = {"AFR": 350, "AMR": 28, "SEAR": 220, "EUR": 28,
                           "EMR": 110, "WPR": 80}[region] + rng.uniform(-20, 20)
                tb = max(2, tb_base - 8 * (t / 10) * tb_base / 100 + rng.normal(0, 3))
                records_tb.append({
                    "country_code": iso3, "country_name": name, "region": region,
                    "year": year, "indicator": "tb_incidence", "value": round(tb, 1)
                })

                # DTP3 immunization coverage (%)
                imm_base = {"AFR": 55, "AMR": 85, "SEAR": 72, "EUR": 93,
                            "EMR": 74, "WPR": 90}[region] + rng.uniform(-5, 5)
                imm = min(99, max(20, imm_base + 0.5 * t + rng.normal(0, 1)))
                records_imm.append({
                    "country_code": iso3, "country_name": name, "region": region,
                    "year": year, "indicator": "dtp3_immunization", "value": round(imm, 1)
                })

    return {
        "life_expectancy": pd.DataFrame(records_le),
        "uhc_index": pd.DataFrame(records_uhc),
        "under5_mortality": pd.DataFrame(records_u5m),
        "tb_incidence": pd.DataFrame(records_tb),
        "dtp3_immunization": pd.DataFrame(records_imm),
    }


def save_synthetic_data(output_dir: str = "data/raw") -> None:
    """Generate and save all synthetic datasets to CSV."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    datasets = generate_synthetic_health_data()
    for name, df in datasets.items():
        path = out / f"{name}.csv"
        df.to_csv(path, index=False)
        logger.info(f"Saved {len(df):,} rows → {path}")

    # Save metadata
    meta = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "source": "Synthetic data based on WHO World Health Statistics 2024/2025",
        "datasets": {k: {"rows": len(v), "columns": list(v.columns)} for k, v in datasets.items()},
    }
    with open(out / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"✓ Saved {len(datasets)} datasets to {output_dir}/")


if __name__ == "__main__":
    import click

    @click.command()
    @click.option("--generate", is_flag=True, help="Generate synthetic demo data")
    @click.option("--validate", is_flag=True, help="Validate existing data files")
    @click.option("--output", default="data/raw", help="Output directory")
    def main(generate, validate, output):
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        if generate:
            save_synthetic_data(output)
        if validate:
            loader = HealthDataLoader(output)
            datasets = loader.load_all()
            print(f"✓ Validated {len(datasets)} datasets")
            for name, df in datasets.items():
                print(f"  {name}: {len(df):,} rows, {df['country_code'].nunique()} countries")

    main()
