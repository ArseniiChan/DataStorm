import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


plt.style.use("default")
sns.set_palette("husl")


def get_project_paths() -> Dict[str, Path]:
    """Return resolved project paths used by the analysis script."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    results_dir = script_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return {
        "root": project_root,
        "raw": raw_dir,
        "processed": processed_dir,
        "results": results_dir,
    }


def read_large_csv_header(path: Path) -> List[str]:
    """Read header of a large CSV without loading entire file."""
    with path.open("r", encoding="utf-8", newline="") as f:
        first_line = f.readline().rstrip("\n")
    return [c.strip() for c in first_line.split(",")]


def load_speeds(files: List[Path]) -> pd.DataFrame:
    """Load and normalize speeds datasets across provided files.

    Expects Socrata export schema with columns such as:
    Year, Month, Timestamp, Day of Week, Hour of Day, Route ID, Direction,
    Borough, Route Type, Stop Order, Timepoint Stop ID, Timepoint Stop Name,
    Timepoint Stop Latitude, Timepoint Stop Longitude, Next Timepoint Stop ID,
    Next Timepoint Stop Name, Next Timepoint Stop Latitude,
    Next Timepoint Stop Longitude, Road Distance, Average Travel Time,
    Average Road Speed, Bus Trip Count, Timepoint Stop Georeference,
    Next Timepoint Stop Georeference
    """
    frames: List[pd.DataFrame] = []

    for fp in files:
        if not fp.exists():
            continue
        df = pd.read_csv(fp)

        rename = {
            "Route ID": "route_id",
            "Timestamp": "timestamp",
            "Average Road Speed": "avg_speed_mph",
            "Year": "year",
            "Month": "month",
            "Borough": "borough",
            "Direction": "direction",
            "Timepoint Stop ID": "tp_stop_id",
            "Timepoint Stop Name": "tp_stop_name",
            "Timepoint Stop Latitude": "tp_stop_lat",
            "Timepoint Stop Longitude": "tp_stop_lon",
            "Next Timepoint Stop ID": "next_tp_stop_id",
            "Next Timepoint Stop Name": "next_tp_stop_name",
            "Next Timepoint Stop Latitude": "next_tp_stop_lat",
            "Next Timepoint Stop Longitude": "next_tp_stop_lon",
        }
        df = df.rename(columns=rename)

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        else:
            # Fallback: construct from year-month if available
            if {"year", "month"}.issubset(df.columns):
                df["timestamp"] = pd.to_datetime(
                    df["year"].astype(str) + "-" +
                    df["month"].astype(str) + "-01",
                    errors="coerce",
                )

        # Ensure types
        for c in ["avg_speed_mph"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        for c in ["tp_stop_lat", "tp_stop_lon", "next_tp_stop_lat", "next_tp_stop_lon"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        # Period label from filename for clarity
        df["source_file"] = fp.name
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    all_speeds = pd.concat(frames, ignore_index=True)
    # Normalize route id
    if "route_id" in all_speeds.columns:
        all_speeds["route_id"] = all_speeds["route_id"].astype(str)
    return all_speeds


def load_ace_routes(ace_files: List[Path]) -> pd.DataFrame:
    """Load ACE violations for given files and return a route-level set per period.

    Output columns: route_id, first_occurrence, period_label
    """
    frames: List[pd.DataFrame] = []
    for fp in ace_files:
        if not fp.exists():
            continue
        df = pd.read_csv(fp)

        # Harmonize columns case and names
        lower_cols = {c.lower(): c for c in df.columns}
        # Accept both snake and title case
        route_col = None
        for candidate in ["bus_route_id", "route id", "route_id"]:
            if candidate in lower_cols:
                route_col = lower_cols[candidate]
                break
        if route_col is None:
            # Try contains
            for c in df.columns:
                if "route" in c.lower():
                    route_col = c
                    break

        date_col = None
        for candidate in ["first_occurrence", "first occurrence"]:
            if candidate in lower_cols:
                date_col = lower_cols[candidate]
                break
        if date_col is None:
            for c in df.columns:
                if "first" in c.lower() and "occurrence" in c.lower():
                    date_col = c
                    break

        if route_col is None or date_col is None:
            continue

        df = df[[route_col, date_col]].rename(
            columns={route_col: "route_id", date_col: "first_occurrence"})
        df["first_occurrence"] = pd.to_datetime(
            df["first_occurrence"], errors="coerce")
        df["route_id"] = df["route_id"].astype(str)

        # Derive simple period label from filename
        period_label = "pre" if "2024" in fp.name or "05_2024" in fp.name else "post"
        df["period_label"] = period_label
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=["route_id", "first_occurrence", "period_label"])

    return pd.concat(frames, ignore_index=True)


def haversine_distance_m(lat1: np.ndarray, lon1: np.ndarray, lat2: float, lon2: float) -> np.ndarray:
    """Compute haversine distance in meters from arrays (lat1, lon1) to a single point (lat2, lon2)."""
    R = 6371000.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * \
        np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def tag_near_campus(speed_df: pd.DataFrame, campuses: pd.DataFrame, radius_m: float = 750.0) -> pd.DataFrame:
    """Tag route segments as near a campus if either endpoint is within radius meters of any campus."""
    if speed_df.empty or campuses.empty:
        speed_df["near_campus"] = False
        return speed_df

    near_any = np.zeros(len(speed_df), dtype=bool)
    # Use timepoint stop lat/lon if available; otherwise fallback to next
    lat_cols = [c for c in ["tp_stop_lat", "next_tp_stop_lat"]
                if c in speed_df.columns]
    lon_cols = [c for c in ["tp_stop_lon", "next_tp_stop_lon"]
                if c in speed_df.columns]
    if not lat_cols or not lon_cols:
        speed_df["near_campus"] = False
        return speed_df

    lat_base = speed_df[lat_cols[0]].astype(float).to_numpy()
    lon_base = speed_df[lon_cols[0]].astype(float).to_numpy()

    for _, row in campuses.iterrows():
        dist = haversine_distance_m(lat_base, lon_base, float(
            row["latitude"]), float(row["longitude"]))
        near_any |= dist <= radius_m

    speed_df["near_campus"] = near_any
    return speed_df


def build_analysis_frames(speeds: pd.DataFrame, ace_routes: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Prepare frames for trend and comparison analysis.

    Returns a tuple: (route_period_summary, campus_route_summary, speeds_enriched)
    """
    if speeds.empty:
        return pd.DataFrame(), pd.DataFrame(), speeds

    speeds = speeds.copy()

    # Identify pre/post from file name pattern
    def infer_period(name: str) -> str:
        name = name.lower()
        if "2024" in name:
            return "pre"
        if "2025" in name:
            return "post"
        # fallback by timestamp year
        return "post" if speeds["timestamp"].dt.year.median() >= 2025 else "pre"

    if "source_file" in speeds.columns:
        speeds["period_label"] = speeds["source_file"].apply(infer_period)
    else:
        speeds["period_label"] = np.where(
            speeds["timestamp"].dt.year >= 2025, "post", "pre")

    # ACE route tagging
    ace_tag = pd.Series(False, index=speeds.index)
    if not ace_routes.empty:
        for period in ["pre", "post"]:
            routes = set(
                ace_routes.loc[ace_routes["period_label"] == period, "route_id"].unique())
            mask = speeds["period_label"].eq(
                period) & speeds["route_id"].isin(routes)
            ace_tag |= mask
    speeds["ace_route"] = ace_tag

    # Trend by route and period
    speeds["year_month"] = speeds["timestamp"].dt.to_period("M")
    route_summary = (
        speeds.dropna(subset=["avg_speed_mph"]).groupby(["route_id", "period_label", "year_month"]).agg(
            avg_speed_mph=("avg_speed_mph", "mean"),
            trip_count=(
                "Bus Trip Count" if "Bus Trip Count" in speeds.columns else "avg_speed_mph", "count"),
        ).reset_index()
    )

    # Route-level pre vs post delta
    route_level = (
        speeds.dropna(subset=["avg_speed_mph"]).groupby(["route_id", "period_label"]).agg(
            avg_speed_mph=("avg_speed_mph", "mean"),
        ).reset_index().pivot(index="route_id", columns="period_label", values="avg_speed_mph").reset_index()
    )
    if "pre" not in route_level.columns:
        route_level["pre"] = np.nan
    if "post" not in route_level.columns:
        route_level["post"] = np.nan
    route_level["delta_mph"] = route_level["post"] - route_level["pre"]

    # Campus-filtered summary if available
    campus_summary = pd.DataFrame()
    if "near_campus" in speeds.columns:
        campus_summary = (
            speeds.loc[speeds["near_campus"]].dropna(subset=["avg_speed_mph"]).groupby(["route_id", "period_label"]).agg(
                avg_speed_mph=("avg_speed_mph", "mean"),
            ).reset_index().pivot(index="route_id", columns="period_label", values="avg_speed_mph").reset_index()
        )
        if "pre" not in campus_summary.columns:
            campus_summary["pre"] = np.nan
        if "post" not in campus_summary.columns:
            campus_summary["post"] = np.nan
        campus_summary["delta_mph"] = campus_summary["post"] - \
            campus_summary["pre"]

    return route_level, campus_summary, speeds


def create_visualizations(route_level: pd.DataFrame, speeds: pd.DataFrame, results_dir: Path) -> None:
    """Create summary visualizations for Q1."""
    if speeds.empty:
        return

    # 1) ACE vs non-ACE comparison by period
    fig, ax = plt.subplots(figsize=(8, 5))
    bar = (
        speeds.dropna(subset=["avg_speed_mph"]).groupby(["period_label", "ace_route"]).agg(
            avg_speed_mph=("avg_speed_mph", "mean")
        )
    )
    bar = bar.reset_index()
    bar["ace_label"] = np.where(
        bar["ace_route"], "ACE routes", "Non-ACE routes")
    sns.barplot(data=bar, x="period_label",
                y="avg_speed_mph", hue="ace_label", ax=ax)
    ax.set_title(
        "Average Road Speed: ACE vs Non-ACE (CUNY-focused routes optional)")
    ax.set_xlabel("Period")
    ax.set_ylabel("Average speed (mph)")
    ax.legend(title="Route Type")
    plt.tight_layout()
    plt.savefig(results_dir / "q1_ace_vs_nonace.png",
                dpi=300, bbox_inches="tight")
    plt.close(fig)

    # 2) Top routes by pre->post change (delta)
    if not route_level.empty and route_level[["pre", "post"]].notna().any().any():
        top_changes = route_level.dropna(subset=["delta_mph"])\
            .sort_values("delta_mph", ascending=False).head(12)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=top_changes, y="route_id",
                    x="delta_mph", ax=ax, color="steelblue")
        ax.set_title("Top Routes by Speed Change (Post - Pre, mph)")
        ax.set_xlabel("Change in avg speed (mph)")
        ax.set_ylabel("Route")
        plt.tight_layout()
        plt.savefig(results_dir / "q1_top_route_changes.png",
                    dpi=300, bbox_inches="tight")
        plt.close(fig)


def generate_summary(route_level: pd.DataFrame, speeds: pd.DataFrame, results_dir: Path) -> None:
    """Write a concise Markdown summary of findings for Q1."""
    if speeds.empty:
        summary = "# Q1 Summary\n\nNo speeds data loaded."
    else:
        overall = (
            speeds.dropna(subset=["avg_speed_mph"]).groupby(["period_label"]).agg(
                avg_speed_mph=("avg_speed_mph", "mean")
            ).reset_index()
        )
        pre = overall.loc[overall["period_label"].eq(
            "pre"), "avg_speed_mph"].mean()
        post = overall.loc[overall["period_label"].eq(
            "post"), "avg_speed_mph"].mean()
        delta = (post - pre) if pd.notna(pre) and pd.notna(post) else np.nan

        summary = [
            "# Question 1: CUNY Routes Speed Trends",
            "",
            "This report compares MTA bus route segment speeds across pre- and post- periods,",
            "with optional tagging for CUNY campus-adjacent segments and ACE vs non-ACE routes.",
            "",
            f"Overall average speed (pre): {pre:.2f} mph" if pd.notna(
                pre) else "Overall average speed (pre): N/A",
            f"Overall average speed (post): {post:.2f} mph" if pd.notna(
                post) else "Overall average speed (post): N/A",
            f"Change (post - pre): {delta:+.2f} mph" if pd.notna(
                delta) else "Change (post - pre): N/A",
            "",
            "See figures: `q1_ace_vs_nonace.png`, `q1_top_route_changes.png`.",
        ]
        summary = "\n".join(summary)

    (results_dir / "q1_summary_report.md").write_text(summary)


def main() -> None:
    paths = get_project_paths()

    # Locate expected files uploaded by user
    speed_files = [
        paths["raw"] / "speeds_05_2024_to_08_2024.csv",
        paths["raw"] / "speeds_05_2025_to_08_2025.csv",
    ]
    speeds = load_speeds(speed_files)
    if speeds.empty:
        print("No speeds data found. Expected speeds_05_2024_to_08_2024.csv and speeds_05_2025_to_08_2025.csv in data/raw/")
        return

    # Optional campus list file
    campus_file = paths["raw"] / "cuny_campuses.csv"
    campuses = pd.DataFrame()
    if campus_file.exists():
        campuses = pd.read_csv(campus_file)
        # Expect columns: name, latitude, longitude
        needed = {"name", "latitude", "longitude"}
        if not needed.issubset(set(campuses.columns.str.lower())):
            # Try to standardize column names
            rename = {c: c.lower() for c in campuses.columns}
            campuses = campuses.rename(columns=rename)
        if {"latitude", "longitude"}.issubset(campuses.columns):
            speeds = tag_near_campus(speeds, campuses)
        else:
            speeds["near_campus"] = False
    else:
        speeds["near_campus"] = False

    # ACE route tagging from violations files
    ace_files = [
        paths["raw"] / "ace_violations_05_2024_to_08_2024.csv",
        paths["raw"] / "ace_violations_05_2025_to_08_2025.csv",
    ]
    ace_routes = load_ace_routes(ace_files)

    # Build frames and create outputs
    route_level, campus_summary, speeds_enriched = build_analysis_frames(
        speeds, ace_routes)

    create_visualizations(route_level, speeds_enriched, paths["results"])
    generate_summary(route_level, speeds_enriched, paths["results"])

    print("Analysis complete. Results saved to:")
    print(f" - {paths['results'] / 'q1_ace_vs_nonace.png'}")
    print(f" - {paths['results'] / 'q1_top_route_changes.png'}")
    print(f" - {paths['results'] / 'q1_summary_report.md'}")


if __name__ == "__main__":
    main()
