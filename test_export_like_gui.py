#!/usr/bin/env python3
"""
Test export exactly like the GUI does to see what the user sees
"""

import pandas as pd
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.executor import OperationExecutor
from utils.export_helper import ExportHelper

def test_gui_export():
    """Simulate what the GUI does for export"""

    print("=" * 100)
    print("SIMULATING GUI EXPORT")
    print("=" * 100)

    # Load file (this becomes self.df in GUI)
    filename = "Volunteer Directors 11.20.25(2).xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    print(f"    Original: {len(df):,} rows")

    # Load preset
    preset_file = "presets/system/zoominfo_healthcare_evs.json"
    with open(preset_file, 'r') as f:
        preset = json.load(f)
    operations = preset['operations']

    # Execute with tracking (like GUI does on line 1039)
    print(f"\n[2] Executing {len(operations)} operations...")
    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df.copy(), operations)

    print(f"    Results: {len(result_df):,} rows")
    print(f"    Removed: {len(removed_df):,} rows")

    # Export like GUI does (lines 1087-1098)
    print(f"\n[3] Creating Excel export...")
    sheets = {}

    # Sheet 1: Original
    sheets['Original'] = df

    # Sheet 2: Results
    sheets['Results'] = result_df

    # Sheet 3: Removed
    if not removed_df.empty:
        sheets['Removed'] = removed_df

    output_file = "TEST_GUI_SIMULATION_EXPORT.xlsx"
    ExportHelper.export_multiple_sheets(sheets, output_file)
    print(f"    Saved to: {output_file}")

    # Analyze what's in each sheet
    print(f"\n[4] Sheet Analysis:")
    print(f"\n    Original sheet:")
    print(f"      Rows: {len(sheets['Original']):,}")
    print(f"      Columns: {list(sheets['Original'].columns[:15])}...")  # First 15 columns
    if 'Person Street' in sheets['Original'].columns:
        ps = sheets['Original']['Person Street']
        print(f"      Person Street: {ps.notna().sum():,} non-blank, {ps.isna().sum():,} blank")

    print(f"\n    Results sheet:")
    print(f"      Rows: {len(sheets['Results']):,}")
    print(f"      Columns: {list(sheets['Results'].columns)}")
    if 'Person Street' in sheets['Results'].columns:
        ps = sheets['Results']['Person Street']
        print(f"      Person Street: {ps.notna().sum():,} non-blank, {ps.isna().sum():,} blank")
    if 'Address 1' in sheets['Results'].columns:
        addr1 = sheets['Results']['Address 1']
        print(f"      Address 1: {addr1.notna().sum():,} non-blank, {addr1.isna().sum():,} blank")
        empty_str = (addr1.astype(str).str.strip() == '').sum()
        print(f"      Address 1 empty strings: {empty_str:,}")

    print(f"\n    Removed sheet:")
    print(f"      Rows: {len(sheets['Removed']):,}")
    print(f"      Columns: {list(sheets['Removed'].columns)}")
    if 'Person Street' in sheets['Removed'].columns:
        ps = sheets['Removed']['Person Street']
        non_blank = ps.notna().sum()
        blank = ps.isna().sum()
        print(f"      Person Street: {non_blank:,} non-blank, {blank:,} blank")

        if non_blank > 0:
            print(f"\n      ⚠️  ISSUE: {non_blank} non-blank Person Street values in Removed sheet!")
            print(f"      First 20 non-blank Person Street values in Removed:")
            for idx, row in sheets['Removed'][ps.notna()].head(20).iterrows():
                ps_val = row['Person Street']
                print(f"        [{idx}] Person Street: '{ps_val}'")
                if 'Address 1' in row:
                    a1 = row['Address 1']
                    is_na = pd.isna(a1)
                    is_empty_str = isinstance(a1, str) and a1.strip() == ''
                    print(f"             Address 1: '{a1}' (is_na={is_na}, is_empty_str={is_empty_str})")
                if '_Removed_By' in row:
                    print(f"             Removed by: {row['_Removed_By']}")

    if 'Address 1' in sheets['Removed'].columns:
        addr1 = sheets['Removed']['Address 1']
        print(f"      Address 1: {addr1.notna().sum():,} non-blank, {addr1.isna().sum():,} blank")
        # Count empty strings (non-NaN but empty after strip)
        empty_strings = addr1[addr1.notna() & (addr1.astype(str).str.strip() == '')]
        print(f"      Address 1 empty strings (not NaN): {len(empty_strings):,}")

    print("\n" + "=" * 100)

if __name__ == '__main__':
    test_gui_export()
