# MHC++ x MTA Datathon 2025 — DataStorm

## Team

- Arsenii
- Diana
- Bekbol
- Lin

## Datasets Used

- MTA Bus Automated Camera Enforcement (ACE) Violations ([data.ny.gov](https://data.ny.gov/Transportation/MTA-Bus-Automated-Camera-Enforcement-Violations-Be/kh8p-hcbm/about_data))
- MTA Bus Route Segment Speeds (2023–2024) ([data.ny.gov](https://data.ny.gov/Transportation/MTA-Bus-Route-Segment-Speeds-2023-2024/58t6-89vi/about_data))
- Additional CUNY-circulated resource ([link](https://cuny.us10.list-manage.com/track/click?u=216b1617c48eebdeb97773f8c&id=e460bceea7&e=dec3d052e0))

## Questions Answered

1. MTA bus routes used by CUNY students: how have camera‑enforced speeds changed over time?
   - Compare cross‑campus routes; compare ACE vs non‑ACE on campus routes
2. Which vehicles are exempt from fines, are they repeated, and which vehicles frequently violate?
   - Visualize exemption breakdown and repeat violators
3. How have violations on routes traveling in the Manhattan Central Business District changed with congestion pricing?
   - Compare before vs after pricing; map/visual comparisons

## Video Summary
- DataStorm submission overview ([link](https://youtu.be/45NB7nAIKMs))

## Quick Start

- Place input CSVs under `data/` (flat folder). For large files, prefer Git LFS or download at runtime.
- Run each analysis from the repo root:
  - Q1 (Speeds):
    ```bash
    python question_1/q1_analysis.py
    ```
  - Q2 (Exemptions & Repeat Violators):
    ```bash
    python question_2/q2_analysis.py
    ```
  - Q3 (CBD & Congestion Pricing):
    ```bash
    python question_3/q3_analysis.py
    ```

## Outputs

- `question_1/results/`: `q1_ace_vs_nonace.png`, `q1_top_route_changes.png`, `q1_summary_report.md`
- `question_2/results/`: `q2_dashboard_YYYYMMDD_HHMM.png`, `q2_summary_report.md`
- `question_3/results/`: `q3_congestion_pricing_analysis.png`, `route_comparison_chart.png`, `q3_summary_report.md`

## Notes

- Data loaders scan `data/` (and legacy `data/raw/`) for expected CSVs and normalize columns.
- If no pre‑pricing data exists for Q3, the report indicates that net change isn’t computable and charts adapt accordingly.
