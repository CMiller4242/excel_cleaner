#!/usr/bin/env python3
"""
Verify the exported Excel file to ensure no data corruption during export

This test:
1. Runs Remove Rows If operation
2. Exports to multi-sheet Excel file
3. Re-reads the exported file
4. Verifies each sheet contains correct data
"""

import pandas as pd
import numpy as np
from engine.executor import OperationExecutor
from utils.export_helper import ExportHelper

def test_exported_file_integrity():
    """Test that exported file has correct data"""

    print("=" * 100)
    print("EXPORTED FILE INTEGRITY TEST")
    print("=" * 100)

    # Load actual file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[1] Loading: {filename}")
    df_original = pd.read_excel(filename)
    print(f"    Loaded: {len(df_original):,} rows")

    # Analyze original data
    person_street = df_original['Person Street']
    is_na = person_street.isna()
    str_vals = person_street.astype(str).str.strip()
    is_empty = str_vals.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    is_blank = is_na | is_empty

    original_blank_count = is_blank.sum()
    original_nonblank_count = (~is_blank).sum()

    print(f"\n[2] Original data analysis:")
    print(f"    Total rows: {len(df_original):,}")
    print(f"    Blank Person Street: {original_blank_count:,}")
    print(f"    Non-blank Person Street: {original_nonblank_count:,}")

    # Get specific addresses to track
    track_addresses = [
        '3203 SE Woodstock Blvd',
        '2525 Glenn Hendren Dr Ste 202',
        '400 Maple Summit Rd',
        '6600 N Lincoln Ave Ste 300',
        '2150 Post St'
    ]

    print(f"\n[3] Tracking specific addresses in original:")
    original_address_counts = {}
    for addr in track_addresses:
        count = (df_original['Person Street'] == addr).sum()
        original_address_counts[addr] = count
        print(f"    '{addr}': {count} instances")

    # Execute operation
    print(f"\n[4] Executing Remove Rows If (Person Street is blank)")
    operations = [{
        'operation_id': 'data_remove_rows_if',
        'parameters': {
            'column': 'Person Street',
            'condition': 'is_blank'
        },
        'enabled': True
    }]

    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df_original, operations)

    print(f"    Results: {len(result_df):,} rows")
    print(f"    Removed: {len(removed_df):,} rows")

    # Export to Excel
    output_file = "Test_Exported_File_Verification.xlsx"
    print(f"\n[5] Exporting to: {output_file}")

    sheets = {
        'Original': df_original,
        'Results': result_df,
        'Removed': removed_df
    }

    ExportHelper.export_multiple_sheets(sheets, output_file)
    print(f"    ✓ Export complete")

    # Read back the exported file
    print(f"\n[6] Reading back exported file")
    exported_original = pd.read_excel(output_file, sheet_name='Original')
    exported_results = pd.read_excel(output_file, sheet_name='Results')
    exported_removed = pd.read_excel(output_file, sheet_name='Removed')

    print(f"    Original sheet: {len(exported_original):,} rows")
    print(f"    Results sheet: {len(exported_results):,} rows")
    print(f"    Removed sheet: {len(exported_removed):,} rows")

    # Verify Results sheet
    print(f"\n[7] Verifying Results sheet in exported file")

    # Check row count
    if len(exported_results) != original_nonblank_count:
        print(f"    ✗ ERROR: Results has {len(exported_results)} rows, expected {original_nonblank_count}")
        return False
    else:
        print(f"    ✓ Row count correct: {len(exported_results):,}")

    # Check for blank Person Street values
    exp_result_ps = exported_results['Person Street']
    exp_result_is_na = exp_result_ps.isna()
    exp_result_str = exp_result_ps.astype(str).str.strip()
    exp_result_is_empty = exp_result_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    exp_result_blank = exp_result_is_na | exp_result_is_empty

    if exp_result_blank.sum() > 0:
        print(f"    ✗ ERROR: Results sheet contains {exp_result_blank.sum()} blank Person Street values")
        return False
    else:
        print(f"    ✓ No blank Person Street values")

    # Check tracked addresses in Results
    print(f"\n    Tracked addresses in Results:")
    all_present = True
    for addr in track_addresses:
        count = (exported_results['Person Street'] == addr).sum()
        expected = original_address_counts[addr]
        if count == expected:
            print(f"      ✓ '{addr}': {count} (expected {expected})")
        else:
            print(f"      ✗ '{addr}': {count} (expected {expected}) - MISSING {expected - count}")
            all_present = False

    if not all_present:
        return False

    # Verify Removed sheet
    print(f"\n[8] Verifying Removed sheet in exported file")

    # Check row count
    if len(exported_removed) != original_blank_count:
        print(f"    ✗ ERROR: Removed has {len(exported_removed)} rows, expected {original_blank_count}")
        return False
    else:
        print(f"    ✓ Row count correct: {len(exported_removed):,}")

    # Check that ALL rows in Removed have blank Person Street
    exp_removed_ps = exported_removed['Person Street']
    exp_removed_is_na = exp_removed_ps.isna()
    exp_removed_str = exp_removed_ps.astype(str).str.strip()
    exp_removed_is_empty = exp_removed_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    exp_removed_blank = exp_removed_is_na | exp_removed_is_empty

    non_blank_count = (~exp_removed_blank).sum()

    if non_blank_count > 0:
        print(f"    ✗ ERROR: Removed sheet contains {non_blank_count} NON-BLANK Person Street values!")
        print(f"\n    FALSE POSITIVES (first 20):")
        false_positives = exported_removed[~exp_removed_blank].head(20)
        for idx, row in false_positives.iterrows():
            addr = row['Person Street']
            removed_by = row.get('_Removed_By', 'Unknown')
            print(f"      [{idx}] '{addr}' (removed by: {removed_by})")

        # Check if tracked addresses are in Removed (they shouldn't be!)
        print(f"\n    Checking if tracked addresses are incorrectly in Removed:")
        for addr in track_addresses:
            count = (exported_removed['Person Street'] == addr).sum()
            if count > 0:
                print(f"      ✗ '{addr}': {count} instances in Removed (FALSE POSITIVE!)")

        return False
    else:
        print(f"    ✓ All Removed rows have blank Person Street")

    # Verify no tracked addresses in Removed
    print(f"\n    Verifying tracked addresses NOT in Removed:")
    for addr in track_addresses:
        count = (exported_removed['Person Street'] == addr).sum()
        if count == 0:
            print(f"      ✓ '{addr}': 0 (correct - not removed)")
        else:
            print(f"      ✗ '{addr}': {count} (FALSE POSITIVE!)")
            return False

    # Verify row balance
    print(f"\n[9] Verifying row balance")
    total_accounted = len(exported_results) + len(exported_removed)
    if total_accounted == len(exported_original):
        print(f"    ✓ Row balance: {len(exported_results):,} + {len(exported_removed):,} = {total_accounted:,}")
    else:
        print(f"    ✗ Row mismatch: {len(exported_results):,} + {len(exported_removed):,} = {total_accounted:,}, expected {len(exported_original):,}")
        return False

    # Final result
    print(f"\n{'='*100}")
    print("✓ EXPORTED FILE VERIFICATION PASSED")
    print("=" * 100)

    print(f"\nVerified that the exported file '{output_file}' contains:")
    print(f"  • Original sheet: {len(exported_original):,} rows")
    print(f"  • Results sheet: {len(exported_results):,} rows (all with valid addresses) ✓")
    print(f"  • Removed sheet: {len(exported_removed):,} rows (all with blank addresses) ✓")
    print(f"  • All tracked addresses present in Results ✓")
    print(f"  • No tracked addresses in Removed ✓")
    print(f"  • Zero false positives ✓")

    return True

if __name__ == '__main__':
    success = test_exported_file_integrity()
    if not success:
        print("\n✗ EXPORTED FILE VERIFICATION FAILED")
        print("The exported Excel file contains incorrect data!")
        exit(1)
    else:
        print("\nThe exported Excel file is correct and ready for use.")
        exit(0)
