# Question 1: CUNY Bus Routes Speed Trends

This analysis compares MTA bus route segment speeds across pre- and post- windows for routes used by CUNY students, with optional tagging of segments near campuses and ACE vs non-ACE route comparisons.

## Inputs

Place files in `data/raw/`:

- `speeds_05_2024_to_08_2024.csv`
- `speeds_05_2025_to_08_2025.csv`
- `ace_violations_05_2024_to_08_2024.csv`
- `ace_violations_05_2025_to_08_2025.csv`
- Optional: `cuny_campuses.csv` with columns: `name, latitude, longitude`

## Run

```bash
python question_1/q1_analysis.py
```

## Outputs (in `question_1/results/`)

- `q1_ace_vs_nonace.png`: Average speed by period for ACE vs non-ACE routes
- `q1_top_route_changes.png`: Top routes by post - pre speed change (mph)
- `q1_summary_report.md`: Short narrative summary
