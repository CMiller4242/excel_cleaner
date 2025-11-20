#!/usr/bin/env python3
"""
Comprehensive diagnostic for Remove Rows If operation
Tests with realistic data matching user's scenario
"""

import pandas as pd
import numpy as np
from operations.data_ops import RemoveRowsIfOperation

def create_realistic_test_data():
    """Create test data matching the user's scenario"""

    # Create 2037 rows matching their description
    # ~1,255 blank, ~782 non-blank

    non_blank_addresses = [
        '3203 SE Woodstock Blvd',
        '2525 Glenn Hendren Dr Ste 202',
        '400 Maple Summit Rd',
        '6600 N Lincoln Ave Ste 300',
        '2150 Post St',
        '1234 Main Street',
        '5678 Oak Avenue',
        '9012 Elm Blvd Ste 100',
    ]

    # Create the dataset
    rows = []

    # Add 782 rows with non-blank addresses (cycling through the addresses)
    for i in range(782):
        addr = non_blank_addresses[i % len(non_blank_addresses)]
        rows.append({
            'ID': i + 1,
            'Person Street': addr,
            'Company': f'Company {i+1}'
        })

    # Add 1255 blank rows (mix of NaN, None, empty strings)
    for i in range(1255):
        blank_value = None
        if i % 4 == 0:
            blank_value = np.nan
        elif i % 4 == 1:
            blank_value = None
        elif i % 4 == 2:
            blank_value = ''
        else:
            blank_value = '   '  # Whitespace

        rows.append({
            'ID': 782 + i + 1,
            'Person Street': blank_value,
            'Company': f'Company {782+i+1}'
        })

    df = pd.DataFrame(rows)
    # Shuffle to mix blank and non-blank
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    return df

def diagnose_operation():
    """Run comprehensive diagnostic"""

    print("=" * 80)
    print("COMPREHENSIVE DIAGNOSTIC: Remove Rows If (is_blank)")
    print("=" * 80)

    # Create test data
    df = create_realistic_test_data()

    print(f"\nTest Data Created:")
    print(f"  Total rows: {len(df)}")

    # Count blanks in original
    person_street = df['Person Street']

    # Count using different methods
    count_isna = person_street.isna().sum()
    count_empty_str = (person_street == '').sum()
    count_whitespace = (person_street.astype(str).str.strip() == '').sum()

    # Count non-blank
    has_text = ~person_street.isna() & (person_street.astype(str).str.strip() != '')
    count_non_blank_old_method = has_text.sum()

    # Count using new method
    is_na = person_street.isna()
    str_values = person_street.astype(str).str.strip()
    is_empty_or_null_string = str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    is_blank_new_method = is_na | is_empty_or_null_string
    count_blank_new_method = is_blank_new_method.sum()
    count_non_blank_new_method = (~is_blank_new_method).sum()

    print(f"\nBlank Analysis (Original Data):")
    print(f"  isna(): {count_isna}")
    print(f"  == '': {count_empty_str}")
    print(f"  str.strip() == '': {count_whitespace}")
    print(f"  Old method (non-blank): {count_non_blank_old_method}")
    print(f"  New method (blank): {count_blank_new_method}")
    print(f"  New method (non-blank): {count_non_blank_new_method}")

    # Show sample blank values
    print(f"\nSample blank values:")
    blank_samples = df[is_blank_new_method]['Person Street'].head(10)
    for idx, val in blank_samples.items():
        print(f"  [{idx}] {repr(val)} (type: {type(val).__name__})")

    # Show sample non-blank values
    print(f"\nSample non-blank values:")
    non_blank_samples = df[~is_blank_new_method]['Person Street'].head(10)
    for idx, val in non_blank_samples.items():
        print(f"  [{idx}] {repr(val)} (type: {type(val).__name__})")

    # Execute operation
    print(f"\n{'='*80}")
    print("EXECUTING OPERATION")
    print("=" * 80)

    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank'
    }

    result_df = operation.execute(df, params)

    print(f"\nResults:")
    print(f"  Input rows: {len(df)}")
    print(f"  Output rows: {len(result_df)}")
    print(f"  Removed rows: {len(df) - len(result_df)}")

    # Verify correctness
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print("=" * 80)

    # Check if any non-blank rows were removed
    errors = []

    # Get the non-blank addresses that should be kept
    expected_kept_addresses = [
        '3203 SE Woodstock Blvd',
        '2525 Glenn Hendren Dr Ste 202',
        '400 Maple Summit Rd',
        '6600 N Lincoln Ave Ste 300',
        '2150 Post St',
    ]

    for addr in expected_kept_addresses:
        original_count = (df['Person Street'] == addr).sum()
        result_count = (result_df['Person Street'] == addr).sum()

        if result_count != original_count:
            errors.append(f"Address '{addr}': Had {original_count}, now has {result_count} (LOST {original_count - result_count})")

    # Check if any blank rows were kept
    result_person_street = result_df['Person Street']
    is_na_result = result_person_street.isna()
    str_values_result = result_person_street.astype(str).str.strip()
    is_empty_or_null_result = str_values_result.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    blank_in_result = is_na_result | is_empty_or_null_result

    blank_count_in_result = blank_in_result.sum()

    if blank_count_in_result > 0:
        errors.append(f"Result contains {blank_count_in_result} blank rows (should be 0)")
        print(f"\nBlank rows that were kept:")
        for idx, val in result_df[blank_in_result]['Person Street'].head(10).items():
            print(f"  {repr(val)}")

    # Print results
    if errors:
        print(f"\n✗ ERRORS FOUND:")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print(f"\n✓ ALL CHECKS PASSED")
        print(f"\nCorrect behavior:")
        print(f"  • All non-blank addresses preserved")
        print(f"  • All blank rows removed")
        print(f"  • Expected output: ~782 rows")
        print(f"  • Actual output: {len(result_df)} rows")
        return True

def test_specific_values():
    """Test with specific problematic values"""

    print(f"\n\n{'='*80}")
    print("TESTING SPECIFIC PROBLEMATIC VALUES")
    print("=" * 80)

    # Test each type of blank value individually
    test_cases = [
        ('NaN', np.nan, True),
        ('None', None, True),
        ('Empty string', '', True),
        ('Whitespace', '   ', True),
        ('Valid address', '3203 SE Woodstock Blvd', False),
        ('Another address', '2525 Glenn Hendren Dr Ste 202', False),
    ]

    for name, value, should_remove in test_cases:
        df = pd.DataFrame({
            'ID': [1],
            'Person Street': [value]
        })

        operation = RemoveRowsIfOperation()
        params = {
            'column': 'Person Street',
            'condition': 'is_blank'
        }

        result_df = operation.execute(df, params)

        was_removed = len(result_df) == 0
        status = "✓" if was_removed == should_remove else "✗"

        print(f"{status} {name:20s} {repr(value):40s} → {'REMOVED' if was_removed else 'KEPT':8s} (expected: {'REMOVE' if should_remove else 'KEEP'})")

        if was_removed != should_remove:
            print(f"   ERROR: Expected {'REMOVE' if should_remove else 'KEEP'}, got {'REMOVED' if was_removed else 'KEPT'}")

if __name__ == '__main__':
    print("Running comprehensive diagnostic...\n")

    test_specific_values()
    success = diagnose_operation()

    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print("=" * 80)

    if success:
        print("✓ Operation is working correctly")
        print("\nThe fix successfully:")
        print("  • Removes all blank rows (NaN, None, empty, whitespace)")
        print("  • Keeps all rows with valid addresses")
        print("  • Handles string conversions properly")
    else:
        print("✗ Operation is still broken")
        print("\nPlease check the errors above to identify the issue.")
