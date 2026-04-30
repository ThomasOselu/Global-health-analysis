"""
preprocessing.py
================
Data cleaning, transformation, and feature engineering pipeline
for the Global Health Analytics project.
"""

import logging
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import KNNImputer
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Missing Data Handlers
# ---------------------------------------------------------------------------

class MissingDataHandler:
    """
    Handles missing values in health time-series data using
    multiple strategies appropriate for longitudinal health data.
    """

    STRATEGIES = ["linear_interpolation", "knn", "regional_mean", "drop"]

    def __init__(self, strategy: str = "linear_interpolation", k_neighbors: int = 5):
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Strategy must be one of: {self.STRATEGIES}")
        self.strategy = strategy
        self.k_neighbors = k_neighbors

    def fit_transform(self, df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
        """Apply missing data strategy and return cleaned DataFrame."""
        missing_count = df[value_col].isna().sum()
        missing_pct = missing_count / len(df) * 100
        logger.info(f"Missing values: {missing_count:,} ({missing_pct:.1f}%)")

        if self.strategy == "linear_interpolation":
            return self._linear_interpolate(df, value_col)
        elif self.strategy == "knn":
            return self._knn_impute(df, value_col)
        elif self.strategy == "regional_mean":
            return self._regional_mean_fill(df, value_col)
        elif self.strategy == "drop":
            return df.dropna(subset=[value_col])

    def _linear_interpolate(self, df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        """Linear interpolation within each country's time series."""
        df = df.copy().sort_values(["country_code", "year"])
        df[value_col] = (
            df.groupby("country_code")[value_col]
            .transform(lambda x: x.interpolate(method="linear", limit_direction="both"))
        )
        return df

    def _knn_impute(self, df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        """KNN imputation using neighboring countries in same region."""
        df = df.copy()
        pivot = df.pivot_table(index="country_code", columns="year", values=value_col)
        imputer = KNNImputer(n_neighbors=self.k_neighbors, weights="distance")
        imputed = imputer.fit_transform(pivot)
        pivot_imputed = pd.DataFrame(imputed, index=pivot.index, columns=pivot.columns)
        melted = pivot_imputed.reset_index().melt(id_vars="country_code", var_name="year", value_name=value_col)
        df = df.drop(columns=[value_col]).merge(melted, on=["country_code", "year"], how="left")
        return df

    def _regional_mean_fill(self, df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        """Fill missing values with regional year means."""
        df = df.copy()
        regional_means = df.groupby(["region", "year"])[value_col].transform("mean")
        df[value_col] = df[value_col].fillna(regional_means)
        return df


# ---------------------------------------------------------------------------
# Outlier Detection
# ---------------------------------------------------------------------------

class OutlierDetector:
    """
    Detects and handles statistical outliers in health indicator data.
    Uses multiple methods suitable for health time-series.
    """

    def __init__(self, method: str = "iqr", threshold: float = 3.0):
        self.method = method
        self.threshold = threshold
        self.outlier_indices_ = []

    def detect(self, df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
        """Flag outliers and return DataFrame with 'is_outlier' column."""
        df = df.copy()

        if self.method == "iqr":
            df["is_outlier"] = self._iqr_method(df[value_col])
        elif self.method == "zscore":
            df["is_outlier"] = self._zscore_method(df[value_col])
        elif self.method == "modified_zscore":
            df["is_outlier"] = self._modified_zscore(df[value_col])

        n_outliers = df["is_outlier"].sum()
        logger.info(f"Detected {n_outliers:,} outliers ({n_outliers/len(df)*100:.2f}%)")
        self.outlier_indices_ = df[df["is_outlier"]].index.tolist()
        return df

    def _iqr_method(self, series: pd.Series) -> pd.Series:
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - self.threshold * IQR
        upper = Q3 + self.threshold * IQR
        return ~series.between(lower, upper)

    def _zscore_method(self, series: pd.Series) -> pd.Series:
        z = np.abs(stats.zscore(series.dropna()))
        mask = pd.Series(False, index=series.index)
        mask.iloc[series.dropna().index] = z > self.threshold
        return mask

    def _modified_zscore(self, series: pd.Series) -> pd.Series:
        median = series.median()
        mad = np.abs(series - median).median()
        modified_z = 0.6745 * (series - median) / mad
        return np.abs(modified_z) > self.threshold


# ---------------------------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------------------------

class HealthFeatureEngineer:
    """
    Creates analytical features from raw health indicator data.
    Produces trend metrics, composite indices, and derived statistics.
    """

    def compute_annual_change(self, df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
        """Compute year-over-year absolute and percentage change per country."""
        df = df.copy().sort_values(["country_code", "year"])
        df["yoy_change"] = df.groupby("country_code")[value_col].diff()
        df["yoy_pct_change"] = df.groupby("country_code")[value_col].pct_change() * 100
        return df

    def compute_rolling_average(
        self, df: pd.DataFrame, window: int = 3, value_col: str = "value"
    ) -> pd.DataFrame:
        """Compute rolling mean for smoothing noisy health series."""
        df = df.copy().sort_values(["country_code", "year"])
        df[f"rolling_{window}yr"] = (
            df.groupby("country_code")[value_col]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
        )
        return df

    def compute_baseline_change(
        self,
        df: pd.DataFrame,
        baseline_year: int = 2018,
        value_col: str = "value",
    ) -> pd.DataFrame:
        """
        Compute change relative to a WHO Triple Billion baseline year.
        Useful for SDG progress tracking.
        """
        df = df.copy()
        baselines = (
            df[df["year"] == baseline_year]
            .set_index("country_code")[value_col]
            .rename("baseline_value")
        )
        df = df.join(baselines, on="country_code")
        df["change_from_baseline"] = df[value_col] - df["baseline_value"]
        df["pct_change_from_baseline"] = (df["change_from_baseline"] / df["baseline_value"]) * 100
        return df

    def compute_linear_trend(self, df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
        """Fit a linear trend to each country's time series and extract slope."""
        trends = []
        for country, group in df.groupby("country_code"):
            group = group.dropna(subset=[value_col]).sort_values("year")
            if len(group) < 3:
                continue
            slope, intercept, r, p, se = stats.linregress(group["year"], group[value_col])
            trends.append({
                "country_code": country,
                "trend_slope": round(slope, 4),
                "trend_r2": round(r**2, 4),
                "trend_p_value": round(p, 4),
                "trend_se": round(se, 4),
                "trend_direction": "improving" if slope > 0 else "declining",
            })
        return pd.DataFrame(trends)

    def compute_regional_stats(
        self, df: pd.DataFrame, value_col: str = "value"
    ) -> pd.DataFrame:
        """Compute regional descriptive statistics per year."""
        return (
            df.groupby(["region", "year"])[value_col]
            .agg(
                mean="mean",
                median="median",
                std="std",
                min="min",
                max="max",
                q25=lambda x: x.quantile(0.25),
                q75=lambda x: x.quantile(0.75),
                n_countries="count",
            )
            .reset_index()
        )

    def compute_health_equity_index(self, df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
        """
        Gini coefficient of health indicator distribution across countries per year.
        Higher value = more inequality.
        """
        def gini(array):
            array = np.sort(array[~np.isnan(array)])
            n = len(array)
            if n == 0:
                return np.nan
            index = np.arange(1, n + 1)
            return (2 * np.sum(index * array) - (n + 1) * np.sum(array)) / (n * np.sum(array))

        equity = df.groupby("year")[value_col].apply(gini).reset_index()
        equity.columns = ["year", "gini_coefficient"]
        return equity


# ---------------------------------------------------------------------------
# Full Preprocessing Pipeline
# ---------------------------------------------------------------------------

class HealthDataPipeline:
    """
    End-to-end preprocessing pipeline:
    1. Standardize column names
    2. Handle missing values
    3. Detect & flag outliers
    4. Engineer features
    5. Normalize for modeling
    """

    def __init__(
        self,
        missing_strategy: str = "linear_interpolation",
        outlier_method: str = "iqr",
        compute_trends: bool = True,
        baseline_year: int = 2018,
    ):
        self.missing_handler = MissingDataHandler(strategy=missing_strategy)
        self.outlier_detector = OutlierDetector(method=outlier_method)
        self.feature_engineer = HealthFeatureEngineer()
        self.compute_trends = compute_trends
        self.baseline_year = baseline_year
        self.scaler = MinMaxScaler()
        self._pipeline_log: List[str] = []

    def run(self, df: pd.DataFrame, value_col: str = "value") -> Tuple[pd.DataFrame, dict]:
        """
        Execute the full preprocessing pipeline.

        Returns:
            Tuple of (processed_df, pipeline_report)
        """
        report = {"input_rows": len(df), "input_nulls": df[value_col].isna().sum()}

        # Step 1: Type coercion
        df = self._standardize_types(df)
        self._log("✓ Types standardized")

        # Step 2: Missing data
        df = self.missing_handler.fit_transform(df, value_col)
        report["post_imputation_nulls"] = df[value_col].isna().sum()
        self._log(f"✓ Missing data handled ({self.missing_handler.strategy})")

        # Step 3: Outlier detection
        df = self.outlier_detector.detect(df, value_col)
        report["n_outliers"] = int(df["is_outlier"].sum())
        self._log(f"✓ Outliers detected: {report['n_outliers']:,}")

        # Step 4: Feature engineering
        df = self.feature_engineer.compute_annual_change(df, value_col)
        df = self.feature_engineer.compute_rolling_average(df, window=3, value_col=value_col)
        df = self.feature_engineer.compute_baseline_change(df, self.baseline_year, value_col)
        self._log("✓ Features engineered")

        # Step 5: Finalize
        report["output_rows"] = len(df)
        report["pipeline_steps"] = self._pipeline_log.copy()

        logger.info(f"Pipeline complete: {report['input_rows']:,} → {report['output_rows']:,} rows")
        return df, report

    def _standardize_types(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        if "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
        if "country_code" in df.columns:
            df["country_code"] = df["country_code"].str.upper().str.strip()
        return df

    def _log(self, message: str) -> None:
        self._pipeline_log.append(message)
        logger.info(message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Demo
    from data_loader import generate_synthetic_health_data
    datasets = generate_synthetic_health_data()
    df = datasets["life_expectancy"]

    pipeline = HealthDataPipeline()
    processed, report = pipeline.run(df)

    print("\n── Pipeline Report ──────────────────────────")
    for k, v in report.items():
        if k != "pipeline_steps":
            print(f"  {k}: {v}")
    print("\n── Sample Output ────────────────────────────")
    print(processed.head(3).to_string())
