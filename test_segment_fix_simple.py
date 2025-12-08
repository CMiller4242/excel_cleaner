"""
Direct test of the segment padding fix without full module imports.
"""
import pandas as pd
import re

class TestCleanMailingOperation:
    """Extracted methods for testing"""

    def _standardize_segment(self, value, length, blank_to_zero):
        """
        FIXED VERSION - copied from text_ops.py
        """
        # Handle None, NaN, or empty string
        if pd.isna(value) or value == '':
            if blank_to_zero:
                return '0' * length
            else:
                return ""

        # CRITICAL FIX: Convert numeric types to int BEFORE string conversion
        if isinstance(value, (int, float)):
            try:
                value_str = str(int(value))
            except (ValueError, OverflowError):
                value_str = str(value).strip()
        else:
            value_str = str(value).strip()

        # Remove any non-digit characters
        digits = re.sub(r'\D', '', value_str)

        if not digits:
            if blank_to_zero:
                return '0' * length
            else:
                return ""

        padded = digits.zfill(length)
        return padded

    def _standardize_customer(self, value, length, handle_non_hyphenated):
        """
        FIXED VERSION - copied from text_ops.py
        """
        if pd.isna(value) or not value:
            return ""

        # CRITICAL FIX: Convert numeric types to int BEFORE string conversion
        if isinstance(value, (int, float)):
            try:
                value_str = str(int(value))
            except (ValueError, OverflowError):
                value_str = str(value).strip()
        else:
            value_str = str(value).strip()

        # Check if hyphen exists
        if '-' in value_str:
            before_hyphen = value_str.split('-')[0].strip()
        else:
            if handle_non_hyphenated == 'Mark as error':
                return f"ERROR: {value_str}"
            elif handle_non_hyphenated == 'Leave unchanged':
                return value_str
            else:  # 'Pad as-is'
                before_hyphen = value_str

        digits = re.sub(r'\D', '', before_hyphen)

        if not digits:
            return '0' * length

        padded = digits.zfill(length)
        return padded


def main():
    print("=" * 70)
    print("SEGMENT PADDING BUG FIX TEST")
    print("=" * 70)

    op = TestCleanMailingOperation()

    # Test cases that exposed the bug
    test_cases = [
        # (value, expected, description)
        (0, "00", "Segment 0 (int)"),
        (0.0, "00", "Segment 0.0 (float)"),
        (2, "02", "Segment 2 (int)"),
        (2.0, "02", "Segment 2.0 (float) - BUG was '20'"),
        (10, "10", "Segment 10 (int)"),
        (10.0, "10", "Segment 10.0 (float) - BUG was '100'"),
        (31, "31", "Segment 31 (int)"),
        (31.0, "31", "Segment 31.0 (float)"),
        ("10", "10", "Segment '10' (string)"),
        ("2", "02", "Segment '2' (string)"),
        (None, "", "Segment None (blank)"),
        ("", "", "Segment '' (empty)"),
    ]

    print("\nTesting _standardize_segment:")
    print("-" * 70)

    all_pass = True
    for value, expected, description in test_cases:
        result = op._standardize_segment(value, length=2, blank_to_zero=False)
        match = result == expected
        status = "✓" if match else "✗"

        if not match:
            all_pass = False
            print(f"{status} {description:40} → '{result}' (expected '{expected}') FAIL")
        else:
            print(f"{status} {description:40} → '{result}'")

    # Test customer standardization
    print("\n" + "=" * 70)
    print("Testing _standardize_customer:")
    print("-" * 70)

    cust_test_cases = [
        ("2098687-662541", "02098687", "Hyphenated customer"),
        ("620729-663907", "00620729", "Hyphenated customer"),
        ("9609-640231", "00009609", "Hyphenated customer"),
        ("5164", "00005164", "Non-hyphenated string"),
        (5164, "00005164", "Non-hyphenated int"),
        (5164.0, "00005164", "Non-hyphenated float - BUG was '000051640'"),
    ]

    for value, expected, description in cust_test_cases:
        result = op._standardize_customer(value, length=8, handle_non_hyphenated='Pad as-is')
        match = result == expected
        status = "✓" if match else "✗"

        if not match:
            all_pass = False
            print(f"{status} {description:40} → '{result}' (expected '{expected}') FAIL")
        else:
            print(f"{status} {description:40} → '{result}'")

    # Test with blank_to_zero option
    print("\n" + "=" * 70)
    print("Testing blank_segments_to_zero option:")
    print("-" * 70)

    blank_tests = [
        (None, False, "", "None with blank_to_zero=False"),
        (None, True, "00", "None with blank_to_zero=True"),
        ("", False, "", "Empty with blank_to_zero=False"),
        ("", True, "00", "Empty with blank_to_zero=True"),
    ]

    for value, blank_to_zero, expected, description in blank_tests:
        result = op._standardize_segment(value, length=2, blank_to_zero=blank_to_zero)
        match = result == expected
        status = "✓" if match else "✗"

        if not match:
            all_pass = False
            print(f"{status} {description:45} → '{result}' (expected '{expected}') FAIL")
        else:
            print(f"{status} {description:45} → '{result}'")

    # Test idempotency
    print("\n" + "=" * 70)
    print("Testing idempotency (running twice):")
    print("-" * 70)

    idempotent_tests = [
        (10.0, "Segment 10.0"),
        (2.0, "Segment 2.0"),
        ("10", "Segment '10'"),
    ]

    for value, description in idempotent_tests:
        result1 = op._standardize_segment(value, length=2, blank_to_zero=False)
        # Run again on the result (it's now a string)
        result2 = op._standardize_segment(result1, length=2, blank_to_zero=False)
        match = result1 == result2
        status = "✓" if match else "✗"

        if not match:
            all_pass = False
            print(f"{status} {description:40} '{result1}' → '{result2}' FAIL (not idempotent)")
        else:
            print(f"{status} {description:40} '{result1}' → '{result2}' (stable)")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if all_pass:
        print("✓✓✓ ALL TESTS PASSED - BUG IS FIXED! ✓✓✓")
        print("\nThe fix correctly handles:")
        print("  • Float values like 10.0 → '10' (not '100')")
        print("  • Float values like 2.0 → '02' (not '20')")
        print("  • Integer and string values work correctly")
        print("  • Blank handling respects the blank_to_zero parameter")
        print("  • Operation is idempotent (running twice gives same result)")
        return 0
    else:
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        return 1


if __name__ == '__main__':
    exit(main())
