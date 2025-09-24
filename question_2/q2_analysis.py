"""
Question 2: Vehicle Exemptions & Repeat Violators
MTA Datathon 2025 - DataStorm Team

Save this file as: question_2/q2_analysis.py
Run from DataStorm root folder: python question_2/q2_analysis.py
"""

import pandas as pd
from sodapy import Socrata
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import json
import sys

def setup_folders():
    """Ensure all folders exist"""
    folders = [
        'data/raw',
        'data/processed',
        'question_2/results',
        'visualizations'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    print("✅ Folder structure ready")

def download_data():
    """Download MTA ACE violation data"""
    print("📥 Downloading MTA ACE violation data...")
    
    try:
        client = Socrata("data.ny.gov", None)
        ACE_id = "kh8p-hcbm"
        
        # Download recent violations
        print("  Connecting to NYC Open Data...")
        violations_data = client.get(
            ACE_id,
            limit=100000,  # 100k records should be enough
        )
        
        df = pd.DataFrame.from_records(violations_data)
        
        # Save raw data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        raw_file = f"data/raw/ace_violations_raw_{timestamp}.csv"
        df.to_csv(raw_file, index=False)
        
        print(f"✅ Downloaded {len(df):,} violation records")
        print(f"✅ Raw data saved: {raw_file}")
        
        return df, raw_file
        
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        print("Check your internet connection and try again.")
        sys.exit(1)

def process_for_q2(df):
    """Process data specifically for Question 2"""
    print("\n🔄 Processing data for Question 2...")
    
    # CUNY bus routes
    cuny_routes = [
        "M100", "M101", "M4", "M5", "BX19", "M66", "M98", "M102", "M103",
        "Q17", "Q20", "Q25", "Q44", "Q64", "Q88", "QM4", "M1", "M2", "M3", 
        "M32", "M15", "S93", "S62"
    ]
    
    print(f"  Original dataset: {len(df):,} records")
    print(f"  Available columns: {list(df.columns)}")
    
    # Filter for CUNY routes if possible
    if 'bus_route_id' in df.columns:
        df = df[df['bus_route_id'].isin(cuny_routes)].copy()
        print(f"  Filtered to CUNY routes: {len(df):,} records")
    else:
        print("  No bus_route_id column found - using all data")
    
    # Find key columns for analysis
    print("\n  Identifying key columns...")
    
    # Find key columns for analysis
    print("\n  Identifying key columns...")
    
    # License plate columns
    plate_cols = [col for col in df.columns if any(word in col.lower() for word in ['plate', 'license'])]
    print(f"    Plate columns found: {plate_cols}")
    
    # Status/exemption columns  
    status_cols = [col for col in df.columns if any(word in col.lower() for word in ['status', 'exempt'])]
    print(f"    Status columns found: {status_cols}")
    
    # Date columns
    date_cols = [col for col in df.columns if any(word in col.lower() for word in ['date', 'time'])]
    print(f"    Date columns found: {date_cols}")

    # Determine what to use for repeat violator analysis
    plate_col = None
    
    if plate_cols:
        # Use license plate if available
        plate_col = plate_cols[0]
        print(f"  Using plate column: {plate_col}")
        df[plate_col] = df[plate_col].fillna('UNKNOWN').str.strip().str.upper()
    elif 'vehicle_id' in df.columns:
        # Use vehicle_id as backup
        plate_col = 'vehicle_id'
        print(f"  Using vehicle_id for repeat violator analysis")
        df[plate_col] = df[plate_col].fillna('UNKNOWN').astype(str)
    else:
        print("  ⚠️  No license plate or vehicle ID columns found - limited repeat analysis possible")
    
    # Status/exemption analysis
    if not status_cols:
        print("  ⚠️  No status columns found - limited exemption analysis possible")
        status_col = None
        df['is_exempt'] = False
    else:
        status_col = status_cols[0]
        print(f"  Using status column: {status_col}")
        df[status_col] = df[status_col].fillna('UNKNOWN')
        
        # Create exemption flag
        exempt_keywords = ['exempt', 'emergency', 'official', 'police', 'fire', 'ambulance']
        df['is_exempt'] = df[status_col].str.lower().str.contains('|'.join(exempt_keywords), na=False)
    
    # Process dates
    for col in date_cols[:2]:  # Just process first 2 date columns
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Add repeat violator analysis (only if we have a plate_col)
    if plate_col:
        plate_counts = df[plate_col].value_counts()
        df['violation_count'] = df[plate_col].map(plate_counts)
        
        # Categorize violators
        df['violator_category'] = pd.cut(
            df['violation_count'],
            bins=[0, 1, 3, 5, 10, float('inf')],
            labels=['Single', '2-3 Violations', '4-5 Violations', '6-10 Violations', '10+ Violations'],
            include_lowest=True
        )
        print(f"  ✅ Added repeat violator analysis using {plate_col}")
    else:
        print("  ⚠️  No repeat violator analysis possible")
    
    if not status_cols:
        print("  ⚠️  No status columns found - limited exemption analysis possible")
        status_col = None
        df['is_exempt'] = False
    else:
        status_col = status_cols[0]
        print(f"  Using status column: {status_col}")
        df[status_col] = df[status_col].fillna('UNKNOWN')
        
        # Create exemption flag
        exempt_keywords = ['exempt', 'emergency', 'official', 'police', 'fire', 'ambulance']
        df['is_exempt'] = df[status_col].str.lower().str.contains('|'.join(exempt_keywords), na=False)
    
    # Process dates
    for col in date_cols[:2]:  # Just process first 2 date columns
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Add repeat violator analysis
    if plate_col:
        plate_counts = df[plate_col].value_counts()
        df['violation_count'] = df[plate_col].map(plate_counts)
        
        # Categorize violators
        df['violator_category'] = pd.cut(
            df['violation_count'],
            bins=[0, 1, 3, 5, 10, float('inf')],
            labels=['Single', '2-3 Violations', '4-5 Violations', '6-10 Violations', '10+ Violations'],
            include_lowest=True
        )
    
    # Save processed data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    processed_file = f"data/processed/q2_processed_{timestamp}.csv"
    df.to_csv(processed_file, index=False)
    print(f"  ✅ Processed data saved: {processed_file}")
    
    return df, plate_col, status_col

def analyze_q2(df, plate_col, status_col):
    """Run Question 2 analysis"""
    print("\n🔍 Running Question 2 Analysis...")
    
    total_violations = len(df)
    print(f"  Analyzing {total_violations:,} violation records")
    
    # Basic stats
    stats = {
        'total_violations': total_violations,
        'analysis_date': datetime.now().isoformat()
    }
    
    # Exemption analysis
    if 'is_exempt' in df.columns:
        exempt_count = df['is_exempt'].sum()
        exempt_pct = (exempt_count / total_violations * 100) if total_violations > 0 else 0
        
        stats.update({
            'exempt_violations': int(exempt_count),
            'exempt_percentage': round(exempt_pct, 2),
            'non_exempt_violations': int(total_violations - exempt_count)
        })
        
        print(f"\n  📊 Exemption Analysis:")
        print(f"     Exempt violations: {exempt_count:,} ({exempt_pct:.1f}%)")
        print(f"     Non-exempt violations: {total_violations - exempt_count:,} ({100-exempt_pct:.1f}%)")
    
    # Repeat violator analysis
    if plate_col:
        unique_vehicles = df[plate_col].nunique()
        plate_counts = df[plate_col].value_counts()
        
        repeat_violators = (plate_counts > 1).sum()
        chronic_violators = (plate_counts >= 10).sum()
        top_violator_count = plate_counts.max()
        
        stats.update({
            'unique_vehicles': int(unique_vehicles),
            'repeat_violators': int(repeat_violators),
            'chronic_violators': int(chronic_violators),
            'top_violator_violations': int(top_violator_count)
        })
        
        print(f"\n  📊 Repeat Violator Analysis:")
        print(f"     Unique vehicles: {unique_vehicles:,}")
        print(f"     Repeat violators: {repeat_violators:,} ({repeat_violators/unique_vehicles*100:.1f}%)")
        print(f"     Chronic violators (10+): {chronic_violators:,}")
        print(f"     Worst offender: {top_violator_count} violations")
        
        # Show top 10 violators
        print(f"\n  🏆 Top 10 Repeat Violators:")
        for i, (plate, count) in enumerate(plate_counts.head(10).items(), 1):
            print(f"     {i:2d}. {plate}: {count} violations")
    
    return stats

def create_visualizations(df, plate_col, status_col):
    """Create Q2 visualizations"""
    print("\n📊 Creating visualizations...")
    
    # Set up the plot
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Question 2: Vehicle Exemptions & Repeat Violators\nMTA Datathon 2025 - DataStorm Team', 
                 fontsize=14, fontweight='bold')
    
    # 1. Exemption status breakdown
    if status_col and status_col in df.columns:
        status_counts = df[status_col].value_counts().head(8)
        axes[0,0].bar(range(len(status_counts)), status_counts.values, 
                      color='skyblue', alpha=0.8, edgecolor='navy')
        axes[0,0].set_title('Violation Status Distribution')
        axes[0,0].set_ylabel('Number of Violations')
        axes[0,0].set_xticks(range(len(status_counts)))
        axes[0,0].set_xticklabels([str(x)[:15] + '...' if len(str(x)) > 15 else str(x) 
                                   for x in status_counts.index], rotation=45, ha='right')
    else:
        axes[0,0].text(0.5, 0.5, 'No status data\navailable', ha='center', va='center',
                       transform=axes[0,0].transAxes, fontsize=12)
        axes[0,0].set_title('Violation Status (No Data)')
    
    # 2. Exempt vs Non-exempt pie chart
    if 'is_exempt' in df.columns:
        exempt_counts = df['is_exempt'].value_counts()
        labels = ['Non-Exempt', 'Exempt']
        colors = ['lightgreen', 'lightcoral']
        sizes = [exempt_counts.get(False, 0), exempt_counts.get(True, 0)]
        
        axes[0,1].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        axes[0,1].set_title('Exempt vs Non-Exempt Violations')
    else:
        axes[0,1].text(0.5, 0.5, 'No exemption data\navailable', ha='center', va='center',
                       transform=axes[0,1].transAxes, fontsize=12)
        axes[0,1].set_title('Exemption Analysis (No Data)')
    
    # 3. Violator categories
    if plate_col and 'violator_category' in df.columns:
        category_counts = df['violator_category'].value_counts()
        axes[1,0].bar(range(len(category_counts)), category_counts.values,
                      color='orange', alpha=0.7, edgecolor='darkorange')
        axes[1,0].set_title('Repeat Violator Categories')
        axes[1,0].set_ylabel('Number of Vehicles')
        axes[1,0].set_xticks(range(len(category_counts)))
        axes[1,0].set_xticklabels(category_counts.index, rotation=45, ha='right')
    else:
        axes[1,0].text(0.5, 0.5, 'No plate data\navailable', ha='center', va='center',
                       transform=axes[1,0].transAxes, fontsize=12)
        axes[1,0].set_title('Violator Categories (No Data)')
    
    # 4. Top violators
    if plate_col:
        plate_counts = df[plate_col].value_counts()
        top_10 = plate_counts.head(10)
        
        axes[1,1].barh(range(len(top_10)), top_10.values, color='red', alpha=0.7)
        axes[1,1].set_title('Top 10 Repeat Violators')
        axes[1,1].set_xlabel('Number of Violations')
        axes[1,1].set_yticks(range(len(top_10)))
        axes[1,1].set_yticklabels([f"{plate[:12]}..." if len(str(plate)) > 12 else str(plate) 
                                   for plate in top_10.index])
        
        # Add value labels
        for i, v in enumerate(top_10.values):
            axes[1,1].text(v + 0.1, i, str(v), va='center')
    else:
        axes[1,1].text(0.5, 0.5, 'No plate data\navailable', ha='center', va='center',
                       transform=axes[1,1].transAxes, fontsize=12)
        axes[1,1].set_title('Top Violators (No Data)')
    
    plt.tight_layout()
    
    # Save visualization
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    viz_file = f"visualizations/q2_dashboard_{timestamp}.png"
    plt.savefig(viz_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Dashboard saved: {viz_file}")
    
    return viz_file

def save_results(df, stats, plate_col, status_col):
    """Save all analysis results"""
    print("\n💾 Saving analysis results...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # 1. Key insights
    insights_file = f"question_2/results/key_insights_{timestamp}.json"
    with open(insights_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"  ✅ Key insights: {insights_file}")
    
    # 2. Top violators (if available)
    if plate_col:
        plate_counts = df[plate_col].value_counts()
        top_violators = pd.DataFrame({
            'license_plate': plate_counts.head(50).index,
            'violation_count': plate_counts.head(50).values
        })
        violators_file = f"question_2/results/top_violators_{timestamp}.csv"
        top_violators.to_csv(violators_file, index=False)
        print(f"  ✅ Top violators: {violators_file}")
    
    # 3. Exemption summary (if available)
    if status_col and status_col in df.columns:
        exemption_summary = df[status_col].value_counts().reset_index()
        exemption_summary.columns = ['status', 'count']
        exemption_summary['percentage'] = (exemption_summary['count'] / len(df) * 100).round(2)
        
        exemption_file = f"question_2/results/exemption_summary_{timestamp}.csv"
        exemption_summary.to_csv(exemption_file, index=False)
        print(f"  ✅ Exemption summary: {exemption_file}")
    
    # 4. Full processed dataset
    full_file = f"question_2/results/q2_full_dataset_{timestamp}.csv"
    df.to_csv(full_file, index=False)
    print(f"  ✅ Full dataset: {full_file}")

def main():
    """Main analysis function"""
    print("🚔 MTA Datathon 2025 - Question 2")
    print("Vehicle Exemptions & Repeat Violators Analysis")
    print("=" * 60)
    
    # Step 1: Setup
    setup_folders()
    
    # Step 2: Download data
    df, raw_file = download_data()
    
    # Step 3: Process for Q2
    df, plate_col, status_col = process_for_q2(df)
    
    # Step 4: Run analysis
    stats = analyze_q2(df, plate_col, status_col)
    
    # Step 5: Create visualizations
    viz_file = create_visualizations(df, plate_col, status_col)
    
    # Step 6: Save results
    save_results(df, stats, plate_col, status_col)
    
    # Step 7: Show completion
    print("\n" + "=" * 60)
    print("🎯 QUESTION 2 COMPLETE!")
    print("=" * 60)
    
    print(f"📊 Analysis Summary:")
    print(f"   Total violations: {stats.get('total_violations', 0):,}")
    if 'unique_vehicles' in stats:
        print(f"   Unique vehicles: {stats['unique_vehicles']:,}")
        print(f"   Repeat violators: {stats['repeat_violators']:,}")
    if 'exempt_violations' in stats:
        print(f"   Exempt violations: {stats['exempt_violations']:,} ({stats['exempt_percentage']:.1f}%)")
    
    print(f"\n📁 Files created:")
    print(f"   📄 Raw data: data/raw/")
    print(f"   📄 Processed data: data/processed/")
    print(f"   📊 Results: question_2/results/")
    print(f"   🎨 Visualizations: visualizations/")
    
    print(f"\n🎥 Ready for:")
    print(f"   • GitHub page creation")
    print(f"   • Video presentation")
    print(f"   • Team integration")
    
    # Show the plot
    plt.show()
    
    return df, stats

if __name__ == "__main__":
    result_df, result_stats = main()