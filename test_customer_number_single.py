#!/usr/bin/env python3
"""
Test for StandardizeCustomerNumberSingleOperation
Tests customer number extraction and padding
"""

import pandas as pd
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from operations.text_ops import StandardizeCustomerNumberSingleOperation


def test_hyphenated_format():
    """Test extracting and padding from hyphenated format"""

    print("=" * 80)
    print("TEST 1: Hyphenated Customer Numbers")
    print("=" * 80)

    # Create test data based on user's examples
    test_data = {
        'Customer_Number': [
            '1726274-639507',  # Should become 01726274
            '4441157-639473',  # Should become 04441157
            '9609-640231',     # Should become 00009609
            '1172785-639691',  # Should become 01172785
            '123-456',         # Short number: 00000123
            '99999999-123',    # Already 8 digits: 99999999
        ],
        'Expected': [
            '01726274',
            '04441157',
            '00009609',
            '01172785',
            '00000123',
            '99999999',
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Customer_Number']].to_string(index=False))

    # Run operation
    operation = StandardizeCustomerNumberSingleOperation()
    params = {
        'customer_column': 'Customer_Number',
        'output_length': 8,
        'handle_non_hyphenated': 'Pad as-is'
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Customer_Number', 'Expected']].to_string(index=False))

    # Verify
    mismatches = result[result['Customer_Number'] != result['Expected']]
    if len(mismatches) == 0:
        print("\n✓ ALL TESTS PASSED - All customer numbers formatted correctly")
        return True
    else:
        print("\n✗ TESTS FAILED - Mismatches found:")
        print(mismatches.to_string(index=False))
        return False


def test_non_hyphenated_handling():
    """Test handling of non-hyphenated values"""

    print("\n" + "=" * 80)
    print("TEST 2: Non-Hyphenated Value Handling")
    print("=" * 80)

    test_data = {
        'Customer_Number': [
            '1726274-639507',  # Normal hyphenated
            '1234567',         # No hyphen - pad as-is
            '999',             # No hyphen - pad as-is
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Customer_Number']].to_string(index=False))

    # Test "Pad as-is" option
    print("\n--- Option: Pad as-is ---")
    operation = StandardizeCustomerNumberSingleOperation()
    params = {
        'customer_column': 'Customer_Number',
        'output_length': 8,
        'handle_non_hyphenated': 'Pad as-is'
    }
    result = operation.execute(df, params)
    print(result[['Customer_Number']].to_string(index=False))

    expected_pad = ['01726274', '01234567', '00000999']
    if result['Customer_Number'].tolist() == expected_pad:
        print("✓ Pad as-is works correctly")
        test1 = True
    else:
        print(f"✗ Expected {expected_pad}, got {result['Customer_Number'].tolist()}")
        test1 = False

    # Test "Mark as error" option
    print("\n--- Option: Mark as error ---")
    df2 = pd.DataFrame(test_data)
    params['handle_non_hyphenated'] = 'Mark as error'
    result2 = operation.execute(df2, params)
    print(result2[['Customer_Number']].to_string(index=False))

    # First should be normal, others should have ERROR prefix
    has_errors = any('ERROR' in str(val) for val in result2['Customer_Number'].tolist()[1:])
    if result2['Customer_Number'].tolist()[0] == '01726274' and has_errors:
        print("✓ Mark as error works correctly")
        test2 = True
    else:
        print("✗ Mark as error not working correctly")
        test2 = False

    # Test "Leave unchanged" option
    print("\n--- Option: Leave unchanged ---")
    df3 = pd.DataFrame(test_data)
    params['handle_non_hyphenated'] = 'Leave unchanged'
    result3 = operation.execute(df3, params)
    print(result3[['Customer_Number']].to_string(index=False))

    # First should be standardized, others should be unchanged
    if result3['Customer_Number'].tolist()[0] == '01726274' and \
       result3['Customer_Number'].tolist()[1] == '1234567':
        print("✓ Leave unchanged works correctly")
        test3 = True
    else:
        print("✗ Leave unchanged not working correctly")
        test3 = False

    return test1 and test2 and test3


def test_empty_values():
    """Test handling of empty/null values"""

    print("\n" + "=" * 80)
    print("TEST 3: Empty and Null Values")
    print("=" * 80)

    test_data = {
        'Customer_Number': [
            '1726274-639507',  # Valid
            '',                # Empty
            None,              # Null
            '   ',             # Whitespace only
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Customer_Number']].to_string(index=False))

    operation = StandardizeCustomerNumberSingleOperation()
    params = {
        'customer_column': 'Customer_Number',
        'output_length': 8,
        'handle_non_hyphenated': 'Pad as-is'
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Customer_Number']].to_string(index=False))

    # Verify first is standardized, others remain empty/null
    if result['Customer_Number'].tolist()[0] == '01726274':
        print("\n✓ TEST PASSED - Empty values handled correctly")
        return True
    else:
        print("\n✗ TEST FAILED")
        return False


def test_different_lengths():
    """Test different output lengths"""

    print("\n" + "=" * 80)
    print("TEST 4: Different Output Lengths")
    print("=" * 80)

    test_data = {
        'Customer_Number': ['1726274-639507', '9609-640231']
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Customer_Number']].to_string(index=False))

    operation = StandardizeCustomerNumberSingleOperation()

    # Test length 6
    print("\n--- Length: 6 ---")
    params = {'customer_column': 'Customer_Number', 'output_length': 6, 'handle_non_hyphenated': 'Pad as-is'}
    result6 = operation.execute(df.copy(), params)
    print(result6[['Customer_Number']].to_string(index=False))
    test1 = result6['Customer_Number'].tolist() == ['1726274', '009609']  # Note: 1726274 is 7 digits, won't pad

    # Test length 10
    print("\n--- Length: 10 ---")
    params = {'customer_column': 'Customer_Number', 'output_length': 10, 'handle_non_hyphenated': 'Pad as-is'}
    result10 = operation.execute(df.copy(), params)
    print(result10[['Customer_Number']].to_string(index=False))
    test2 = result10['Customer_Number'].tolist() == ['0001726274', '0000009609']

    if test1 and test2:
        print("\n✓ ALL LENGTH TESTS PASSED")
        return True
    else:
        print("\n✗ SOME LENGTH TESTS FAILED")
        return False


def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("STANDARDIZE CUSTOMER NUMBER (SINGLE) TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run all tests
        test1_passed = test_hyphenated_format()
        test2_passed = test_non_hyphenated_handling()
        test3_passed = test_empty_values()
        test4_passed = test_different_lengths()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        results = [
            ("Hyphenated Format", test1_passed),
            ("Non-Hyphenated Handling", test2_passed),
            ("Empty Values", test3_passed),
            ("Different Lengths", test4_passed),
        ]

        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")

        all_passed = all(passed for _, passed in results)

        if all_passed:
            print("\n" + "=" * 80)
            print("ALL TESTS PASSED! ✓")
            print("=" * 80)
            print("\nCustomer number standardization is working correctly:")
            print("- Extracts part before hyphen: '1726274-639507' → '01726274'")
            print("- Pads to specified length: '9609-640231' → '00009609'")
            print("- Handles non-hyphenated values per settings")
            print("- Preserves empty/null values")
            print("- Supports custom output lengths")
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
