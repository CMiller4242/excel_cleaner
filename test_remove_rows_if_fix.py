#!/usr/bin/env python3
"""
Test the Remove Rows If operation fix for blank value detection
"""

import pandas as pd
import numpy as np
from operations.data_ops import RemoveRowsIfOperation

def test_remove_blank_rows():
    """Test that is_blank condition correctly identifies blank vs non-blank rows"""

    print("=" * 80)
    print("TESTING REMOVE ROWS IF - 'is_blank' CONDITION FIX")
    print("=" * 80)

    # Create test data with various types of blank and non-blank values
    data = {
        'ID': range(1, 16),
        'Address': [
            '3203 SE Woodstock Blvd',         # Non-blank - should be KEPT
            '2525 Glenn Hendren Dr Ste 202',  # Non-blank - should be KEPT
            '',                                # Empty string - should be REMOVED
            None,                              # None - should be REMOVED
            np.nan,                            # NaN - should be REMOVED
            '400 Maple Summit Rd',             # Non-blank - should be KEPT
            '   ',                             # Whitespace only - should be REMOVED
            '6600 N Lincoln Ave Ste 300',      # Non-blank - should be KEPT
            pd.NaT,                            # NaT - should be REMOVED
            '2150 Post St',                    # Non-blank - should be KEPT
            '',                                # Empty string - should be REMOVED
            '123 Main Street',                 # Non-blank - should be KEPT
            None,                              # None - should be REMOVED
            '456 Oak Ave',                     # Non-blank - should be KEPT
            np.nan,                            # NaN - should be REMOVED
        ]
    }

    df = pd.DataFrame(data)

    print(f"\nInput DataFrame: {len(df)} rows")
    print("\nData:")
    print(df.to_string())

    # Count expected results
    non_blank_count = 7  # Rows with actual addresses
    blank_count = 8      # Rows with None, NaN, empty string, whitespace, NaT

    print(f"\nExpected:")
    print(f"  Non-blank (should be kept): {non_blank_count} rows")
    print(f"  Blank (should be removed): {blank_count} rows")

    # Execute operation
    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Address',
        'condition': 'is_blank'
    }

    result_df = operation.execute(df, params)

    print(f"\n{'='*80}")
    print("RESULTS AFTER 'Remove Rows If Address is blank'")
    print("=" * 80)

    print(f"\nResult DataFrame: {len(result_df)} rows")
    print("\nKept rows:")
    print(result_df.to_string())

    # Verify results
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print("=" * 80)

    success = True

    # Check that we kept the correct number of rows
    if len(result_df) == non_blank_count:
        print(f"✓ Correct number of rows kept: {len(result_df)}")
    else:
        print(f"✗ ERROR: Expected {non_blank_count} rows, got {len(result_df)}")
        success = False

    # Check that all kept rows have non-blank addresses
    for idx, row in result_df.iterrows():
        address = row['Address']
        if pd.isna(address) or str(address).strip() == '':
            print(f"✗ ERROR: Row {row['ID']} has blank address but was kept: {repr(address)}")
            success = False

    if success and len(result_df) == non_blank_count:
        print(f"✓ All kept rows have non-blank addresses")

    # Check that no non-blank rows were removed
    kept_ids = set(result_df['ID'])
    expected_kept_ids = {1, 2, 6, 8, 10, 12, 14}  # IDs of rows with actual addresses

    if kept_ids == expected_kept_ids:
        print(f"✓ Correct rows were kept (IDs: {sorted(kept_ids)})")
    else:
        missing = expected_kept_ids - kept_ids
        extra = kept_ids - expected_kept_ids
        if missing:
            print(f"✗ ERROR: Expected rows missing: {sorted(missing)}")
            success = False
        if extra:
            print(f"✗ ERROR: Unexpected rows kept: {sorted(extra)}")
            success = False

    print(f"\n{'='*80}")
    if success:
        print("✓ TEST PASSED - Bug is fixed!")
        print("=" * 80)
        print("\nThe operation now correctly:")
        print("  • Identifies NaN, None, empty strings, and whitespace as blank")
        print("  • Handles pandas string conversions ('nan', 'None', 'NaT')")
        print("  • Keeps all rows with actual non-blank values")
        print("  • Removes only truly blank rows")
        return True
    else:
        print("✗ TEST FAILED - Bug still exists")
        print("=" * 80)
        return False

def test_with_realistic_data():
    """Test with data similar to the user's ZoomInfo scenario"""

    print("\n\n" + "=" * 80)
    print("TESTING WITH REALISTIC ZOOMINFO-LIKE DATA")
    print("=" * 80)

    # Create data similar to user's issue - mix of blank and non-blank addresses
    addresses = [
        '3203 SE Woodstock Blvd',
        '2525 Glenn Hendren Dr Ste 202',
        np.nan,
        None,
        '400 Maple Summit Rd',
        '',
        '6600 N Lincoln Ave Ste 300',
        np.nan,
        '2150 Post St',
        None,
    ] * 100  # Repeat to get 1000 rows

    data = {
        'ID': range(len(addresses)),
        'Person Street': addresses,
        'Company': [f'Company {i}' for i in range(len(addresses))]
    }

    df = pd.DataFrame(data)

    print(f"\nInput: {len(df)} rows")

    # Count actual blanks
    blank_count = df['Person Street'].isna().sum()
    empty_count = (df['Person Street'].astype(str).str.strip().isin(['', 'nan', 'None', 'NaT', '<NA>'])).sum()

    print(f"Blank (NaN/None): {blank_count} rows")
    print(f"Empty/null strings: {empty_count} rows")

    # Execute operation
    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank'
    }

    result_df = operation.execute(df, params)

    print(f"\nAfter removing blank Person Street:")
    print(f"  Kept: {len(result_df)} rows")
    print(f"  Removed: {len(df) - len(result_df)} rows")

    # Verify no non-blank addresses were removed
    non_blank_addresses = ['3203 SE Woodstock Blvd', '2525 Glenn Hendren Dr Ste 202',
                          '400 Maple Summit Rd', '6600 N Lincoln Ave Ste 300', '2150 Post St']

    errors = []
    for addr in non_blank_addresses:
        count_in_result = (result_df['Person Street'] == addr).sum()
        count_in_original = (df['Person Street'] == addr).sum()
        if count_in_result != count_in_original:
            errors.append(f"Address '{addr}': Expected {count_in_original}, got {count_in_result}")

    if errors:
        print("\n✗ ERRORS FOUND:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✓ All non-blank addresses were preserved correctly!")
        return True

if __name__ == '__main__':
    test1_passed = test_remove_blank_rows()
    test2_passed = test_with_realistic_data()

    print("\n\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    if test1_passed and test2_passed:
        print("✓ ALL TESTS PASSED")
        print("\nThe bug has been fixed successfully!")
        print("\nWhat was wrong:")
        print("  • Old code: df[column].notna() & (df[column].astype(str).str.strip() != '')")
        print("  • Problem: NaN converts to string 'nan', which != '', so NaN rows were kept")
        print("\nHow it's fixed:")
        print("  • Now checks: is_na OR is_empty_or_null_string")
        print("  • Handles: NaN, None, empty strings, and string representations ('nan', 'None', 'NaT')")
        exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        exit(1)
