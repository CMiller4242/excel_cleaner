#!/usr/bin/env python3
"""
Test with full multi-operation workflow to identify if the issue
is with multi-operation tracking rather than single operation.
"""

import pandas as pd
import numpy as np
from engine.executor import OperationExecutor

def test_full_workflow():
    """Test with multiple operations like a real preset would run"""

    print("=" * 100)
    print("FULL WORKFLOW TEST - Multiple Operations")
    print("=" * 100)

    # Load actual file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[LOAD] Loading: {filename}")
    df_original = pd.read_excel(filename)
    print(f"  Loaded: {len(df_original):,} rows × {len(df_original.columns)} columns")

    # Create a realistic workflow similar to what user would run
    operations = [
        {
            'operation_id': 'clean_remove_blank_rows',
            'parameters': {},
            'enabled': True,
            'description': 'Step 1: Remove completely empty rows'
        },
        {
            'operation_id': 'data_remove_rows_if',
            'parameters': {
                'column': 'Person Street',
                'condition': 'is_blank'
            },
            'enabled': True,
            'description': 'Step 2: Remove rows with blank Person Street'
        }
    ]

    print(f"\n[WORKFLOW] Operations to execute:")
    for i, op in enumerate(operations, 1):
        desc = op.get('description', op['operation_id'])
        print(f"  {i}. {desc}")

    # Execute with tracking
    print(f"\n[EXECUTE] Running workflow with tracking...")
    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df_original, operations)

    print(f"\n[RESULTS]")
    print(f"  Original: {len(df_original):,} rows")
    print(f"  Results:  {len(result_df):,} rows")
    print(f"  Removed:  {len(removed_df):,} rows")
    print(f"  Balance:  {len(result_df):,} + {len(removed_df):,} = {len(result_df) + len(removed_df):,}")

    if len(result_df) + len(removed_df) == len(df_original):
        print(f"  ✓ Row count balanced")
    else:
        print(f"  ✗ Row count MISMATCH!")

    # Analyze removed sheet
    print(f"\n[ANALYZE REMOVED SHEET]")
    if not removed_df.empty:
        # Check which operations removed rows
        if '_Removed_By' in removed_df.columns:
            print(f"\n  Rows removed by each operation:")
            removal_counts = removed_df['_Removed_By'].value_counts()
            for op_name, count in removal_counts.items():
                print(f"    • {op_name}: {count:,} rows")

        # Check Person Street column in removed sheet
        if 'Person Street' in removed_df.columns:
            print(f"\n  Analyzing Person Street in Removed sheet:")
            removed_person_street = removed_df['Person Street']

            # Apply same blank detection logic
            is_na = removed_person_street.isna()
            str_vals = removed_person_street.astype(str).str.strip()
            is_empty = str_vals.isin(['', 'nan', 'None', 'NaT', '<NA>'])
            is_blank = is_na | is_empty

            blank_count = is_blank.sum()
            non_blank_count = (~is_blank).sum()

            print(f"    Total rows in Removed sheet: {len(removed_df):,}")
            print(f"    Blank Person Street: {blank_count:,} rows")
            print(f"    NON-blank Person Street: {non_blank_count:,} rows")

            if non_blank_count > 0:
                print(f"\n  ✗ ERROR: {non_blank_count} rows with valid Person Street in Removed sheet!")
                print(f"\n  FALSE POSITIVES (first 30):")
                false_positives = removed_df[~is_blank]
                for idx, row in false_positives.head(30).iterrows():
                    addr = row['Person Street']
                    removed_by = row.get('_Removed_By', 'Unknown')
                    step = row.get('_Step', '?')
                    print(f"    [{step}] '{addr}' (removed by: {removed_by})")

                # Group false positives by operation
                print(f"\n  False positives by operation:")
                fp_by_op = false_positives.groupby('_Removed_By').size()
                for op_name, count in fp_by_op.items():
                    print(f"    • {op_name}: {count} false positives")

                return False
            else:
                print(f"    ✓ All rows in Removed sheet have blank Person Street")
        else:
            print(f"    ⚠ Person Street column not in Removed sheet")
    else:
        print(f"  Removed sheet is empty")

    # Analyze results sheet
    print(f"\n[ANALYZE RESULTS SHEET]")
    if 'Person Street' in result_df.columns:
        result_person_street = result_df['Person Street']

        # Check for blanks in results
        is_na = result_person_street.isna()
        str_vals = result_person_street.astype(str).str.strip()
        is_empty = str_vals.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        is_blank = is_na | is_empty

        blank_count = is_blank.sum()

        print(f"  Total rows in Results sheet: {len(result_df):,}")
        print(f"  Blank Person Street: {blank_count:,} rows")

        if blank_count > 0:
            print(f"  ✗ ERROR: Results sheet contains {blank_count} blank Person Street values!")
            return False
        else:
            print(f"  ✓ Results sheet contains NO blank Person Street values")
    else:
        print(f"  ⚠ Person Street column not in Results sheet")

    print(f"\n{'='*100}")
    print("✓ ALL CHECKS PASSED")
    print("=" * 100)
    print(f"\nSummary:")
    print(f"  • Original: {len(df_original):,} rows")
    print(f"  • Results: {len(result_df):,} rows (all with valid Person Street)")
    print(f"  • Removed: {len(removed_df):,} rows (all with blank Person Street)")
    print(f"  • False positives: 0")
    print(f"  • Multi-operation tracking: WORKING CORRECTLY")

    return True

if __name__ == '__main__':
    success = test_full_workflow()
    exit(0 if success else 1)
