#!/usr/bin/env python3
"""
Test Remove Rows If operation with actual user file
Tests with Volunteer Directors 11.20.25.xlsx
"""

import pandas as pd
from operations.data_ops import RemoveRowsIfOperation

def test_with_actual_file():
    """Test with the actual user's file"""

    print("=" * 80)
    print("TESTING WITH ACTUAL FILE: Volunteer Directors 11.20.25.xlsx")
    print("=" * 80)

    # Load the actual file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\nLoading: {filename}")

    try:
        df = pd.read_excel(filename)
    except Exception as e:
        print(f"Error loading file: {e}")
        return False

    print(f"File loaded: {len(df)} rows, {len(df.columns)} columns")

    # Show column names
    print(f"\nColumns in file:")
    for col in df.columns:
        print(f"  - {col}")

    # Check if Person Street column exists
    if 'Person Street' not in df.columns:
        print("\n✗ ERROR: 'Person Street' column not found!")
        print("Available columns are listed above.")
        return False

    print(f"\n{'='*80}")
    print("ANALYZING 'Person Street' COLUMN")
    print("=" * 80)

    person_street = df['Person Street']

    # Count different types of blank values
    is_na = person_street.isna()
    count_na = is_na.sum()

    # Check for empty strings and whitespace
    str_values = person_street.astype(str).str.strip()
    is_empty_or_null_string = str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])

    # Combined blank check (this is what the fix uses)
    is_blank = is_na | is_empty_or_null_string
    count_blank = is_blank.sum()
    count_non_blank = (~is_blank).sum()

    print(f"\nOriginal data analysis:")
    print(f"  Total rows: {len(df)}")
    print(f"  Blank rows (NaN/None/empty): {count_blank}")
    print(f"  Non-blank rows (with addresses): {count_non_blank}")

    # Show sample blank values
    print(f"\nSample blank values (first 10):")
    blank_samples = df[is_blank]['Person Street'].head(10)
    if len(blank_samples) > 0:
        for idx, val in blank_samples.items():
            print(f"  [{idx}] {repr(val)} (type: {type(val).__name__})")
    else:
        print("  (No blank values found)")

    # Show sample non-blank values
    print(f"\nSample non-blank values (first 10):")
    non_blank_samples = df[~is_blank]['Person Street'].head(10)
    if len(non_blank_samples) > 0:
        for idx, val in non_blank_samples.items():
            print(f"  [{idx}] {repr(val)}")
    else:
        print("  (No non-blank values found)")

    # Execute operation
    print(f"\n{'='*80}")
    print("EXECUTING: Remove Rows If (Person Street is blank)")
    print("=" * 80)

    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank'
    }

    result_df = operation.execute(df, params)

    print(f"\nResults:")
    print(f"  Input rows:   {len(df):,}")
    print(f"  Output rows:  {len(result_df):,}")
    print(f"  Removed rows: {len(df) - len(result_df):,}")

    # Verify correctness
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print("=" * 80)

    errors = []

    # Check if result matches expected non-blank count
    expected_kept = count_non_blank
    actual_kept = len(result_df)

    if actual_kept == expected_kept:
        print(f"✓ Correct number of rows kept: {actual_kept} (expected {expected_kept})")
    else:
        errors.append(f"Row count mismatch: kept {actual_kept}, expected {expected_kept}")
        print(f"✗ ERROR: Expected to keep {expected_kept} rows, actually kept {actual_kept}")

    # Check that result has no blank Person Street values
    result_person_street = result_df['Person Street']
    result_is_na = result_person_street.isna()
    result_str_values = result_person_street.astype(str).str.strip()
    result_is_empty = result_str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    result_blank = result_is_na | result_is_empty
    result_blank_count = result_blank.sum()

    if result_blank_count == 0:
        print(f"✓ No blank rows in result (all {len(result_df)} rows have addresses)")
    else:
        errors.append(f"Result contains {result_blank_count} blank rows")
        print(f"✗ ERROR: Result contains {result_blank_count} blank 'Person Street' values")
        print(f"\nBlank values that were incorrectly kept:")
        for idx, val in result_df[result_blank]['Person Street'].head(10).items():
            print(f"  {repr(val)}")

    # Check specific addresses mentioned in bug report
    print(f"\nChecking specific addresses from bug report:")
    test_addresses = [
        '3203 SE Woodstock Blvd',
        '2525 Glenn Hendren Dr Ste 202',
        '400 Maple Summit Rd',
        '6600 N Lincoln Ave Ste 300',
        '2150 Post St'
    ]

    for addr in test_addresses:
        count_in_original = (df['Person Street'] == addr).sum()
        count_in_result = (result_df['Person Street'] == addr).sum()

        if count_in_original > 0:
            if count_in_result == count_in_original:
                print(f"  ✓ '{addr}': {count_in_original} → {count_in_result} (preserved)")
            else:
                print(f"  ✗ '{addr}': {count_in_original} → {count_in_result} (LOST {count_in_original - count_in_result})")
                errors.append(f"Lost {count_in_original - count_in_result} rows with address '{addr}'")

    # Final result
    print(f"\n{'='*80}")
    if errors:
        print("✗ TEST FAILED")
        print("=" * 80)
        print("\nErrors found:")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print("✓ TEST PASSED")
        print("=" * 80)
        print("\nThe fix is working correctly with your actual data!")
        print(f"\nSummary:")
        print(f"  • Started with {len(df):,} rows")
        print(f"  • Removed {len(df) - len(result_df):,} blank rows")
        print(f"  • Kept {len(result_df):,} rows with addresses")
        print(f"  • All non-blank addresses preserved")
        print(f"  • Zero false positives")
        return True

if __name__ == '__main__':
    success = test_with_actual_file()
    exit(0 if success else 1)
