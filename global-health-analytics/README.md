# 🌍 Global Health Analytics 2015–2024

> A full-stack data analysis project demonstrating end-to-end health data expertise — from synthetic data generation through statistical analysis to an interactive visual dashboard.

## 📊 Project Overview

This project showcases a complete data analytics pipeline applied to global public health metrics across **34 countries**, **7 WHO regions**, and **10 years** (2015–2024), with special focus on:

- 📈 Long-term trend analysis of key health indicators
- 🦠 COVID-19 disruption quantification and recovery tracking
- ⚖️ Regional health equity benchmarking
- 🎯 SDG 3 (Good Health) progress assessment
- 🔗 Correlation and regression analysis across health determinants

---

## 🗂️ Repository Structure

```
global-health-analytics/
├── data/
│   ├── generate_data.py          # Synthetic data generator (reproducible seed)
│   └── global_health_data.json   # Generated dataset (340 obs, 7 tables)
│
├── notebooks/
│   └── eda_analysis.py           # Full EDA pipeline with statistical outputs
│
├── public/
│   └── dashboard.html            # Self-contained interactive dashboard
│
├── build_dashboard.py            # Injects data into dashboard HTML
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 📦 Dataset Schema

### `timeseries` (340 records)

| Field | Type | Description |
|-------|------|-------------|
| `year` | int | 2015-2024 |
| `country` | str | Country name (34 countries) |
| `region` | str | WHO region grouping (7 regions) |
| `life_expectancy` | float | Years at birth |
| `u5_mortality_rate` | float | Deaths per 1,000 live births |
| `maternal_mortality_ratio` | float | Deaths per 100,000 live births |
| `vaccination_coverage` | float | % of target population |
| `hospital_beds_per_1k` | float | Beds per 1,000 population |
| `out_of_pocket_pct` | float | % of total health expenditure |
| `uhc_index` | float | Universal Health Coverage index (0-100) |

### `disease_burden` (70 records)
Disease-specific DALYs per 100,000 by region across 10 disease categories.

### `sdg_indicators` (7 records)
SDG 3 sub-target progress scores per region (0-100 scale, 100 = target met).

### `financing` (7 records)
Health financing mix: government, private, out-of-pocket, external aid.

---

## 🔬 Key Analytical Findings

| Finding | Value |
|---------|-------|
| Global life expectancy gain (2015 to 2024) | +2.1 years |
| COVID-19 vaccination coverage shock | -9.6 percentage points |
| North America vs Sub-Saharan Africa LE gap | 21.2 years |
| UHC to Life Expectancy correlation | r = +0.97 |
| Vaccination to U5 Mortality correlation | r = -0.98 |
| Regions on-track for SDG 3.8 by 2030 | 3 of 7 |

---

## 📊 Dashboard Features

The interactive dashboard (`public/dashboard.html`) includes:

- 6 KPI cards with 2015 vs 2024 delta indicators
- Line chart showing life expectancy trends by region (2015-2024)
- COVID impact chart with baseline-indexed disruption visualization
- Disease burden bar chart filterable by region
- Health financing chart showing government vs private vs OOP spending mix
- Scatter plot of UHC Index vs Life Expectancy for all 34 countries
- Radar chart for multi-dimensional regional health benchmarking
- SDG progress tracker with per-region progress bars for 6 SDG 3 targets
- Sortable country rankings table with sparklines
- Key findings panel with evidence-based analytical conclusions

---

## 🚀 Quick Start

### 1. Generate Data
```bash
cd data/
python generate_data.py
```

### 2. Run EDA
```bash
cd notebooks/
python eda_analysis.py
```

### 3. Build and Open Dashboard
```bash
python build_dashboard.py
open public/dashboard.html
```

---

## 📐 Analytical Methods

### Descriptive Statistics
Mean, median, standard deviation, and range across all indicators. Regional and global aggregations for all 10 years.

### Trend Analysis
Year-over-year change rates per region. COVID-19 disruption quantified as percentage deviation from 2019 baseline. Recovery tracking through 2024.

### Correlation Analysis
Pearson correlation coefficients between UHC Index and Life Expectancy, Vaccination Coverage and U5 Mortality Rate, Hospital Beds and Life Expectancy, and Out-of-Pocket Spending and UHC Index.

### SDG Progress Assessment
Each region scored 0-100 on 6 SDG 3 sub-targets. Regions scoring 75 or above classified as on track for 2030.

### Multi-dimensional Benchmarking
Radar chart normalization: each indicator min-max scaled to 0-100 for cross-metric comparison. Inverse normalization applied to lower-is-better metrics such as U5 mortality rate and out-of-pocket spending.

---

## 🎨 Dashboard Design

Built with vanilla HTML/CSS/JS for zero-dependency portability using Chart.js 4.4 for all visualizations. Features a dark theme with CSS custom properties, responsive CSS Grid layout, JetBrains Mono and Syne typography, animated SDG progress bars, interactive region filtering, and country-level tooltips.

---

## 📚 Data Sources (Reference)

This synthetic dataset is modeled after real-world distributions from the WHO Global Health Observatory, World Bank Health Nutrition and Population data, IHME Global Burden of Disease, and the UN SDG Database.

Note: All data is synthetically generated for demonstration purposes. Values are not to be used for policy or clinical decision-making.

---

## 🛠️ Requirements

Python 3.8 or higher. No external packages required (stdlib only: json, random, math, statistics). Dashboard runs in any modern browser.

---

*Built to demonstrate data engineering, statistical analysis, and interactive visualization skills in the global health domain.*
