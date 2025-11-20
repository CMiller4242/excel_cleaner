#!/usr/bin/env python3
"""
Diagnose the executor tracking bug with reset_index

The issue: RemoveRowsIfOperation calls reset_index(drop=True) after filtering,
which changes the row indices. The executor's execute_queue_with_tracking
compares indices before/after to identify removed rows, but this breaks when
indices are reset.
"""

import pandas as pd
import numpy as np
from engine.executor import OperationExecutor

def test_index_tracking_bug():
    """Demonstrate the index tracking bug"""

    print("=" * 80)
    print("DEMONSTRATING INDEX TRACKING BUG")
    print("=" * 80)

    # Create test data
    data = {
        'ID': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'Address': [
            '123 Main St',      # Keep
            np.nan,              # Remove
            '456 Oak Ave',       # Keep
            '',                  # Remove
            '789 Elm Blvd',      # Keep
            None,                # Remove
            '111 Pine Dr',       # Keep
            '   ',               # Remove
            '222 Maple Ln',      # Keep
            np.nan               # Remove
        ]
    }

    df = pd.DataFrame(data)

    print("\nOriginal DataFrame:")
    print(df)
    print(f"\nOriginal indices: {list(df.index)}")

    # Create operation config
    operations = [{
        'operation_id': 'data_remove_rows_if',
        'parameters': {
            'column': 'Address',
            'condition': 'is_blank'
        },
        'enabled': True
    }]

    # Execute with tracking
    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df, operations)

    print("\n" + "=" * 80)
    print("AFTER OPERATION")
    print("=" * 80)

    print(f"\nResult DataFrame (rows that were KEPT):")
    print(result_df)
    print(f"Result indices: {list(result_df.index)}")

    print(f"\nRemoved DataFrame (rows that were REMOVED):")
    print(removed_df[['ID', 'Address']] if not removed_df.empty else "Empty")

    # Verify correctness
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    # Which IDs should be removed? (blank addresses)
    expected_removed_ids = {2, 4, 6, 8, 10}  # IDs with blank addresses
    expected_kept_ids = {1, 3, 5, 7, 9}      # IDs with addresses

    # Which IDs were actually removed?
    if not removed_df.empty:
        actual_removed_ids = set(removed_df['ID'].values)
    else:
        actual_removed_ids = set()

    # Which IDs were actually kept?
    actual_kept_ids = set(result_df['ID'].values)

    print(f"\nExpected to remove IDs: {sorted(expected_removed_ids)}")
    print(f"Actually removed IDs:   {sorted(actual_removed_ids)}")

    print(f"\nExpected to keep IDs:   {sorted(expected_kept_ids)}")
    print(f"Actually kept IDs:      {sorted(actual_kept_ids)}")

    # Check for errors
    errors = []

    if actual_kept_ids != expected_kept_ids:
        errors.append(f"KEPT IDs mismatch: expected {expected_kept_ids}, got {actual_kept_ids}")

    if actual_removed_ids != expected_removed_ids:
        errors.append(f"REMOVED IDs mismatch: expected {expected_removed_ids}, got {actual_removed_ids}")

    # Check for false positives (kept rows shown as removed)
    false_positives = actual_removed_ids - expected_removed_ids
    if false_positives:
        errors.append(f"False positives: IDs {false_positives} have valid data but marked as removed")
        print(f"\n✗ FALSE POSITIVES: {false_positives}")
        print("These rows have valid addresses but are marked as removed:")
        for id_val in false_positives:
            orig_row = df[df['ID'] == id_val]
            if not orig_row.empty:
                addr = orig_row['Address'].values[0]
                print(f"  ID {id_val}: '{addr}'")

    # Check for false negatives (removed rows shown as kept)
    false_negatives = actual_kept_ids - expected_kept_ids
    if false_negatives:
        errors.append(f"False negatives: IDs {false_negatives} are blank but marked as kept")
        print(f"\n✗ FALSE NEGATIVES: {false_negatives}")

    print("\n" + "=" * 80)
    if errors:
        print("✗ TEST FAILED - BUG CONFIRMED")
        print("=" * 80)
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print("✓ TEST PASSED - NO BUG")
        print("=" * 80)
        return True

def demonstrate_index_reset_issue():
    """Show why reset_index breaks index-based tracking"""

    print("\n\n" + "=" * 80)
    print("DEMONSTRATING WHY reset_index() BREAKS INDEX TRACKING")
    print("=" * 80)

    # Create simple dataframe
    df = pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Value': ['Keep', 'Remove', 'Keep', 'Remove', 'Keep']
    })

    print("\nStep 1: Original DataFrame")
    print(df)
    print(f"Indices: {list(df.index)}")

    # Apply mask (keep rows where Value == 'Keep')
    mask = df['Value'] == 'Keep'
    df_filtered = df[mask]

    print("\nStep 2: After applying mask (before reset_index)")
    print(df_filtered)
    print(f"Indices: {list(df_filtered.index)}")
    print(f"Note: Indices are [0, 2, 4] - the original row positions")

    # Reset index
    df_reset = df_filtered.reset_index(drop=True)

    print("\nStep 3: After reset_index(drop=True)")
    print(df_reset)
    print(f"Indices: {list(df_reset.index)}")
    print(f"Note: Indices are now [0, 1, 2] - consecutive from 0")

    print("\n" + "-" * 80)
    print("THE PROBLEM:")
    print("-" * 80)
    print("If executor compares indices:")
    print(f"  Before: {set([0, 1, 2, 3, 4])}")
    print(f"  After:  {set([0, 1, 2])} (after reset_index)")
    print(f"  Difference: {set([0, 1, 2, 3, 4]) - set([0, 1, 2])} = {3, 4}")
    print(f"\nBut the ACTUAL removed rows were at indices [1, 3]!")
    print(f"The executor will think rows 3 and 4 were removed.")
    print(f"It will then try to get df_before.loc[[3, 4]] to save removed data.")
    print(f"This gives WRONG rows in the 'Removed' sheet!")

if __name__ == '__main__':
    # First demonstrate the concept
    demonstrate_index_reset_issue()

    # Then test with actual operation
    print("\n\n")
    success = test_index_tracking_bug()

    exit(0 if success else 1)
