"""Analyze exported files to check for false positives in Removed sheet"""
import pandas as pd

print("="*80)
print("Analyzing TEST_EXPORT_DEBUG.xlsx")
print("="*80)

try:
    # Read the Results and Removed sheets
    xls = pd.ExcelFile('TEST_EXPORT_DEBUG.xlsx')
    print(f"Sheet names: {xls.sheet_names}\n")

    if 'Results' in xls.sheet_names:
        results_df = pd.read_excel('TEST_EXPORT_DEBUG.xlsx', sheet_name='Results')
        print(f"Results sheet: {len(results_df)} rows")

        if 'Person Street' in results_df.columns:
            print(f"  Person Street - NaN: {results_df['Person Street'].isna().sum()}, Non-NaN: {results_df['Person Street'].notna().sum()}")

            # Check for any blanks that shouldn't be there
            nan_in_results = results_df[results_df['Person Street'].isna()]
            if len(nan_in_results) > 0:
                print(f"  ⚠️  WARNING: {len(nan_in_results)} rows with blank Person Street in Results sheet!")

    if 'Removed' in xls.sheet_names:
        removed_df = pd.read_excel('TEST_EXPORT_DEBUG.xlsx', sheet_name='Removed')
        print(f"\nRemoved sheet: {len(removed_df)} rows")

        if 'Person Street' in removed_df.columns:
            print(f"  Person Street - NaN: {removed_df['Person Street'].isna().sum()}, Non-NaN: {removed_df['Person Street'].notna().sum()}")

            # Check for false positives (valid addresses in Removed sheet)
            valid_in_removed = removed_df[removed_df['Person Street'].notna()]
            if len(valid_in_removed) > 0:
                print(f"  ⚠️  BUG FOUND: {len(valid_in_removed)} rows with VALID Person Street in Removed sheet!")
                print(f"\n  Examples of valid addresses in Removed sheet:")
                for idx, row in valid_in_removed.head(20).iterrows():
                    val = row['Person Street']
                    print(f"    Row {idx}: '{val}'")

                # Check if these are actually empty strings or whitespace
                non_empty = valid_in_removed[valid_in_removed['Person Street'].astype(str).str.strip() != '']
                print(f"\n  Of which {len(non_empty)} are non-empty strings")
            else:
                print(f"  ✅ All removed rows have blank Person Street")

        # Check for _Removed_By column to see which operation removed them
        if '_Removed_By' in removed_df.columns:
            print(f"\nRemoval reasons:")
            print(removed_df['_Removed_By'].value_counts())

            # Check if valid addresses were removed by specific operations
            if 'Person Street' in removed_df.columns:
                valid_removed_by_op = removed_df[removed_df['Person Street'].notna()].groupby('_Removed_By').size()
                if len(valid_removed_by_op) > 0:
                    print(f"\nValid addresses removed by operation:")
                    for op, count in valid_removed_by_op.items():
                        print(f"  {op}: {count} valid addresses")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Analyzing TEST_GUI_SIMULATION_EXPORT.xlsx")
print("="*80)

try:
    xls2 = pd.ExcelFile('TEST_GUI_SIMULATION_EXPORT.xlsx')
    print(f"Sheet names: {xls2.sheet_names}\n")

    if 'Results' in xls2.sheet_names:
        results_df2 = pd.read_excel('TEST_GUI_SIMULATION_EXPORT.xlsx', sheet_name='Results')
        print(f"Results sheet: {len(results_df2)} rows")

        if 'Person Street' in results_df2.columns:
            print(f"  Person Street - NaN: {results_df2['Person Street'].isna().sum()}, Non-NaN: {results_df2['Person Street'].notna().sum()}")

    if 'Removed' in xls2.sheet_names:
        removed_df2 = pd.read_excel('TEST_GUI_SIMULATION_EXPORT.xlsx', sheet_name='Removed')
        print(f"\nRemoved sheet: {len(removed_df2)} rows")

        if 'Person Street' in removed_df2.columns:
            print(f"  Person Street - NaN: {removed_df2['Person Street'].isna().sum()}, Non-NaN: {removed_df2['Person Street'].notna().sum()}")

            valid_in_removed2 = removed_df2[removed_df2['Person Street'].notna()]
            if len(valid_in_removed2) > 0:
                print(f"  ⚠️  BUG FOUND: {len(valid_in_removed2)} rows with VALID Person Street in Removed sheet!")
                print(f"\n  Examples:")
                for idx, row in valid_in_removed2.head(10).iterrows():
                    val = row['Person Street']
                    print(f"    '{val}'")
            else:
                print(f"  ✅ All removed rows have blank Person Street")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
