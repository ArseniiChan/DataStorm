import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

# Set styling
plt.style.use('default')
sns.set_palette("husl")


def load_ace_violations_data():
    """Load ACE violations from data/ or data/raw (multiple filenames supported), normalize, and combine.

    Supports files like:
    - ace_violations_05_2024_to_08_2024.csv
    - ace_violations_05_2025_to_08_2025.csv
    - MTA_Bus_Automated_Camera_Enforcement_Violations__Beginning_October_2019_*.csv
    - ace_violations_raw_*.csv
    """
    print("Loading ACE violations data...")

    # Resolve base dirs relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_base = os.path.abspath(os.path.join(script_dir, '..', 'data'))
    legacy_raw = os.path.join(data_base, 'raw')

    search_dirs = [d for d in [data_base, legacy_raw] if os.path.isdir(d)]
    if not search_dirs:
        print(f"  - Missing data dirs: {data_base} (and legacy {legacy_raw})")
        return pd.DataFrame()

    # Gather candidate CSVs
    candidates = []
    for d in search_dirs:
        for fn in os.listdir(d):
            if not fn.lower().endswith('.csv'):
                continue
            name = fn.lower()
            if ('ace' in name and 'violation' in name) or ('automated_camera_enforcement' in name):
                candidates.append(os.path.join(d, fn))

    if not candidates:
        print("Error: No ACE files found in data/ or data/raw.")
        return pd.DataFrame()

    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        # Harmonize columns from possible title/snake cases
        rename_map = {
            'Violation ID': 'violation_id',
            'Vehicle ID': 'vehicle_id',
            'First Occurrence': 'first_occurrence',
            'Last Occurrence': 'last_occurrence',
            'Violation Status': 'violation_status',
            'Violation Type': 'violation_type',
            'Bus Route ID': 'bus_route_id',
            'Violation Latitude': 'violation_latitude',
            'Violation Longitude': 'violation_longitude',
            'Stop ID': 'stop_id',
            'Stop Name': 'stop_name',
            'Bus Stop Latitude': 'bus_stop_latitude',
            'Bus Stop Longitude': 'bus_stop_longitude',
            'Violation Georeference': 'violation_georeference',
            'Bus Stop Georeference': 'bus_stop_georeference',
        }
        df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})
        for col in ['first_occurrence', 'last_occurrence']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        for col in [c for c in df.columns if any(k in c.lower() for k in ['lat', 'lon'])]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'bus_route_id' in df.columns:
            df['bus_route_id'] = df['bus_route_id'].astype(str)
        return df

    frames = []
    for path in sorted(candidates):
        try:
            print(f"  - Reading: {os.path.basename(path)}")
            df = pd.read_csv(path)
            df = normalize(df)
            frames.append(df)
        except Exception as e:
            print(f"  - Error reading {path}: {e}")

    if not frames:
        print("Error: Failed to load ACE CSVs")
        return pd.DataFrame()

    all_df = pd.concat(frames, ignore_index=True)
    if 'violation_id' in all_df.columns:
        before = len(all_df)
        all_df = all_df.drop_duplicates(subset=['violation_id'])
        print(f"  De-duplicated: {before:,} -> {len(all_df):,}")

    print(f"Loaded {len(all_df):,} violation records")
    if 'first_occurrence' in all_df.columns:
        print(
            f"Date range: {all_df['first_occurrence'].min()} -> {all_df['first_occurrence'].max()}")

    return all_df


def identify_manhattan_cbd_routes(df):
    """
    Identify bus routes that travel within or cross Manhattan's Central Business District
    """

    print("\nIdentifying Manhattan CBD routes...")

    # Manhattan routes that cross or travel within CBD (south of 61st Street)
    # These are the key routes for congestion pricing analysis
    manhattan_cbd_routes = [
        # Crosstown routes (clearly in CBD)
        'M14A', 'M14D',      # 14th Street
        'M23',               # 23rd Street
        'M34A', 'M34',       # 34th Street
        'M42',               # 42nd Street
        'M57',               # 57th Street

        # North-South routes that enter/cross CBD
        'M15',               # 1st Avenue
        'M2',                # Madison Avenue
        'M3',                # 5th Avenue/Amsterdam
        'M4',                # Broadway
        'M5',                # 5th Avenue/Riverside
        'M6',                # Broadway/6th Avenue
        'M7',                # 6th/7th Avenue
        'M8',                # 8th Street
        'M9',                # Avenue C/6th Avenue
        'M20',               # 7th/8th Avenue
        'M21',               # Houston Street
        'M101',              # Lexington/3rd Avenue
        'M103',              # Lexington Avenue

        # SBS (Select Bus Service) equivalents
        'M15+', 'M34+', 'M23+', 'M14+', 'M60+', 'M79+'
    ]

    # Filter for routes that match our CBD list
    # Use flexible matching in case route names have variations
    route_column = None
    for col in df.columns:
        if 'route' in col.lower() or 'line' in col.lower():
            route_column = col
            break

    if route_column is None:
        print("Warning: Could not identify route column in data")
        return df, manhattan_cbd_routes

    # Create mask for Manhattan CBD routes
    cbd_mask = df[route_column].astype(str).str.contains(
        '|'.join(manhattan_cbd_routes), na=False)
    cbd_df = df[cbd_mask].copy()

    # Add geographic boundary check for CBD zone
    lat_col = None
    lon_col = None
    for col in df.columns:
        if 'lat' in col.lower() and lat_col is None:
            lat_col = col
        if 'lon' in col.lower() and lon_col is None:
            lon_col = col

    if lat_col and lon_col:
        # CBD boundaries (approximate)
        cbd_south = 40.7047   # Around Houston Street
        cbd_north = 40.7614   # Around 61st Street
        cbd_west = -74.0150   # West Side Highway
        cbd_east = -73.9441   # East River

        cbd_df['in_cbd_zone'] = (
            (cbd_df[lat_col] >= cbd_south) &
            (cbd_df[lat_col] <= cbd_north) &
            (cbd_df[lon_col] >= cbd_west) &
            (cbd_df[lon_col] <= cbd_east)
        )
    else:
        # Assume all Manhattan routes potentially in CBD
        cbd_df['in_cbd_zone'] = True

    print(f"Found {len(cbd_df):,} violations on Manhattan CBD routes")
    actual_routes = sorted(cbd_df[route_column].unique())
    print(f"Routes found in data: {actual_routes[:10]}...")  # Show first 10

    return cbd_df, manhattan_cbd_routes


def analyze_congestion_pricing_impact(cbd_df):
    """
    Analyze violations before and after congestion pricing implementation
    """

    print("\nAnalyzing congestion pricing impact...")

    # Congestion pricing implementation date
    congestion_start = pd.to_datetime('2025-01-05')

    # Use first_occurrence as the primary date column
    date_col = 'first_occurrence'

    if date_col not in cbd_df.columns:
        print("Warning: first_occurrence column not found")
        return {}

    # Add time period analysis
    cbd_df['post_congestion_pricing'] = cbd_df[date_col] >= congestion_start
    cbd_df['year_month'] = cbd_df[date_col].dt.to_period('M')
    cbd_df['week'] = cbd_df[date_col].dt.to_period('W')

    # Basic statistics
    pre_cp = cbd_df[cbd_df['post_congestion_pricing'] == False]
    post_cp = cbd_df[cbd_df['post_congestion_pricing'] == True]

    results = {
        'total_violations': len(cbd_df),
        'pre_cp_violations': len(pre_cp),
        'post_cp_violations': len(post_cp),
        'congestion_start_date': congestion_start,
        'analysis_date_range': (cbd_df[date_col].min(), cbd_df[date_col].max())
    }

    # Calculate change percentage and track if a true pre-CP period exists
    if len(pre_cp) > 0:
        results['percent_change'] = (
            (len(post_cp) - len(pre_cp)) / len(pre_cp)) * 100
        results['has_pre_period'] = True
    else:
        results['percent_change'] = None
        results['has_pre_period'] = False

    # Monthly trend analysis
    monthly_counts = cbd_df.groupby(
        ['year_month', 'post_congestion_pricing']).size().unstack(fill_value=0)
    results['monthly_trends'] = monthly_counts

    # Route-specific analysis
    route_col = [col for col in cbd_df.columns if 'route' in col.lower()][0]
    route_analysis = []

    for route in cbd_df[route_col].unique():
        route_data = cbd_df[cbd_df[route_col] == route]
        route_pre = route_data[route_data['post_congestion_pricing'] == False]
        route_post = route_data[route_data['post_congestion_pricing'] == True]

        route_stats = {
            'route': route,
            'total_violations': len(route_data),
            'pre_cp_violations': len(route_pre),
            'post_cp_violations': len(route_post),
            'change_percent': ((len(route_post) - len(route_pre)) / len(route_pre) * 100) if len(route_pre) > 0 else 0,
            'cbd_zone_violations': len(route_data[route_data.get('in_cbd_zone', True) == True])
        }
        route_analysis.append(route_stats)

    results['route_analysis'] = pd.DataFrame(
        route_analysis).sort_values('total_violations', ascending=False)

    # Violation type analysis (if available)
    violation_type_col = None
    for col in cbd_df.columns:
        if 'type' in col.lower() and 'violation' in col.lower():
            violation_type_col = col
            break

    if violation_type_col:
        violation_types = cbd_df.groupby(
            [violation_type_col, 'post_congestion_pricing']).size().unstack(fill_value=0)
        results['violation_types'] = violation_types

    print(f"Analysis complete:")
    print(f"  - Pre-CP violations: {results['pre_cp_violations']:,}")
    print(f"  - Post-CP violations: {results['post_cp_violations']:,}")
    if results.get('has_pre_period'):
        print(f"  - Change: {results['percent_change']:+.1f}%")
    else:
        print("  - Change: Not computable (no pre-CP data)")

    return results


def create_visualizations(cbd_df, results):
    """Create comprehensive visualizations for Question 3"""

    print("\nCreating visualizations...")

    # Set up the plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Question 3: Congestion Pricing Impact on CBD Route Violations',
                 fontsize=16, fontweight='bold')

    # 1. Before vs After comparison
    pre_post_data = [results['pre_cp_violations'],
                     results['post_cp_violations']]
    labels = ['Pre-Congestion Pricing\n(Before Jan 5, 2025)',
              'Post-Congestion Pricing\n(After Jan 5, 2025)']
    colors = ['#ff7f0e', '#1f77b4']

    bars = axes[0, 0].bar(labels, pre_post_data, color=colors)
    axes[0, 0].set_title(
        'Total Violations: Before vs After Congestion Pricing')
    axes[0, 0].set_ylabel('Number of Violations')

    # Add percentage change annotation or info when not computable
    if results.get('has_pre_period'):
        change_pct = results['percent_change']
        axes[0, 0].annotate(f'Change: {change_pct:.1f}%',
                            xy=(0.5, max(pre_post_data) * 0.8),
                            ha='center', fontsize=12, fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    else:
        axes[0, 0].annotate('No pre-CP data in this dataset\nChange not computable',
                            xy=(0.5, max(pre_post_data) * 0.8),
                            ha='center', fontsize=12, fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))

    # Add value labels on bars
    for bar, value in zip(bars, pre_post_data):
        axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(pre_post_data)*0.02,
                        f'{value:,}', ha='center', va='bottom', fontweight='bold')

    # 2. Monthly trends (if available)
    if 'monthly_trends' in results and not results['monthly_trends'].empty:
        monthly_data = results['monthly_trends']
        monthly_data.plot(kind='line', ax=axes[0, 1], marker='o', linewidth=2)
        axes[0, 1].set_title('Monthly Violation Trends')
        axes[0, 1].set_xlabel('Month')
        axes[0, 1].set_ylabel('Number of Violations')
        axes[0, 1].legend(['Pre-CP', 'Post-CP'])
        axes[0, 1].grid(True, alpha=0.3)
    else:
        axes[0, 1].text(0.5, 0.5, 'Monthly trends\ndata not available',
                        ha='center', va='center', transform=axes[0, 1].transAxes)

    # 3. Top routes by violations
    if not results['route_analysis'].empty:
        top_routes = results['route_analysis'].head(10)
        axes[1, 0].barh(top_routes['route'],
                        top_routes['total_violations'], color='steelblue')
        axes[1, 0].set_title('Top 10 Routes by Total Violations')
        axes[1, 0].set_xlabel('Total Violations')
        axes[1, 0].set_ylabel('Bus Route')

    # 4. Geographic distribution (if coordinates available)
    if 'in_cbd_zone' in cbd_df.columns:
        cbd_violations = cbd_df[cbd_df['in_cbd_zone'] == True]
        if not cbd_violations.empty:
            # Find coordinate columns
            lat_col = [col for col in cbd_df.columns if 'lat' in col.lower()][0]
            lon_col = [col for col in cbd_df.columns if 'lon' in col.lower()][0]

            scatter = axes[1, 1].scatter(cbd_violations[lon_col], cbd_violations[lat_col],
                                         c=cbd_violations['post_congestion_pricing'],
                                         cmap='RdYlBu_r', alpha=0.6, s=20)
            axes[1, 1].set_title('Violation Locations in CBD Zone')
            axes[1, 1].set_xlabel('Longitude')
            axes[1, 1].set_ylabel('Latitude')

            # Add colorbar
            cbar = plt.colorbar(scatter, ax=axes[1, 1])
            cbar.set_label('Post-Congestion Pricing')
            cbar.set_ticks([0, 1])
            cbar.set_ticklabels(['Pre-CP', 'Post-CP'])
        else:
            axes[1, 1].text(0.5, 0.5, 'No CBD zone\nviolations found',
                            ha='center', va='center', transform=axes[1, 1].transAxes)
    else:
        axes[1, 1].text(0.5, 0.5, 'Geographic data\nnot available',
                        ha='center', va='center', transform=axes[1, 1].transAxes)

    plt.tight_layout()
    plt.savefig('results/q3_congestion_pricing_analysis.png',
                dpi=300, bbox_inches='tight')
    plt.show()

    # Create additional route-specific visualization
    create_route_comparison_chart(results)


def create_route_comparison_chart(results):
    """Create detailed route comparison chart"""

    route_data = results['route_analysis'].head(8)  # Top 8 routes

    fig, ax = plt.subplots(figsize=(12, 6))

    # If no pre-CP data, show a single-series ranking to avoid misleading comparison
    if not results.get('has_pre_period'):
        ax.barh(route_data['route'],
                route_data['total_violations'], color='#1f77b4')
        ax.set_title('Top Routes by Violations (post-CP dataset only)')
        ax.set_xlabel('Total Violations')
        ax.set_ylabel('Bus Route')
        plt.tight_layout()
        plt.savefig('results/route_comparison_chart.png',
                    dpi=300, bbox_inches='tight')
        plt.show()
        return

    x = np.arange(len(route_data))
    width = 0.35

    bars1 = ax.bar(x - width/2, route_data['pre_cp_violations'], width,
                   label='Pre-Congestion Pricing', color='#ff7f0e')
    bars2 = ax.bar(x + width/2, route_data['post_cp_violations'], width,
                   label='Post-Congestion Pricing', color='#1f77b4')

    ax.set_xlabel('Bus Routes')
    ax.set_ylabel('Number of Violations')
    ax.set_title('Route-Specific Comparison: Pre vs Post Congestion Pricing')
    ax.set_xticks(x)
    ax.set_xticklabels(route_data['route'])
    ax.legend()

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)

    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('results/route_comparison_chart.png',
                dpi=300, bbox_inches='tight')
    plt.show()


def generate_summary_report(results):
    """Generate a concise summary report aligned with Q1/Q2 style"""

    print("\nGenerating summary report...")

    # Build Net change line conditionally
    if results.get('has_pre_period'):
        net_change_line = f"Net change: {results['percent_change']:+.1f}%"
        notes_line = "Notes: Results reflect CBD routes; see figures for route details."
    else:
        net_change_line = "Net change: Not computable (no pre-CP data)"
        notes_line = "Notes: No pre-CP observations; figures show post-CP levels only."

    report = (
        f"# Question 3: Congestion Pricing Impact\n\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Overall\n\n"
        f"- Total violations: {results['total_violations']:,}\n"
        f"- Pre-CP: {results['pre_cp_violations']:,}\n"
        f"- Post-CP: {results['post_cp_violations']:,}\n"
        f"- {net_change_line}\n\n"
        f"Window\n\n"
        f"- Data spans: {results['analysis_date_range'][0].strftime('%Y-%m-%d')} to {results['analysis_date_range'][1].strftime('%Y-%m-%d')}\n"
        f"- CP start: {results['congestion_start_date'].strftime('%Y-%m-%d')}\n\n"
        f"{notes_line}\n\n"
        f"See figures: `q3_congestion_pricing_analysis.png`, `route_comparison_chart.png`.\n"
    )

    # Save report (standardized filename)
    with open('results/q3_summary_report.md', 'w') as f:
        f.write(report)

    print("Summary report saved to: results/q3_summary_report.md")


def main():
    """
    Main analysis function for Question 3
    """

    print("="*80)
    print("QUESTION 3: CONGESTION PRICING IMPACT ON CBD ROUTE VIOLATIONS")
    print("MTA Datathon 2025")
    print("="*80)

    # Step 1: Load data
    df = load_ace_violations_data()
    if df.empty:
        print("Cannot proceed without data. Please check data file location.")
        return

    # Step 2: Filter for Manhattan CBD routes
    cbd_df, route_list = identify_manhattan_cbd_routes(df)
    if cbd_df.empty:
        print("No Manhattan CBD routes found in data.")
        return

    # Step 3: Analyze congestion pricing impact
    results = analyze_congestion_pricing_impact(cbd_df)
    if not results:
        print("Could not complete analysis due to data issues.")
        return

    # Step 4: Create visualizations
    create_visualizations(cbd_df, results)

    # Step 5: Generate report
    generate_summary_report(results)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print(f"✅ Analyzed {results['total_violations']:,} violations")
    if results.get('has_pre_period'):
        print(
            f"✅ Found {results['percent_change']:+.1f}% change post-congestion pricing")
    else:
        print("✅ Net change not computable (no pre-CP data in dataset)")
    print(f"✅ Generated visualizations and summary report")
    print(f"✅ Results saved in results/ folder")

    return results


if __name__ == "__main__":
    # Run the complete analysis
    results = main()
