#!/usr/bin/env python3
"""
Create an actual Excel export file to verify multi-sheet export is correct.
This mimics exactly what the GUI does when saving results.
"""

import pandas as pd
from engine.executor import OperationExecutor
from utils.export_helper import ExportHelper

def test_actual_export():
    """Create actual Excel file with multi-sheet export"""

    print("=" * 100)
    print("ACTUAL EXPORT TEST - Creating Real Excel File")
    print("=" * 100)

    # Load file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[1] Loading: {filename}")
    df_original = pd.read_excel(filename)
    print(f"    Loaded: {len(df_original):,} rows")

    # Execute workflow
    print(f"\n[2] Executing workflow...")
    operations = [
        {
            'operation_id': 'clean_remove_blank_rows',
            'parameters': {},
            'enabled': True
        },
        {
            'operation_id': 'data_remove_rows_if',
            'parameters': {
                'column': 'Person Street',
                'condition': 'is_blank'
            },
            'enabled': True
        }
    ]

    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df_original, operations)

    print(f"    Results: {len(result_df):,} rows")
    print(f"    Removed: {len(removed_df):,} rows")

    # Analyze before exporting
    print(f"\n[3] Pre-export analysis:")

    # Check Results sheet
    result_person_street = result_df['Person Street']
    result_is_na = result_person_street.isna()
    result_str = result_person_street.astype(str).str.strip()
    result_is_empty = result_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    result_blank = result_is_na | result_is_empty

    print(f"    Results sheet:")
    print(f"      • Total rows: {len(result_df):,}")
    print(f"      • Blank Person Street: {result_blank.sum()}")
    print(f"      • Non-blank Person Street: {(~result_blank).sum()}")

    # Check Removed sheet
    removed_person_street = removed_df['Person Street']
    removed_is_na = removed_person_street.isna()
    removed_str = removed_person_street.astype(str).str.strip()
    removed_is_empty = removed_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    removed_blank = removed_is_na | removed_is_empty

    print(f"    Removed sheet:")
    print(f"      • Total rows: {len(removed_df):,}")
    print(f"      • Blank Person Street: {removed_blank.sum()}")
    print(f"      • Non-blank Person Street: {(~removed_blank).sum()}")

    if (~removed_blank).sum() > 0:
        print(f"\n    ✗ ERROR BEFORE EXPORT: Removed sheet has {(~removed_blank).sum()} non-blank values!")
        print(f"    Examples:")
        false_positives = removed_df[~removed_blank].head(10)
        for idx, row in false_positives.iterrows():
            print(f"      '{row['Person Street']}'")
    else:
        print(f"    ✓ Pre-export validation passed")

    # Create multi-sheet export (exactly like GUI does)
    print(f"\n[4] Creating multi-sheet Excel file...")
    output_filename = "Test_Export_Verification.xlsx"

    sheets = {
        'Original': df_original,
        'Results': result_df,
        'Removed': removed_df
    }

    ExportHelper.export_multiple_sheets(sheets, output_filename)
    print(f"    ✓ Created: {output_filename}")

    # Read back the exported file and verify
    print(f"\n[5] Reading back exported file to verify...")
    exported_original = pd.read_excel(output_filename, sheet_name='Original')
    exported_results = pd.read_excel(output_filename, sheet_name='Results')
    exported_removed = pd.read_excel(output_filename, sheet_name='Removed')

    print(f"    Original sheet: {len(exported_original):,} rows")
    print(f"    Results sheet: {len(exported_results):,} rows")
    print(f"    Removed sheet: {len(exported_removed):,} rows")

    # Verify Removed sheet in exported file
    print(f"\n[6] Verifying Removed sheet in exported file:")
    if 'Person Street' in exported_removed.columns:
        exported_person_street = exported_removed['Person Street']
        exp_is_na = exported_person_street.isna()
        exp_str = exported_person_street.astype(str).str.strip()
        exp_is_empty = exp_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        exp_blank = exp_is_na | exp_is_empty

        blank_count = exp_blank.sum()
        non_blank_count = (~exp_blank).sum()

        print(f"    Blank Person Street: {blank_count:,} rows")
        print(f"    NON-blank Person Street: {non_blank_count:,} rows")

        if non_blank_count > 0:
            print(f"\n    ✗ ERROR IN EXPORTED FILE!")
            print(f"    The exported Removed sheet contains {non_blank_count} rows with valid Person Street data!")
            print(f"\n    Examples of false positives in exported file:")
            false_positives = exported_removed[~exp_blank].head(20)
            for idx, row in false_positives.iterrows():
                addr = row['Person Street']
                removed_by = row.get('_Removed_By', 'Unknown')
                print(f"      '{addr}' (removed by: {removed_by})")

            return False
        else:
            print(f"    ✓ Exported Removed sheet contains ONLY blank values")
    else:
        print(f"    ⚠ Person Street column not in exported Removed sheet")

    # Verify Results sheet
    print(f"\n[7] Verifying Results sheet in exported file:")
    if 'Person Street' in exported_results.columns:
        exp_result_person_street = exported_results['Person Street']
        exp_r_is_na = exp_result_person_street.isna()
        exp_r_str = exp_result_person_street.astype(str).str.strip()
        exp_r_is_empty = exp_r_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        exp_r_blank = exp_r_is_na | exp_r_is_empty

        blank_count = exp_r_blank.sum()

        print(f"    Blank Person Street: {blank_count:,} rows")

        if blank_count > 0:
            print(f"    ✗ ERROR: Results sheet contains {blank_count} blank Person Street values!")
            return False
        else:
            print(f"    ✓ Results sheet contains NO blank values")

    print(f"\n{'='*100}")
    print("✓ EXPORT VERIFICATION PASSED")
    print("=" * 100)

    print(f"\nThe exported file '{output_filename}' is correct:")
    print(f"  • Original: {len(exported_original):,} rows")
    print(f"  • Results: {len(exported_results):,} rows (all valid)")
    print(f"  • Removed: {len(exported_removed):,} rows (all blank)")
    print(f"  • False positives: 0")

    print(f"\nPlease open '{output_filename}' and verify:")
    print(f"  1. Go to 'Removed' sheet")
    print(f"  2. Check 'Person Street' column")
    print(f"  3. All values should be blank/NaN")
    print(f"  4. No valid addresses should appear")

    return True

if __name__ == '__main__':
    success = test_actual_export()
    exit(0 if success else 1)
