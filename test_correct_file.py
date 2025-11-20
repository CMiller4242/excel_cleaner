#!/usr/bin/env python3
"""
Test with the CORRECT file: Volunteer Directors 11.20.25(2).xlsx
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.executor import OperationExecutor
from operations.registry import registry

def test_correct_file():
    """Test with the file the user is actually using"""

    print("=" * 100)
    print("TESTING WITH CORRECT FILE: Volunteer Directors 11.20.25(2).xlsx")
    print("=" * 100)

    # Load the CORRECT file
    filename = "Volunteer Directors 11.20.25(2).xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    print(f"    Loaded: {len(df):,} rows")
    print(f"    Columns: {len(df.columns)} columns")

    # Check Person Street column
    if 'Person Street' not in df.columns:
        print(f"    ERROR: 'Person Street' column not found!")
        return False

    # Analyze Person Street values BEFORE operation
    print(f"\n[2] BEFORE - Person Street Analysis:")
    person_street = df['Person Street']
    print(f"    Total values: {len(person_street):,}")
    print(f"    Non-blank values: {person_street.notna().sum():,}")
    print(f"    Blank (NaN) values: {person_street.isna().sum():,}")

    # Show some non-blank values
    print(f"\n    First 20 non-blank values:")
    non_blank = person_street[person_street.notna()].head(20)
    for idx, val in non_blank.items():
        print(f"      [{idx}] '{val}'")

    # Create operation (Remove Rows If Person Street is blank)
    print(f"\n[3] Creating operation: Remove Rows If Person Street is blank")
    operations = [
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

    # Execute
    print(f"\n[4] Executing operation...")
    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df.copy(), operations)

    print(f"    Results sheet: {len(result_df):,} rows")
    print(f"    Removed sheet: {len(removed_df):,} rows")
    print(f"    Expected to remove: {person_street.isna().sum():,} rows")

    # CRITICAL: Analyze what was removed
    print(f"\n[5] ANALYZING REMOVED SHEET:")
    if not removed_df.empty and 'Person Street' in removed_df.columns:
        removed_person_street = removed_df['Person Street']

        # Count blank vs non-blank in removed
        blank_in_removed = removed_person_street.isna().sum()
        non_blank_in_removed = removed_person_street.notna().sum()

        print(f"    Total rows in Removed: {len(removed_df):,}")
        print(f"    Blank (NaN) values: {blank_in_removed:,}")
        print(f"    NON-BLANK values: {non_blank_in_removed:,}")

        if non_blank_in_removed > 0:
            print(f"\n    ⚠️  ERROR: {non_blank_in_removed:,} NON-BLANK values incorrectly removed!")
            print(f"    These are FALSE POSITIVES!")

            # Show the false positives
            print(f"\n    First 50 FALSE POSITIVES (non-blank values in Removed):")
            false_positives = removed_df[removed_person_street.notna()].head(50)
            for idx, row in false_positives.iterrows():
                addr = row['Person Street']
                # Show the actual value and its type
                print(f"      [{idx}] '{addr}' (type: {type(addr).__name__}, repr: {repr(addr)})")

            # Analyze RESULTS sheet too
            print(f"\n[6] ANALYZING RESULTS SHEET:")
            if not result_df.empty and 'Person Street' in result_df.columns:
                result_person_street = result_df['Person Street']
                blank_in_results = result_person_street.isna().sum()
                non_blank_in_results = result_person_street.notna().sum()

                print(f"    Total rows in Results: {len(result_df):,}")
                print(f"    Blank (NaN) values: {blank_in_results:,}")
                print(f"    NON-BLANK values: {non_blank_in_results:,}")

                if blank_in_results > 0:
                    print(f"\n    ⚠️  WARNING: {blank_in_results:,} blank values remain in Results!")
                    print(f"    These should have been removed!")

            return False
        else:
            print(f"    ✓ All values in Removed are blank (correct)")
            return True
    else:
        print(f"    No rows removed")
        return False

if __name__ == '__main__':
    success = test_correct_file()
    print("\n" + "=" * 100)
    if success:
        print("✓ TEST PASSED")
    else:
        print("✗ TEST FAILED - FALSE POSITIVES DETECTED")
    print("=" * 100)
    exit(0 if success else 1)
