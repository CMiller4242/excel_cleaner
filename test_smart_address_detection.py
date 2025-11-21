"""
Test the new smart address detection logic

When checking "Person Street is_blank", it should now also check
"Company Street Address" and only remove if ALL address columns are blank.
"""
import pandas as pd
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation

df = pd.read_excel('Volunteer Directors 11.20.25.xlsx')

print("=" * 100)
print("TESTING NEW SMART ADDRESS DETECTION")
print("=" * 100)

print(f"\nTotal rows: {len(df):,}")
print(f"Person Street - Blank: {df['Person Street'].isna().sum():,}, Valid: {df['Person Street'].notna().sum():,}")
print(f"Company Street Address - Blank: {df['Company Street Address'].isna().sum():,}, Valid: {df['Company Street Address'].notna().sum():,}")

# Test the operation
operation = RemoveRowsIfOperation()
params = {
    'column': 'Person Street',
    'condition': 'is_blank',
    'enhanced_blank_detection': False  # Standard mode
}

print(f"\nExecuting 'Remove Rows If (Person Street is_blank)' with smart detection...")
result = operation.execute(df, params)

removed_indices = set(df.index) - set(result.index)
removed = df.loc[list(removed_indices)]

print(f"\nResults:")
print(f"  Input: {len(df):,} rows")
print(f"  Kept: {len(result):,} rows")
print(f"  Removed: {len(removed):,} rows")

# Analyze what was kept
person_street_in_kept = result['Person Street'].notna().sum()
company_street_in_kept = result['Company Street Address'].notna().sum()
any_address_in_kept = (result['Person Street'].notna() | result['Company Street Address'].notna()).sum()

print(f"\nKept rows breakdown:")
print(f"  Has Person Street: {person_street_in_kept:,}")
print(f"  Has Company Street: {company_street_in_kept:,}")
print(f"  Has ANY address: {any_address_in_kept:,}")

# Analyze what was removed
person_street_in_removed = removed['Person Street'].notna().sum()
company_street_in_removed = removed['Company Street Address'].notna().sum()
any_address_in_removed = (removed['Person Street'].notna() | removed['Company Street Address'].notna()).sum()

print(f"\nRemoved rows breakdown:")
print(f"  Has Person Street: {person_street_in_removed:,}")
print(f"  Has Company Street: {company_street_in_removed:,}")
print(f"  Has ANY address: {any_address_in_removed:,}")

# Check against user expectations
print(f"\n{'=' * 100}")
print("COMPARISON TO USER EXPECTATIONS")
print(f"{'=' * 100}")

print(f"\nUser expected:")
print(f"  Kept: 1,450-1,550 rows")
print(f"  Removed: 500-550 rows")

print(f"\nActual results:")
print(f"  Kept: {len(result):,} rows")
print(f"  Removed: {len(removed):,} rows")

matches_expectation = (1450 <= len(result) <= 1550) and (500 <= len(removed) <= 550)

print(f"\nMatches expectation: {'✓ YES' if matches_expectation else '✗ NO'}")

if not matches_expectation:
    print(f"\nAnalyzing discrepancy...")
    if any_address_in_removed > 0:
        print(f"  WARNING: {any_address_in_removed} rows with addresses were removed!")
        print(f"  Examples of removed rows with Company addresses:")
        removed_with_company = removed[removed['Company Street Address'].notna()]
        for idx in removed_with_company.head(5).index:
            company_addr = removed_with_company.loc[idx, 'Company Street Address']
            person_addr = removed_with_company.loc[idx, 'Person Street']
            print(f"    Row {idx}: Person={repr(person_addr)}, Company={repr(company_addr)}")

# Show sample of what's in kept
print(f"\n{'=' * 100}")
print("SAMPLE OF KEPT ROWS")
print(f"{'=' * 100}")
for idx in result.head(10).index:
    person = result.loc[idx, 'Person Street']
    company = result.loc[idx, 'Company Street Address']
    print(f"Row {idx}: Person={repr(person)[:30]}, Company={repr(company)[:30]}")

print(f"\n{'=' * 100}")
if matches_expectation:
    print("✅ SUCCESS - Results match user expectations!")
else:
    print("❌ STILL NOT MATCHING - Need more investigation")
print(f"{'=' * 100}")
