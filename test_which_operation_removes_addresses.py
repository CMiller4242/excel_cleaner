#!/usr/bin/env python3
"""
Identify which operation is removing the specific addresses

Since is_blank logic is correct, these addresses must be removed by a different operation.
This test runs common preset operations to see which one removes them.
"""

import pandas as pd
from engine.executor import OperationExecutor

def test_which_operation_removes_addresses():
    """Test each operation to see which removes the addresses"""

    print("=" * 100)
    print("IDENTIFYING WHICH OPERATION REMOVES SPECIFIC ADDRESSES")
    print("=" * 100)

    # Load file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[1] Loading: {filename}")
    df_original = pd.read_excel(filename)
    print(f"    Loaded: {len(df_original):,} rows")

    # Addresses user reports seeing in Removed sheet
    test_addresses = [
        "5700 Lindell Blvd",
        "2301 Vanderbilt Pl",
        "3840 Hulen St Ste 603",
        "210 S Prince St",
        "476 5th Ave",
        "1323 Yakima Ave",
        "615 Chestnut St Fl 17",
        "1 W Main St Ste 303",
        "10 Link Dr",
        "2845 Hamline Ave N Ste 200"
    ]

    print(f"\n[2] Test addresses in original file:")
    for addr in test_addresses:
        count = (df_original['Person Street'] == addr).sum()
        print(f"    '{addr}': {count} instances")

    # Test different operations that might remove rows
    operations_to_test = [
        {
            'name': 'Remove Rows If (is_blank)',
            'config': {
                'operation_id': 'data_remove_rows_if',
                'parameters': {
                    'column': 'Person Street',
                    'condition': 'is_blank'
                },
                'enabled': True
            }
        },
        {
            'name': 'Remove Excluded States',
            'config': {
                'operation_id': 'remove_excluded_states',
                'parameters': {
                    'column': 'Person State',
                    'excluded_states': 'AK,HI,PR,VI,GU'
                },
                'enabled': True
            }
        },
        {
            'name': 'Remove PO Boxes',
            'config': {
                'operation_id': 'remove_rows_containing',
                'parameters': {
                    'columns': ['Person Street'],
                    'patterns': 'PO BOX,P.O. BOX,P O BOX',
                    'preset': 'PO Boxes',
                    'case_sensitive': False,
                    'match_whole_cell': False,
                    'remove_blanks': False
                },
                'enabled': True
            }
        },
        {
            'name': 'Remove Blank Rows (all columns)',
            'config': {
                'operation_id': 'clean_remove_blank_rows',
                'parameters': {},
                'enabled': True
            }
        }
    ]

    print(f"\n[3] Testing each operation:")

    for op_info in operations_to_test:
        op_name = op_info['name']
        op_config = op_info['config']

        print(f"\n  Testing: {op_name}")

        executor = OperationExecutor()
        result_df, removed_df = executor.execute_queue_with_tracking(df_original, [op_config])

        print(f"    Results: {len(result_df):,} rows, Removed: {len(removed_df):,} rows")

        # Check if any test addresses were removed
        removed_addresses = []
        if not removed_df.empty and 'Person Street' in removed_df.columns:
            for addr in test_addresses:
                count_in_removed = (removed_df['Person Street'] == addr).sum()
                if count_in_removed > 0:
                    removed_addresses.append((addr, count_in_removed))

        if removed_addresses:
            print(f"    ✗ THIS OPERATION REMOVED:")
            for addr, count in removed_addresses:
                print(f"      • '{addr}' ({count} instances)")
        else:
            print(f"    ✓ Did not remove any test addresses")

    # Test full ZoomInfo workflow
    print(f"\n[4] Testing full ZoomInfo Healthcare/EVS preset workflow:")

    zoominfo_operations = [
        {
            'operation_id': 'clean_remove_blank_rows',
            'parameters': {},
            'enabled': True
        },
        {
            'operation_id': 'clean_remove_columns',
            'parameters': {
                'columns': [
                    'ZoomInfo Contact ID', 'Middle Name', 'Salutation', 'Suffix',
                    'Management Level', 'Job Start Date', 'Job Function', 'Department',
                    # ... (simplified for test)
                ]
            },
            'enabled': True
        },
        {
            'operation_id': 'remove_excluded_states',
            'parameters': {
                'column': 'Person State',
                'excluded_states': 'AK,HI,PR,VI,GU'
            },
            'enabled': True
        },
        {
            'operation_id': 'data_remove_rows_if',
            'parameters': {
                'column': 'Person Street',
                'condition': 'is_blank'
            },
            'enabled': True
        }
    ]

    executor = OperationExecutor()
    result_df, removed_df = executor.execute_queue_with_tracking(df_original, zoominfo_operations)

    print(f"    Results: {len(result_df):,} rows, Removed: {len(removed_df):,} rows")

    if not removed_df.empty and 'Person Street' in removed_df.columns:
        # Check operations that removed rows
        if '_Removed_By' in removed_df.columns:
            print(f"\n    Rows removed by each operation:")
            removal_counts = removed_df['_Removed_By'].value_counts()
            for op_name, count in removal_counts.items():
                print(f"      • {op_name}: {count:,} rows")

        # Check if test addresses were removed
        print(f"\n    Checking test addresses in Removed sheet:")
        for addr in test_addresses:
            if addr in removed_df['Person Street'].values:
                # Find which operation removed it
                rows_with_addr = removed_df[removed_df['Person Street'] == addr]
                if '_Removed_By' in rows_with_addr.columns:
                    removed_by = rows_with_addr['_Removed_By'].iloc[0]
                else:
                    removed_by = 'Unknown'
                print(f"      ✗ '{addr}' was REMOVED by: {removed_by}")
            else:
                print(f"      ✓ '{addr}' was NOT removed (correctly kept)")

    print(f"\n{'='*100}")
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == '__main__':
    test_which_operation_removes_addresses()
