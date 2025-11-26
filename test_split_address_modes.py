#!/usr/bin/env python3
"""
Test for Split Address Operation with both modes
Tests both "Split Full Address" and "Extract Suite from Address 1" modes
"""

import sys
from pathlib import Path

# Add operations to path
sys.path.insert(0, str(Path(__file__).parent))

def test_split_address_operation():
    """Test SplitAddressOperation with both modes"""

    print("=" * 70)
    print("TEST: SplitAddressOperation - Both Modes")
    print("=" * 70)

    # Create test dataframe
    import pandas as pd

    # Test data simulating EVS_REORDERS.xlsx scenario
    test_data = {
        'Full Address': [
            '150 BERGEN ST STE 1',
            '4311 CARSWELL AVE',
            '2500 METROHEALTH DR STE C2001',
            '3715 NORTHSIDE PKWY NW BLDG 300 STE 110',
            '251 STENTON AVE'
        ],
        'Address 1': [
            '150 BERGEN ST STE 1',
            '4311 CARSWELL AVE',
            '2500 METROHEALTH DR STE C2001',
            '3715 NORTHSIDE PKWY NW BLDG 300 STE 110',
            '251 STENTON AVE'
        ],
        'Address 2': [
            'EVS',
            '',
            'Building B',
            '',
            ''
        ]
    }

    df = pd.DataFrame(test_data)

    print("\n" + "=" * 70)
    print("TEST 1: Split Full Address Mode")
    print("=" * 70)

    print("\nINITIAL DATA (Full Address column):")
    print("-" * 70)
    print(df[['Full Address']].to_string())

    # Import operation
    from operations.zoominfo_ops import SplitAddressOperation

    operation = SplitAddressOperation()
    params1 = {
        'mode': 'Split Full Address',
        'source_column': 'Full Address',
        'suite_keywords': 'Ste,Suite,Suites,Unit,Units,Apt,Apartment,Bldg,Building,Floor,Flr,#,Room,Rm',
        'address1_output': 'New Address 1',
        'address2_output': 'New Address 2',
        'remove_original': False
    }

    result_df1 = operation.execute(df.copy(), params1)

    print("\nRESULT (Mode 1 - Split Full Address):")
    print("-" * 70)
    print(result_df1[['Full Address', 'New Address 1', 'New Address 2']].to_string())

    # Verify
    assert result_df1.at[0, 'New Address 1'] == '150 BERGEN ST', "Row 0 Address 1 incorrect"
    assert result_df1.at[0, 'New Address 2'] == 'STE 1', "Row 0 Address 2 incorrect"
    assert result_df1.at[1, 'New Address 1'] == '4311 CARSWELL AVE', "Row 1 Address 1 incorrect"
    assert result_df1.at[1, 'New Address 2'] == '', "Row 1 Address 2 should be empty"
    assert result_df1.at[2, 'New Address 1'] == '2500 METROHEALTH DR', "Row 2 Address 1 incorrect"
    assert result_df1.at[2, 'New Address 2'] == 'STE C2001', "Row 2 Address 2 incorrect"

    # Check LAST occurrence (should split at last Ste, not Bldg)
    assert result_df1.at[3, 'New Address 1'] == '3715 NORTHSIDE PKWY NW BLDG 300', "Row 3 should split at LAST suite keyword"
    assert result_df1.at[3, 'New Address 2'] == 'STE 110', "Row 3 Address 2 incorrect"

    print("\n✓ TEST 1 PASSED - Split Full Address works correctly")
    print("  - Correctly splits at LAST occurrence of suite keyword")
    print("  - Handles addresses without suite info")
    print("  - Creates new columns as expected")

    print("\n" + "=" * 70)
    print("TEST 2: Extract Suite from Address 1 Mode")
    print("=" * 70)

    print("\nINITIAL DATA (Address 1 and Address 2 columns):")
    print("-" * 70)
    print(df[['Address 1', 'Address 2']].to_string())

    params2 = {
        'mode': 'Extract Suite from Address 1',
        'source_column': 'Address 1',
        'address2_column': 'Address 2',
        'suite_keywords': 'Ste,Suite,Suites,Unit,Units,Apt,Apartment,Bldg,Building,Floor,Flr,#,Room,Rm'
    }

    result_df2 = operation.execute(df.copy(), params2)

    print("\nRESULT (Mode 2 - Extract Suite from Address 1):")
    print("-" * 70)
    print(result_df2[['Address 1', 'Address 2']].to_string())

    # Verify
    assert result_df2.at[0, 'Address 1'] == '150 BERGEN ST', "Row 0 Address 1 should have suite removed"
    assert result_df2.at[0, 'Address 2'] == 'STE 1', "Row 0 Address 2 should have extracted suite"

    assert result_df2.at[1, 'Address 1'] == '4311 CARSWELL AVE', "Row 1 should remain unchanged"
    assert result_df2.at[1, 'Address 2'] == '', "Row 1 Address 2 should remain empty"

    assert result_df2.at[2, 'Address 1'] == '2500 METROHEALTH DR', "Row 2 Address 1 should have suite removed"
    assert result_df2.at[2, 'Address 2'] == 'STE C2001', "Row 2 Address 2 should have extracted suite"

    # Check LAST occurrence
    assert result_df2.at[3, 'Address 1'] == '3715 NORTHSIDE PKWY NW BLDG 300', "Row 3 should extract LAST suite keyword"
    assert result_df2.at[3, 'Address 2'] == 'STE 110', "Row 3 Address 2 should have extracted suite"

    print("\n✓ TEST 2 PASSED - Extract Suite from Address 1 works correctly")
    print("  - Correctly extracts suite from Address 1")
    print("  - Moves suite to Address 2 (overwrites existing)")
    print("  - Handles addresses without suite info")
    print("  - Splits at LAST occurrence of suite keyword")

    print("\n" + "=" * 70)
    print("TEST 3: Error Handling - Missing Address 2 Column")
    print("=" * 70)

    params3 = {
        'mode': 'Extract Suite from Address 1',
        'source_column': 'Address 1',
        # Missing address2_column parameter
        'suite_keywords': 'Ste,Suite,Suites,Unit,Units,Apt,Apartment,Bldg,Building,Floor,Flr'
    }

    try:
        result_df3 = operation.execute(df.copy(), params3)
        print("\n❌ TEST 3 FAILED: Should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✓ TEST 3 PASSED: Correctly raised ValueError")
        print(f"  Error message: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
    print("\nSplitAddressOperation is working correctly:")
    print("✓ Mode 1: Split Full Address into NEW columns")
    print("✓ Mode 2: Extract Suite from Address 1 → move to Address 2")
    print("✓ Uses LAST occurrence of suite keyword (correct behavior)")
    print("✓ Handles addresses without suite info")
    print("✓ Proper error handling for missing parameters")
    print("\nReady for use with EVS_REORDERS.xlsx!")

    return True

if __name__ == "__main__":
    try:
        test_split_address_operation()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
