"""
Test for Bug Report: 539 valid addresses incorrectly marked as blank

This test verifies that the is_blank logic correctly:
1. ONLY removes NaN/None values
2. KEEPS all valid string addresses (even empty strings)
3. Results in ZERO false positives
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation

def test_with_actual_file():
    """Test with the actual Volunteer Directors file"""

    print("=" * 100)
    print("BUG REPORT TEST: 539 Valid Addresses Incorrectly Marked as Blank")
    print("=" * 100)

    # Load the file
    filename = 'Volunteer Directors 11.20.25.xlsx'
    print(f"\n[1] Loading file: {filename}")
    df = pd.read_excel(filename)
    print(f"    Loaded: {len(df):,} rows")

    # Check if Person Street column exists
    if 'Person Street' not in df.columns:
        print(f"\n✗ ERROR: 'Person Street' column not found")
        print(f"Available columns: {', '.join(df.columns)}")
        return False

    # Analyze original data
    print(f"\n[2] Original 'Person Street' column analysis:")
    total_rows = len(df)
    blank_rows = df['Person Street'].isna().sum()
    non_blank_rows = df['Person Street'].notna().sum()

    print(f"    Total rows: {total_rows:,}")
    print(f"    Blank (NaN) rows: {blank_rows:,}")
    print(f"    Non-blank rows: {non_blank_rows:,}")

    # Show some example addresses
    print(f"\n[3] Sample of non-blank addresses in original file:")
    sample_addresses = df[df['Person Street'].notna()]['Person Street'].head(10)
    for i, addr in enumerate(sample_addresses, 1):
        print(f"    {i}. {repr(addr)}")

    # Execute the operation
    print(f"\n[4] Executing 'Remove Rows If (Person Street is_blank)'...")
    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank'
    }

    result_df = operation.execute(df, params)

    # Calculate removed rows
    removed_indices = set(df.index) - set(result_df.index)
    removed_df = df.loc[list(removed_indices)]

    print(f"    Results sheet: {len(result_df):,} rows")
    print(f"    Removed sheet: {len(removed_df):,} rows")

    # Analyze removed sheet
    print(f"\n[5] Analyzing Removed sheet:")
    actual_blanks_removed = removed_df['Person Street'].isna().sum()
    valid_addresses_removed = removed_df['Person Street'].notna().sum()

    print(f"    Total removed: {len(removed_df):,} rows")
    print(f"    Actual blanks (NaN): {actual_blanks_removed:,} ✓")
    print(f"    Valid addresses: {valid_addresses_removed:,} {'✗ BUG!' if valid_addresses_removed > 0 else '✓'}")

    # If there are false positives, show them
    if valid_addresses_removed > 0:
        print(f"\n    ✗ FALSE POSITIVES FOUND - Valid addresses incorrectly removed:")
        false_positives = removed_df[removed_df['Person Street'].notna()]['Person Street']
        for i, addr in enumerate(false_positives.head(20), 1):
            print(f"       {i}. {repr(addr)}")
        if len(false_positives) > 20:
            print(f"       ... and {len(false_positives) - 20} more")

    # Analyze results sheet
    print(f"\n[6] Analyzing Results sheet:")
    blanks_in_results = result_df['Person Street'].isna().sum()
    valid_in_results = result_df['Person Street'].notna().sum()

    print(f"    Total kept: {len(result_df):,} rows")
    print(f"    Valid addresses: {valid_in_results:,} ✓")
    print(f"    Blank values: {blanks_in_results:,} {'✗ Should be 0!' if blanks_in_results > 0 else '✓'}")

    # Test specific addresses mentioned in bug report
    print(f"\n[7] Testing specific addresses from bug report:")
    test_addresses = [
        "6600 N Lincoln Ave Ste 300",
        "2150 Post St",
        "4205 NW 6th St",
        "1718 Patterson St",
        "36 S State St",
    ]

    for addr in test_addresses:
        # Check if this address exists in original file
        in_original = (df['Person Street'] == addr).any()
        if in_original:
            in_results = (result_df['Person Street'] == addr).any()
            in_removed = (removed_df['Person Street'] == addr).any()
            status = '✓' if in_results and not in_removed else '✗'
            location = 'Results' if in_results else 'Removed' if in_removed else 'Not found'
            print(f"    {status} {repr(addr):<35} -> {location}")
        else:
            print(f"    - {repr(addr):<35} -> Not in original file")

    # Final verdict
    print(f"\n{'=' * 100}")
    print("FINAL VERDICT")
    print(f"{'=' * 100}")

    success = valid_addresses_removed == 0 and blanks_in_results == 0

    if success:
        print(f"\n✓ SUCCESS - BUG IS FIXED!")
        print(f"  - Zero false positives (no valid addresses in Removed sheet)")
        print(f"  - All valid addresses kept in Results sheet")
        print(f"  - Only actual NaN values removed ({actual_blanks_removed:,} rows)")
        print(f"\nExpected results:")
        print(f"  Results sheet: {len(result_df):,} rows (all with valid addresses)")
        print(f"  Removed sheet: {len(removed_df):,} rows (all with NaN)")
    else:
        print(f"\n✗ FAILURE - BUG STILL EXISTS!")
        if valid_addresses_removed > 0:
            print(f"  - {valid_addresses_removed:,} valid addresses incorrectly removed")
        if blanks_in_results > 0:
            print(f"  - {blanks_in_results:,} blank values incorrectly kept in Results")

    return success

if __name__ == '__main__':
    success = test_with_actual_file()
    sys.exit(0 if success else 1)
