#!/usr/bin/env python3
"""
Test for Standardize Customer Numbers Operation
Tests padding of customer numbers and segments with leading zeros
"""

import sys
from pathlib import Path

# Add operations to path
sys.path.insert(0, str(Path(__file__).parent))

def test_standardize_customer_numbers():
    """Test StandardizeCustomerNumbersOperation"""
    import pandas as pd
    import numpy as np

    print("=" * 70)
    print("TEST: StandardizeCustomerNumbersOperation")
    print("=" * 70)

    # Create test dataframe matching user's examples
    test_data = {
        'Customer #': [5164, 8966, 21601, 30941, 99782, 100045, 100204, 5164.0, 123, np.nan],
        'Segment': [69, 11, 65, 6, 58, 49, np.nan, 6.0, '', 99]
    }

    df = pd.DataFrame(test_data)

    print("\nINITIAL DATA:")
    print("-" * 70)
    print(df.to_string())

    # Import operation
    from operations.text_ops import StandardizeCustomerNumbersOperation

    operation = StandardizeCustomerNumbersOperation()
    params = {
        'customer_number_column': 'Customer #',
        'segment_column': 'Segment',
        'customer_length': 8,
        'segment_length': 2,
        'blank_segment_value': '00'
    }

    result_df = operation.execute(df, params)

    print("\nRESULT (after standardization):")
    print("-" * 70)
    print(result_df.to_string())

    print("\n" + "=" * 70)
    print("VERIFICATION:")
    print("=" * 70)

    # Verify customer numbers
    print("\nCustomer Numbers:")
    assert result_df.at[0, 'Customer #'] == '00005164', f"Row 0: Expected 00005164, got {result_df.at[0, 'Customer #']}"
    print("  ✓ 5164 → 00005164")

    assert result_df.at[1, 'Customer #'] == '00008966', f"Row 1: Expected 00008966, got {result_df.at[1, 'Customer #']}"
    print("  ✓ 8966 → 00008966")

    assert result_df.at[2, 'Customer #'] == '00021601', f"Row 2: Expected 00021601, got {result_df.at[2, 'Customer #']}"
    print("  ✓ 21601 → 00021601")

    assert result_df.at[5, 'Customer #'] == '00100045', f"Row 5: Expected 00100045, got {result_df.at[5, 'Customer #']}"
    print("  ✓ 100045 → 00100045")

    assert result_df.at[7, 'Customer #'] == '00005164', f"Row 7: Expected 00005164, got {result_df.at[7, 'Customer #']}"
    print("  ✓ 5164.0 (decimal) → 00005164")

    assert result_df.at[8, 'Customer #'] == '00000123', f"Row 8: Expected 00000123, got {result_df.at[8, 'Customer #']}"
    print("  ✓ 123 → 00000123")

    assert result_df.at[9, 'Customer #'] == '00000000', f"Row 9: Expected 00000000, got {result_df.at[9, 'Customer #']}"
    print("  ✓ NaN → 00000000")

    # Verify segments
    print("\nSegments:")
    assert result_df.at[0, 'Segment'] == '69', f"Row 0: Expected 69, got {result_df.at[0, 'Segment']}"
    print("  ✓ 69 → 69 (already 2 digits)")

    assert result_df.at[3, 'Segment'] == '06', f"Row 3: Expected 06, got {result_df.at[3, 'Segment']}"
    print("  ✓ 6 → 06 (padded)")

    assert result_df.at[6, 'Segment'] == '00', f"Row 6: Expected 00, got {result_df.at[6, 'Segment']}"
    print("  ✓ blank/NaN → 00")

    assert result_df.at[7, 'Segment'] == '06', f"Row 7: Expected 06, got {result_df.at[7, 'Segment']}"
    print("  ✓ 6.0 (decimal) → 06")

    assert result_df.at[8, 'Segment'] == '00', f"Row 8: Expected 00, got {result_df.at[8, 'Segment']}"
    print("  ✓ empty string → 00")

    assert result_df.at[9, 'Segment'] == '99', f"Row 9: Expected 99, got {result_df.at[9, 'Segment']}"
    print("  ✓ 99 → 99 (already 2 digits)")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
    print("\nStandardizeCustomerNumbersOperation is working correctly:")
    print("✓ Customer numbers padded to 8 digits")
    print("✓ Segments padded to 2 digits")
    print("✓ Blank segments converted to '00'")
    print("✓ Decimal values handled correctly (5164.0 → 00005164)")
    print("✓ Already-correct lengths preserved")
    print("✓ NaN/empty values handled correctly")
    print("\nReady for use with your data!")

    return True

if __name__ == "__main__":
    try:
        test_standardize_customer_numbers()
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
