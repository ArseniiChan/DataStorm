# Question 2: Vehicle Exemptions & Repeat Violators

**Analyst:** Diana Lucero  
**Question:** "Which vehicles are exempt from fines, are they repeated, which vehicles frequently violate?"

## 🎯 Analysis Objective

Investigate patterns in vehicle exemptions and identify repeat violators in MTA Bus ACE violations, with focus on CUNY-serving routes.

## 📊 Key Findings

### Exemption Analysis

- **Total exempt violations:** 38% of all violations (13,024 out of 34,274)
- **Main exemption categories:** Violation Issue (highest), Exempt Emergency, Driver/Vehicle, Technical Issue
- **Policy impact:** High exemption rate suggests potential policy review needed

### Repeat Violator Analysis

- **Unique vehicles:** 20,513 total vehicles in dataset
- **Repeat violators:** 22.7% have multiple violations (4,664 vehicles)
- **Chronic violators:** 251 vehicles with 10+ violations
- **Top violator:** Vehicle ID c45c0ba983b1 with 108 violations

### Business Impact

- **Enforcement concentration:** 22.7% of vehicles account for disproportionate violations
- **Chronic offender problem:** 251 vehicles with extreme violation patterns
- **Revenue considerations:** 38% exemption rate impacts fine collection

## 📈 Visualizations

1. **Exemption Status Breakdown** - Shows 7 categories of violation status
2. **Repeat Violator Distribution** - Most vehicles are single violators, but significant repeat offender population
3. **Top Violator Rankings** - Top 10 violators range from 77-108 violations each
4. **Exempt vs Non-Exempt Split** - Clear 62%/38% division

## 💼 Business Recommendations

1. **🎯 Target Enforcement:** Focus on 4,664 repeat violators responsible for disproportionate violations
2. **📋 Review Exemptions:** 38% exemption rate suggests policy review needed
3. **💰 Enhanced Penalties:** Implement escalating fines for 251 chronic violators
4. **🔍 Investigation Priority:** Vehicle with 108 violations requires immediate attention

## 🔧 Technical Approach

### Data Processing

- **Dataset:** MTA Bus ACE Violations (100K records downloaded, 34K CUNY-filtered)
- **Filtering:** 24 CUNY-serving bus routes analyzed
- **Cleaning:** Standardized vehicle IDs, categorized exemption status

### Analysis Methods

- Frequency analysis of vehicle IDs for repeat patterns
- Exemption status classification using keyword matching
- Statistical categorization of violation frequency
- Top violator identification and ranking

### Tools Used

- **Python:** pandas, matplotlib, seaborn
- **Data Source:** NYC Open Data (Socrata API)
- **Visualizations:** 4-panel dashboard with multiple chart types

## 📁 Files Generated

### Data Files

- `q2_full_dataset_20250923_2345.csv` - Full processed dataset (34,274 records)
- `top_violators_20250923_2345.csv` - Top 50 repeat violator rankings
- `exemption_summary_20250923_2345.csv` - Exemption status breakdown

### Visualizations

- `q2_dashboard_20250923_2345.png` - Main 4-panel analysis dashboard
- Individual charts for exemption status, repeat patterns, and top violators

### Scripts

- `q2_analysis.py` - Complete analysis pipeline
- Raw data automatically saved to `data/raw/`

## 🚀 How to Run

```bash
# Install requirements
pip install pandas sodapy matplotlib seaborn

# Run main analysis from DataStorm root
python question_2/q2_analysis.py

# Results automatically saved to question_2/results/
```

## 📝 Methodology Notes

- **Sample Size:** 34,274 violations across 20,513 unique vehicles
- **Time Period:** Recent data from NYC Open Data (2024-2025)
- **Geographic Scope:** 24 CUNY-serving bus routes in NYC
- **Data Quality:** Vehicle IDs used instead of license plates due to data structure
- **Limitations:** Anonymous vehicle IDs prevent cross-referencing with other datasets

## 📈 Statistical Summary

- **Mean violations per vehicle:** 1.67
- **Violation distribution:** Highly skewed toward single violators
- **Repeat violator threshold:** 2+ violations (22.7% of vehicles)
- **Chronic violator threshold:** 10+ violations (1.2% of vehicles)
- **Maximum violations:** 108 (extreme outlier requiring investigation)

## 🔗 Integration with Team Analysis

- **Connects to Q1:** Speed violations can be cross-referenced with repeat offender patterns
- **Connects to Q3:** Manhattan CBD repeat violators may be affected by congestion pricing
- **Overall Impact:** Provides enforcement-focused perspective showing concentration of violations among small subset of vehicles

## 💡 Key Insights for Policy

1. **Enforcement Efficiency:** Focus resources on 4,664 repeat violators rather than broad enforcement
2. **Exemption Policy:** 38% exemption rate warrants review of exemption criteria and abuse
3. **Escalating Penalties:** Current system allows vehicles to accumulate 100+ violations
4. **Data Integration:** Vehicle tracking across violation types could improve enforcement
