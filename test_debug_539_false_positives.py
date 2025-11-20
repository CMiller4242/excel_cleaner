"""
Comprehensive test to debug the 539 false positives issue

This test will:
1. Test both standard and enhanced modes
2. Show exactly what each mode does
3. Identify if enhanced mode has a bug
4. Provide the definitive fix
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation

def test_both_modes_debug():
    """Debug test for both standard and enhanced modes"""

    print("=" * 100)
    print("DEBUGGING: Remove Rows If - 539 False Positives Issue")
    print("=" * 100)

    # Load the actual file
    filename = 'Volunteer Directors 11.20.25.xlsx'
    print(f"\n[1] Loading file: {filename}")
    df = pd.read_excel(filename)
    print(f"    Total rows: {len(df):,}")
    print(f"    Actual NaN in 'Person Street': {df['Person Street'].isna().sum():,}")
    print(f"    Non-NaN in 'Person Street': {df['Person Street'].notna().sum():,}")

    operation = RemoveRowsIfOperation()

    # TEST 1: Standard Mode (enhanced_blank_detection = False)
    print(f"\n{'=' * 100}")
    print("[2] TESTING STANDARD MODE (enhanced_blank_detection = False)")
    print(f"{'=' * 100}")

    params_standard = {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': False
    }

    print(f"\nExecuting operation with standard mode...")
    result_std = operation.execute(df, params_standard)

    removed_std_indices = set(df.index) - set(result_std.index)
    removed_std = df.loc[list(removed_std_indices)]

    print(f"\nResults:")
    print(f"  Input: {len(df):,} rows")
    print(f"  Results (kept): {len(result_std):,} rows")
    print(f"  Removed: {len(removed_std):,} rows")

    # Check for false positives
    false_pos_std = removed_std['Person Street'].notna().sum()
    print(f"\n  Non-NaN values in Removed: {false_pos_std:,}")

    if false_pos_std > 0:
        print(f"\n  ✗ BUG IN STANDARD MODE: {false_pos_std} non-NaN values removed!")
        print(f"  Examples:")
        for val in removed_std[removed_std['Person Street'].notna()]['Person Street'].head(10):
            print(f"    - {repr(val)}")
    else:
        print(f"  ✓ Standard mode works correctly - only NaN values removed")

    # TEST 2: Enhanced Mode (enhanced_blank_detection = True)
    print(f"\n{'=' * 100}")
    print("[3] TESTING ENHANCED MODE (enhanced_blank_detection = True)")
    print(f"{'=' * 100}")

    params_enhanced = {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': True
    }

    print(f"\nExecuting operation with enhanced mode...")
    result_enh = operation.execute(df, params_enhanced)

    removed_enh_indices = set(df.index) - set(result_enh.index)
    removed_enh = df.loc[list(removed_enh_indices)]

    print(f"\nResults:")
    print(f"  Input: {len(df):,} rows")
    print(f"  Results (kept): {len(result_enh):,} rows")
    print(f"  Removed: {len(removed_enh):,} rows")

    # Analyze what was removed
    print(f"\n  Removed breakdown:")
    print(f"    Actual NaN: {removed_enh['Person Street'].isna().sum():,}")
    print(f"    Non-NaN: {removed_enh['Person Street'].notna().sum():,}")

    # Check the non-NaN values that were removed
    non_nan_removed = removed_enh[removed_enh['Person Street'].notna()]
    if len(non_nan_removed) > 0:
        print(f"\n  Non-NaN values removed by enhanced mode:")

        # Categorize them
        empty_strings = 0
        whitespace = 0
        na_variants = 0
        valid_addresses = 0

        for val in non_nan_removed['Person Street']:
            if isinstance(val, str):
                stripped = val.strip()
                if stripped == "":
                    if val == "":
                        empty_strings += 1
                    else:
                        whitespace += 1
                elif stripped.lower() in ['n/a', 'na', 'null', 'none']:
                    na_variants += 1
                else:
                    valid_addresses += 1
                    if valid_addresses <= 10:
                        print(f"    ✗ VALID ADDRESS REMOVED: {repr(val)}")

        print(f"\n  Categorization:")
        print(f"    Empty strings (''): {empty_strings}")
        print(f"    Whitespace only: {whitespace}")
        print(f"    N/A variants: {na_variants}")
        print(f"    VALID ADDRESSES (BUG!): {valid_addresses}")

        if valid_addresses > 0:
            print(f"\n  ✗ BUG IN ENHANCED MODE: {valid_addresses} valid addresses removed!")
        else:
            print(f"\n  ✓ Enhanced mode working as designed (only blanks/N/A removed)")

    # TEST 3: Check specific problematic addresses
    print(f"\n{'=' * 100}")
    print("[4] CHECKING SPECIFIC PROBLEM ADDRESSES")
    print(f"{'=' * 100}")

    problem_addresses = [
        "6600 N Lincoln Ave Ste 300",
        "2150 Post St",
        "4205 NW 6th St",
        "4205 NW 8th St",
        "1718 Patterson St",
        "36 S State St",
        "365 State St"
    ]

    print(f"\nChecking if problem addresses exist in original file:")
    for addr in problem_addresses:
        exists = (df['Person Street'] == addr).any()
        if exists:
            in_std_results = (result_std['Person Street'] == addr).any()
            in_enh_results = (result_enh['Person Street'] == addr).any()

            std_status = '✓ KEPT' if in_std_results else '✗ REMOVED'
            enh_status = '✓ KEPT' if in_enh_results else '✗ REMOVED'

            print(f"\n  {addr:<35}")
            print(f"    Standard mode: {std_status}")
            print(f"    Enhanced mode: {enh_status}")

            if not in_enh_results:
                # This address was removed by enhanced mode - let's see why
                val = df[df['Person Street'] == addr]['Person Street'].iloc[0]
                print(f"    Value: {repr(val)}")
                print(f"    Type: {type(val)}")
                print(f"    Is NaN: {pd.isna(val)}")
                if isinstance(val, str):
                    print(f"    Stripped: {repr(val.strip())}")
                    print(f"    Lower: {repr(val.strip().lower())}")
                    print(f"    In blank list: {val.strip().lower() in ['', 'n/a', 'na', 'null', 'none']}")
        else:
            print(f"  {addr:<35} - NOT FOUND in file")

    # TEST 4: Manual check of _is_blank_enhanced logic
    print(f"\n{'=' * 100}")
    print("[5] MANUAL TEST OF _is_blank_enhanced LOGIC")
    print(f"{'=' * 100}")

    test_values = [
        ("6600 N Lincoln Ave Ste 300", False),
        ("2150 Post St", False),
        ("", True),
        ("   ", True),
        ("N/A", True),
        ("n/a", True),
        ("null", True),
        (np.nan, True),
        (None, True),
        ("Valid Address 123", False)
    ]

    print(f"\nTesting _is_blank_enhanced directly:")
    for val, expected in test_values:
        result = operation._is_blank_enhanced(val)
        status = '✓' if result == expected else '✗ BUG'
        print(f"  {status} {repr(val):<35} -> {result} (expected {expected})")

    # FINAL DIAGNOSIS
    print(f"\n{'=' * 100}")
    print("FINAL DIAGNOSIS")
    print(f"{'=' * 100}")

    std_false_pos = removed_std['Person Street'].notna().sum()
    enh_false_pos = len([v for v in removed_enh[removed_enh['Person Street'].notna()]['Person Street']
                         if isinstance(v, str) and v.strip() != '' and v.strip().lower() not in ['n/a', 'na', 'null', 'none']])

    print(f"\nStandard Mode:")
    print(f"  False positives (non-NaN removed): {std_false_pos}")
    print(f"  Status: {'✗ BROKEN' if std_false_pos > 0 else '✓ WORKING'}")

    print(f"\nEnhanced Mode:")
    print(f"  Valid addresses removed: {enh_false_pos}")
    print(f"  Status: {'✗ BROKEN' if enh_false_pos > 0 else '✓ WORKING (removes empty/N/A as designed)'}")

    print(f"\n{'=' * 100}")
    if std_false_pos == 0 and enh_false_pos == 0:
        print("✓ BOTH MODES WORKING CORRECTLY")
        print("\nIf user is seeing 539 false positives, possible causes:")
        print("  1. Enhanced mode checkbox is checked (should be unchecked)")
        print("  2. Using old cached code (need to reload)")
        print("  3. Different version of the file")
    elif std_false_pos > 0:
        print("✗ STANDARD MODE IS BROKEN - This is critical!")
    elif enh_false_pos > 0:
        print("✗ ENHANCED MODE IS BROKEN - Should not remove valid addresses!")
        print(f"\nThe bug is in _is_blank_enhanced method")
    print(f"{'=' * 100}")

if __name__ == '__main__':
    test_both_modes_debug()
