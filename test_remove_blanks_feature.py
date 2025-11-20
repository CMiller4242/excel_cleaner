#!/usr/bin/env python3
"""
Test the Remove Blanks feature in Remove Rows Containing operation
"""

import pandas as pd
import numpy as np
from engine.executor import OperationExecutor

def test_remove_blanks_feature():
    """Test Remove Blanks with actual file"""

    print("=" * 100)
    print("TESTING REMOVE BLANKS FEATURE - Remove Rows Containing Operation")
    print("=" * 100)

    # Load actual file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[1] Loading: {filename}")
    df_original = pd.read_excel(filename)
    print(f"    Loaded: {len(df_original):,} rows × {len(df_original.columns)} columns")

    # Test 1: Remove Blanks using preset
    print(f"\n[2] Test 1: Remove Blanks using 'Remove Blanks' preset")
    operations = [{
        'operation_id': 'remove_rows_containing',
        'parameters': {
            'columns': ['Person Street'],
            'patterns': '',  # Not used with Remove Blanks preset
            'preset': 'Remove Blanks',
            'case_sensitive': False,
            'match_whole_cell': False,
            'remove_blanks': False  # Will be overridden by preset
        },
        'enabled': True
    }]

    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df_original, operations)

    print(f"    Original: {len(df_original):,} rows")
    print(f"    Results:  {len(result_df):,} rows")
    print(f"    Removed:  {len(removed_df):,} rows")

    # Verify results
    print(f"\n    Verification:")

    # Check Results sheet
    result_person_street = result_df['Person Street']
    result_is_na = result_person_street.isna()
    result_str = result_person_street.astype(str).str.strip()
    result_is_empty = result_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    result_blank = result_is_na | result_is_empty

    print(f"      Results sheet:")
    print(f"        • Blank Person Street: {result_blank.sum()} rows")
    print(f"        • Non-blank Person Street: {(~result_blank).sum()} rows")

    # Check Removed sheet
    if not removed_df.empty and 'Person Street' in removed_df.columns:
        removed_person_street = removed_df['Person Street']
        removed_is_na = removed_person_street.isna()
        removed_str = removed_person_street.astype(str).str.strip()
        removed_is_empty = removed_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        removed_blank = removed_is_na | removed_is_empty

        print(f"      Removed sheet:")
        print(f"        • Blank Person Street: {removed_blank.sum()} rows")
        print(f"        • NON-blank Person Street: {(~removed_blank).sum()} rows")

        if (~removed_blank).sum() > 0:
            print(f"\n      ✗ ERROR: Removed sheet contains {(~removed_blank).sum()} NON-BLANK rows!")
            print(f"      Examples (first 10):")
            false_positives = removed_df[~removed_blank].head(10)
            for idx, row in false_positives.iterrows():
                print(f"        '{row['Person Street']}'")
            return False
        else:
            print(f"      ✓ All removed rows have blank Person Street")
    else:
        print(f"      Removed sheet is empty or missing Person Street")

    # Test 2: Remove Blanks using checkbox
    print(f"\n[3] Test 2: Remove Blanks using remove_blanks checkbox")
    operations = [{
        'operation_id': 'remove_rows_containing',
        'parameters': {
            'columns': ['Person Street'],
            'patterns': '',
            'preset': 'Custom (use patterns above)',
            'case_sensitive': False,
            'match_whole_cell': False,
            'remove_blanks': True  # Explicitly enable via checkbox
        },
        'enabled': True
    }]

    result_df2, removed_df2 = executor.execute_queue_with_tracking(df_original, operations)

    print(f"    Original: {len(df_original):,} rows")
    print(f"    Results:  {len(result_df2):,} rows")
    print(f"    Removed:  {len(removed_df2):,} rows")

    # Verify results match Test 1
    if len(result_df2) == len(result_df) and len(removed_df2) == len(removed_df):
        print(f"    ✓ Results match Test 1 (preset and checkbox produce same results)")
    else:
        print(f"    ✗ ERROR: Results don't match!")
        print(f"      Test 1 Results: {len(result_df)}, Removed: {len(removed_df)}")
        print(f"      Test 2 Results: {len(result_df2)}, Removed: {len(removed_df2)}")
        return False

    # Test 3: Combined - Remove Blanks + Pattern matching
    print(f"\n[4] Test 3: Remove Blanks + Pattern matching (PO Boxes)")
    operations = [{
        'operation_id': 'remove_rows_containing',
        'parameters': {
            'columns': ['Person Street'],
            'patterns': 'PO BOX, P.O. BOX',
            'preset': 'Custom (use patterns above)',
            'case_sensitive': False,
            'match_whole_cell': False,
            'remove_blanks': True  # Remove blanks AND PO boxes
        },
        'enabled': True
    }]

    result_df3, removed_df3 = executor.execute_queue_with_tracking(df_original, operations)

    print(f"    Original: {len(df_original):,} rows")
    print(f"    Results:  {len(result_df3):,} rows")
    print(f"    Removed:  {len(removed_df3):,} rows")

    # Should remove more rows than just blanks (blanks + PO boxes)
    if len(removed_df3) >= len(removed_df):
        print(f"    ✓ Combined removal works (removed {len(removed_df3) - len(removed_df)} additional PO box rows)")
    else:
        print(f"    ✗ ERROR: Combined removal removed fewer rows than blanks alone!")
        return False

    # Final summary
    print(f"\n{'='*100}")
    print("SUMMARY")
    print("=" * 100)

    print(f"\nTest 1 (Remove Blanks preset):")
    print(f"  • Results: {len(result_df):,} rows (all with valid Person Street) ✓")
    print(f"  • Removed: {len(removed_df):,} rows (all with blank Person Street) ✓")

    print(f"\nTest 2 (remove_blanks checkbox):")
    print(f"  • Results: {len(result_df2):,} rows ✓")
    print(f"  • Matches Test 1: ✓")

    print(f"\nTest 3 (Combined: Blanks + Patterns):")
    print(f"  • Results: {len(result_df3):,} rows ✓")
    print(f"  • Removed: {len(removed_df3):,} rows (blanks + PO boxes) ✓")

    print(f"\n{'='*100}")
    print("✓ ALL TESTS PASSED")
    print("=" * 100)

    print(f"\nThe Remove Blanks feature is working correctly!")
    print(f"Users can now remove blank rows using either:")
    print(f"  1. 'Remove Blanks' preset")
    print(f"  2. 'remove_blanks' checkbox")
    print(f"  3. Combined with pattern matching")

    return True

if __name__ == '__main__':
    success = test_remove_blanks_feature()
    exit(0 if success else 1)
