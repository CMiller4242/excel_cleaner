#!/usr/bin/env python3
"""
Test for CleanMailingCustomerDataOperation
Tests customer number extraction, segment padding, and dual-column processing
"""

import pandas as pd
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from operations.text_ops import CleanMailingCustomerDataOperation


def test_customer_numbers_only():
    """Test processing customer numbers without segment column"""

    print("=" * 80)
    print("TEST 1: Customer Numbers Only (No Segment Column)")
    print("=" * 80)

    # Create test data
    test_data = {
        'Customer_Number': [
            '1726274-639507',
            '4441157-639473',
            '9609-640231',
            '1172785-639691',
        ],
        'Expected': [
            '01726274',
            '04441157',
            '00009609',
            '01172785',
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Customer_Number']].to_string(index=False))

    # Run operation (customer only)
    operation = CleanMailingCustomerDataOperation()
    params = {
        'customer_column': 'Customer_Number',
        'customer_length': 8,
        'handle_non_hyphenated': 'Pad as-is'
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Customer_Number', 'Expected']].to_string(index=False))

    # Verify
    mismatches = result[result['Customer_Number'] != result['Expected']]
    if len(mismatches) == 0:
        print("\n✓ TEST PASSED - Customer numbers formatted correctly")
        return True
    else:
        print("\n✗ TEST FAILED - Mismatches found:")
        print(mismatches.to_string(index=False))
        return False


def test_segment_numbers_only():
    """Test processing segment numbers independently"""

    print("\n" + "=" * 80)
    print("TEST 2: Segment Numbers Padding")
    print("=" * 80)

    test_data = {
        'Segment': ['0', '1', '5', '31', '99'],
        'Expected': ['00', '01', '05', '31', '99']
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Segment']].to_string(index=False))

    # Run operation (segment only, using a dummy customer column)
    df['Customer_Dummy'] = '1234567-999999'
    operation = CleanMailingCustomerDataOperation()
    params = {
        'customer_column': 'Customer_Dummy',
        'segment_column': 'Segment',
        'segment_length': 2,
        'blank_segments_to_zero': False
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Segment', 'Expected']].to_string(index=False))

    # Verify
    mismatches = result[result['Segment'] != result['Expected']]
    if len(mismatches) == 0:
        print("\n✓ TEST PASSED - Segment numbers padded correctly")
        return True
    else:
        print("\n✗ TEST FAILED - Mismatches found:")
        print(mismatches.to_string(index=False))
        return False


def test_dual_column_processing():
    """Test processing both customer and segment columns together"""

    print("\n" + "=" * 80)
    print("TEST 3: Dual Column Processing (Customer + Segment)")
    print("=" * 80)

    # Create test data matching real mailing list format
    test_data = {
        'Customer_Number': [
            '1726274-639507',
            '4441157-639473',
            '9609-640231',
            '1172785-639691',
        ],
        'Segment': ['0', '1', '31', '5'],
        'Expected_Customer': ['01726274', '04441157', '00009609', '01172785'],
        'Expected_Segment': ['00', '01', '31', '05']
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Customer_Number', 'Segment']].to_string(index=False))

    # Run operation (both columns)
    operation = CleanMailingCustomerDataOperation()
    params = {
        'customer_column': 'Customer_Number',
        'customer_length': 8,
        'segment_column': 'Segment',
        'segment_length': 2,
        'handle_non_hyphenated': 'Pad as-is',
        'blank_segments_to_zero': False
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Customer_Number', 'Segment', 'Expected_Customer', 'Expected_Segment']].to_string(index=False))

    # Verify both columns
    customer_match = (result['Customer_Number'] == result['Expected_Customer']).all()
    segment_match = (result['Segment'] == result['Expected_Segment']).all()

    if customer_match and segment_match:
        print("\n✓ TEST PASSED - Both columns formatted correctly")
        return True
    else:
        print("\n✗ TEST FAILED")
        if not customer_match:
            print("Customer mismatches:")
            print(result[result['Customer_Number'] != result['Expected_Customer']])
        if not segment_match:
            print("Segment mismatches:")
            print(result[result['Segment'] != result['Expected_Segment']])
        return False


def test_blank_segment_handling():
    """Test handling of blank segment values"""

    print("\n" + "=" * 80)
    print("TEST 4: Blank Segment Handling")
    print("=" * 80)

    test_data = {
        'Customer_Number': ['1726274-639507', '4441157-639473', '9609-640231'],
        'Segment': ['1', '', None]  # Mix of value, blank, and null
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Customer_Number', 'Segment']].to_string(index=False))

    # Test 1: Keep blanks as blank (default)
    print("\n--- Option: Keep Blanks ---")
    operation = CleanMailingCustomerDataOperation()
    params = {
        'customer_column': 'Customer_Number',
        'segment_column': 'Segment',
        'segment_length': 2,
        'blank_segments_to_zero': False
    }

    result1 = operation.execute(df.copy(), params)
    print(result1[['Customer_Number', 'Segment']].to_string(index=False))

    # Verify: first should be '01', others should be blank
    test1_pass = (result1['Segment'].iloc[0] == '01' and
                  result1['Segment'].iloc[1] == '' and
                  (pd.isna(result1['Segment'].iloc[2]) or result1['Segment'].iloc[2] == ''))

    if test1_pass:
        print("✓ Keep blanks works correctly")
    else:
        print(f"✗ Keep blanks failed: {result1['Segment'].tolist()}")

    # Test 2: Convert blanks to "00"
    print("\n--- Option: Convert Blanks to '00' ---")
    params['blank_segments_to_zero'] = True

    result2 = operation.execute(df.copy(), params)
    print(result2[['Customer_Number', 'Segment']].to_string(index=False))

    # Verify: first should be '01', others should be '00'
    test2_pass = (result2['Segment'].iloc[0] == '01' and
                  result2['Segment'].iloc[1] == '00' and
                  result2['Segment'].iloc[2] == '00')

    if test2_pass:
        print("✓ Convert blanks to '00' works correctly")
    else:
        print(f"✗ Convert blanks to '00' failed: {result2['Segment'].tolist()}")

    return test1_pass and test2_pass


def test_real_world_scenario():
    """Test with realistic mailing list data"""

    print("\n" + "=" * 80)
    print("TEST 5: Real World Mailing List Scenario")
    print("=" * 80)

    # Simulate real mailing list data
    test_data = {
        'First_Name': ['John', 'Jane', 'Bob', 'Alice'],
        'Last_Name': ['Smith', 'Doe', 'Johnson', 'Williams'],
        'Customer_Number': [
            '1726274-639507',
            '4441157-639473',
            '9609-640231',
            '1172785-639691'
        ],
        'Segment': ['0', '1', '0', '31'],
        'Email': [
            'john@example.com',
            'jane@example.com',
            'bob@example.com',
            'alice@example.com'
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT DATA (Mailing List Export):")
    print(df.to_string(index=False))

    # Apply operation
    operation = CleanMailingCustomerDataOperation()
    params = {
        'customer_column': 'Customer_Number',
        'customer_length': 8,
        'segment_column': 'Segment',
        'segment_length': 2,
        'handle_non_hyphenated': 'Pad as-is',
        'blank_segments_to_zero': False
    }

    result = operation.execute(df, params)

    print("\nRESULT DATA (Cleaned for Mailing):")
    print(result.to_string(index=False))

    # Verify customer numbers
    expected_customers = ['01726274', '04441157', '00009609', '01172785']
    expected_segments = ['00', '01', '00', '31']

    customer_correct = result['Customer_Number'].tolist() == expected_customers
    segment_correct = result['Segment'].tolist() == expected_segments

    if customer_correct and segment_correct:
        print("\n✓ TEST PASSED - Real world scenario works correctly")
        print(f"  Customer Numbers: {result['Customer_Number'].tolist()}")
        print(f"  Segment Numbers:  {result['Segment'].tolist()}")
        return True
    else:
        print("\n✗ TEST FAILED")
        print(f"  Expected Customers: {expected_customers}")
        print(f"  Got Customers:      {result['Customer_Number'].tolist()}")
        print(f"  Expected Segments:  {expected_segments}")
        print(f"  Got Segments:       {result['Segment'].tolist()}")
        return False


def test_non_hyphenated_handling():
    """Test handling of non-hyphenated customer numbers"""

    print("\n" + "=" * 80)
    print("TEST 6: Non-Hyphenated Customer Number Handling")
    print("=" * 80)

    test_data = {
        'Customer_Number': [
            '1726274-639507',  # Normal
            '1234567',         # No hyphen
            '999'              # Short, no hyphen
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Customer_Number']].to_string(index=False))

    operation = CleanMailingCustomerDataOperation()

    # Test "Pad as-is"
    print("\n--- Option: Pad as-is ---")
    params = {
        'customer_column': 'Customer_Number',
        'customer_length': 8,
        'handle_non_hyphenated': 'Pad as-is'
    }
    result1 = operation.execute(df.copy(), params)
    print(result1[['Customer_Number']].to_string(index=False))

    test1 = result1['Customer_Number'].tolist() == ['01726274', '01234567', '00000999']
    print(f"{'✓' if test1 else '✗'} Pad as-is: {result1['Customer_Number'].tolist()}")

    # Test "Mark as error"
    print("\n--- Option: Mark as error ---")
    params['handle_non_hyphenated'] = 'Mark as error'
    result2 = operation.execute(df.copy(), params)
    print(result2[['Customer_Number']].to_string(index=False))

    test2 = (result2['Customer_Number'].iloc[0] == '01726274' and
             'ERROR' in result2['Customer_Number'].iloc[1] and
             'ERROR' in result2['Customer_Number'].iloc[2])
    print(f"{'✓' if test2 else '✗'} Mark as error works correctly")

    # Test "Leave unchanged"
    print("\n--- Option: Leave unchanged ---")
    params['handle_non_hyphenated'] = 'Leave unchanged'
    result3 = operation.execute(df.copy(), params)
    print(result3[['Customer_Number']].to_string(index=False))

    test3 = result3['Customer_Number'].tolist() == ['01726274', '1234567', '999']
    print(f"{'✓' if test3 else '✗'} Leave unchanged: {result3['Customer_Number'].tolist()}")

    return test1 and test2 and test3


def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("CLEAN MAILING LIST CUSTOMER DATA - TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run all tests
        test1_passed = test_customer_numbers_only()
        test2_passed = test_segment_numbers_only()
        test3_passed = test_dual_column_processing()
        test4_passed = test_blank_segment_handling()
        test5_passed = test_real_world_scenario()
        test6_passed = test_non_hyphenated_handling()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        results = [
            ("Customer Numbers Only", test1_passed),
            ("Segment Numbers Padding", test2_passed),
            ("Dual Column Processing", test3_passed),
            ("Blank Segment Handling", test4_passed),
            ("Real World Scenario", test5_passed),
            ("Non-Hyphenated Handling", test6_passed),
        ]

        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")

        all_passed = all(passed for _, passed in results)

        if all_passed:
            print("\n" + "=" * 80)
            print("ALL TESTS PASSED! ✓")
            print("=" * 80)
            print("\nOperation ready for production:")
            print("- Customer: '1726274-639507' → '01726274' (8 digits)")
            print("- Segment: '0' → '00' (2 digits)")
            print("- Handles both columns independently or together")
            print("- Configurable blank handling")
            print("- Configurable non-hyphenated handling")
            return 0
        else:
            print("\n" + "=" * 80)
            print("SOME TESTS FAILED ✗")
            print("=" * 80)
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
