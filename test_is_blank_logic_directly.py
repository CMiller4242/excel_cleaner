#!/usr/bin/env python3
"""
Direct test of is_blank logic with the specific addresses reported as false positives

This tests the ACTUAL is_blank condition logic to see if it incorrectly
identifies valid addresses as blank.
"""

import pandas as pd
import numpy as np

def test_is_blank_logic_directly():
    """Test is_blank logic with specific addresses that are being incorrectly removed"""

    print("=" * 100)
    print("DIRECT TEST OF is_blank CONDITION LOGIC")
    print("=" * 100)

    # These are the addresses the user reports are being incorrectly removed
    test_values = [
        ("5700 Lindell Blvd", False, "Valid address - should NOT be blank"),
        ("2301 Vanderbilt Pl", False, "Valid address - should NOT be blank"),
        ("3840 Hulen St Ste 603", False, "Valid address - should NOT be blank"),
        ("210 S Prince St", False, "Valid address - should NOT be blank"),
        ("476 5th Ave", False, "Valid address - should NOT be blank"),
        ("1323 Yakima Ave", False, "Valid address - should NOT be blank"),
        ("615 Chestnut St Fl 17", False, "Valid address - should NOT be blank"),
        ("1 W Main St Ste 303", False, "Valid address - should NOT be blank"),
        ("10 Link Dr", False, "Valid address - should NOT be blank"),
        ("2845 Hamline Ave N Ste 200", False, "Valid address - should NOT be blank"),
        (np.nan, True, "NaN - should be blank"),
        (None, True, "None - should be blank"),
        ("", True, "Empty string - should be blank"),
        ("   ", True, "Whitespace - should be blank"),
    ]

    print("\n[1] Testing is_blank logic from operations/data_ops.py")
    print("\nThis is the EXACT logic used in RemoveRowsIfOperation:\n")
    print("```python")
    print("is_na = df[column].isna()")
    print("str_values = df[column].astype(str).str.strip()")
    print("is_empty_or_null_string = str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])")
    print("is_blank = is_na | is_empty_or_null_string")
    print("```")

    print("\n[2] Testing each value:")
    print(f"  {'Value':<40} {'Expected':<10} {'Result':<10} {'Status':<10}")
    print(f"  {'-'*40} {'-'*10} {'-'*10} {'-'*10}")

    errors = []

    for value, expected_blank, description in test_values:
        # Create a single-value series to test
        series = pd.Series([value])

        # Apply EXACT logic from operations/data_ops.py
        is_na = series.isna()
        str_values = series.astype(str).str.strip()
        is_empty_or_null_string = str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        is_blank = is_na | is_empty_or_null_string

        result_blank = is_blank.iloc[0]

        # Check if result matches expectation
        if result_blank == expected_blank:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            errors.append({
                'value': value,
                'expected': expected_blank,
                'actual': result_blank,
                'description': description
            })

        value_display = repr(value)[:38]
        expected_display = "BLANK" if expected_blank else "NON-BLANK"
        result_display = "BLANK" if result_blank else "NON-BLANK"

        print(f"  {value_display:<40} {expected_display:<10} {result_display:<10} {status:<10}")

        # Debug info for failures
        if status == "✗ FAIL":
            print(f"    DEBUG:")
            print(f"      is_na: {is_na.iloc[0]}")
            print(f"      str_values: {repr(str_values.iloc[0])}")
            print(f"      is_empty_or_null_string: {is_empty_or_null_string.iloc[0]}")
            print(f"      is_blank: {is_blank.iloc[0]}")

    # Summary
    print(f"\n{'='*100}")
    if errors:
        print("✗ is_blank LOGIC HAS ERRORS")
        print("=" * 100)
        print(f"\nFound {len(errors)} errors in is_blank condition logic:\n")
        for error in errors:
            print(f"  • {error['description']}")
            print(f"    Value: {repr(error['value'])}")
            print(f"    Expected is_blank={error['expected']}, got is_blank={error['actual']}")
            print()

        print("THE is_blank CONDITION IS BROKEN!")
        print("It is incorrectly identifying valid addresses as blank.")
        return False
    else:
        print("✓ is_blank LOGIC IS CORRECT")
        print("=" * 100)
        print("\nAll test values correctly identified as blank or non-blank.")
        print("The is_blank condition logic is working as expected.")
        return True

def test_with_actual_addresses_from_file():
    """Test with actual addresses from the Volunteer Directors file"""

    print("\n\n" + "=" * 100)
    print("TESTING WITH ACTUAL FILE ADDRESSES")
    print("=" * 100)

    # Load actual file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    print(f"    Loaded: {len(df):,} rows")

    # Get specific addresses that user says are being incorrectly removed
    test_addresses = [
        "5700 Lindell Blvd",
        "2301 Vanderbilt Pl",
        "3840 Hulen St Ste 603",
        "210 S Prince St",
        "476 5th Ave",
        "1323 Yakima Ave",
        "615 Chestnut St Fl 17",
        "1 W Main St Ste 303",
        "10 Link Dr",
        "2845 Hamline Ave N Ste 200"
    ]

    print(f"\n[2] Checking if these addresses exist in file:")
    for addr in test_addresses:
        count = (df['Person Street'] == addr).sum()
        print(f"    '{addr}': {count} instances")

    print(f"\n[3] Testing is_blank logic on Person Street column:")

    person_street = df['Person Street']

    # Apply is_blank logic
    is_na = person_street.isna()
    str_values = person_street.astype(str).str.strip()
    is_empty_or_null_string = str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    is_blank = is_na | is_empty_or_null_string

    print(f"    Total rows: {len(df):,}")
    print(f"    Identified as blank: {is_blank.sum():,}")
    print(f"    Identified as non-blank: {(~is_blank).sum():,}")

    print(f"\n[4] Checking if test addresses are marked as blank:")
    errors = []
    for addr in test_addresses:
        mask = df['Person Street'] == addr
        if mask.any():
            # Get is_blank value for this address
            is_blank_for_addr = is_blank[mask].any()

            if is_blank_for_addr:
                print(f"    ✗ '{addr}' is marked as BLANK (WRONG!)")
                errors.append(addr)
            else:
                print(f"    ✓ '{addr}' is marked as NON-BLANK (correct)")

    if errors:
        print(f"\n✗ ERROR: {len(errors)} valid addresses incorrectly marked as blank!")
        print("The is_blank condition is BROKEN!")
        return False
    else:
        print(f"\n✓ All test addresses correctly marked as non-blank")
        return True

if __name__ == '__main__':
    # Test 1: Direct logic test with specific values
    test1_pass = test_is_blank_logic_directly()

    # Test 2: Test with actual file
    test2_pass = test_with_actual_addresses_from_file()

    print("\n\n" + "=" * 100)
    print("FINAL RESULTS")
    print("=" * 100)

    if test1_pass and test2_pass:
        print("\n✓ ALL TESTS PASSED")
        print("\nThe is_blank condition logic is working correctly.")
        print("Valid addresses are NOT being marked as blank.")
        exit(0)
    else:
        print("\n✗ TESTS FAILED")
        print("\nThe is_blank condition logic is BROKEN.")
        print("Valid addresses are being incorrectly marked as blank.")
        exit(1)
