#!/usr/bin/env python3
"""
Test for StandardizePhoneNumbersOperation
Tests various input formats and output options
"""

import pandas as pd
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from operations.text_ops import StandardizePhoneNumbersOperation


def test_digits_only_format():
    """Test converting various formats to digits only"""

    print("=" * 80)
    print("TEST 1: Digits Only Format")
    print("=" * 80)

    # Create test data with various formats
    test_data = {
        'Phone': [
            '386.917.5481',  # Periods
            '941-766-4125',  # Dashes
            '(256) 429-4000',  # Parentheses + dashes
            '256 429 4000',  # Spaces
            '2564294000',  # Already clean
            '+1 (256) 429-4000',  # Country code with parentheses
            '1-256-429-4000',  # Country code with dashes
            '(256) 429.4000',  # Mixed
            '',  # Empty
        ],
        'Expected': [
            '3869175481',
            '9417664125',
            '2564294000',
            '2564294000',
            '2564294000',
            '2564294000',
            '2564294000',
            '2564294000',
            '',
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Phone']].to_string(index=False))

    # Run operation
    operation = StandardizePhoneNumbersOperation()
    params = {
        'phone_column': 'Phone',
        'output_format': 'Digits Only (2564294000)',
        'handle_extensions': False,
        'remove_country_code': True,
        'validate_length': False
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Phone', 'Expected']].to_string(index=False))

    # Verify
    mismatches = result[result['Phone'] != result['Expected']]
    if len(mismatches) == 0:
        print("\n✓ ALL TESTS PASSED - All phones formatted correctly")
        return True
    else:
        print("\n✗ TESTS FAILED - Mismatches found:")
        print(mismatches.to_string(index=False))
        return False


def test_us_format():
    """Test converting to US format (256) 429-4000"""

    print("\n" + "=" * 80)
    print("TEST 2: US Format (256) 429-4000")
    print("=" * 80)

    test_data = {
        'Phone': [
            '2564294000',
            '386.917.5481',
            '941-766-4125',
        ],
        'Expected': [
            '(256) 429-4000',
            '(386) 917-5481',
            '(941) 766-4125',
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Phone']].to_string(index=False))

    operation = StandardizePhoneNumbersOperation()
    params = {
        'phone_column': 'Phone',
        'output_format': 'US Format (256) 429-4000',
        'handle_extensions': False,
        'remove_country_code': True,
        'validate_length': False
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Phone', 'Expected']].to_string(index=False))

    # Verify
    mismatches = result[result['Phone'] != result['Expected']]
    if len(mismatches) == 0:
        print("\n✓ ALL TESTS PASSED - All phones formatted correctly")
        return True
    else:
        print("\n✗ TESTS FAILED - Mismatches found:")
        print(mismatches.to_string(index=False))
        return False


def test_extensions():
    """Test handling extensions"""

    print("\n" + "=" * 80)
    print("TEST 3: Extensions Handling")
    print("=" * 80)

    test_data = {
        'Phone': [
            '256-429-4000 x123',
            '(256) 429-4000 ext 456',
            '256.429.4000 extension 789',
            '2564294000x999',
        ],
        'Expected': [
            '2564294000 x123',
            '2564294000 x456',
            '2564294000 x789',
            '2564294000 x999',
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Phone']].to_string(index=False))

    operation = StandardizePhoneNumbersOperation()
    params = {
        'phone_column': 'Phone',
        'output_format': 'Digits Only (2564294000)',
        'handle_extensions': True,  # Enable extension handling
        'remove_country_code': True,
        'validate_length': False
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Phone', 'Expected']].to_string(index=False))

    # Verify
    mismatches = result[result['Phone'] != result['Expected']]
    if len(mismatches) == 0:
        print("\n✓ ALL TESTS PASSED - Extensions preserved correctly")
        return True
    else:
        print("\n✗ TESTS FAILED - Mismatches found:")
        print(mismatches.to_string(index=False))
        return False


def test_validation():
    """Test phone number validation"""

    print("\n" + "=" * 80)
    print("TEST 4: Phone Number Validation")
    print("=" * 80)

    test_data = {
        'Phone': [
            '2564294000',  # Valid
            '256429',  # Too short
            '12564294000999',  # Too long
            '',  # Empty
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nINPUT:")
    print(df[['Phone']].to_string(index=False))

    operation = StandardizePhoneNumbersOperation()
    params = {
        'phone_column': 'Phone',
        'output_format': 'Digits Only (2564294000)',
        'handle_extensions': False,
        'remove_country_code': True,
        'validate_length': True  # Enable validation
    }

    result = operation.execute(df, params)

    print("\nRESULT:")
    print(result[['Phone', '_Phone_Valid']].to_string(index=False))

    # Verify
    expected_valid = [True, False, False, False]
    actual_valid = result['_Phone_Valid'].tolist()

    if actual_valid == expected_valid:
        print("\n✓ ALL TESTS PASSED - Validation correct")
        return True
    else:
        print(f"\n✗ TESTS FAILED - Expected {expected_valid}, got {actual_valid}")
        return False


def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("STANDARDIZE PHONE NUMBERS TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run all tests
        test1_passed = test_digits_only_format()
        test2_passed = test_us_format()
        test3_passed = test_extensions()
        test4_passed = test_validation()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        results = [
            ("Digits Only Format", test1_passed),
            ("US Format", test2_passed),
            ("Extensions Handling", test3_passed),
            ("Validation", test4_passed),
        ]

        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")

        all_passed = all(passed for _, passed in results)

        if all_passed:
            print("\n" + "=" * 80)
            print("ALL TESTS PASSED! ✓")
            print("=" * 80)
            print("\nPhone standardization is working correctly:")
            print("- Periods: 386.917.5481 → 3869175481")
            print("- Dashes: 941-766-4125 → 9417664125")
            print("- Parentheses: (256) 429-4000 → 2564294000")
            print("- Spaces: 256 429 4000 → 2564294000")
            print("- Country codes: +1 (256) 429-4000 → 2564294000")
            print("- Extensions: 256-429-4000 x123 → 2564294000 x123")
            print("- Multiple formats supported")
            print("- Validation works correctly")
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
