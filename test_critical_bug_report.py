"""
Test for critical bug report: 539 valid addresses incorrectly marked as blank
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation

def test_is_blank_with_reported_addresses():
    """Test with the exact addresses reported as incorrectly removed"""

    # Create test data with addresses user reported as incorrectly removed
    test_data = {
        'Person Street': [
            "6600 N Lincoln Ave Ste 300",
            "2150 Post St",
            "4205 NW 6th St",
            "1718 Patterson St",
            "36 S State St",
            np.nan,  # Actual blank
            None,    # Actual blank
            "",      # Empty string
            "Valid Address 123",
            "Another Valid St"
        ]
    }

    df = pd.DataFrame(test_data)

    print("=" * 80)
    print("TESTING REMOVE ROWS IF WITH REPORTED ADDRESSES")
    print("=" * 80)
    print(f"\nOriginal DataFrame ({len(df)} rows):")
    print(df)
    print(f"\nNaN count: {df['Person Street'].isna().sum()}")
    print(f"Non-NaN count: {df['Person Street'].notna().sum()}")

    # Test the operation
    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank'
    }

    result_df = operation.execute(df, params)

    print(f"\n{'=' * 80}")
    print(f"RESULTS AFTER 'Remove Rows If Person Street is_blank'")
    print(f"{'=' * 80}")
    print(f"\nResults DataFrame ({len(result_df)} rows - these were KEPT):")
    print(result_df)

    # Calculate removed rows
    removed_indices = set(df.index) - set(result_df.index)
    removed_df = df.loc[list(removed_indices)]

    print(f"\nRemoved DataFrame ({len(removed_df)} rows - these were REMOVED):")
    print(removed_df)

    # Analyze removed rows
    valid_in_removed = removed_df['Person Street'].notna().sum()
    actual_blanks_removed = removed_df['Person Street'].isna().sum()

    print(f"\n{'=' * 80}")
    print("ANALYSIS OF REMOVED ROWS")
    print(f"{'=' * 80}")
    print(f"Total removed: {len(removed_df)}")
    print(f"Actual blanks (NaN) removed: {actual_blanks_removed} ✓")
    print(f"Valid addresses removed: {valid_in_removed} {'✗ BUG!' if valid_in_removed > 0 else '✓'}")

    if valid_in_removed > 0:
        print(f"\nVALID ADDRESSES INCORRECTLY REMOVED:")
        for addr in removed_df[removed_df['Person Street'].notna()]['Person Street']:
            print(f"  ✗ {repr(addr)}")

    # Test each address individually
    print(f"\n{'=' * 80}")
    print("INDIVIDUAL ADDRESS TESTING")
    print(f"{'=' * 80}")

    test_addresses = [
        "6600 N Lincoln Ave Ste 300",
        "2150 Post St",
        "4205 NW 6th St",
        "1718 Patterson St",
        "36 S State St",
    ]

    for addr in test_addresses:
        series = pd.Series([addr])
        is_na = series.isna()
        str_values = series.astype(str).str.strip()
        is_empty_or_null_string = str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        is_blank = is_na | is_empty_or_null_string
        would_be_removed = is_blank.iloc[0]

        print(f"\nAddress: {repr(addr)}")
        print(f"  is_na: {is_na.iloc[0]}")
        print(f"  as_string: {repr(str_values.iloc[0])}")
        print(f"  is_empty_or_null_string: {is_empty_or_null_string.iloc[0]}")
        print(f"  Would be removed: {would_be_removed} {'✗ BUG!' if would_be_removed else '✓'}")

    # Final verdict
    print(f"\n{'=' * 80}")
    print("FINAL VERDICT")
    print(f"{'=' * 80}")
    if valid_in_removed == 0:
        print("✓ SUCCESS: No valid addresses were incorrectly removed")
        print("✓ All reported addresses are correctly kept in Results")
        return True
    else:
        print(f"✗ FAILURE: {valid_in_removed} valid addresses incorrectly removed")
        print("✗ Bug confirmed - is_blank logic is broken")
        return False

if __name__ == '__main__':
    success = test_is_blank_with_reported_addresses()
    sys.exit(0 if success else 1)
