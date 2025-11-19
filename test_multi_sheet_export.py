#!/usr/bin/env python3
"""
Test Multi-Sheet Export Feature

This script demonstrates and tests the new multi-sheet export system.
"""

import pandas as pd
from pathlib import Path
from engine.executor import OperationExecutor

def create_test_data():
    """Create sample data for testing"""
    data = {
        'First Name': ['John', 'Jane', '', 'Bob', 'Alice', 'Charlie', 'David', 'Emma', 'Frank', ''],
        'Last Name': ['Doe', 'Smith', '', 'Johnson', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson', ''],
        'Company': ['ABC Corp', 'XYZ Inc', 'Test Co', 'DEF Ltd', 'GHI Inc', 'JKL Corp', 'MNO Ltd', 'PQR Inc', '', 'UVW Corp'],
        'Email': ['john@abc.com', 'jane@xyz.com', 'test@test.com', 'bob@def.com', 'alice@ghi.com',
                 'charlie@jkl.com', 'david@mno.com', 'emma@pqr.com', 'frank@stu.com', 'zyx@uvw.com'],
        'Phone': ['555-1234', '555-5678', '555-0000', '555-1111', '555-2222',
                 '555-3333', '555-4444', '555-5555', '555-6666', '555-7777'],
        'State': ['OH', 'IL', 'TX', 'NY', 'CA', 'AK', 'HI', 'FL', 'PR', 'VI']
    }

    return pd.DataFrame(data)

def test_tracking():
    """Test the removed rows tracking"""
    print("=" * 80)
    print("TESTING MULTI-SHEET EXPORT FEATURE")
    print("=" * 80)

    # Create test data
    df = create_test_data()

    print(f"\nInput data: {len(df)} rows")
    print("\nSample data:")
    print(df.head())

    # Create executor
    executor = OperationExecutor()

    # Create operation queue
    operations = [
        {
            'operation_id': 'clean_remove_blank_rows',
            'parameters': {},
            'enabled': True
        },
        {
            'operation_id': 'remove_excluded_states',
            'parameters': {
                'column': 'State',
                'excluded_states': 'AK,HI,PR,VI'
            },
            'enabled': True
        }
    ]

    print("\n" + "=" * 80)
    print("EXECUTING OPERATIONS WITH TRACKING")
    print("=" * 80)

    # Execute with tracking
    result_df, removed_df = executor.execute_queue_with_tracking(df, operations)

    print(f"\n✓ Execution complete!")
    print(f"\nResults:")
    print(f"  Original: {len(df)} rows")
    print(f"  Results:  {len(result_df)} rows")
    print(f"  Removed:  {len(removed_df)} rows")

    print("\n" + "=" * 80)
    print("RESULTS DATAFRAME")
    print("=" * 80)
    print(result_df)

    if not removed_df.empty:
        print("\n" + "=" * 80)
        print("REMOVED DATAFRAME")
        print("=" * 80)
        print(removed_df)

        print("\n" + "=" * 80)
        print("REMOVED ROWS BY OPERATION")
        print("=" * 80)

        # Group by operation
        for operation in removed_df['_Removed_By'].unique():
            count = len(removed_df[removed_df['_Removed_By'] == operation])
            print(f"  {operation}: {count} rows")

    # Test export
    print("\n" + "=" * 80)
    print("TESTING EXPORT")
    print("=" * 80)

    output_file = Path("test_output_multisheet.xlsx")

    try:
        from utils.export_helper import ExportHelper

        sheets = {
            'Original': df,
            'Results': result_df,
            'Removed': removed_df
        }

        ExportHelper.export_multiple_sheets(sheets, str(output_file))

        print(f"\n✓ Exported to: {output_file}")
        print("\nSheet structure:")
        print(f"  • Original: {len(df)} rows × {len(df.columns)} columns")
        print(f"  • Results:  {len(result_df)} rows × {len(result_df.columns)} columns")
        print(f"  • Removed:  {len(removed_df)} rows × {len(removed_df.columns)} columns")

        print("\nRemoved sheet metadata columns:")
        removed_cols = [col for col in removed_df.columns if col.startswith('_')]
        for col in removed_cols:
            print(f"  • {col}")

        print(f"\n✓ Test completed successfully!")
        print(f"\nYou can open {output_file} to verify the multi-sheet export.")

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_tracking()
