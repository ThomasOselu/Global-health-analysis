"""
Global Health Status Dataset Generator
Produces realistic synthetic health metrics for 2015-2024
"""

import json
import random
import math

random.seed(42)

REGIONS = {
    "Sub-Saharan Africa": {"gdp_factor": 0.3, "base_le": 58, "color": "#e67e22"},
    "South Asia": {"gdp_factor": 0.5, "base_le": 68, "color": "#e74c3c"},
    "East Asia & Pacific": {"gdp_factor": 0.85, "base_le": 74, "color": "#3498db"},
    "Latin America": {"gdp_factor": 0.7, "base_le": 73, "color": "#2ecc71"},
    "Middle East & N. Africa": {"gdp_factor": 0.75, "base_le": 72, "color": "#9b59b6"},
    "Europe & Central Asia": {"gdp_factor": 0.9, "base_le": 76, "color": "#1abc9c"},
    "North America": {"gdp_factor": 1.0, "base_le": 79, "color": "#f39c12"},
}

COUNTRIES = {
    "Nigeria": "Sub-Saharan Africa", "Ethiopia": "Sub-Saharan Africa",
    "Kenya": "Sub-Saharan Africa", "South Africa": "Sub-Saharan Africa",
    "Ghana": "Sub-Saharan Africa", "Tanzania": "Sub-Saharan Africa",
    "India": "South Asia", "Pakistan": "South Asia",
    "Bangladesh": "South Asia", "Nepal": "South Asia",
    "China": "East Asia & Pacific", "Indonesia": "East Asia & Pacific",
    "Philippines": "East Asia & Pacific", "Vietnam": "East Asia & Pacific",
    "Japan": "East Asia & Pacific", "Australia": "East Asia & Pacific",
    "Brazil": "Latin America", "Mexico": "Latin America",
    "Colombia": "Latin America", "Argentina": "Latin America",
    "Peru": "Latin America", "Chile": "Latin America",
    "Egypt": "Middle East & N. Africa", "Morocco": "Middle East & N. Africa",
    "Saudi Arabia": "Middle East & N. Africa", "Turkey": "Middle East & N. Africa",
    "Germany": "Europe & Central Asia", "France": "Europe & Central Asia",
    "United Kingdom": "Europe & Central Asia", "Italy": "Europe & Central Asia",
    "Spain": "Europe & Central Asia", "Poland": "Europe & Central Asia",
    "United States": "North America", "Canada": "North America",
}

DISEASES = [
    "Cardiovascular Disease", "Malaria", "HIV/AIDS",
    "Tuberculosis", "Respiratory Infections", "Diabetes",
    "Cancer", "Diarrheal Diseases", "Malnutrition", "Mental Health"
]

YEARS = list(range(2015, 2025))

def noise(scale=1.0):
    return (random.random() - 0.5) * 2 * scale

def trend(year, base, annual_change, noise_scale=0.3):
    return base + (year - 2015) * annual_change + noise(noise_scale)

def covid_impact(year, metric_type):
    """Simulate COVID-19 disruption in 2020-2021"""
    if year == 2020:
        if metric_type == "mortality": return 1.15
        if metric_type == "coverage": return 0.88
        if metric_type == "le": return -1.2
    elif year == 2021:
        if metric_type == "mortality": return 1.08
        if metric_type == "coverage": return 0.92
        if metric_type == "le": return -0.5
    return 1.0 if metric_type in ["mortality", "coverage"] else 0.0

# ── Time-series data ─────────────────────────────────────────────────────────
timeseries = []
for year in YEARS:
    for country, region in COUNTRIES.items():
        r = REGIONS[region]
        f = r["gdp_factor"]

        le_base = r["base_le"] + trend(year, 0, 0.25, 0.2) + covid_impact(year, "le")
        le = round(le_base + noise(0.4), 1)

        u5mr_base = (120 - 80 * f) * (0.93 ** (year - 2015)) * covid_impact(year, "mortality")
        u5mr = round(max(3, u5mr_base + noise(2)), 1)

        mmr_base = (500 - 380 * f) * (0.94 ** (year - 2015)) * covid_impact(year, "mortality")
        mmr = round(max(5, mmr_base + noise(10)), 0)

        vacc_base = 65 + 28 * f + trend(year, 0, 0.8, 0.5)
        vacc = round(min(99, vacc_base * covid_impact(year, "coverage") + noise(1.5)), 1)

        hosp_base = 0.5 + 3.5 * f + trend(year, 0, 0.05, 0.02)
        hosp = round(min(10, max(0.2, hosp_base + noise(0.1))), 2)

        oop_base = 60 - 45 * f + trend(year, 0, -0.5, 0.3)
        oop = round(min(90, max(5, oop_base + noise(1))), 1)

        uhc_base = 30 + 55 * f + trend(year, 0, 1.2, 0.4)
        uhc = round(min(95, uhc_base * covid_impact(year, "coverage") + noise(1)), 1)

        timeseries.append({
            "year": year, "country": country, "region": region,
            "life_expectancy": le,
            "u5_mortality_rate": u5mr,
            "maternal_mortality_ratio": mmr,
            "vaccination_coverage": vacc,
            "hospital_beds_per_1k": hosp,
            "out_of_pocket_pct": oop,
            "uhc_index": uhc,
        })

# ── Disease burden ────────────────────────────────────────────────────────────
disease_burden = []
for region, meta in REGIONS.items():
    f = meta["gdp_factor"]
    for disease in DISEASES:
        # DALYs per 100k — varies by disease and region
        if disease == "Malaria":
            base_daly = max(10, 8000 * (1 - f) + noise(200))
        elif disease == "HIV/AIDS":
            base_daly = max(20, 5000 * (1 - f * 0.7) + noise(150))
        elif disease == "Cardiovascular Disease":
            base_daly = 3000 + 2000 * f + noise(200)
        elif disease == "Diabetes":
            base_daly = 800 + 1500 * f + noise(100)
        elif disease == "Cancer":
            base_daly = 1000 + 2500 * f + noise(200)
        elif disease == "Mental Health":
            base_daly = 1200 + 800 * f + noise(100)
        elif disease == "Tuberculosis":
            base_daly = max(30, 3500 * (1 - f) + noise(100))
        elif disease == "Diarrheal Diseases":
            base_daly = max(20, 4000 * (1 - f) ** 1.5 + noise(150))
        elif disease == "Malnutrition":
            base_daly = max(10, 5000 * (1 - f) ** 2 + noise(200))
        else:  # Respiratory
            base_daly = 1500 + noise(200)

        disease_burden.append({
            "region": region,
            "disease": disease,
            "dalys_per_100k": round(max(10, base_daly), 0),
            "color": meta["color"]
        })

# ── SDG health indicators (latest year) ──────────────────────────────────────
sdg_indicators = []
sdg_metrics = [
    {"id": "SDG 3.1", "name": "Maternal Mortality", "unit": "per 100k", "target": 70},
    {"id": "SDG 3.2", "name": "Child Mortality", "unit": "per 1k live births", "target": 25},
    {"id": "SDG 3.3", "name": "Epidemic Control", "unit": "index 0-100", "target": 90},
    {"id": "SDG 3.4", "name": "NCD Reduction", "unit": "% premature deaths", "target": 17},
    {"id": "SDG 3.8", "name": "UHC Coverage", "unit": "index 0-100", "target": 80},
    {"id": "SDG 3.b", "name": "Essential Medicines", "unit": "% availability", "target": 95},
]
for region, meta in REGIONS.items():
    f = meta["gdp_factor"]
    sdg_indicators.append({
        "region": region,
        "sdg_3_1_progress": round(min(100, 40 + 55 * f + noise(3)), 1),
        "sdg_3_2_progress": round(min(100, 35 + 58 * f + noise(3)), 1),
        "sdg_3_3_progress": round(min(100, 30 + 60 * f + noise(3)), 1),
        "sdg_3_4_progress": round(min(100, 45 + 50 * f + noise(3)), 1),
        "sdg_3_8_progress": round(min(100, 30 + 55 * f + noise(3)), 1),
        "sdg_3b_progress": round(min(100, 40 + 52 * f + noise(3)), 1),
        "color": meta["color"]
    })

# ── Health financing ──────────────────────────────────────────────────────────
financing = []
for region, meta in REGIONS.items():
    f = meta["gdp_factor"]
    financing.append({
        "region": region,
        "govt_health_spending_gdp": round(2 + 6 * f + noise(0.3), 1),
        "external_aid_pct": round(max(0, 25 - 22 * f + noise(2)), 1),
        "private_spending_pct": round(20 + 15 * f + noise(2), 1),
        "oop_pct": round(max(5, 60 - 45 * f + noise(3)), 1),
        "color": meta["color"]
    })

# ── Pack everything ───────────────────────────────────────────────────────────
output = {
    "metadata": {
        "title": "Global Health Status Analytics 2015-2024",
        "generated": "2024-01-15",
        "sources": ["WHO Global Health Observatory", "World Bank Health Data",
                    "IHME Global Burden of Disease", "UN SDG Database"],
        "note": "Synthetic dataset generated for analytical demonstration"
    },
    "timeseries": timeseries,
    "disease_burden": disease_burden,
    "sdg_indicators": sdg_indicators,
    "financing": financing,
    "regions": {k: {"color": v["color"], "gdp_factor": v["gdp_factor"]} for k, v in REGIONS.items()},
    "countries": COUNTRIES,
    "years": YEARS,
    "diseases": DISEASES,
}

with open("global_health_data.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"✓ Generated {len(timeseries)} time-series records")
print(f"✓ Generated {len(disease_burden)} disease-burden records")
print(f"✓ Generated {len(sdg_indicators)} SDG indicator records")
print(f"✓ Generated {len(financing)} financing records")
print("✓ Saved to global_health_data.json")
