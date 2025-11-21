#!/usr/bin/env python3
"""
Test if enhanced blank detection mode has the bug
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.executor import OperationExecutor

def test_enhanced_mode():
    """Test with enhanced_blank_detection=True"""

    print("=" * 100)
    print("TESTING ENHANCED BLANK DETECTION MODE")
    print("=" * 100)

    # Load the file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    print(f"    Loaded: {len(df):,} rows")

    # Test with ENHANCED blank detection
    print(f"\n[2] Testing with enhanced_blank_detection=TRUE")
    operations = [
        {
            'operation_id': 'data_remove_rows_if',
            'parameters': {
                'column': 'Person Street',
                'condition': 'is_blank',
                'enhanced_blank_detection': True  # ENHANCED MODE
            },
            'enabled': True
        }
    ]

    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df.copy(), operations)

    print(f"    Results: {len(result_df):,} rows")
    print(f"    Removed: {len(removed_df):,} rows")

    # Analyze what's in the Removed sheet
    print(f"\n[3] Analyzing Removed sheet:")
    if not removed_df.empty and 'Person Street' in removed_df.columns:
        removed_person_street = removed_df['Person Street']

        # Check for actual NaN
        removed_is_na = removed_person_street.isna()

        # Check for valid addresses (non-blank, non-NaN, not empty)
        valid_addresses = []
        for idx, val in removed_person_street.items():
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str and val_str not in ['', 'n/a', 'na', 'null', 'none']:
                    valid_addresses.append((idx, val))

        blank_count = removed_is_na.sum()
        valid_count = len(valid_addresses)

        print(f"    Total in Removed: {len(removed_df):,}")
        print(f"    Blank (NaN) values: {blank_count:,}")
        print(f"    VALID addresses removed: {valid_count:,}")

        if valid_count > 0:
            print(f"\n    ✗ BUG FOUND: {valid_count} valid addresses removed!")
            print(f"    First 20 valid addresses in Removed:")
            for idx, addr in valid_addresses[:20]:
                print(f"      [{idx}] '{addr}'")
            return False
        else:
            print(f"    ✓ No valid addresses removed")
            return True

    print(f"\n{'='*100}")
    return True

def test_both_modes():
    """Test both standard and enhanced modes"""

    print("\n\n")
    print("#" * 100)
    print("COMPREHENSIVE TEST: STANDARD vs ENHANCED MODE")
    print("#" * 100)

    filename = "Volunteer Directors 11.20.25.xlsx"
    df = pd.read_excel(filename)

    # Test standard mode
    print("\n" + "=" * 100)
    print("TEST 1: STANDARD MODE (enhanced_blank_detection=False)")
    print("=" * 100)

    operations_standard = [
        {
            'operation_id': 'data_remove_rows_if',
            'parameters': {
                'column': 'Person Street',
                'condition': 'is_blank',
                'enhanced_blank_detection': False
            },
            'enabled': True
        }
    ]

    executor1 = OperationExecutor()
    result1, removed1 = executor1.execute_queue_with_tracking(df.copy(), operations_standard)

    print(f"Results: {len(result1):,} rows")
    print(f"Removed: {len(removed1):,} rows")

    # Check for false positives in standard mode
    false_positives_standard = 0
    if not removed1.empty and 'Person Street' in removed1.columns:
        for idx, val in removed1['Person Street'].items():
            if pd.notna(val):
                val_str = str(val).strip()
                if val_str and val_str.lower() not in ['nan', 'none', 'nat', '<na>']:
                    false_positives_standard += 1

    print(f"False positives: {false_positives_standard}")

    # Test enhanced mode
    print("\n" + "=" * 100)
    print("TEST 2: ENHANCED MODE (enhanced_blank_detection=True)")
    print("=" * 100)

    operations_enhanced = [
        {
            'operation_id': 'data_remove_rows_if',
            'parameters': {
                'column': 'Person Street',
                'condition': 'is_blank',
                'enhanced_blank_detection': True
            },
            'enabled': True
        }
    ]

    executor2 = OperationExecutor()
    result2, removed2 = executor2.execute_queue_with_tracking(df.copy(), operations_enhanced)

    print(f"Results: {len(result2):,} rows")
    print(f"Removed: {len(removed2):,} rows")

    # Check for false positives in enhanced mode
    false_positives_enhanced = 0
    examples = []
    if not removed2.empty and 'Person Street' in removed2.columns:
        for idx, val in removed2['Person Street'].items():
            if pd.notna(val):
                val_str = str(val).strip().lower()
                if val_str and val_str not in ['', 'n/a', 'na', 'null', 'none']:
                    false_positives_enhanced += 1
                    if len(examples) < 10:
                        examples.append(val)

    print(f"False positives: {false_positives_enhanced}")
    if examples:
        print(f"Examples: {examples}")

    # Summary
    print("\n" + "#" * 100)
    print("SUMMARY")
    print("#" * 100)
    print(f"Standard mode false positives: {false_positives_standard}")
    print(f"Enhanced mode false positives: {false_positives_enhanced}")

    if false_positives_standard > 0:
        print(f"\n✗ STANDARD MODE HAS BUG")
    else:
        print(f"\n✓ STANDARD MODE OK")

    if false_positives_enhanced > 0:
        print(f"✗ ENHANCED MODE HAS BUG")
    else:
        print(f"✓ ENHANCED MODE OK")

    return false_positives_standard == 0 and false_positives_enhanced == 0

if __name__ == '__main__':
    success = test_both_modes()
    exit(0 if success else 1)
