#!/usr/bin/env python3
"""
Test the EXACT addresses mentioned by the user
"""

import pandas as pd
import numpy as np
from operations.data_ops import RemoveRowsIfOperation

def test_user_reported_addresses():
    """Test specific addresses user says are being incorrectly removed"""

    print("=" * 100)
    print("TESTING USER-REPORTED ADDRESSES")
    print("=" * 100)

    # Load file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    print(f"    Loaded: {len(df):,} rows")

    # These are the addresses user reports are incorrectly in Removed sheet
    test_addresses = [
        "2150 Post St",
        "4205 NW 8th St",
        "1718 Patterson St",
        "365 State St",
        "25701 Science Park Dr"
    ]

    print(f"\n[2] Checking if these addresses exist in original file:")
    for addr in test_addresses:
        matches = df[df['Person Street'] == addr]
        if not matches.empty:
            idx = matches.index[0]
            value = df.loc[idx, 'Person Street']
            is_na = pd.isna(value)
            print(f"    Row {idx}: '{addr}'")
            print(f"      pd.isna() = {is_na}")
            print(f"      type = {type(value)}")
            print(f"      repr = {repr(value)}")
        else:
            print(f"    '{addr}' - NOT FOUND in file")

    # Test with Remove Rows If operation
    print(f"\n[3] Testing with RemoveRowsIfOperation")

    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank'
    }

    result_df = operation.execute(df.copy(), params)

    # Calculate what was removed
    removed_indices = set(df.index) - set(result_df.index)
    if removed_indices:
        removed_df = df.loc[list(removed_indices)]
    else:
        removed_df = pd.DataFrame()

    print(f"    Results: {len(result_df):,} rows")
    print(f"    Removed: {len(removed_df):,} rows")

    # Check where each test address ended up
    print(f"\n[4] Checking where test addresses ended up:")
    errors = []

    for addr in test_addresses:
        in_results = addr in result_df['Person Street'].values if len(result_df) > 0 else False
        in_removed = addr in removed_df['Person Street'].values if len(removed_df) > 0 else False

        if in_removed:
            print(f"    ✗ ERROR: '{addr}' is in REMOVED sheet!")
            errors.append(addr)
        elif in_results:
            print(f"    ✓ OK: '{addr}' is in RESULTS sheet")
        else:
            print(f"    ? NOT FOUND: '{addr}' not in either sheet")

    # Check ALL addresses in removed sheet
    if not removed_df.empty and 'Person Street' in removed_df.columns:
        print(f"\n[5] Analyzing what's actually in Removed sheet:")

        removed_person_street = removed_df['Person Street']
        removed_is_na = removed_person_street.isna()
        removed_str = removed_person_street.astype(str).str.strip()
        removed_is_empty = removed_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        removed_blank = removed_is_na | removed_is_empty

        blank_count = removed_blank.sum()
        non_blank_count = (~removed_blank).sum()

        print(f"    Total in Removed: {len(removed_df):,}")
        print(f"    Blank values: {blank_count:,}")
        print(f"    NON-blank values: {non_blank_count:,}")

        if non_blank_count > 0:
            print(f"\n    ✗ ERROR: Found {non_blank_count} NON-BLANK values in Removed!")
            print(f"    First 20 non-blank values in Removed:")
            non_blank_removed = removed_df[~removed_blank].head(20)
            for idx, row in non_blank_removed.iterrows():
                addr = row['Person Street']
                print(f"      [{idx}] '{addr}'")
            errors.append("Non-blank values in Removed")

    # Final verdict
    print(f"\n{'='*100}")
    if errors:
        print("✗ TEST FAILED - BUGS FOUND")
        print("=" * 100)
        print(f"\nErrors: {errors}")
        return False
    else:
        print("✓ TEST PASSED - NO BUGS")
        print("=" * 100)
        return True

if __name__ == '__main__':
    success = test_user_reported_addresses()
    exit(0 if success else 1)
