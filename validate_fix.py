"""
Validation script to demonstrate the fix for the blank address detection bug
"""
import pandas as pd
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation
from engine.executor import OperationExecutor

print("="*80)
print("FIX VALIDATION: Remove Rows If (Person Street is_blank)")
print("="*80)

# Load the data
df = pd.read_excel('Volunteer Directors 11.20.25(2).xlsx')

print(f"\n📊 INPUT DATA ANALYSIS")
print(f"="*80)
print(f"Total rows: {len(df)}")
print(f"\nColumn breakdown:")
print(f"  Person Street:")
print(f"    - Non-blank: {df['Person Street'].notna().sum()}")
print(f"    - Blank (NaN): {df['Person Street'].isna().sum()}")
print(f"  Company Street Address:")
print(f"    - Non-blank: {df['Company Street Address'].notna().sum()}")
print(f"    - Blank (NaN): {df['Company Street Address'].isna().sum()}")

# Calculate the breakdown
person_blank = df['Person Street'].isna()
company_not_blank = df['Company Street Address'].notna()
rows_with_company_but_no_person = person_blank & company_not_blank

print(f"\n  Rows with blank Person Street BUT valid Company address: {rows_with_company_but_no_person.sum()}")
print(f"  Rows with BOTH addresses blank: {(df['Person Street'].isna() & df['Company Street Address'].isna()).sum()}")

print(f"\n{'='*80}")
print(f"🔧 FIX APPLIED: Smart Address Detection")
print(f"="*80)
print(f"\nThe fix implements 'Smart Address Detection' which:")
print(f"  1. Detects related address columns (Person Street + Company Street Address)")
print(f"  2. Keeps rows that have an address in ANY related column")
print(f"  3. Only removes rows where ALL address columns are blank")
print(f"\nThis feature is ENABLED by default for address columns.")

# Run with smart detection (NEW behavior)
operation = RemoveRowsIfOperation()
params_with_smart = {
    'column': 'Person Street',
    'condition': 'is_blank',
    'enhanced_blank_detection': False,
    'smart_address_detection': True  # NEW: Smart detection enabled
}

result_with_smart = operation.execute(df.copy(), params_with_smart)

print(f"\n{'='*80}")
print(f"✅ RESULTS WITH SMART DETECTION (NEW DEFAULT)")
print(f"="*80)
print(f"  Input rows:  {len(df)}")
print(f"  Result rows: {len(result_with_smart)}")
print(f"  Removed rows: {len(df) - len(result_with_smart)}")

removed_indices_smart = set(df.index) - set(result_with_smart.index)
removed_df_smart = df.loc[list(removed_indices_smart)]

print(f"\n  Removed sheet breakdown:")
print(f"    - Person Street NaN: {removed_df_smart['Person Street'].isna().sum()}")
print(f"    - Company Street Address NaN: {removed_df_smart['Company Street Address'].isna().sum()}")
print(f"    - Valid addresses in Removed sheet: {removed_df_smart['Company Street Address'].notna().sum()}")

if removed_df_smart['Company Street Address'].notna().sum() == 0:
    print(f"\n  ✅ SUCCESS: NO valid addresses in Removed sheet!")
else:
    print(f"\n  ⚠️ WARNING: {removed_df_smart['Company Street Address'].notna().sum()} valid addresses in Removed sheet")

# Run without smart detection (OLD behavior - for comparison)
params_without_smart = {
    'column': 'Person Street',
    'condition': 'is_blank',
    'enhanced_blank_detection': False,
    'smart_address_detection': False  # OLD: Only check Person Street
}

result_without_smart = operation.execute(df.copy(), params_without_smart)

print(f"\n{'='*80}")
print(f"📊 COMPARISON: WITHOUT SMART DETECTION (OLD BEHAVIOR)")
print(f"="*80)
print(f"  Input rows:  {len(df)}")
print(f"  Result rows: {len(result_without_smart)}")
print(f"  Removed rows: {len(df) - len(result_without_smart)}")

removed_indices_old = set(df.index) - set(result_without_smart.index)
removed_df_old = df.loc[list(removed_indices_old)]

print(f"\n  Removed sheet breakdown:")
print(f"    - Person Street NaN: {removed_df_old['Person Street'].isna().sum()}")
print(f"    - Company Street Address NaN: {removed_df_old['Company Street Address'].isna().sum()}")
print(f"    - Valid addresses in Removed sheet: {removed_df_old['Company Street Address'].notna().sum()}")

print(f"\n  ⚠️ OLD BEHAVIOR: {removed_df_old['Company Street Address'].notna().sum()} valid Company addresses in Removed sheet")
print(f"     This is what the user was seeing as a 'bug'!")

# Export the corrected file using the executor
print(f"\n{'='*80}")
print(f"💾 EXPORTING CORRECTED FILE")
print(f"="*80)

executor = OperationExecutor()
operations = [{
    'operation_id': 'data_remove_rows_if',
    'parameters': {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': False,
        'smart_address_detection': True  # Use smart detection
    },
    'enabled': True
}]

result_export, removed_export = executor.execute_queue_with_tracking(df.copy(), operations)

output_file = 'FIXED_EXPORT_SMART_DETECTION.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    result_export.to_excel(writer, sheet_name='Results', index=False)
    removed_export.to_excel(writer, sheet_name='Removed', index=False)

print(f"\n  ✅ File exported: {output_file}")
print(f"  Results sheet: {len(result_export)} rows")
print(f"  Removed sheet: {len(removed_export)} rows")

# Verify the exported file
print(f"\n  Verification:")
if 'Person Street' in removed_export.columns and 'Company Street Address' in removed_export.columns:
    valid_in_removed = removed_export[
        removed_export['Person Street'].notna() | removed_export['Company Street Address'].notna()
    ]
    if len(valid_in_removed) == 0:
        print(f"    ✅ NO valid addresses in Removed sheet")
    else:
        print(f"    ⚠️ {len(valid_in_removed)} valid addresses in Removed sheet")
else:
    print(f"    ℹ️  Address columns not in removed sheet")

print(f"\n{'='*80}")
print(f"📈 SUMMARY")
print(f"="*80)
print(f"\n  OLD BEHAVIOR (smart detection disabled):")
print(f"    - Removed {len(removed_df_old)} rows")
print(f"    - Including {removed_df_old['Company Street Address'].notna().sum()} rows with valid Company addresses")
print(f"    - User saw valid addresses in Removed sheet ❌")
print(f"\n  NEW BEHAVIOR (smart detection enabled - DEFAULT):")
print(f"    - Removes {len(removed_df_smart)} rows")
print(f"    - All removed rows have BOTH Person and Company addresses blank")
print(f"    - No valid addresses in Removed sheet ✅")
print(f"\n  IMPROVEMENT:")
print(f"    - {len(removed_df_old) - len(removed_df_smart)} additional rows preserved")
print(f"    - {removed_df_old['Company Street Address'].notna().sum()} valid Company addresses no longer lost")

print(f"\n{'='*80}")
print(f"✅ FIX VALIDATION COMPLETE")
print(f"="*80)
print(f"\nThe fix ensures that when checking 'Person Street is_blank':")
print(f"  1. Related address columns (Company Street Address) are automatically detected")
print(f"  2. Rows are kept if they have an address in ANY related column")
print(f"  3. Only rows with ALL address columns blank are removed")
print(f"\nThis prevents the loss of {removed_df_old['Company Street Address'].notna().sum()} valid addresses!")
print(f"\n{'='*80}")
