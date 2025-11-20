#!/usr/bin/env python3
"""
Minimal 20-row test case for Remove Rows If bug investigation

This creates a controlled test case with:
- 10 rows with valid Person Street addresses (should be KEPT)
- 10 rows with blank Person Street values (should be REMOVED)
"""

import pandas as pd
import numpy as np
from engine.executor import OperationExecutor
from utils.export_helper import ExportHelper

def create_minimal_test_data():
    """Create minimal 20-row test case"""

    data = {
        'ID': range(1, 21),
        'Name': [
            'Alice',      # Row 1 - HAS address
            'Bob',        # Row 2 - blank
            'Carol',      # Row 3 - HAS address
            'David',      # Row 4 - blank
            'Eve',        # Row 5 - HAS address
            'Frank',      # Row 6 - blank
            'Grace',      # Row 7 - HAS address
            'Henry',      # Row 8 - blank
            'Iris',       # Row 9 - HAS address
            'Jack',       # Row 10 - blank
            'Karen',      # Row 11 - HAS address
            'Larry',      # Row 12 - blank
            'Mary',       # Row 13 - HAS address
            'Nancy',      # Row 14 - blank
            'Oscar',      # Row 15 - HAS address
            'Paula',      # Row 16 - blank
            'Quinn',      # Row 17 - HAS address
            'Rachel',     # Row 18 - blank
            'Steve',      # Row 19 - HAS address
            'Tom',        # Row 20 - blank
        ],
        'Person Street': [
            '123 Main St',    # Row 1 - KEEP
            np.nan,           # Row 2 - REMOVE
            '456 Oak Ave',    # Row 3 - KEEP
            np.nan,           # Row 4 - REMOVE
            '789 Elm Blvd',   # Row 5 - KEEP
            np.nan,           # Row 6 - REMOVE
            '321 Pine Dr',    # Row 7 - KEEP
            np.nan,           # Row 8 - REMOVE
            '654 Maple Ln',   # Row 9 - KEEP
            np.nan,           # Row 10 - REMOVE
            '987 Cedar St',   # Row 11 - KEEP
            np.nan,           # Row 12 - REMOVE
            '147 Birch Ave',  # Row 13 - KEEP
            np.nan,           # Row 14 - REMOVE
            '258 Ash Rd',     # Row 15 - KEEP
            np.nan,           # Row 16 - REMOVE
            '369 Willow Way', # Row 17 - KEEP
            np.nan,           # Row 18 - REMOVE
            '741 Spruce St',  # Row 19 - KEEP
            np.nan,           # Row 20 - REMOVE
        ],
        'Email': [f'{name.lower()}@example.com' for name in [
            'Alice', 'Bob', 'Carol', 'David', 'Eve', 'Frank', 'Grace', 'Henry',
            'Iris', 'Jack', 'Karen', 'Larry', 'Mary', 'Nancy', 'Oscar', 'Paula',
            'Quinn', 'Rachel', 'Steve', 'Tom'
        ]]
    }

    return pd.DataFrame(data)

def test_minimal_case():
    """Test Remove Rows If with minimal 20-row case"""

    print("=" * 100)
    print("MINIMAL 20-ROW TEST CASE - Remove Rows If Bug Investigation")
    print("=" * 100)

    # Create test data
    df = create_minimal_test_data()

    print("\n[1] TEST DATA CREATED")
    print(f"    Total rows: {len(df)}")
    print("\n    Data:")
    print(df.to_string(index=True))

    # Identify expected results
    has_address = df['Person Street'].notna()
    expected_keep_count = has_address.sum()
    expected_remove_count = (~has_address).sum()

    print(f"\n[2] EXPECTED RESULTS")
    print(f"    Rows with address (should be KEPT): {expected_keep_count}")
    print(f"    Expected KEEP IDs: {list(df[has_address]['ID'].values)}")
    print(f"    Rows with blank address (should be REMOVED): {expected_remove_count}")
    print(f"    Expected REMOVE IDs: {list(df[~has_address]['ID'].values)}")

    # Save test data to Excel
    test_filename = "Test_20_Rows.xlsx"
    df.to_excel(test_filename, index=False)
    print(f"\n    ✓ Saved test data to: {test_filename}")

    # Test with Remove Rows If operation
    print(f"\n[3] EXECUTING: Remove Rows If (Person Street is blank)")

    operations = [{
        'operation_id': 'data_remove_rows_if',
        'parameters': {
            'column': 'Person Street',
            'condition': 'is_blank'
        },
        'enabled': True
    }]

    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df, operations)

    print(f"\n[4] ACTUAL RESULTS")
    print(f"    Results sheet: {len(result_df)} rows")
    print(f"    Removed sheet: {len(removed_df)} rows")

    # Show what's in Results sheet
    print(f"\n    Results sheet IDs: {list(result_df['ID'].values)}")
    print(f"    Results sheet Names: {list(result_df['Name'].values)}")

    # Show what's in Removed sheet
    if not removed_df.empty:
        print(f"\n    Removed sheet IDs: {list(removed_df['ID'].values)}")
        print(f"    Removed sheet Names: {list(removed_df['Name'].values)}")

    # Export to multi-sheet Excel
    output_filename = "Test_20_Rows_Results.xlsx"
    sheets = {
        'Original': df,
        'Results': result_df,
        'Removed': removed_df
    }
    ExportHelper.export_multiple_sheets(sheets, output_filename)
    print(f"\n    ✓ Exported to: {output_filename}")

    # Verification
    print(f"\n[5] VERIFICATION")

    errors = []

    # Check Results sheet count
    if len(result_df) != expected_keep_count:
        errors.append(f"Results sheet has {len(result_df)} rows, expected {expected_keep_count}")
        print(f"    ✗ Results sheet: {len(result_df)} rows (expected {expected_keep_count})")
    else:
        print(f"    ✓ Results sheet: {len(result_df)} rows (correct)")

    # Check Removed sheet count
    if len(removed_df) != expected_remove_count:
        errors.append(f"Removed sheet has {len(removed_df)} rows, expected {expected_remove_count}")
        print(f"    ✗ Removed sheet: {len(removed_df)} rows (expected {expected_remove_count})")
    else:
        print(f"    ✓ Removed sheet: {len(removed_df)} rows (correct)")

    # Check which IDs are in Results (should be odd numbers: 1, 3, 5, 7, 9, 11, 13, 15, 17, 19)
    actual_result_ids = set(result_df['ID'].values)
    expected_result_ids = set(df[has_address]['ID'].values)

    if actual_result_ids != expected_result_ids:
        missing = expected_result_ids - actual_result_ids
        extra = actual_result_ids - expected_result_ids
        if missing:
            errors.append(f"Results missing IDs: {missing}")
            print(f"    ✗ Results MISSING IDs: {sorted(missing)}")
        if extra:
            errors.append(f"Results has EXTRA IDs: {extra}")
            print(f"    ✗ Results has EXTRA IDs: {sorted(extra)}")
    else:
        print(f"    ✓ Results has correct IDs")

    # Check which IDs are in Removed (should be even numbers: 2, 4, 6, 8, 10, 12, 14, 16, 18, 20)
    actual_removed_ids = set(removed_df['ID'].values)
    expected_removed_ids = set(df[~has_address]['ID'].values)

    if actual_removed_ids != expected_removed_ids:
        missing = expected_removed_ids - actual_removed_ids
        extra = actual_removed_ids - expected_removed_ids
        if missing:
            errors.append(f"Removed missing IDs: {missing}")
            print(f"    ✗ Removed MISSING IDs: {sorted(missing)}")
        if extra:
            errors.append(f"Removed has EXTRA IDs: {extra}")
            print(f"    ✗ Removed has EXTRA IDs: {sorted(extra)}")
    else:
        print(f"    ✓ Removed has correct IDs")

    # Check for false positives in Removed sheet
    if not removed_df.empty and 'Person Street' in removed_df.columns:
        removed_person_street = removed_df['Person Street']
        removed_is_na = removed_person_street.isna()
        removed_str = removed_person_street.astype(str).str.strip()
        removed_is_empty = removed_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        removed_blank = removed_is_na | removed_is_empty

        non_blank_in_removed = (~removed_blank).sum()
        if non_blank_in_removed > 0:
            errors.append(f"Removed sheet has {non_blank_in_removed} rows with NON-BLANK addresses (FALSE POSITIVES)")
            print(f"    ✗ FALSE POSITIVES: {non_blank_in_removed} rows with addresses in Removed sheet")
            print(f"      IDs with false positives: {list(removed_df[~removed_blank]['ID'].values)}")
            print(f"      Names: {list(removed_df[~removed_blank]['Name'].values)}")
            print(f"      Addresses: {list(removed_df[~removed_blank]['Person Street'].values)}")
        else:
            print(f"    ✓ No false positives (all removed rows are blank)")

    # Final result
    print(f"\n{'='*100}")
    if errors:
        print("✗ TEST FAILED")
        print("=" * 100)
        print("\nErrors detected:")
        for error in errors:
            print(f"  • {error}")
        print("\nThe Remove Rows If operation is NOT working correctly.")
        return False
    else:
        print("✓ TEST PASSED")
        print("=" * 100)
        print("\nThe Remove Rows If operation is working correctly!")
        return True

if __name__ == '__main__':
    success = test_minimal_case()
    exit(0 if success else 1)
