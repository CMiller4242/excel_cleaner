"""
CRITICAL INVESTIGATION: What's really in the "NaN" rows?

The user reports that out of 1,255 "NaN" rows, 715-780 are actually VALID DATA!

Expected results should be:
- Valid addresses: 1,450-1,550 (not 782!)
- Actual NaN: 500-550 (not 1,255!)

Let's see what pandas isna() is incorrectly flagging as blank.
"""
import pandas as pd
import numpy as np

# Load file
df = pd.read_excel('Volunteer Directors 11.20.25.xlsx')

print("=" * 100)
print("CRITICAL INVESTIGATION: What's in the 'NaN' rows?")
print("=" * 100)

print(f"\nTotal rows: {len(df):,}")
print(f"Rows pandas says are NaN: {df['Person Street'].isna().sum():,}")
print(f"Rows pandas says are NOT NaN: {df['Person Street'].notna().sum():,}")

# Let's look at the raw values that pandas thinks are NaN
print(f"\n{'=' * 100}")
print("INVESTIGATING ROWS PANDAS MARKS AS NaN")
print(f"{'=' * 100}")

nan_rows = df[df['Person Street'].isna()]
print(f"\nFound {len(nan_rows):,} rows where pandas isna() returns True")

# But let's check what's ACTUALLY in those cells
print(f"\nLet's look at the RAW VALUES in these 'NaN' rows:")
print(f"(Showing first 50 values)\n")

for i, idx in enumerate(nan_rows.head(50).index):
    raw_val = df.at[idx, 'Person Street']
    val_type = type(raw_val)
    is_na = pd.isna(raw_val)

    # Try to convert to string to see what it looks like
    try:
        str_val = str(raw_val)
    except:
        str_val = "<error converting to string>"

    print(f"Row {idx}: isna()={is_na}, type={val_type.__name__}, str={repr(str_val)}")

    # Check if it's actually a valid address being misidentified
    if str_val not in ['nan', 'None', 'NaT', ''] and len(str_val) > 3:
        print(f"  ⚠️  WARNING: This looks like VALID DATA but isna() returned True!")

# Now let's check ALL the "NaN" rows for potential valid data
print(f"\n{'=' * 100}")
print("COUNTING VALID DATA IN 'NaN' ROWS")
print(f"{'=' * 100}")

valid_data_count = 0
actual_blank_count = 0
valid_examples = []

for idx in nan_rows.index:
    raw_val = df.at[idx, 'Person Street']

    # Try to determine if this is actually valid data
    try:
        str_val = str(raw_val)
        # If it converts to a non-empty string that's not a null representation
        if str_val not in ['nan', 'None', 'NaT', ''] and len(str_val.strip()) > 0:
            valid_data_count += 1
            if len(valid_examples) < 20:
                valid_examples.append(str_val)
        else:
            actual_blank_count += 1
    except:
        actual_blank_count += 1

print(f"\nResults of analyzing {len(nan_rows):,} 'NaN' rows:")
print(f"  Rows with VALID DATA: {valid_data_count:,} ⚠️")
print(f"  Rows that are ACTUALLY BLANK: {actual_blank_count:,}")

if valid_data_count > 0:
    print(f"\n  ❌ CRITICAL BUG CONFIRMED!")
    print(f"  pandas isna() is incorrectly flagging {valid_data_count:,} valid addresses as NaN!")
    print(f"\n  Examples of valid data incorrectly marked as NaN:")
    for ex in valid_examples:
        print(f"    - {repr(ex)}")

# Calculate what the ACTUAL expected values should be
total_valid = df['Person Street'].notna().sum() + valid_data_count
total_blank = len(df) - total_valid

print(f"\n{'=' * 100}")
print("CORRECT EXPECTED VALUES")
print(f"{'=' * 100}")
print(f"\nTotal rows: {len(df):,}")
print(f"ACTUAL valid addresses: {total_valid:,} (not 782!)")
print(f"ACTUAL blank rows: {total_blank:,} (not 1,255!)")

# Check the dtype of the column
print(f"\n{'=' * 100}")
print("COLUMN DTYPE ANALYSIS")
print(f"{'=' * 100}")
print(f"\nColumn dtype: {df['Person Street'].dtype}")
print(f"Column dtypes in DataFrame:")
print(df.dtypes)

# Check if there are any special values
print(f"\n{'=' * 100}")
print("UNIQUE VALUE ANALYSIS (first 30 'NaN' values)")
print(f"{'=' * 100}")

unique_nan_vals = []
for idx in nan_rows.head(100).index:
    val = df.at[idx, 'Person Street']
    str_val = str(val)
    if str_val not in unique_nan_vals:
        unique_nan_vals.append(str_val)
        if len(unique_nan_vals) <= 30:
            print(f"  {repr(str_val)}")

print(f"\n{'=' * 100}")
print("RECOMMENDATION")
print(f"{'=' * 100}")
print(f"""
The is_blank logic needs to be fixed to:
1. NOT rely on pandas isna() alone
2. Actually check if the cell contains valid string data
3. Only mark as blank if truly empty/null
""")
