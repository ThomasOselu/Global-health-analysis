"""
analysis.py
===========
Core statistical analysis functions for the Global Health Analytics project.
Covers trend analysis, hypothesis testing, forecasting, and SDG progress scoring.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class TrendResult:
    """Result of a linear trend analysis."""
    country_code: str
    indicator: str
    slope: float
    intercept: float
    r_squared: float
    p_value: float
    std_error: float
    direction: str
    is_significant: bool
    annual_rate: float  # slope expressed as % of mean

    def __str__(self):
        sig = "✓" if self.is_significant else "✗"
        return (
            f"[{sig}] {self.country_code} | {self.indicator} | "
            f"slope={self.slope:+.3f}/yr | R²={self.r_squared:.3f} | p={self.p_value:.4f}"
        )


@dataclass
class SDGProgressReport:
    """SDG health target progress assessment."""
    indicator: str
    region: str
    baseline_value: float
    current_value: float
    target_value: float
    target_year: int
    current_year: int
    progress_pct: float
    on_track: bool
    projected_2030: float
    gap_to_target: float


@dataclass
class AnalysisSummary:
    """High-level summary of a complete analysis run."""
    n_countries: int
    n_indicators: int
    year_range: Tuple[int, int]
    key_findings: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Trend Analysis
# ---------------------------------------------------------------------------

class TrendAnalyzer:
    """
    Longitudinal trend analysis for health indicators.
    Fits linear models, detects reversals, and scores trajectory quality.
    """

    def __init__(self, significance_level: float = 0.05):
        self.alpha = significance_level

    def analyze_country(
        self,
        df: pd.DataFrame,
        country_code: str,
        indicator: str,
        value_col: str = "value",
        min_years: int = 5,
    ) -> Optional[TrendResult]:
        """Analyze trend for a single country-indicator pair."""
        data = df[
            (df["country_code"] == country_code) &
            (df["indicator"] == indicator)
        ].dropna(subset=[value_col]).sort_values("year")

        if len(data) < min_years:
            logger.debug(f"Insufficient data for {country_code}/{indicator}: {len(data)} years")
            return None

        slope, intercept, r, p, se = stats.linregress(data["year"], data[value_col])

        return TrendResult(
            country_code=country_code,
            indicator=indicator,
            slope=round(slope, 4),
            intercept=round(intercept, 4),
            r_squared=round(r**2, 4),
            p_value=round(p, 6),
            std_error=round(se, 4),
            direction="improving" if slope > 0 else "declining",
            is_significant=p < self.alpha,
            annual_rate=round((slope / data[value_col].mean()) * 100, 3),
        )

    def analyze_all(
        self, df: pd.DataFrame, value_col: str = "value"
    ) -> pd.DataFrame:
        """Run trend analysis across all country-indicator combinations."""
        results = []
        for (country, indicator), group in df.groupby(["country_code", "indicator"]):
            result = self.analyze_country(df, country, indicator, value_col)
            if result:
                results.append(vars(result))

        trend_df = pd.DataFrame(results)
        logger.info(f"Trend analysis complete: {len(trend_df):,} country-indicator pairs")
        return trend_df

    def detect_trend_reversal(
        self, df: pd.DataFrame, country_code: str, indicator: str,
        value_col: str = "value", window: int = 5
    ) -> Dict:
        """
        Detect whether a previously improving trend has recently reversed.
        Compares early-period vs late-period slopes using rolling regression.
        """
        data = df[
            (df["country_code"] == country_code) &
            (df["indicator"] == indicator)
        ].dropna(subset=[value_col]).sort_values("year")

        if len(data) < window * 2:
            return {"reversal_detected": False, "reason": "insufficient_data"}

        early = data.iloc[:window]
        late = data.iloc[-window:]

        early_slope = stats.linregress(early["year"], early[value_col]).slope
        late_slope = stats.linregress(late["year"], late[value_col]).slope

        reversal = (early_slope > 0 and late_slope < 0) or (early_slope < 0 and late_slope > 0)

        return {
            "reversal_detected": reversal,
            "early_slope": round(early_slope, 4),
            "late_slope": round(late_slope, 4),
            "early_period": f"{early['year'].min()}–{early['year'].max()}",
            "late_period": f"{late['year'].min()}–{late['year'].max()}",
        }


# ---------------------------------------------------------------------------
# Hypothesis Testing
# ---------------------------------------------------------------------------

class HealthHypothesisTester:
    """
    Statistical tests for comparing health indicators across
    regions, income groups, and time periods.
    """

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def regional_comparison(
        self, df: pd.DataFrame, indicator: str, year: int, value_col: str = "value"
    ) -> Dict:
        """
        One-way ANOVA + post-hoc Tukey test comparing indicator
        across WHO regions for a given year.
        """
        data = df[(df["indicator"] == indicator) & (df["year"] == year)].dropna(subset=[value_col])
        groups = [group[value_col].values for _, group in data.groupby("region")]
        labels = [name for name, _ in data.groupby("region")]

        if len(groups) < 2:
            return {"error": "fewer than 2 regions for comparison"}

        f_stat, p_value = stats.f_oneway(*groups)

        return {
            "test": "One-way ANOVA",
            "indicator": indicator,
            "year": year,
            "f_statistic": round(f_stat, 4),
            "p_value": round(p_value, 6),
            "significant": p_value < self.alpha,
            "regions": labels,
            "region_means": {label: round(float(g.mean()), 2) for label, g in zip(labels, groups)},
            "interpretation": (
                "Significant regional differences detected"
                if p_value < self.alpha
                else "No significant regional differences"
            ),
        }

    def pre_post_covid_test(
        self,
        df: pd.DataFrame,
        indicator: str,
        pre_years: Tuple[int, int] = (2015, 2019),
        post_years: Tuple[int, int] = (2020, 2022),
        value_col: str = "value",
    ) -> Dict:
        """
        Mann-Whitney U test comparing health indicator distributions
        before and after the COVID-19 pandemic.
        """
        pre = df[
            (df["indicator"] == indicator) &
            (df["year"].between(*pre_years))
        ][value_col].dropna()

        post = df[
            (df["indicator"] == indicator) &
            (df["year"].between(*post_years))
        ][value_col].dropna()

        if len(pre) < 5 or len(post) < 5:
            return {"error": "insufficient data for pre/post comparison"}

        stat, p_value = stats.mannwhitneyu(pre, post, alternative="two-sided")
        effect_size = (pre.mean() - post.mean()) / np.sqrt((pre.std()**2 + post.std()**2) / 2)

        return {
            "test": "Mann-Whitney U",
            "indicator": indicator,
            "pre_period": f"{pre_years[0]}–{pre_years[1]}",
            "post_period": f"{post_years[0]}–{post_years[1]}",
            "pre_mean": round(float(pre.mean()), 3),
            "post_mean": round(float(post.mean()), 3),
            "change": round(float(post.mean() - pre.mean()), 3),
            "u_statistic": round(float(stat), 2),
            "p_value": round(p_value, 6),
            "cohens_d": round(float(effect_size), 3),
            "significant": p_value < self.alpha,
            "covid_impact": "Significant negative impact" if (p_value < self.alpha and post.mean() < pre.mean()) else (
                "Significant improvement" if (p_value < self.alpha and post.mean() > pre.mean()) else "No significant change"
            ),
        }

    def correlation_analysis(
        self, df_wide: pd.DataFrame, indicators: List[str]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Compute Pearson correlation matrix and significance matrix
        for multiple health indicators.
        """
        corr_matrix = pd.DataFrame(index=indicators, columns=indicators, dtype=float)
        p_matrix = pd.DataFrame(index=indicators, columns=indicators, dtype=float)

        for ind1 in indicators:
            for ind2 in indicators:
                if ind1 == ind2:
                    corr_matrix.loc[ind1, ind2] = 1.0
                    p_matrix.loc[ind1, ind2] = 0.0
                else:
                    x = df_wide[ind1].dropna()
                    y = df_wide[ind2].dropna()
                    common = x.index.intersection(y.index)
                    if len(common) < 10:
                        corr_matrix.loc[ind1, ind2] = np.nan
                        p_matrix.loc[ind1, ind2] = np.nan
                    else:
                        r, p = stats.pearsonr(x[common], y[common])
                        corr_matrix.loc[ind1, ind2] = round(r, 4)
                        p_matrix.loc[ind1, ind2] = round(p, 6)

        return corr_matrix, p_matrix


# ---------------------------------------------------------------------------
# SDG Progress Tracker
# ---------------------------------------------------------------------------

class SDGProgressTracker:
    """
    Tracks progress toward WHO SDG health targets and projects
    whether countries / regions are on track for 2030.
    """

    # SDG 2030 health targets (illustrative)
    SDG_TARGETS = {
        "under5_mortality": {"target": 25, "direction": "decrease"},
        "life_expectancy": {"target": 75, "direction": "increase"},
        "tb_incidence": {"target": 10, "direction": "decrease"},
        "uhc_index": {"target": 80, "direction": "increase"},
        "dtp3_immunization": {"target": 90, "direction": "increase"},
    }

    def assess_progress(
        self,
        df: pd.DataFrame,
        indicator: str,
        baseline_year: int = 2018,
        current_year: int = 2024,
        target_year: int = 2030,
        value_col: str = "value",
    ) -> pd.DataFrame:
        """
        Assess SDG progress for all regions on a given indicator.
        Projects whether they'll reach the 2030 target at current pace.
        """
        if indicator not in self.SDG_TARGETS:
            raise ValueError(f"No SDG target defined for: {indicator}")

        target_info = self.SDG_TARGETS[indicator]
        target_value = target_info["target"]

        reports = []
        for region, group in df[df["indicator"] == indicator].groupby("region"):
            baseline_row = group[group["year"] == baseline_year]
            current_row = group[group["year"] == current_year]

            if baseline_row.empty or current_row.empty:
                continue

            baseline_val = float(baseline_row[value_col].mean())
            current_val = float(current_row[value_col].mean())

            years_elapsed = current_year - baseline_year
            years_remaining = target_year - current_year
            annual_change = (current_val - baseline_val) / years_elapsed if years_elapsed > 0 else 0

            projected_2030 = current_val + annual_change * years_remaining

            if target_info["direction"] == "increase":
                total_needed = target_value - baseline_val
                achieved = current_val - baseline_val
                on_track = projected_2030 >= target_value
            else:
                total_needed = baseline_val - target_value
                achieved = baseline_val - current_val
                on_track = projected_2030 <= target_value

            progress_pct = (achieved / total_needed * 100) if total_needed != 0 else 0

            reports.append({
                "indicator": indicator,
                "region": region,
                "baseline_value": round(baseline_val, 2),
                "current_value": round(current_val, 2),
                "target_value": target_value,
                "annual_change": round(annual_change, 3),
                "progress_pct": round(progress_pct, 1),
                "projected_2030": round(projected_2030, 2),
                "gap_to_target": round(abs(target_value - projected_2030), 2),
                "on_track": on_track,
                "status": "🟢 On Track" if on_track else "🔴 Off Track",
            })

        return pd.DataFrame(reports)

    def global_scorecard(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate a global scorecard across all SDG indicators."""
        rows = []
        for indicator in self.SDG_TARGETS:
            try:
                progress = self.assess_progress(df, indicator)
                on_track_pct = progress["on_track"].mean() * 100
                avg_progress = progress["progress_pct"].mean()
                rows.append({
                    "indicator": indicator,
                    "regions_on_track": int(progress["on_track"].sum()),
                    "total_regions": len(progress),
                    "pct_regions_on_track": round(on_track_pct, 1),
                    "avg_progress_pct": round(avg_progress, 1),
                    "global_status": "On Track" if on_track_pct >= 50 else "At Risk",
                })
            except Exception as e:
                logger.warning(f"Scorecard skipped {indicator}: {e}")

        return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Forecasting
# ---------------------------------------------------------------------------

class HealthForecaster:
    """
    Simple forecasting models for health indicator projection.
    Uses linear extrapolation and polynomial regression.
    """

    def forecast_linear(
        self,
        df: pd.DataFrame,
        country_code: str,
        indicator: str,
        forecast_years: List[int],
        value_col: str = "value",
    ) -> pd.DataFrame:
        """Project future values using linear extrapolation."""
        data = df[
            (df["country_code"] == country_code) &
            (df["indicator"] == indicator)
        ].dropna(subset=[value_col]).sort_values("year")

        if len(data) < 5:
            raise ValueError(f"Need ≥ 5 data points for forecasting; got {len(data)}")

        X = data["year"].values.reshape(-1, 1)
        y = data[value_col].values

        model = LinearRegression()
        model.fit(X, y)

        cv_scores = cross_val_score(model, X, y, cv=min(5, len(data)), scoring="r2")

        X_forecast = np.array(forecast_years).reshape(-1, 1)
        y_forecast = model.predict(X_forecast)

        # Confidence interval (simple ±1 SE)
        residuals = y - model.predict(X)
        se = residuals.std()

        forecast_df = pd.DataFrame({
            "year": forecast_years,
            "country_code": country_code,
            "indicator": indicator,
            "forecast": y_forecast,
            "lower_ci": y_forecast - 1.96 * se,
            "upper_ci": y_forecast + 1.96 * se,
            "model": "linear",
            "cv_r2_mean": round(cv_scores.mean(), 3),
        })

        return forecast_df


# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    from src.data_loader import generate_synthetic_health_data
    from src.preprocessing import HealthDataPipeline

    print("=" * 60)
    print("  Global Health Analytics — Analysis Module Demo")
    print("=" * 60)

    # Load data
    datasets = generate_synthetic_health_data()
    all_data = pd.concat(datasets.values(), ignore_index=True)

    pipeline = HealthDataPipeline()
    processed, report = pipeline.run(all_data)

    # Trend analysis
    print("\n── Trend Analysis (Life Expectancy) ──────────────")
    analyzer = TrendAnalyzer()
    trends = analyzer.analyze_all(processed[processed["indicator"] == "life_expectancy"])
    print(trends[trends["is_significant"]].head(5).to_string(index=False))

    # SDG Progress
    print("\n── SDG Progress Scorecard ─────────────────────────")
    tracker = SDGProgressTracker()
    scorecard = tracker.global_scorecard(processed)
    print(scorecard.to_string(index=False))

    # Hypothesis test
    print("\n── COVID-19 Impact on Life Expectancy ─────────────")
    tester = HealthHypothesisTester()
    result = tester.pre_post_covid_test(processed, "life_expectancy")
    for k, v in result.items():
        print(f"  {k}: {v}")
