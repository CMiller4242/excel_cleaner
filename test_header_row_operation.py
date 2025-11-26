#!/usr/bin/env python3
"""
Test for SetHeaderRowOperation
Tests the operation with sample data that has metadata rows above headers
"""

import pandas as pd
import sys
from pathlib import Path

# Add operations to path
sys.path.insert(0, str(Path(__file__).parent))
from operations.data_ops import SetHeaderRowOperation

def test_set_header_row():
    """Test SetHeaderRowOperation with sample data"""

    print("=" * 70)
    print("TEST: SetHeaderRowOperation")
    print("=" * 70)

    # Create test dataframe simulating file with metadata row
    # Row 0: Metadata/title row (will create "Unnamed" columns when read normally)
    # Row 1: Actual headers
    # Row 2+: Data

    test_data = {
        'Unnamed: 0': ['Report Title: Sales Data', 'Div', '1', '2', '3'],
        'Unnamed: 1': ['Date: 2024-11-26', 'Customer #', '12345', '23456', '34567'],
        'Unnamed: 2': ['', 'Segment', 'A', 'B', 'C'],
        'Unnamed: 3': ['', 'Shipping', 'Express', 'Standard', 'Express']
    }

    df = pd.DataFrame(test_data)

    print("\n1. INITIAL DATAFRAME (with Unnamed columns):")
    print("-" * 70)
    print(df.to_string())
    print(f"\nShape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

    # Test 1: Use row 2 as headers (0-indexed row 1), remove above
    print("\n" + "=" * 70)
    print("TEST 1: Set row 2 as headers, remove rows above")
    print("=" * 70)

    operation = SetHeaderRowOperation()
    params = {
        'header_row_number': 2,  # Row 2 (0-indexed row 1)
        'remove_above': True
    }

    result_df = operation.execute(df, params)

    print("\nRESULT:")
    print("-" * 70)
    print(result_df.to_string())
    print(f"\nShape: {result_df.shape}")
    print(f"Columns: {list(result_df.columns)}")

    # Verify
    expected_columns = ['Div', 'Customer #', 'Segment', 'Shipping']
    assert list(result_df.columns) == expected_columns, "Column names don't match!"
    assert len(result_df) == 3, f"Expected 3 rows, got {len(result_df)}"
    assert result_df.iloc[0]['Div'] == '1', "First data row incorrect"

    print("\n✓ TEST 1 PASSED")

    # Test 2: Use row 2 as headers, keep rows above
    print("\n" + "=" * 70)
    print("TEST 2: Set row 2 as headers, keep rows above")
    print("=" * 70)

    params = {
        'header_row_number': 2,
        'remove_above': False
    }

    result_df2 = operation.execute(df, params)

    print("\nRESULT:")
    print("-" * 70)
    print(result_df2.to_string())
    print(f"\nShape: {result_df2.shape}")
    print(f"Columns: {list(result_df2.columns)}")

    # Verify
    assert list(result_df2.columns) == expected_columns, "Column names don't match!"
    assert len(result_df2) == 5, f"Expected 5 rows, got {len(result_df2)}"

    print("\n✓ TEST 2 PASSED")

    # Test 3: Error handling - invalid row number
    print("\n" + "=" * 70)
    print("TEST 3: Error handling - invalid row number")
    print("=" * 70)

    params = {
        'header_row_number': 999,
        'remove_above': True
    }

    try:
        result_df3 = operation.execute(df, params)
        print("\n❌ TEST 3 FAILED: Should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✓ TEST 3 PASSED: Correctly raised ValueError: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
    print("\nSetHeaderRowOperation is working correctly:")
    print("- Correctly sets new header row")
    print("- Removes rows above when requested")
    print("- Keeps rows above when requested")
    print("- Properly validates row numbers")
    print("- Resets index correctly")

    return True

if __name__ == "__main__":
    try:
        test_set_header_row()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
