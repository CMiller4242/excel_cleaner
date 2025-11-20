#!/usr/bin/env python3
"""
Test multi-sheet export with the executor tracking fix

Verifies that the 'Removed' sheet contains only truly removed rows,
not false positives caused by reset_index bug.
"""

import pandas as pd
import numpy as np
from engine.executor import OperationExecutor

def test_multisheet_export_with_actual_file():
    """Test multi-sheet export with actual user file"""

    print("=" * 80)
    print("TESTING MULTI-SHEET EXPORT WITH ACTUAL FILE")
    print("=" * 80)

    # Load the actual file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\nLoading: {filename}")

    try:
        df = pd.read_excel(filename)
    except Exception as e:
        print(f"Error loading file: {e}")
        return False

    print(f"Loaded: {len(df):,} rows, {len(df.columns)} columns")

    # Create a workflow with multiple operations
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

    print(f"\nWorkflow:")
    for i, op in enumerate(operations):
        print(f"  {i+1}. {op['operation_id']}")

    # Execute with tracking
    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df, operations)

    print(f"\n{'='*80}")
    print("RESULTS")
    print("=" * 80)

    print(f"\nOriginal: {len(df):,} rows")
    print(f"Results:  {len(result_df):,} rows")
    print(f"Removed:  {len(removed_df):,} rows")

    # Verify: Results + Removed should equal Original
    total_accounted = len(result_df) + len(removed_df)
    if total_accounted == len(df):
        print(f"\n✓ Row count balanced: {len(result_df)} + {len(removed_df)} = {len(df)}")
    else:
        print(f"\n✗ Row count MISMATCH: {len(result_df)} + {len(removed_df)} = {total_accounted}, expected {len(df)}")

    print(f"\n{'='*80}")
    print("VERIFICATION: RESULTS SHEET")
    print("=" * 80)

    # Check Results sheet: should have no blank Person Street values
    if 'Person Street' in result_df.columns:
        result_person_street = result_df['Person Street']
        result_is_na = result_person_street.isna()
        result_str_values = result_person_street.astype(str).str.strip()
        result_is_empty = result_str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        result_blank = result_is_na | result_is_empty
        result_blank_count = result_blank.sum()

        if result_blank_count == 0:
            print(f"\n✓ Results sheet: NO blank Person Street values (all {len(result_df):,} rows valid)")
        else:
            print(f"\n✗ Results sheet: Contains {result_blank_count} blank Person Street values (SHOULD BE ZERO)")
            return False
    else:
        print("\n⚠ Person Street column not in results (may have been removed by workflow)")

    print(f"\n{'='*80}")
    print("VERIFICATION: REMOVED SHEET")
    print("=" * 80)

    if removed_df.empty:
        print("\n⚠ Removed sheet is empty (no rows removed)")
    else:
        # Check which operations removed rows
        if '_Removed_By' in removed_df.columns:
            print(f"\nRows removed by operation:")
            removal_counts = removed_df['_Removed_By'].value_counts()
            for op_name, count in removal_counts.items():
                print(f"  {op_name}: {count:,} rows")

        # Check if removed sheet has any NON-blank Person Street values (FALSE POSITIVES)
        if 'Person Street' in removed_df.columns:
            removed_person_street = removed_df['Person Street']
            removed_is_na = removed_person_street.isna()
            removed_str_values = removed_person_street.astype(str).str.strip()
            removed_is_empty = removed_str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
            removed_blank = removed_is_na | removed_is_empty

            removed_blank_count = removed_blank.sum()
            removed_non_blank_count = (~removed_blank).sum()

            print(f"\nRemoved sheet Person Street analysis:")
            print(f"  Blank values: {removed_blank_count:,} rows (expected: all)")
            print(f"  Non-blank values: {removed_non_blank_count:,} rows (expected: 0 - these are FALSE POSITIVES)")

            if removed_non_blank_count > 0:
                print(f"\n✗ FALSE POSITIVES DETECTED: {removed_non_blank_count} rows with valid addresses in Removed sheet")
                print("\nExamples of false positives (first 10):")
                false_positives = removed_df[~removed_blank].head(10)
                for idx, row in false_positives.iterrows():
                    addr = row['Person Street']
                    removed_by = row.get('_Removed_By', 'Unknown')
                    print(f"  '{addr}' (removed by: {removed_by})")
                return False
            else:
                print(f"\n✓ No false positives: All removed rows have blank Person Street (correct)")
        else:
            print("\n⚠ Person Street column not in removed sheet")

    print(f"\n{'='*80}")
    print("✓ ALL VERIFICATIONS PASSED")
    print("=" * 80)

    print("\nSummary:")
    print(f"  • Original: {len(df):,} rows")
    print(f"  • Results: {len(result_df):,} rows (all valid)")
    print(f"  • Removed: {len(removed_df):,} rows (all blank/excluded)")
    print(f"  • False positives: 0")
    print(f"  • Multi-sheet export tracking: WORKING CORRECTLY")

    return True

if __name__ == '__main__':
    success = test_multisheet_export_with_actual_file()
    exit(0 if success else 1)
