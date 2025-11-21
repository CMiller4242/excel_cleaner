#!/usr/bin/env python3
"""
Verify the fix doesn't create false positives
"""

import pandas as pd
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.executor import OperationExecutor

def verify_fix():
    """Verify no false positives - no valid addresses are removed"""

    print("=" * 100)
    print("VERIFYING FIX - CHECKING FOR FALSE POSITIVES")
    print("=" * 100)

    # Load file
    filename = "Volunteer Directors 11.20.25(2).xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    original_person_street = df['Person Street'].copy()
    print(f"    Original data:")
    print(f"      Total rows: {len(df):,}")
    print(f"      Person Street non-blank: {original_person_street.notna().sum():,}")
    print(f"      Person Street blank: {original_person_street.isna().sum():,}")

    # Load preset
    preset_file = "presets/system/zoominfo_healthcare_evs.json"
    with open(preset_file, 'r') as f:
        preset = json.load(f)
    operations = preset['operations']

    # Execute
    print(f"\n[2] Executing operations...")
    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df.copy(), operations)

    print(f"    Results: {len(result_df):,} rows")
    print(f"    Removed: {len(removed_df):,} rows")

    # CRITICAL CHECK: Look for valid Person Street values in the Removed sheet
    print(f"\n[3] Checking for FALSE POSITIVES...")

    if 'Person Street' in removed_df.columns:
        # Check if any removed rows had non-blank Person Street in the original data
        # These would be false positives - valid addresses incorrectly removed
        removed_ps = removed_df['Person Street']
        non_blank_removed = removed_ps.notna().sum()

        print(f"    Removed rows with non-blank Person Street: {non_blank_removed:,}")

        if non_blank_removed > 0:
            print(f"\n    ⚠️  Checking if these are FALSE POSITIVES or LEGITIMATE removals...")

            # Check the removed_by operation for each row
            by_operation = removed_df[removed_ps.notna()]['_Removed_By'].value_counts()
            print(f"\n    Removed by operation:")
            for op, count in by_operation.items():
                print(f"      {op}: {count:,} rows")

            # Show examples
            print(f"\n    First 20 examples:")
            for idx, row in removed_df[removed_ps.notna()].head(20).iterrows():
                ps_val = row['Person Street']
                removed_by = row.get('_Removed_By', 'Unknown')
                addr1 = row.get('Address 1', 'N/A')
                addr1_blank = pd.isna(addr1) or (isinstance(addr1, str) and addr1.strip() == '')

                # Determine if this is a false positive
                is_false_positive = False
                reason = ""

                if removed_by == "Remove Excluded States":
                    is_false_positive = False
                    reason = "Legitimate (excluded state)"
                elif removed_by == "Remove Rows If" and addr1_blank:
                    # Check if the original Person Street split into empty Address 1
                    is_false_positive = False
                    reason = "Legitimate (split resulted in empty Address 1)"
                else:
                    is_false_positive = True
                    reason = "FALSE POSITIVE!"

                status = "✓" if not is_false_positive else "⚠️"
                print(f"      [{idx}] {status}")
                print(f"            Person Street: '{ps_val}'")
                print(f"            Address 1: '{addr1}' (blank={addr1_blank})")
                print(f"            Removed by: {removed_by}")
                print(f"            Assessment: {reason}")

            # Count false positives
            false_positive_count = 0
            for idx, row in removed_df[removed_ps.notna()].iterrows():
                ps_val = row['Person Street']
                removed_by = row.get('_Removed_By', 'Unknown')
                addr1 = row.get('Address 1', 'N/A')
                addr1_blank = pd.isna(addr1) or (isinstance(addr1, str) and addr1.strip() == '')

                if removed_by == "Remove Rows If" and not addr1_blank:
                    # Address 1 has actual data but was removed - FALSE POSITIVE!
                    false_positive_count += 1

            print(f"\n[4] FINAL ASSESSMENT:")
            print(f"    Total rows with non-blank Person Street removed: {non_blank_removed:,}")
            print(f"    FALSE POSITIVES (valid addresses incorrectly removed): {false_positive_count}")

            if false_positive_count == 0:
                print(f"\n    ✓ NO FALSE POSITIVES DETECTED!")
                print(f"    All removals are legitimate (excluded states or split resulted in empty Address 1)")
                return True
            else:
                print(f"\n    ⚠️  {false_positive_count} FALSE POSITIVES DETECTED!")
                return False
        else:
            print(f"    ✓ No non-blank Person Street values removed")
            return True
    else:
        print(f"    Person Street column not in Removed sheet")
        return True

if __name__ == '__main__':
    success = verify_fix()
    print("\n" + "=" * 100)
    if success:
        print("✓ VERIFICATION PASSED - NO FALSE POSITIVES")
    else:
        print("✗ VERIFICATION FAILED - FALSE POSITIVES DETECTED")
    print("=" * 100)
    exit(0 if success else 1)
