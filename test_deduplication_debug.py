"""
Test multi-level deduplication with debug logging to see what's happening
"""
import pandas as pd
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

# Clear cache
for module in list(sys.modules.keys()):
    if module.startswith('operations'):
        del sys.modules[module]

from operations.data_ops import RemoveDuplicatesOperation

print("="*80)
print("TEST: Multi-Level Deduplication with DEBUG Logging")
print("="*80)

# Create test data with KNOWN duplicates
test_data = {
    'First Name': ['John', 'John', 'Jane', 'Jane', 'Bob'],
    'Last Name': ['Doe', 'Doe', 'Smith', 'Smith', 'Johnson'],
    'Email Address': [
        'john@example.com',   # Row 0
        'john@example.com',   # Row 1 - DUPLICATE of row 0 (same email)
        'jane@example.com',   # Row 2
        'jane@example.com',   # Row 3 - DUPLICATE of row 2 (same email)
        'bob@example.com'     # Row 4
    ],
    'Person Street': ['123 Main St', '456 Oak Ave', '789 Pine Rd', '101 Elm St', '202 Maple Dr'],
    'Person City': ['Boston', 'Chicago', 'Denver', 'Seattle', 'Portland'],
    'Person State': ['MA', 'IL', 'CO', 'WA', 'OR'],
    'Direct Phone Number': ['555-1001', '555-1002', '555-2001', '555-2002', '555-3001']
}

df = pd.DataFrame(test_data)

print(f"\n📊 TEST DATA: {len(df)} rows")
print(df[['First Name', 'Last Name', 'Email Address']].to_string(index=True))
print(f"\nExpected result: 3 rows (remove 2 duplicates - rows 1 and 3)")

# Test with multi-level deduplication
operation = RemoveDuplicatesOperation()
params = {
    'keep': 'first',
    'multi_level_deduplication': True
}

print(f"\n{'='*80}")
print(f"RUNNING OPERATION (check stderr for debug output)")
print(f"{'='*80}")

result = operation.execute(df.copy(), params)

print(f"\n📋 RESULT: {len(result)} rows")
print(result[['First Name', 'Last Name', 'Email Address']].to_string(index=True))

print(f"\n{'='*80}")
print(f"VERIFICATION:")
print(f"{'='*80}")

if len(result) == 3:
    print(f"✅ SUCCESS: Correctly removed 2 duplicates")
    print(f"   Expected: 3 rows")
    print(f"   Got: {len(result)} rows")
else:
    print(f"❌ FAILED: Expected 3 rows, got {len(result)}")
    print(f"   Input: {len(df)} rows")
    print(f"   Output: {len(result)} rows")
    print(f"   Removed: {len(df) - len(result)} rows")

# Check which rows were kept
kept_indices = sorted(result.index.tolist())
print(f"\nKept row indices: {kept_indices}")
print(f"Expected: [0, 2, 4]")

if kept_indices == [0, 2, 4]:
    print(f"✅ Correct rows kept (first occurrence of each email)")
else:
    print(f"❌ Unexpected rows kept")

print(f"\n{'='*80}")
print(f"Check the debug output above (stderr) to see execution details")
print(f"{'='*80}")
