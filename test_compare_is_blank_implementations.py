"""
Compare current is_blank implementation vs. suggested pd.isna() only implementation
"""
import pandas as pd
import numpy as np

def current_is_blank_logic(series):
    """Current implementation in operations/data_ops.py lines 220-229"""
    is_na = series.isna()
    str_values = series.astype(str).str.strip()
    is_empty_or_null_string = str_values.isin(['', 'nan', 'None', 'NaT', '<NA>'])
    is_blank = is_na | is_empty_or_null_string
    return is_blank

def suggested_is_blank_logic(series):
    """Suggested implementation: ONLY pd.isna()"""
    return series.isna()

# Test cases
test_data = {
    'Description': [
        'Valid address 1',
        'Valid address 2',
        'NaN value',
        'None value',
        'Empty string',
        'String "nan"',
        'String "None"',
        'Whitespace only',
        'Valid address 3',
    ],
    'Value': [
        "6600 N Lincoln Ave Ste 300",
        "2150 Post St",
        np.nan,
        None,
        "",
        "nan",  # Literal string "nan"
        "None",  # Literal string "None"
        "   ",
        "36 S State St",
    ]
}

df = pd.DataFrame(test_data)

print("=" * 100)
print("COMPARISON: Current Implementation vs. Suggested Implementation")
print("=" * 100)

current_blank = current_is_blank_logic(df['Value'])
suggested_blank = suggested_is_blank_logic(df['Value'])

print(f"\n{'Index':<6} {'Description':<20} {'Value':<30} {'Current':<12} {'Suggested':<12} {'Diff':<6}")
print("-" * 100)

for i in range(len(df)):
    desc = df.iloc[i]['Description']
    val = repr(df.iloc[i]['Value'])
    curr = current_blank.iloc[i]
    sugg = suggested_blank.iloc[i]
    diff = '✗' if curr != sugg else ''

    print(f"{i:<6} {desc:<20} {val:<30} {str(curr):<12} {str(sugg):<12} {diff:<6}")

print("\n" + "=" * 100)
print("ANALYSIS")
print("=" * 100)

differences = (current_blank != suggested_blank).sum()
print(f"\nDifferences found: {differences}")

if differences > 0:
    print("\nRows that would be treated differently:")
    diff_mask = current_blank != suggested_blank
    for i in df[diff_mask].index:
        desc = df.iloc[i]['Description']
        val = repr(df.iloc[i]['Value'])
        curr_removed = current_blank.iloc[i]
        sugg_removed = suggested_blank.iloc[i]
        print(f"  Row {i} ({desc}): {val}")
        print(f"    Current: {'REMOVE' if curr_removed else 'KEEP'}")
        print(f"    Suggested: {'REMOVE' if sugg_removed else 'KEEP'}")
        print()

# Now test with actual valid addresses
print("\n" + "=" * 100)
print("TESTING WITH VALID ADDRESSES ONLY")
print("=" * 100)

valid_addresses = pd.Series([
    "6600 N Lincoln Ave Ste 300",
    "2150 Post St",
    "4205 NW 6th St",
    "1718 Patterson St",
    "36 S State St",
])

current_valid_blank = current_is_blank_logic(valid_addresses)
suggested_valid_blank = suggested_is_blank_logic(valid_addresses)

print("\nAddress Testing:")
for i, addr in enumerate(valid_addresses):
    curr = current_valid_blank.iloc[i]
    sugg = suggested_valid_blank.iloc[i]
    status = '✗ BUG' if curr or sugg else '✓ OK'
    print(f"  {status} {repr(addr):<35} Current={curr}, Suggested={sugg}")

current_removes_valid = current_valid_blank.sum()
suggested_removes_valid = suggested_valid_blank.sum()

print(f"\nValid addresses incorrectly marked as blank:")
print(f"  Current implementation: {current_removes_valid}")
print(f"  Suggested implementation: {suggested_removes_valid}")

if current_removes_valid > 0:
    print("\n✗ BUG FOUND: Current implementation marks valid addresses as blank!")
elif suggested_removes_valid > 0:
    print("\n✗ BUG FOUND: Suggested implementation marks valid addresses as blank!")
else:
    print("\n✓ Both implementations correctly identify all valid addresses as NON-blank")
