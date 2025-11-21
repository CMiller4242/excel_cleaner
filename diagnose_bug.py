"""
Diagnostic script to identify the root cause of the blank detection bug
"""
import pandas as pd
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation
from engine.executor import OperationExecutor

# Load the actual data file
print("Loading data file...")
df = pd.read_excel('Volunteer Directors 11.20.25(2).xlsx')
print(f"Original DataFrame: {len(df)} rows\n")

# Check the Person Street column
person_street = df['Person Street']
print("Person Street column statistics:")
print(f"  Total values: {len(person_street)}")
print(f"  NaN values: {person_street.isna().sum()}")
print(f"  Non-NaN values: {person_street.notna().sum()}")
print(f"  Empty string values: {(person_street == '').sum()}")
print(f"  Non-empty strings: {((person_street.notna()) & (person_street.astype(str).str.strip() != '')).sum()}")
print()

# Show sample non-NaN values
non_nan_values = person_street[person_street.notna()]
print(f"Sample non-NaN Person Street values (first 10):")
for idx, val in non_nan_values.head(10).items():
    print(f"  Index {idx}: '{val}' (type: {type(val).__name__}, len: {len(str(val)) if pd.notna(val) else 'N/A'})")
print()

# Now test the RemoveRowsIfOperation in STANDARD mode
print("="*80)
print("TEST 1: STANDARD MODE (enhanced_blank_detection=False)")
print("="*80)

operation = RemoveRowsIfOperation()
params = {
    'column': 'Person Street',
    'condition': 'is_blank',
    'enhanced_blank_detection': False
}

# Execute the operation
result_df = operation.execute(df.copy(), params)

print(f"\nResults:")
print(f"  Before: {len(df)} rows")
print(f"  After: {len(result_df)} rows")
print(f"  Removed: {len(df) - len(result_df)} rows")

# Identify which rows were removed
removed_indices = set(df.index) - set(result_df.index)
removed_df = df.loc[list(removed_indices)]

print(f"\nRemoved rows analysis:")
print(f"  Total removed: {len(removed_df)}")
print(f"  Removed with NaN in Person Street: {removed_df['Person Street'].isna().sum()}")
print(f"  Removed with non-NaN in Person Street: {removed_df['Person Street'].notna().sum()}")

# Check for false positives (non-NaN values that were removed)
false_positives = removed_df[removed_df['Person Street'].notna()]
if len(false_positives) > 0:
    print(f"\n⚠️  CRITICAL BUG DETECTED: {len(false_positives)} non-NaN values were removed!")
    print(f"\nExamples of incorrectly removed addresses:")
    for idx, row in false_positives.head(20).iterrows():
        val = row['Person Street']
        print(f"  Index {idx}: '{val}' (type: {type(val).__name__}, is_blank={pd.isna(val)}, str_len={len(str(val))})")
else:
    print(f"\n✅ No false positives detected - all removed rows have NaN in Person Street")

print()
print("="*80)
print("TEST 2: ENHANCED MODE (enhanced_blank_detection=True)")
print("="*80)

params_enhanced = {
    'column': 'Person Street',
    'condition': 'is_blank',
    'enhanced_blank_detection': True
}

result_df_enhanced = operation.execute(df.copy(), params_enhanced)

print(f"\nResults:")
print(f"  Before: {len(df)} rows")
print(f"  After: {len(result_df_enhanced)} rows")
print(f"  Removed: {len(df) - len(result_df_enhanced)} rows")

removed_indices_enhanced = set(df.index) - set(result_df_enhanced.index)
removed_df_enhanced = df.loc[list(removed_indices_enhanced)]

print(f"\nRemoved rows analysis:")
print(f"  Total removed: {len(removed_df_enhanced)}")
print(f"  Removed with NaN: {removed_df_enhanced['Person Street'].isna().sum()}")
print(f"  Removed with non-NaN: {removed_df_enhanced['Person Street'].notna().sum()}")

false_positives_enhanced = removed_df_enhanced[removed_df_enhanced['Person Street'].notna()]
if len(false_positives_enhanced) > 0:
    print(f"\n⚠️  BUG IN ENHANCED MODE: {len(false_positives_enhanced)} non-NaN values removed")
    # Check if they're legitimate (empty strings, N/A, etc.)
    non_empty_removed = false_positives_enhanced[
        (false_positives_enhanced['Person Street'].astype(str).str.strip() != '') &
        (~false_positives_enhanced['Person Street'].astype(str).str.lower().isin(['n/a', 'na', 'null', 'none']))
    ]
    if len(non_empty_removed) > 0:
        print(f"  Of which {len(non_empty_removed)} are ACTUAL valid addresses (BUG!)")
        print(f"\n  Examples:")
        for idx, row in non_empty_removed.head(10).iterrows():
            val = row['Person Street']
            print(f"    Index {idx}: '{val}'")
else:
    print(f"\n✅ Enhanced mode working correctly")

print()
print("="*80)
print("TEST 3: Testing with OperationExecutor (tracks removed rows)")
print("="*80)

executor = OperationExecutor()
operations = [{
    'operation_id': 'data_remove_rows_if',
    'parameters': {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': False
    },
    'enabled': True
}]

result_with_tracking, removed_with_tracking = executor.execute_queue_with_tracking(df.copy(), operations)

print(f"\nExecutor Results:")
print(f"  Result rows: {len(result_with_tracking)}")
print(f"  Removed rows: {len(removed_with_tracking)}")

if len(removed_with_tracking) > 0:
    print(f"\nRemoved rows Person Street analysis:")
    print(f"  NaN: {removed_with_tracking['Person Street'].isna().sum()}")
    print(f"  Non-NaN: {removed_with_tracking['Person Street'].notna().sum()}")

    fp_in_removed = removed_with_tracking[removed_with_tracking['Person Street'].notna()]
    if len(fp_in_removed) > 0:
        print(f"\n⚠️  EXECUTOR BUG: {len(fp_in_removed)} non-NaN values in removed sheet")
        print(f"\n  Examples from Removed sheet:")
        for idx, row in fp_in_removed.head(10).iterrows():
            val = row['Person Street']
            print(f"    '{val}' (type: {type(val).__name__})")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
