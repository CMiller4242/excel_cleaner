#!/usr/bin/env python3
"""
Comprehensive validation of the is_blank fix for empty strings
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from operations.data_ops import RemoveRowsIfOperation

def test_is_blank_with_empty_strings():
    """Test that is_blank now correctly handles empty strings"""

    print("=" * 100)
    print("COMPREHENSIVE VALIDATION: is_blank handles empty strings")
    print("=" * 100)

    # Create test data with various "blank" scenarios
    test_data = {
        'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Henry'],
        'Address': [
            '123 Main St',      # Valid address
            '',                 # Empty string
            '   ',              # Whitespace only
            None,               # NaN/None
            'PO Box 123',       # Valid address
            '',                 # Empty string
            '456 Oak Ave',      # Valid address
            pd.NA               # pd.NA (pandas missing value)
        ]
    }

    df = pd.DataFrame(test_data)

    print(f"\n[1] Test Data:")
    print(f"    Total rows: {len(df)}")
    print(f"\n    Address column:")
    for idx, row in df.iterrows():
        addr = row['Address']
        addr_type = type(addr).__name__
        is_na = pd.isna(addr)
        is_empty = isinstance(addr, str) and addr.strip() == ''
        print(f"      [{idx}] '{addr}' (type: {addr_type}, is_na: {is_na}, is_empty: {is_empty})")

    # Test standard mode (should remove NaN, None, empty strings, whitespace)
    print(f"\n[2] Testing STANDARD MODE (enhanced_blank_detection=False):")
    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Address',
        'condition': 'is_blank',
        'enhanced_blank_detection': False
    }

    result_df = operation.execute(df.copy(), params)

    print(f"    Before: {len(df)} rows")
    print(f"    After: {len(result_df)} rows")
    print(f"    Removed: {len(df) - len(result_df)} rows")

    print(f"\n    Remaining rows (should only have valid addresses):")
    for idx, row in result_df.iterrows():
        print(f"      [{idx}] Name: {row['Name']}, Address: '{row['Address']}'")

    # Verify correct behavior
    expected_remaining = ['Alice', 'David', 'Eve', 'Grace']  # Bob, Charlie, Frank, Henry should be removed
    actual_remaining = result_df['Name'].tolist()

    # Actually wait - David has None, so should be removed. Let me recalculate:
    # - Alice: '123 Main St' → KEEP
    # - Bob: '' → REMOVE (empty string)
    # - Charlie: '   ' → REMOVE (whitespace only)
    # - David: None → REMOVE (NaN)
    # - Eve: 'PO Box 123' → KEEP
    # - Frank: '' → REMOVE (empty string)
    # - Grace: '456 Oak Ave' → KEEP
    # - Henry: pd.NA → REMOVE (NaN)

    expected_remaining_correct = ['Alice', 'Eve', 'Grace']
    actual_remaining = result_df['Name'].tolist()

    print(f"\n[3] Validation:")
    print(f"    Expected remaining: {expected_remaining_correct}")
    print(f"    Actual remaining: {actual_remaining}")

    if actual_remaining == expected_remaining_correct:
        print(f"    ✓ PASS: Standard mode correctly removes NaN, None, empty strings, and whitespace")
        return True
    else:
        print(f"    ✗ FAIL: Unexpected results")
        print(f"    Missing: {set(expected_remaining_correct) - set(actual_remaining)}")
        print(f"    Extra: {set(actual_remaining) - set(expected_remaining_correct)}")
        return False

def test_real_world_scenario():
    """Test with real-world ZoomInfo split address scenario"""

    print(f"\n\n" + "=" * 100)
    print("REAL-WORLD SCENARIO: ZoomInfo Address Split")
    print("=" * 100)

    # Simulate what happens after zoominfo_split_address
    test_data = {
        'Company': ['Acme Corp', 'Beta Inc', 'Gamma LLC', 'Delta Co'],
        'Address 1': [
            '400 W 7th St',  # Valid street address
            '',              # Empty (split resulted in no street)
            '123 Main St',   # Valid street address
            ''               # Empty (split resulted in no street)
        ],
        'Address 2': [
            '',              # No suite
            'Ste 300',       # Suite info
            'Apt 5B',        # Apartment info
            'Floor 2'        # Floor info
        ]
    }

    df = pd.DataFrame(test_data)

    print(f"\n[1] After zoominfo_split_address:")
    print(df.to_string())

    print(f"\n[2] Executing: Remove Rows If Address 1 is blank")
    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Address 1',
        'condition': 'is_blank',
        'enhanced_blank_detection': False
    }

    result_df = operation.execute(df.copy(), params)

    print(f"\n[3] Results:")
    print(f"    Before: {len(df)} rows")
    print(f"    After: {len(result_df)} rows")
    print(f"    Removed: {len(df) - len(result_df)} rows")

    print(f"\n    Remaining companies (should only have valid Address 1):")
    print(result_df.to_string())

    # Verify
    expected_companies = ['Acme Corp', 'Gamma LLC']
    actual_companies = result_df['Company'].tolist()

    print(f"\n[4] Validation:")
    print(f"    Expected: {expected_companies}")
    print(f"    Actual: {actual_companies}")

    if actual_companies == expected_companies:
        print(f"    ✓ PASS: Correctly removed rows with empty Address 1")
        return True
    else:
        print(f"    ✗ FAIL: Unexpected results")
        return False

if __name__ == '__main__':
    test1 = test_is_blank_with_empty_strings()
    test2 = test_real_world_scenario()

    print("\n" + "=" * 100)
    if test1 and test2:
        print("✓ ALL TESTS PASSED")
        exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        exit(1)
