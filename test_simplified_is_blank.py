"""
Test the simplified is_blank implementation using ONLY pd.isna()
This test verifies that the new implementation correctly:
1. Removes NaN and None values
2. Keeps all valid addresses (including empty strings if any)
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation

def test_simplified_is_blank():
    """Test the simplified is_blank logic with various edge cases"""

    # Create comprehensive test data
    test_data = {
        'Row_Type': [
            'Valid address 1',
            'Valid address 2',
            'Valid address 3',
            'Valid address 4',
            'Valid address 5',
            'NaN value',
            'None value',
            'Empty string',
            'Whitespace only',
            'Literal "nan"',
            'Literal "None"',
            'Zero string',
            'Zero number',
            'Valid address 6',
        ],
        'Person Street': [
            "6600 N Lincoln Ave Ste 300",
            "2150 Post St",
            "4205 NW 6th St",
            "1718 Patterson St",
            "36 S State St",
            np.nan,
            None,
            "",  # Empty string - NEW: This will be KEPT, not removed
            "   ",  # Whitespace - NEW: This will be KEPT, not removed
            "nan",  # Literal string - NEW: This will be KEPT, not removed
            "None",  # Literal string - NEW: This will be KEPT, not removed
            "0",
            0,
            "PO Box 3310",
        ]
    }

    df = pd.DataFrame(test_data)

    print("=" * 100)
    print("TESTING SIMPLIFIED is_blank IMPLEMENTATION (ONLY pd.isna())")
    print("=" * 100)
    print(f"\nOriginal DataFrame ({len(df)} rows):")
    print(df)

    # Execute operation
    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank'
    }

    result_df = operation.execute(df, params)

    # Calculate removed
    removed_indices = set(df.index) - set(result_df.index)
    removed_df = df.loc[list(removed_indices)] if removed_indices else pd.DataFrame()

    print(f"\n{'=' * 100}")
    print(f"RESULTS AFTER 'Remove Rows If Person Street is_blank'")
    print(f"{'=' * 100}")
    print(f"\nResults DataFrame ({len(result_df)} rows - KEPT):")
    print(result_df)

    print(f"\nRemoved DataFrame ({len(removed_df)} rows - REMOVED):")
    if len(removed_df) > 0:
        print(removed_df)
    else:
        print("(None)")

    # Analyze results
    print(f"\n{'=' * 100}")
    print("DETAILED ANALYSIS")
    print(f"{'=' * 100}")

    print(f"\nOriginal: {len(df)} rows")
    print(f"Results: {len(result_df)} rows")
    print(f"Removed: {len(removed_df)} rows")

    # Check each category
    print(f"\nWhat was REMOVED:")
    if len(removed_df) > 0:
        for idx in removed_df.index:
            row_type = removed_df.loc[idx, 'Row_Type']
            value = removed_df.loc[idx, 'Person Street']
            print(f"  - {row_type}: {repr(value)}")
    else:
        print("  (Nothing)")

    print(f"\nWhat was KEPT:")
    for idx in result_df.index:
        row_type = result_df.loc[idx, 'Row_Type']
        value = result_df.loc[idx, 'Person Street']
        is_na = pd.isna(value)
        print(f"  - {row_type}: {repr(value)} (isna={is_na})")

    # Verify valid addresses
    valid_address_rows = [0, 1, 2, 3, 4, 13]  # Indices of valid address rows
    valid_in_results = all(idx in result_df.index for idx in valid_address_rows)

    print(f"\n{'=' * 100}")
    print("VERIFICATION")
    print(f"{'=' * 100}")

    print(f"\n✓ Valid addresses kept: {valid_in_results}")
    print(f"✓ NaN values removed: {5 in removed_df.index and 6 in removed_df.index if len(removed_df) > 0 else False}")

    # Test with user-reported addresses
    print(f"\n{'=' * 100}")
    print("TESTING USER-REPORTED ADDRESSES")
    print(f"{'=' * 100}")

    user_addresses = pd.DataFrame({
        'Person Street': [
            "6600 N Lincoln Ave Ste 300",
            "2150 Post St",
            "4205 NW 6th St",
            "1718 Patterson St",
            "36 S State St",
            np.nan,  # Should be removed
        ]
    })

    result = operation.execute(user_addresses, params)
    removed_idx = set(user_addresses.index) - set(result.index)
    removed = user_addresses.loc[list(removed_idx)] if removed_idx else pd.DataFrame()

    print(f"\nTest data: {len(user_addresses)} rows (5 valid addresses + 1 NaN)")
    print(f"Results: {len(result)} rows")
    print(f"Removed: {len(removed)} rows")

    valid_removed = result['Person Street'].isna().sum()
    actual_blanks_removed = removed['Person Street'].isna().sum() if len(removed) > 0 else 0

    print(f"\nAnalysis:")
    print(f"  Valid addresses in Results: {len(result) - valid_removed}")
    print(f"  Blanks in Results: {valid_removed}")
    print(f"  Blanks in Removed: {actual_blanks_removed}")

    # Final verdict
    print(f"\n{'=' * 100}")
    print("FINAL VERDICT")
    print(f"{'=' * 100}")

    all_valid_kept = len(result) == 5  # Should keep 5 valid addresses
    only_nan_removed = len(removed) == 1 and removed['Person Street'].isna().sum() == 1

    if all_valid_kept and only_nan_removed:
        print("✓ SUCCESS: All valid addresses kept, only NaN removed")
        return True
    else:
        print("✗ FAILURE:")
        if not all_valid_kept:
            print(f"  - Expected 5 valid addresses in Results, got {len(result)}")
        if not only_nan_removed:
            print(f"  - Expected only NaN in Removed, got {len(removed)} rows")
        return False

if __name__ == '__main__':
    success = test_simplified_is_blank()
    sys.exit(0 if success else 1)
