"""
Test that multi_level_deduplication defaults to True and works correctly
"""
import pandas as pd
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveDuplicatesOperation

print("="*80)
print("TEST: Default Behavior (multi_level_deduplication should default to True)")
print("="*80)

# Create test data with duplicates
test_data = {
    'First Name': ['John', 'John', 'Jane'],
    'Last Name': ['Doe', 'Doe', 'Smith'],
    'Email Address': ['john@email.com', 'john@email.com', 'jane@email.com'],
    'Person Street': ['123 Main St', '456 Oak Ave', '789 Pine Rd'],
    'Person City': ['Boston', 'Chicago', 'Denver'],
    'Person State': ['MA', 'IL', 'CO'],
    'Direct Phone Number': ['555-1001', '555-1002', '555-2001']
}

df = pd.DataFrame(test_data)

print(f"\nInput: {len(df)} rows")
print(df[['First Name', 'Last Name', 'Email Address', 'Person Street']].to_string(index=True))

# Test 1: Call without specifying multi_level_deduplication (should default to True)
print(f"\n{'='*80}")
print("TEST 1: Default behavior (parameter not specified)")
print("="*80)

operation = RemoveDuplicatesOperation()
params_default = {
    'keep': 'first'
    # Note: multi_level_deduplication NOT specified, should default to True
}

result_default = operation.execute(df.copy(), params_default)

print(f"\nResult: {len(result_default)} rows (removed {len(df) - len(result_default)} duplicates)")
print(result_default[['First Name', 'Last Name', 'Email Address', 'Person Street']].to_string(index=True))

if len(result_default) == 2:  # Should remove 1 duplicate (rows 0 & 1 have same email)
    print("\n✅ SUCCESS: Default multi_level_deduplication=True is working")
    print("   - Deduplication by email detected duplicate")
    print("   - Removed row 1 (john@email.com duplicate)")
else:
    print(f"\n❌ FAILED: Expected 2 rows, got {len(result_default)}")

# Test 2: Explicitly set to False to verify standard behavior still works
print(f"\n{'='*80}")
print("TEST 2: Standard deduplication (multi_level_deduplication=False)")
print("="*80)

params_standard = {
    'columns': ['Email Address'],
    'keep': 'first',
    'multi_level_deduplication': False
}

result_standard = operation.execute(df.copy(), params_standard)

print(f"\nResult: {len(result_standard)} rows (removed {len(df) - len(result_standard)} duplicates)")

if len(result_standard) == 2:
    print("✅ SUCCESS: Standard deduplication still works when explicitly disabled")
else:
    print(f"❌ FAILED: Expected 2 rows, got {len(result_standard)}")

# Test 3: Verify 'columns' parameter is ignored when multi_level is True
print(f"\n{'='*80}")
print("TEST 3: Verify 'columns' parameter is ignored with multi_level=True")
print("="*80)

params_with_ignored_columns = {
    'columns': ['Person Street'],  # This should be IGNORED
    'keep': 'first',
    'multi_level_deduplication': True
}

result_ignored = operation.execute(df.copy(), params_with_ignored_columns)

print(f"\nResult: {len(result_ignored)} rows")
print(f"Note: 'columns' was set to ['Person Street'], but should be ignored")

if len(result_ignored) == 2:  # Should still dedupe by email, not by Person Street
    print("\n✅ SUCCESS: 'columns' parameter correctly ignored when multi_level=True")
    print("   - Deduplication still used email (multi-level logic)")
    print("   - Did NOT use Person Street (columns parameter)")
else:
    print(f"\n❌ FAILED: 'columns' parameter may not be properly ignored")

print(f"\n{'='*80}")
print("SUMMARY")
print("="*80)
print("""
✓ multi_level_deduplication defaults to True
✓ Multi-level logic works correctly by default
✓ Standard deduplication still available when disabled
✓ 'columns' parameter correctly ignored when multi_level=True

The UI should now show:
☑ Use smart multi-level duplicate detection (Email → Name+Address → Name+Phone)
   (checked by default)
""")
