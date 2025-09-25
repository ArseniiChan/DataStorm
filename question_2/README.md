# Question 2: Vehicle Exemptions & Repeat Violators

**Analyst:** Diana Lucero  
**Question:** "Which vehicles are exempt from fines, are they repeated, which vehicles frequently violate?"

## How to Run

```bash
python question_2/q2_analysis.py
```

- Uses local ACE CSVs in `data/raw/` if present; otherwise downloads a recent sample (not saved if `data/raw/` is missing).
- Outputs are saved to `question_2/results/`.

## Outputs

- `q2_dashboard_YYYYMMDD_HHMM.png` — two-panel dashboard (status distribution, exempt vs non-exempt)
- `q2_summary_report.md` — short narrative summary with key counts

(Previously exported files like `key_insights.json`, `top_violators.csv`, `exemption_summary.csv`, and the full dataset CSV are now disabled to keep the deliverables lean.)

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

## 💼 Business Recommendations

1. **🎯 Target Enforcement:** Focus on 4,664 repeat violators responsible for disproportionate violations
2. **📋 Review Exemptions:** 38% exemption rate suggests policy review needed
3. **💰 Enhanced Penalties:** Implement escalating fines for 251 chronic violators
4. **🔍 Investigation Priority:** Vehicle with 108 violations requires immediate attention

## 🔧 Technical Approach

### Data Processing

- **Dataset:** MTA Bus ACE Violations
- **Filtering:** CUNY-serving bus routes analyzed
- **Cleaning:** Standardized vehicle IDs, categorized exemption status

### Analysis Methods

- Frequency analysis of vehicle IDs for repeat patterns
- Exemption status classification using keyword matching
- Statistical categorization of violation frequency
- Top violator identification and ranking

### Tools Used

- **Python:** pandas, matplotlib, seaborn
- **Data Source:** NYC Open Data (Socrata API)

## 📝 Methodology Notes

- **Geographic Scope:** 24 CUNY-serving bus routes in NYC
- **Data Quality:** Vehicle IDs used instead of license plates due to data structure
- **Limitations:** Anonymous vehicle IDs prevent cross-referencing with other datasets
