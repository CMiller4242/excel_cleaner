#!/usr/bin/env python3
"""
Simulate the exact GUI workflow to reproduce the false positives issue
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.executor import OperationExecutor
from operations.registry import registry

def test_gui_workflow():
    """Simulate the exact workflow the user is running"""

    print("=" * 100)
    print("GUI WORKFLOW SIMULATION TEST")
    print("=" * 100)

    # Load the file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    print(f"    Loaded: {len(df):,} rows")
    print(f"    Columns: {list(df.columns)}")

    # Check if Person Street column exists
    if 'Person Street' not in df.columns:
        print(f"    ERROR: 'Person Street' column not found!")
        print(f"    Available columns: {list(df.columns)}")
        return False

    # Show sample of Person Street values
    print(f"\n[2] Sample Person Street values:")
    person_street = df['Person Street']
    print(f"    Total values: {len(person_street)}")
    print(f"    Non-blank values: {person_street.notna().sum()}")
    print(f"    Blank (NaN) values: {person_street.isna().sum()}")
    print(f"    First 10 non-blank values:")
    non_blank = person_street[person_street.notna()].head(10)
    for idx, val in non_blank.items():
        print(f"      [{idx}] {repr(val)}")

    # Create operation queue simulating user's workflow
    print(f"\n[3] Creating operation queue (Remove Rows If Person Street is blank)")
    operations = [
        {
            'operation_id': 'data_remove_rows_if',
            'parameters': {
                'column': 'Person Street',
                'condition': 'is_blank',
                'enhanced_blank_detection': False  # Standard mode
            },
            'enabled': True
        }
    ]

    # Execute with tracking (like GUI does)
    print(f"\n[4] Executing operations with tracking...")
    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df.copy(), operations)

    print(f"    Results: {len(result_df):,} rows")
    print(f"    Removed: {len(removed_df):,} rows")

    # Analyze what's in the Removed sheet
    print(f"\n[5] Analyzing Removed sheet:")
    if not removed_df.empty and 'Person Street' in removed_df.columns:
        removed_person_street = removed_df['Person Street']

        # Check which values are actually blank
        removed_is_na = removed_person_street.isna()
        removed_not_na = ~removed_is_na

        blank_count = removed_is_na.sum()
        non_blank_count = removed_not_na.sum()

        print(f"    Total in Removed: {len(removed_df):,}")
        print(f"    Blank (NaN) values: {blank_count:,}")
        print(f"    NON-BLANK values: {non_blank_count:,} ⚠️")

        if non_blank_count > 0:
            print(f"\n    ✗ ERROR: Found {non_blank_count} NON-BLANK values in Removed!")
            print(f"    This is the bug!")
            print(f"\n    First 20 non-blank values in Removed:")
            non_blank_removed = removed_df[removed_not_na].head(20)
            for idx, row in non_blank_removed.iterrows():
                addr = row['Person Street']
                print(f"      [{idx}] '{addr}'")

            # Check specific addresses from user's screenshot
            test_addresses = [
                "6600 N Lincoln Ave Ste 300",
                "2150 Post St",
                "4205 NW 6th St",
                "1718 Patterson St",
                "95 S State St",
                "25701 Science Park Dr",
                "201 Alabama St",
                "137 Field St Apt 28",
                "4747 Arapahoe Ave",
                "5301 E Grant Rd",
                "233 N Michigan Ave Fl 21",
                "393 Maple St Ste 1"
            ]

            print(f"\n[6] Checking specific addresses from screenshot:")
            for addr in test_addresses:
                in_removed = addr in removed_df['Person Street'].values
                in_results = addr in result_df['Person Street'].values

                if in_removed:
                    print(f"      ✗ '{addr}' is in REMOVED (FALSE POSITIVE)")
                elif in_results:
                    print(f"      ✓ '{addr}' is in RESULTS (correct)")
                else:
                    print(f"      ? '{addr}' not found in either sheet")

            return False
        else:
            print(f"    ✓ All values in Removed are blank (correct)")
            return True
    else:
        print(f"    No rows removed or Person Street column missing")
        return True

    print(f"\n{'='*100}")
    if non_blank_count > 0:
        print("✗ TEST FAILED - FALSE POSITIVES FOUND")
        print(f"   {non_blank_count} valid addresses incorrectly removed")
    else:
        print("✓ TEST PASSED - NO FALSE POSITIVES")
    print("=" * 100)

    return non_blank_count == 0

if __name__ == '__main__':
    success = test_gui_workflow()
    exit(0 if success else 1)
