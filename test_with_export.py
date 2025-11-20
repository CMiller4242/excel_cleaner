#!/usr/bin/env python3
"""
Test and EXPORT the results to Excel so we can inspect them
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.executor import OperationExecutor

def test_and_export():
    """Test and export results for manual inspection"""

    print("=" * 100)
    print("TEST WITH EXPORT")
    print("=" * 100)

    # Load the file
    filename = "Volunteer Directors 11.20.25(2).xlsx"
    print(f"\n[1] Loading: {filename}")
    df = pd.read_excel(filename)
    print(f"    Loaded: {len(df):,} rows")

    # Analyze BEFORE
    person_street = df['Person Street']
    print(f"\n[2] BEFORE operation:")
    print(f"    Total rows: {len(df):,}")
    print(f"    Person Street non-blank: {person_street.notna().sum():,}")
    print(f"    Person Street blank: {person_street.isna().sum():,}")

    # Create operation
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
    print(f"\n[3] Executing operation...")
    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df.copy(), operations)

    print(f"    Results: {len(result_df):,} rows")
    print(f"    Removed: {len(removed_df):,} rows")

    # Analyze RESULTS
    print(f"\n[4] RESULTS sheet analysis:")
    if 'Person Street' in result_df.columns:
        result_ps = result_df['Person Street']
        print(f"    Total rows: {len(result_df):,}")
        print(f"    Person Street non-blank: {result_ps.notna().sum():,}")
        print(f"    Person Street blank: {result_ps.isna().sum():,}")

        if result_ps.notna().sum() > 0:
            print(f"\n    First 10 values in RESULTS:")
            for idx, val in result_ps[result_ps.notna()].head(10).items():
                print(f"      [{idx}] '{val}'")

    # Analyze REMOVED
    print(f"\n[5] REMOVED sheet analysis:")
    if 'Person Street' in removed_df.columns:
        removed_ps = removed_df['Person Street']
        print(f"    Total rows: {len(removed_df):,}")
        print(f"    Person Street non-blank: {removed_ps.notna().sum():,}")
        print(f"    Person Street blank: {removed_ps.isna().sum():,}")

        # This is the KEY check
        if removed_ps.notna().sum() > 0:
            print(f"\n    ⚠️  FALSE POSITIVES DETECTED: {removed_ps.notna().sum():,} non-blank values!")
            print(f"\n    First 20 FALSE POSITIVES in REMOVED:")
            for idx, val in removed_ps[removed_ps.notna()].head(20).items():
                print(f"      [{idx}] '{val}' (type={type(val).__name__})")

    # EXPORT to Excel
    output_file = "TEST_EXPORT_DEBUG.xlsx"
    print(f"\n[6] Exporting to: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        result_df.to_excel(writer, sheet_name='Results', index=False)
        removed_df.to_excel(writer, sheet_name='Removed', index=False)

    print(f"    ✓ Exported to {output_file}")
    print(f"    You can now open this file and inspect the sheets manually")

    # Also create a summary of Person Street values
    print(f"\n[7] Creating Person Street summary...")

    # Get all unique Person Street values from Removed sheet
    if 'Person Street' in removed_df.columns:
        removed_values = removed_df['Person Street'].dropna()
        if len(removed_values) > 0:
            print(f"    Found {len(removed_values)} non-blank Person Street values in REMOVED sheet")
            print(f"    This should be ZERO for the operation to be correct!")

            # Export just the Person Street column from removed for easier inspection
            summary_df = pd.DataFrame({
                'Person Street': removed_df['Person Street'],
                'Is Blank (pandas)': removed_df['Person Street'].isna(),
                'Is Blank (str)': removed_df['Person Street'].astype(str) == 'nan',
                'Value Type': removed_df['Person Street'].apply(lambda x: type(x).__name__),
                'String Repr': removed_df['Person Street'].apply(repr)
            })

            summary_file = "REMOVED_PERSON_STREET_ANALYSIS.xlsx"
            summary_df.to_excel(summary_file, index=True)
            print(f"    ✓ Exported detailed analysis to {summary_file}")

    print("\n" + "=" * 100)

if __name__ == '__main__':
    test_and_export()
