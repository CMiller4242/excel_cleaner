#!/usr/bin/env python3
"""
Test the FULL preset workflow to identify where false positives occur
"""

import pandas as pd
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.executor import OperationExecutor

def test_full_preset():
    """Test with the full ZoomInfo Healthcare/EVS preset"""

    print("=" * 100)
    print("TESTING FULL PRESET WORKFLOW")
    print("=" * 100)

    # Load file
    filename = "Volunteer Directors 11.20.25(2).xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    print(f"    Initial: {len(df):,} rows, {len(df.columns)} columns")

    # Check Person Street column before any operations
    if 'Person Street' in df.columns:
        ps_before = df['Person Street']
        print(f"\n[2] Person Street BEFORE operations:")
        print(f"    Total: {len(ps_before):,}")
        print(f"    Non-blank: {ps_before.notna().sum():,}")
        print(f"    Blank: {ps_before.isna().sum():,}")

        # Show first 10 non-blank
        print(f"\n    First 10 non-blank Person Street values:")
        for idx, val in ps_before[ps_before.notna()].head(10).items():
            print(f"      [{idx}] '{val}'")

    # Load the preset
    preset_file = "presets/system/zoominfo_healthcare_evs.json"
    with open(preset_file, 'r') as f:
        preset = json.load(f)

    operations = preset['operations']
    print(f"\n[3] Loaded preset: {len(operations)} operations")

    # Execute with tracking
    print(f"\n[4] Executing preset...")
    executor = OperationExecutor()

    # Execute step by step to see what happens
    current_df = df.copy()
    all_removed = pd.DataFrame()

    for i, op in enumerate(operations):
        if not op.get('enabled', True):
            continue

        op_id = op['operation_id']
        op_desc = op.get('description', '')
        params = op['parameters']

        print(f"\n    Step {i+1}: {op_id}")
        print(f"            {op_desc}")
        print(f"            Before: {len(current_df):,} rows")

        # Show columns before this operation
        if i == 3:  # After split address operation
            print(f"            Columns: {list(current_df.columns)}")
            if 'Address 1' in current_df.columns:
                addr1 = current_df['Address 1']
                print(f"            Address 1 stats:")
                print(f"              Non-blank: {addr1.notna().sum():,}")
                print(f"              NaN/None: {addr1.isna().sum():,}")
                # Check for empty strings
                empty_str_count = (addr1.astype(str).str.strip() == '').sum()
                print(f"              Empty strings: {empty_str_count:,}")

        # Execute single operation
        single_op_list = [op]
        result_df, removed_df = executor.execute_queue_with_tracking(current_df, single_op_list)

        rows_removed = len(current_df) - len(result_df)
        print(f"            After: {len(result_df):,} rows (removed {rows_removed:,})")

        # Check if this operation removes rows with non-blank Person Street
        if not removed_df.empty and 'Person Street' in removed_df.columns:
            ps_removed = removed_df['Person Street']
            non_blank_removed = ps_removed.notna().sum()
            if non_blank_removed > 0:
                print(f"            ⚠️  FALSE POSITIVES: {non_blank_removed} non-blank Person Street values removed!")
                print(f"            First 5 false positives:")
                for idx, row in removed_df[ps_removed.notna()].head(5).iterrows():
                    addr = row['Person Street']
                    print(f"              [{idx}] '{addr}'")
                    # Also show Address 1 if it exists
                    if 'Address 1' in row:
                        print(f"                  → Address 1: '{row['Address 1']}' (type: {type(row['Address 1']).__name__}, is_na: {pd.isna(row['Address 1'])})")
                    if 'Address 2' in row:
                        print(f"                  → Address 2: '{row['Address 2']}'")

        # Check if Address 1 column exists and has empty strings (not NaN)
        if 'Address 1' in removed_df.columns:
            addr1_removed = removed_df['Address 1']
            # Count empty strings that are NOT NaN
            empty_strings = addr1_removed[addr1_removed.notna() & (addr1_removed.astype(str).str.strip() == '')]
            if len(empty_strings) > 0:
                print(f"            ⚠️  Address 1 has {len(empty_strings)} empty strings (not NaN)!")

        current_df = result_df

        # Accumulate removed rows
        if not removed_df.empty:
            if all_removed.empty:
                all_removed = removed_df.copy()
            else:
                all_removed = pd.concat([all_removed, removed_df], ignore_index=True)

    print(f"\n[5] FINAL RESULTS:")
    print(f"    Results: {len(current_df):,} rows")
    print(f"    Total removed: {len(all_removed):,} rows")

    # Analyze all removed rows
    if not all_removed.empty and 'Person Street' in all_removed.columns:
        ps_all_removed = all_removed['Person Street']
        non_blank_total = ps_all_removed.notna().sum()
        print(f"\n[6] ANALYSIS OF ALL REMOVED ROWS:")
        print(f"    Non-blank Person Street values removed: {non_blank_total:,}")

        if non_blank_total > 0:
            print(f"\n    ⚠️  CRITICAL BUG: {non_blank_total} non-blank addresses were removed!")
            return False
        else:
            print(f"    ✓ All removed rows have blank Person Street (correct)")
            return True

    return True

if __name__ == '__main__':
    success = test_full_preset()
    print("\n" + "=" * 100)
    if success:
        print("✓ TEST PASSED")
    else:
        print("✗ TEST FAILED")
    print("=" * 100)
    exit(0 if success else 1)
