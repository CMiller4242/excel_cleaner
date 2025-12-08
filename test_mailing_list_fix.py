"""
Integration test for the Clean Mailing List Customer Data operation fix.

Tests that segment padding now works correctly for float values from Excel.
"""
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

import pandas as pd
from operations.text_ops import CleanMailingCustomerDataOperation

def test_segment_padding_with_floats():
    """
    Test the CRITICAL BUG FIX for segment padding.

    Before fix:
    - Segment 10.0 → "100" ❌
    - Segment 2.0 → "20" ❌

    After fix:
    - Segment 10.0 → "10" ✓
    - Segment 2.0 → "02" ✓
    """
    print("=" * 70)
    print("TEST: SEGMENT PADDING WITH FLOAT VALUES (THE BUG)")
    print("=" * 70)

    # Create test dataframe mimicking the problematic Excel data
    # Excel stores numeric values as floats (10.0, 2.0, etc.)
    df = pd.DataFrame({
        'Cust': [
            "2098687-662541",
            "620729-663907",
            "1551731-664186",
            "5164-640000"
        ],
        'Seg': [
            0.0,    # Should become "00"
            10.0,   # Should become "10" (NOT "100" - this was the bug!)
            2.0,    # Should become "02" (NOT "20" - this was the bug!)
            31.0    # Should become "31"
        ]
    })

    print("\nBEFORE Operation:")
    print(df)
    print(f"\nSegment column dtype: {df['Seg'].dtype}")

    # Apply the operation
    operation = CleanMailingCustomerDataOperation()

    params = {
        'customer_column': 'Cust',
        'customer_length': 8,
        'segment_column': 'Seg',
        'segment_length': 2,
        'handle_non_hyphenated': 'Pad as-is',
        'blank_segments_to_zero': False
    }

    result_df = operation.execute(df, params)

    print("\nAFTER Operation:")
    print(result_df)

    # Verify expected results
    expected_customers = ["02098687", "00620729", "01551731", "00005164"]
    expected_segments = ["00", "10", "02", "31"]

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    all_pass = True

    for i, (expected_cust, expected_seg) in enumerate(zip(expected_customers, expected_segments)):
        actual_cust = result_df.iloc[i]['Cust']
        actual_seg = result_df.iloc[i]['Seg']

        cust_match = actual_cust == expected_cust
        seg_match = actual_seg == expected_seg

        cust_status = "✓" if cust_match else "✗"
        seg_status = "✓" if seg_match else "✗"

        print(f"\nRow {i}:")
        print(f"  Customer: {actual_cust:12} (expected: {expected_cust}) {cust_status}")
        print(f"  Segment:  {actual_seg:12} (expected: {expected_seg}) {seg_status}")

        if not cust_match or not seg_match:
            all_pass = False

    print("\n" + "=" * 70)
    if all_pass:
        print("✓ ALL TESTS PASSED - Bug is FIXED!")
    else:
        print("✗ TESTS FAILED - Bug still exists")
    print("=" * 70)

    return all_pass


def test_customer_padding_with_floats():
    """Test customer number padding with numeric values"""
    print("\n\n" + "=" * 70)
    print("TEST: CUSTOMER PADDING WITH NUMERIC VALUES")
    print("=" * 70)

    df = pd.DataFrame({
        'Cust': [
            5164,       # Should become "00005164"
            5164.0,     # Should become "00005164" (not "000051640")
            "5164",     # Should become "00005164"
            "9609-640231"  # Should extract "9609" → "00009609"
        ]
    })

    print("\nBEFORE Operation:")
    print(df)

    operation = CleanMailingCustomerDataOperation()

    params = {
        'customer_column': 'Cust',
        'customer_length': 8,
        'handle_non_hyphenated': 'Pad as-is'
    }

    result_df = operation.execute(df, params)

    print("\nAFTER Operation:")
    print(result_df)

    expected = ["00005164", "00005164", "00005164", "00009609"]

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    all_pass = True
    for i, expected_val in enumerate(expected):
        actual = result_df.iloc[i]['Cust']
        match = actual == expected_val
        status = "✓" if match else "✗"
        print(f"Row {i}: {actual:12} (expected: {expected_val}) {status}")
        if not match:
            all_pass = False

    print("\n" + "=" * 70)
    if all_pass:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ TESTS FAILED")
    print("=" * 70)

    return all_pass


def test_idempotency():
    """Test that running the operation twice produces the same result"""
    print("\n\n" + "=" * 70)
    print("TEST: IDEMPOTENCY (Running operation twice)")
    print("=" * 70)

    df = pd.DataFrame({
        'Cust': ["2098687-662541", "620729-663907"],
        'Seg': [10.0, 2.0]
    })

    operation = CleanMailingCustomerDataOperation()

    params = {
        'customer_column': 'Cust',
        'customer_length': 8,
        'segment_column': 'Seg',
        'segment_length': 2,
        'handle_non_hyphenated': 'Pad as-is',
        'blank_segments_to_zero': False
    }

    # Run once
    result1 = operation.execute(df.copy(), params)
    print("\nAfter first run:")
    print(result1)

    # Run again on the result
    result2 = operation.execute(result1.copy(), params)
    print("\nAfter second run (should be identical):")
    print(result2)

    # Check if identical
    identical = result1.equals(result2)

    print("\n" + "=" * 70)
    if identical:
        print("✓ IDEMPOTENCY TEST PASSED - Results are identical")
    else:
        print("✗ IDEMPOTENCY TEST FAILED - Results differ after second run")
        print("\nDifferences:")
        for col in result1.columns:
            for i in range(len(result1)):
                if result1.iloc[i][col] != result2.iloc[i][col]:
                    print(f"  Row {i}, Col {col}: '{result1.iloc[i][col]}' → '{result2.iloc[i][col]}'")
    print("=" * 70)

    return identical


def test_blank_segments():
    """Test handling of blank segment values"""
    print("\n\n" + "=" * 70)
    print("TEST: BLANK SEGMENT HANDLING")
    print("=" * 70)

    df = pd.DataFrame({
        'Cust': ["1234-5678", "9999-8888"],
        'Seg': [None, ""]
    })

    operation = CleanMailingCustomerDataOperation()

    # Test with blank_segments_to_zero = False
    params1 = {
        'customer_column': 'Cust',
        'customer_length': 8,
        'segment_column': 'Seg',
        'segment_length': 2,
        'blank_segments_to_zero': False
    }

    result1 = operation.execute(df.copy(), params1)
    print("\nWith blank_segments_to_zero=False:")
    print(result1)
    print(f"Segments: {list(result1['Seg'])}")

    # Test with blank_segments_to_zero = True
    params2 = {
        'customer_column': 'Cust',
        'customer_length': 8,
        'segment_column': 'Seg',
        'segment_length': 2,
        'blank_segments_to_zero': True
    }

    result2 = operation.execute(df.copy(), params2)
    print("\nWith blank_segments_to_zero=True:")
    print(result2)
    print(f"Segments: {list(result2['Seg'])}")

    print("\n" + "=" * 70)
    blanks_stay_blank = result1['Seg'].iloc[0] == "" and result1['Seg'].iloc[1] == ""
    blanks_to_zero = result2['Seg'].iloc[0] == "00" and result2['Seg'].iloc[1] == "00"

    if blanks_stay_blank and blanks_to_zero:
        print("✓ BLANK HANDLING TEST PASSED")
    else:
        print("✗ BLANK HANDLING TEST FAILED")
    print("=" * 70)

    return blanks_stay_blank and blanks_to_zero


if __name__ == '__main__':
    print("\n")
    print("█" * 70)
    print("CLEAN MAILING LIST CUSTOMER DATA - SEGMENT PADDING BUG FIX TEST")
    print("█" * 70)

    results = []

    # Run all tests
    results.append(("Segment Padding with Floats", test_segment_padding_with_floats()))
    results.append(("Customer Padding with Floats", test_customer_padding_with_floats()))
    results.append(("Idempotency", test_idempotency()))
    results.append(("Blank Segment Handling", test_blank_segments()))

    # Summary
    print("\n\n" + "█" * 70)
    print("TEST SUMMARY")
    print("█" * 70)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:40} {status}")

    all_passed = all(result[1] for result in results)

    print("█" * 70)
    if all_passed:
        print("✓✓✓ ALL TESTS PASSED - BUG IS FIXED ✓✓✓")
    else:
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
    print("█" * 70)

    sys.exit(0 if all_passed else 1)
