"""
Test the rewritten explicit loop-based is_blank logic

This tests the new implementation that uses explicit loops instead of
pandas vectorized operations to avoid any indexing ambiguity.
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation

def test_rewritten_logic():
    """Test the new explicit loop-based implementation"""

    print("=" * 100)
    print("TESTING: Rewritten Explicit Loop-Based is_blank Logic")
    print("=" * 100)

    # Load actual file
    filename = 'Volunteer Directors 11.20.25.xlsx'
    print(f"\n[1] Loading file: {filename}")
    df = pd.read_excel(filename)
    print(f"    Total rows: {len(df):,}")
    print(f"    NaN in 'Person Street': {df['Person Street'].isna().sum():,}")
    print(f"    Valid in 'Person Street': {df['Person Street'].notna().sum():,}")

    operation = RemoveRowsIfOperation()

    # TEST 1: Standard Mode
    print(f"\n{'=' * 100}")
    print("[2] TESTING STANDARD MODE (enhanced_blank_detection = False)")
    print(f"{'=' * 100}")

    params_std = {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': False
    }

    result_std = operation.execute(df, params_std)
    removed_std_indices = set(df.index) - set(result_std.index)
    removed_std = df.loc[list(removed_std_indices)]

    print(f"\nResults:")
    print(f"  Input: {len(df):,} rows")
    print(f"  Results (kept): {len(result_std):,} rows")
    print(f"  Removed: {len(removed_std):,} rows")

    # Validate
    expected_kept = df['Person Street'].notna().sum()
    expected_removed = df['Person Street'].isna().sum()

    print(f"\nValidation:")
    print(f"  Expected to keep: {expected_kept:,} rows")
    print(f"  Actually kept: {len(result_std):,} rows")
    print(f"  Match: {'✓' if len(result_std) == expected_kept else '✗ ERROR'}")

    print(f"\n  Expected to remove: {expected_removed:,} rows")
    print(f"  Actually removed: {len(removed_std):,} rows")
    print(f"  Match: {'✓' if len(removed_std) == expected_removed else '✗ ERROR'}")

    # Check for false positives
    false_pos = removed_std['Person Street'].notna().sum()
    print(f"\n  False positives (non-NaN removed): {false_pos}")
    print(f"  Status: {'✓ PERFECT' if false_pos == 0 else '✗ BUG'}")

    if false_pos > 0:
        print(f"\n  Examples of incorrectly removed values:")
        for val in removed_std[removed_std['Person Street'].notna()]['Person Street'].head(10):
            print(f"    - {repr(val)}")

    # TEST 2: Enhanced Mode
    print(f"\n{'=' * 100}")
    print("[3] TESTING ENHANCED MODE (enhanced_blank_detection = True)")
    print(f"{'=' * 100}")

    params_enh = {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': True
    }

    result_enh = operation.execute(df, params_enh)
    removed_enh_indices = set(df.index) - set(result_enh.index)
    removed_enh = df.loc[list(removed_enh_indices)]

    print(f"\nResults:")
    print(f"  Input: {len(df):,} rows")
    print(f"  Results (kept): {len(result_enh):,} rows")
    print(f"  Removed: {len(removed_enh):,} rows")

    # Analyze removed
    nan_removed = removed_enh['Person Street'].isna().sum()
    non_nan_removed = removed_enh['Person Street'].notna().sum()

    print(f"\n  Removed breakdown:")
    print(f"    NaN values: {nan_removed:,}")
    print(f"    Non-NaN values: {non_nan_removed:,}")

    if non_nan_removed > 0:
        # Check if they are expected (empty/"N/A") or bugs (addresses)
        valid_addresses_removed = 0
        for val in removed_enh[removed_enh['Person Street'].notna()]['Person Street']:
            if isinstance(val, str):
                cleaned = val.strip().lower()
                if cleaned not in ['', 'n/a', 'na', 'null', 'none']:
                    valid_addresses_removed += 1
                    if valid_addresses_removed <= 5:
                        print(f"    ✗ BUG: Valid address removed: {repr(val)}")

        if valid_addresses_removed > 0:
            print(f"\n  ✗ ERROR: {valid_addresses_removed} valid addresses removed!")
        else:
            print(f"\n  ✓ OK: Only blank/N/A values removed (as designed)")

    # TEST 3: Specific addresses
    print(f"\n{'=' * 100}")
    print("[4] CHECKING SPECIFIC PROBLEM ADDRESSES")
    print(f"{'=' * 100}")

    problem_addresses = [
        "6600 N Lincoln Ave Ste 300",
        "2150 Post St",
        "4205 NW 6th St",
        "1718 Patterson St",
        "36 S State St"
    ]

    all_kept_std = True
    all_kept_enh = True

    for addr in problem_addresses:
        exists = (df['Person Street'] == addr).any()
        if exists:
            in_std = (result_std['Person Street'] == addr).any()
            in_enh = (result_enh['Person Street'] == addr).any()

            std_status = '✓ KEPT' if in_std else '✗ REMOVED'
            enh_status = '✓ KEPT' if in_enh else '✗ REMOVED'

            if not in_std:
                all_kept_std = False
            if not in_enh:
                all_kept_enh = False

            print(f"\n  {addr}")
            print(f"    Standard: {std_status}")
            print(f"    Enhanced: {enh_status}")

    # FINAL VERDICT
    print(f"\n{'=' * 100}")
    print("FINAL VERDICT")
    print(f"{'=' * 100}")

    std_success = (len(result_std) == expected_kept and false_pos == 0 and all_kept_std)
    enh_success = (all_kept_enh)

    print(f"\nStandard Mode:")
    print(f"  Expected: {expected_kept:,} rows kept")
    print(f"  Actual: {len(result_std):,} rows kept")
    print(f"  False positives: {false_pos}")
    print(f"  Critical addresses preserved: {'✓' if all_kept_std else '✗'}")
    print(f"  Status: {'✅ SUCCESS' if std_success else '❌ FAILURE'}")

    print(f"\nEnhanced Mode:")
    print(f"  Rows kept: {len(result_enh):,}")
    print(f"  Critical addresses preserved: {'✓' if all_kept_enh else '✗'}")
    print(f"  Status: {'✅ SUCCESS' if enh_success else '❌ FAILURE'}")

    if std_success and enh_success:
        print(f"\n{'=' * 100}")
        print("🎉 ALL TESTS PASSED - EXPLICIT LOOP LOGIC WORKING PERFECTLY!")
        print(f"{'=' * 100}")
        return True
    else:
        print(f"\n{'=' * 100}")
        print("❌ TESTS FAILED - THERE ARE STILL ISSUES")
        print(f"{'=' * 100}")
        return False

if __name__ == '__main__':
    success = test_rewritten_logic()
    sys.exit(0 if success else 1)
