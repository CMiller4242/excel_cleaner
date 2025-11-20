#!/usr/bin/env python3
"""
COMPREHENSIVE LINE-BY-LINE DIAGNOSTIC

This traces EXACTLY what happens during Remove Rows If execution
and multi-sheet tracking to identify the true root cause.
"""

import pandas as pd
import numpy as np
from operations.data_ops import RemoveRowsIfOperation
from engine.executor import OperationExecutor

def analyze_value(value, idx):
    """Analyze a single value in detail"""
    info = {
        'index': idx,
        'value': value,
        'repr': repr(value),
        'type': type(value).__name__,
        'is_na': pd.isna(value),
        'is_none': value is None,
    }

    if not pd.isna(value) and value is not None:
        str_val = str(value).strip()
        info['str_value'] = str_val
        info['str_len'] = len(str_val)
        info['is_empty_str'] = str_val == ''
        info['is_null_str'] = str_val in ['nan', 'None', 'NaT', '<NA>']
    else:
        info['str_value'] = None
        info['str_len'] = 0
        info['is_empty_str'] = False
        info['is_null_str'] = False

    return info

def deep_diagnostic():
    """Run comprehensive diagnostic"""

    print("=" * 100)
    print("COMPREHENSIVE LINE-BY-LINE DIAGNOSTIC - Remove Rows If Operation")
    print("=" * 100)

    # Load actual file
    filename = "Volunteer Directors 11.20.25.xlsx"
    print(f"\n[STEP 1] Loading file: {filename}")
    df_original = pd.read_excel(filename)
    print(f"  Loaded: {len(df_original):,} rows × {len(df_original.columns)} columns")

    # Focus on Person Street column
    print(f"\n[STEP 2] Analyzing Person Street column")
    person_street = df_original['Person Street'].copy()

    print(f"  Total values: {len(person_street)}")
    print(f"  Data type: {person_street.dtype}")
    print(f"  Memory usage: {person_street.memory_usage(deep=True)} bytes")

    # Count value types
    na_count = person_street.isna().sum()
    none_count = (person_street == None).sum()

    print(f"\n  Value type breakdown:")
    print(f"    pd.isna() = True: {na_count}")
    print(f"    value is None: {none_count}")

    # Analyze a sample of values
    print(f"\n[STEP 3] Detailed analysis of first 30 values")
    print(f"  {'Idx':<6} {'IsNA':<6} {'IsNone':<8} {'Type':<10} {'Repr':<40} {'StrVal':<30}")
    print(f"  {'-'*6} {'-'*6} {'-'*8} {'-'*10} {'-'*40} {'-'*30}")

    for idx in range(min(30, len(person_street))):
        val = person_street.iloc[idx]
        info = analyze_value(val, idx)
        str_display = info['str_value'] if info['str_value'] is not None else '(None)'
        print(f"  {info['index']:<6} {str(info['is_na']):<6} {str(info['is_none']):<8} "
              f"{info['type']:<10} {info['repr']:<40} {str_display:<30}")

    # Test is_blank logic step by step
    print(f"\n[STEP 4] Testing is_blank logic step-by-step")

    print(f"\n  4a) Checking pd.isna():")
    is_na = person_street.isna()
    print(f"      Count where is_na = True: {is_na.sum()}")
    print(f"      First 10 indices where is_na = True: {list(is_na[is_na].head(10).index)}")

    print(f"\n  4b) Converting to string and stripping:")
    str_values = person_street.astype(str).str.strip()
    print(f"      Sample conversions (first 10):")
    for idx in range(min(10, len(person_street))):
        orig = person_street.iloc[idx]
        conv = str_values.iloc[idx]
        print(f"        [{idx}] {repr(orig):<25} → {repr(conv):<25}")

    print(f"\n  4c) Checking for null-like strings:")
    is_empty_or_null_string = str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    print(f"      Count where is_empty_or_null_string = True: {is_empty_or_null_string.sum()}")
    print(f"      First 10 indices: {list(is_empty_or_null_string[is_empty_or_null_string].head(10).index)}")

    print(f"\n  4d) Combining with OR logic:")
    is_blank = is_na | is_empty_or_null_string
    print(f"      Count where is_blank = True: {is_blank.sum()}")
    print(f"      Count where is_blank = False: {(~is_blank).sum()}")

    print(f"\n  4e) Creating keep mask (NOT blank):")
    mask = ~is_blank
    print(f"      Count where mask = True (KEEP): {mask.sum()}")
    print(f"      Count where mask = False (REMOVE): {(~mask).sum()}")

    # Apply the mask directly
    print(f"\n[STEP 5] Applying mask directly (without operation)")
    df_direct = df_original[mask].copy()
    print(f"  Result: {len(df_direct)} rows")
    print(f"  Removed: {len(df_original) - len(df_direct)} rows")

    # Check if result has any blanks
    result_person_street = df_direct['Person Street']
    result_is_na = result_person_street.isna()
    result_str = result_person_street.astype(str).str.strip()
    result_is_empty = result_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    result_blank = result_is_na | result_is_empty

    print(f"\n  Verification of result:")
    print(f"    Blank values in result: {result_blank.sum()}")
    if result_blank.sum() > 0:
        print(f"    ERROR: Result contains blank values!")
    else:
        print(f"    ✓ Result contains NO blank values")

    # Now test with the actual operation
    print(f"\n[STEP 6] Testing with RemoveRowsIfOperation")
    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank'
    }

    df_before_op = df_original.copy()
    print(f"  Input: {len(df_before_op)} rows")
    print(f"  Input indices: {list(df_before_op.index[:10])}... (first 10)")

    df_after_op = operation.execute(df_before_op, params)
    print(f"  Output: {len(df_after_op)} rows")
    print(f"  Output indices: {list(df_after_op.index[:10])}... (first 10)")
    print(f"  Removed: {len(df_before_op) - len(df_after_op)} rows")

    # Compare indices
    before_indices = set(df_before_op.index)
    after_indices = set(df_after_op.index)
    removed_by_operation = before_indices - after_indices

    print(f"\n  Index analysis:")
    print(f"    Before: {len(before_indices)} indices")
    print(f"    After: {len(after_indices)} indices")
    print(f"    Removed indices count: {len(removed_by_operation)}")
    print(f"    Removed indices (first 20): {sorted(list(removed_by_operation))[:20]}")

    # Check what was actually removed
    if len(removed_by_operation) > 0:
        actually_removed = df_before_op.loc[list(removed_by_operation), 'Person Street']

        print(f"\n  Analyzing what was removed:")
        removed_is_na = actually_removed.isna()
        removed_str = actually_removed.astype(str).str.strip()
        removed_is_empty = removed_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        removed_blank = removed_is_na | removed_is_empty

        print(f"    Removed rows that are blank: {removed_blank.sum()}")
        print(f"    Removed rows that are NON-blank: {(~removed_blank).sum()}")

        if (~removed_blank).sum() > 0:
            print(f"\n    ERROR: Operation removed {(~removed_blank).sum()} NON-BLANK rows!")
            print(f"    Examples of non-blank values that were removed:")
            non_blank_removed = actually_removed[~removed_blank].head(10)
            for idx, val in non_blank_removed.items():
                print(f"      [{idx}] {repr(val)}")
        else:
            print(f"    ✓ Operation only removed blank rows")

    # Test with executor tracking
    print(f"\n[STEP 7] Testing with OperationExecutor.execute_queue_with_tracking()")
    executor = OperationExecutor()
    operations = [{
        'operation_id': 'data_remove_rows_if',
        'parameters': {
            'column': 'Person Street',
            'condition': 'is_blank'
        },
        'enabled': True
    }]

    df_input = df_original.copy()
    print(f"  Input: {len(df_input)} rows")

    result_df, removed_df = executor.execute_queue_with_tracking(df_input, operations)

    print(f"  Result: {len(result_df)} rows")
    print(f"  Removed sheet: {len(removed_df)} rows")

    # Verify result sheet
    print(f"\n  Verifying Result sheet:")
    result_person_street = result_df['Person Street']
    result_is_na = result_person_street.isna()
    result_str = result_person_street.astype(str).str.strip()
    result_is_empty = result_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    result_blank = result_is_na | result_is_empty

    print(f"    Blank values in Result: {result_blank.sum()}")
    if result_blank.sum() > 0:
        print(f"    ERROR: Result contains {result_blank.sum()} blank values!")
    else:
        print(f"    ✓ Result contains NO blank values")

    # Verify removed sheet
    print(f"\n  Verifying Removed sheet:")
    if not removed_df.empty and 'Person Street' in removed_df.columns:
        removed_person_street = removed_df['Person Street']
        removed_is_na = removed_person_street.isna()
        removed_str = removed_person_street.astype(str).str.strip()
        removed_is_empty = removed_str.isin(['', 'nan', 'None', 'NaT', '<NA>'])
        removed_blank = removed_is_na | removed_is_empty

        print(f"    Blank values in Removed: {removed_blank.sum()}")
        print(f"    NON-blank values in Removed: {(~removed_blank).sum()}")

        if (~removed_blank).sum() > 0:
            print(f"\n    ERROR: Removed sheet contains {(~removed_blank).sum()} NON-BLANK rows!")
            print(f"    These are FALSE POSITIVES!")
            print(f"\n    Examples of false positives (first 20):")
            false_positives = removed_df[~removed_blank].head(20)
            for idx, row in false_positives.iterrows():
                addr = row['Person Street']
                print(f"      {repr(addr)}")

            return False
        else:
            print(f"    ✓ Removed sheet contains ONLY blank values")
    else:
        print(f"    Removed sheet is empty or missing Person Street column")

    # Final summary
    print(f"\n{'='*100}")
    print("DIAGNOSTIC SUMMARY")
    print("=" * 100)

    print(f"\nInput file: {len(df_original)} rows")
    print(f"Expected to remove (blank): {is_blank.sum()} rows")
    print(f"Expected to keep (non-blank): {(~is_blank).sum()} rows")

    print(f"\nActual operation results:")
    print(f"  Operation removed: {len(df_before_op) - len(df_after_op)} rows")
    print(f"  Operation kept: {len(df_after_op)} rows")

    print(f"\nExecutor tracking results:")
    print(f"  Result sheet: {len(result_df)} rows")
    print(f"  Removed sheet: {len(removed_df)} rows")
    print(f"  Total accounted: {len(result_df) + len(removed_df)} rows")

    # Check for discrepancies
    errors = []

    if len(df_after_op) != (~is_blank).sum():
        errors.append(f"Operation kept {len(df_after_op)} rows, expected {(~is_blank).sum()}")

    if len(result_df) != (~is_blank).sum():
        errors.append(f"Result sheet has {len(result_df)} rows, expected {(~is_blank).sum()}")

    if len(removed_df) != is_blank.sum():
        errors.append(f"Removed sheet has {len(removed_df)} rows, expected {is_blank.sum()}")

    if len(result_df) + len(removed_df) != len(df_original):
        errors.append(f"Row count mismatch: {len(result_df)} + {len(removed_df)} != {len(df_original)}")

    if errors:
        print(f"\n✗ ERRORS DETECTED:")
        for error in errors:
            print(f"  • {error}")
        return False
    else:
        print(f"\n✓ ALL CHECKS PASSED")
        return True

if __name__ == '__main__':
    success = deep_diagnostic()
    exit(0 if success else 1)
