"""
Direct test of is_blank logic as specified in bug report

This test directly tests the is_blank implementation with the exact test cases
provided in the bug report.
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation

def test_is_blank_direct():
    """Test is_blank logic with individual values"""

    print("=" * 100)
    print("DIRECT is_blank LOGIC TEST")
    print("=" * 100)

    # Test cases from bug report
    test_cases = [
        (np.nan, True, "NaN should be blank"),
        (None, True, "None should be blank"),
        ("6600 N Lincoln Ave Ste 300", False, "Valid address should NOT be blank"),
        ("2150 Post St", False, "Valid address should NOT be blank"),
        ("PO Box 3310", False, "PO Box should NOT be blank"),
        ("", False, "Empty string - treated as non-blank (use Remove Rows Containing for this)"),
        (0, False, "Zero should NOT be blank"),
        ("0", False, "String '0' should NOT be blank"),
    ]

    print("\nTesting individual values with pd.isna():")
    print(f"{'Value':<40} {'Expected':<10} {'Result':<10} {'Status':<10} {'Description'}")
    print("-" * 100)

    all_passed = True
    for value, expected, description in test_cases:
        # Test with pd.isna() directly (the implementation)
        result = pd.isna(value)
        status = "✓" if result == expected else "✗"

        if result != expected:
            all_passed = False

        print(f"{repr(value):<40} {str(expected):<10} {str(result):<10} {status:<10} {description}")

    # Test with actual DataFrame operation
    print(f"\n{'=' * 100}")
    print("TESTING WITH DATAFRAME OPERATION")
    print(f"{'=' * 100}")

    test_df = pd.DataFrame({
        'Description': [tc[2] for tc in test_cases],
        'Value': [tc[0] for tc in test_cases],
        'Expected_Blank': [tc[1] for tc in test_cases]
    })

    print(f"\nTest DataFrame:")
    print(test_df)

    # Execute operation
    operation = RemoveRowsIfOperation()
    params = {'column': 'Value', 'condition': 'is_blank'}

    result_df = operation.execute(test_df, params)
    removed_indices = set(test_df.index) - set(result_df.index)
    removed_df = test_df.loc[list(removed_indices)] if removed_indices else pd.DataFrame()

    print(f"\nResults after 'Remove Rows If (Value is_blank)':")
    print(f"  Original: {len(test_df)} rows")
    print(f"  Results: {len(result_df)} rows (kept)")
    print(f"  Removed: {len(removed_df)} rows")

    print(f"\nRemoved rows (should only be NaN and None):")
    if len(removed_df) > 0:
        for idx in removed_df.index:
            desc = removed_df.loc[idx, 'Description']
            val = removed_df.loc[idx, 'Value']
            expected = removed_df.loc[idx, 'Expected_Blank']
            status = '✓' if expected else '✗ ERROR'
            print(f"  {status} {desc}: {repr(val)}")
    else:
        print("  (None)")

    print(f"\nKept rows (should be all non-NaN values):")
    for idx in result_df.index:
        desc = result_df.loc[idx, 'Description']
        val = result_df.loc[idx, 'Value']
        expected_blank = result_df.loc[idx, 'Expected_Blank']
        status = '✓' if not expected_blank else '✗ ERROR'
        print(f"  {status} {desc}: {repr(val)}")

    # Final check
    print(f"\n{'=' * 100}")
    print("FINAL VERIFICATION")
    print(f"{'=' * 100}")

    # Verify only NaN and None were removed
    expected_removed = 2  # Only NaN and None
    expected_kept = len(test_cases) - expected_removed

    correct_count = len(removed_df) == expected_removed and len(result_df) == expected_kept

    # Verify no valid addresses in removed
    valid_addresses = ["6600 N Lincoln Ave Ste 300", "2150 Post St", "PO Box 3310"]
    no_valid_removed = all(addr not in removed_df['Value'].values for addr in valid_addresses)

    success = all_passed and correct_count and no_valid_removed

    if success:
        print("\n✓ SUCCESS: is_blank logic is correct!")
        print(f"  - All individual tests passed")
        print(f"  - Removed exactly {len(removed_df)} blank values (NaN, None)")
        print(f"  - Kept all {len(result_df)} non-blank values")
        print(f"  - No valid addresses were removed")
    else:
        print("\n✗ FAILURE: is_blank logic has issues!")
        if not all_passed:
            print("  - Some individual tests failed")
        if not correct_count:
            print(f"  - Expected to remove {expected_removed}, but removed {len(removed_df)}")
        if not no_valid_removed:
            print("  - Valid addresses were incorrectly removed")

    return success

if __name__ == '__main__':
    success = test_is_blank_direct()
    sys.exit(0 if success else 1)
