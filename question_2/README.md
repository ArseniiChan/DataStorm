# Question 2: Vehicle Exemptions & Repeat Violators

**Analyst:** Diana Lucero
**Question:** "Which vehicles are exempt from fines, are they repeated, which vehicles frequently violate?"

## 🎯 Analysis Objective

Investigate patterns in vehicle exemptions and identify repeat violators in MTA Bus ACE violations, with focus on CUNY-serving routes.

## 📊 Key Findings

### Exemption Analysis

- **Total exempt violations:** [X]% of all violations
- **Main exemption categories:** Emergency, Official, Police vehicles
- **Exemption abuse:** [Finding about whether exempt vehicles are repeat offenders]

### Repeat Violator Analysis

- **Unique vehicles:** [X] total vehicles in dataset
- **Repeat violators:** [X]% have multiple violations
- **Chronic violators:** [X] vehicles with 10+ violations
- **Top violator:** [License plate] with [X] violations

### Business Impact

- **Revenue loss:** $[X] in exempt violations
- **Enforcement efficiency:** [X]% of violations from [Y]% of vehicles

## 📈 Visualizations

1. **Exemption Status Breakdown** - `results/q2_exemptions_dashboard.png`
2. **Repeat Violator Distribution** - Shows violation frequency patterns
3. **Top Violator Rankings** - Chronic offender identification
4. **Exempt vs Non-Exempt Patterns** - Comparison analysis

## 💼 Business Recommendations

1. **🎯 Target Enforcement:** Focus on [X] repeat violators responsible for [Y]% of violations
2. **📋 Review Exemptions:** [X]% exemption rate suggests policy review needed
3. **💰 Enhanced Penalties:** Implement escalating fines for repeat offenders
4. **🗺️ Hotspot Mapping:** Deploy cameras at locations with highest repeat violations

## 🔧 Technical Approach

### Data Processing

- **Dataset:** MTA Bus ACE Violations (150K+ records)
- **Filtering:** CUNY-serving routes only
- **Cleaning:** Standardized license plates, categorized exemption status

### Analysis Methods

- Frequency analysis of license plates
- Exemption status classification
- Statistical analysis of repeat patterns
- Geographic clustering (planned)

### Tools Used

- **Python:** pandas, seaborn, plotly
- **Data Source:** NYC Open Data (Socrata API)
- **Visualizations:** Static charts + interactive dashboards

## 📁 Files Generated

### Data Files

- `q2_exemptions_repeats.csv` - Full processed dataset
- `q2_top_violators.csv` - Repeat violator rankings
- `q2_exemption_summary.csv` - Exemption status breakdown

### Visualizations

- `q2_exemptions_dashboard.png` - Main analysis dashboard
- `q2_repeat_patterns.png` - Violation frequency charts

### Scripts

- `q2_analysis.py` - Main analysis code
- `data_exploration.py` - Initial data investigation

## 🚀 How to Run

```bash
# Install requirements
pip install pandas sodapy matplotlib seaborn plotly

# Run main analysis
python q2_analysis.py

# Results saved to results/ folder
```

## 📝 Methodology Notes

- **Sample Size:** [X] violations across [Y] unique vehicles
- **Time Period:** [Date range]
- **Geographic Scope:** CUNY-serving bus routes in NYC
- **Limitations:** [Any data quality issues or scope limitations]

## 🔗 Integration with Team Analysis

- **Connects to Q1:** Speed violations can be cross-referenced with repeat offender data
- **Connects to Q3:** Manhattan CBD repeat violators affected by congestion pricing
- **Overall Impact:** Provides violator-focused perspective on enforcement effectiveness
