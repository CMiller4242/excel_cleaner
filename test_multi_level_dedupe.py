"""
Test multi-level deduplication for RemoveDuplicatesOperation
"""
import pandas as pd
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveDuplicatesOperation

print("="*80)
print("TEST: Multi-Level Deduplication")
print("="*80)

# Create test data with various duplicate scenarios
test_data = {
    'First Name': [
        'John', 'John', 'John',      # Same person, different data completeness
        'Jane', 'Jane',              # Same email, duplicate
        'Bob', 'Bob',                # Same name+address, no email
        'Alice', 'Alice',            # Same name+phone, no email/address
        'Charlie',                   # Unique, has email
        'David',                     # Unique, no email but has address
        'Eve',                       # Unique, only name+phone
    ],
    'Last Name': [
        'Doe', 'Doe', 'Doe',
        'Smith', 'Smith',
        'Johnson', 'Johnson',
        'Williams', 'Williams',
        'Brown',
        'Davis',
        'Miller',
    ],
    'Email Address': [
        'john@example.com', 'john@example.com', None,  # First two are duplicates by email
        'jane@example.com', 'jane@example.com',        # Duplicates by email
        None, None,                                     # No email
        None, None,                                     # No email
        'charlie@example.com',                          # Unique email
        None,                                            # No email
        None,                                            # No email
    ],
    'Person Street': [
        '123 Main St', '123 Main St', '123 Main St',
        '456 Oak Ave', '456 Oak Ave',
        '789 Pine Rd', '789 Pine Rd',  # Duplicate name+address
        None, None,                      # No address
        '321 Elm St',
        '654 Maple Dr',  # Unique address
        None,            # No address
    ],
    'Person City': [
        'Boston', 'Boston', 'Boston',
        'Chicago', 'Chicago',
        'Denver', 'Denver',
        None, None,
        'Seattle',
        'Portland',
        None,
    ],
    'Person State': [
        'MA', 'MA', 'MA',
        'IL', 'IL',
        'CO', 'CO',
        None, None,
        'WA',
        'OR',
        None,
    ],
    'Direct Phone Number': [
        '555-1001', '555-1001', '555-1001',
        '555-2001', '555-2001',
        '555-3001', '555-3001',
        '555-4001', '555-4001',  # Duplicate name+phone
        '555-5001',
        '555-6001',
        '555-7001',  # Unique phone
    ],
}

df = pd.DataFrame(test_data)

print(f"\n📊 INPUT DATA: {len(df)} rows")
print(df.to_string(index=True))

# Test 1: Standard deduplication (without multi-level)
print(f"\n{'='*80}")
print("TEST 1: Standard Deduplication (multi_level_deduplication=False)")
print("="*80)

operation = RemoveDuplicatesOperation()
params_standard = {
    'columns': ['Email Address'],  # Only dedupe by email
    'keep': 'first',
    'multi_level_deduplication': False
}

result_standard = operation.execute(df.copy(), params_standard)
print(f"\nResult: {len(result_standard)} rows (removed {len(df) - len(result_standard)} duplicates)")
print(f"Note: Only checks Email Address column, misses other types of duplicates")

# Test 2: Multi-level deduplication
print(f"\n{'='*80}")
print("TEST 2: Multi-Level Deduplication (multi_level_deduplication=True)")
print("="*80)

params_multilevel = {
    'keep': 'first',
    'multi_level_deduplication': True
}

result_multilevel = operation.execute(df.copy(), params_multilevel)
print(f"\nResult: {len(result_multilevel)} rows (removed {len(df) - len(result_multilevel)} duplicates)")

print(f"\n📋 DEDUPLICATED DATA:")
print(result_multilevel[['First Name', 'Last Name', 'Email Address', 'Person Street', 'Direct Phone Number']].to_string(index=True))

# Analyze what was removed
removed_indices = set(df.index) - set(result_multilevel.index)
print(f"\n🗑️  REMOVED ROWS (duplicates): {len(removed_indices)}")
for idx in sorted(removed_indices):
    row = df.loc[idx]
    print(f"  Row {idx}: {row['First Name']} {row['Last Name']} - Email: {row['Email Address']}, Address: {row['Person Street']}, Phone: {row['Direct Phone Number']}")

# Test 3: Verify the logic
print(f"\n{'='*80}")
print("VERIFICATION: Multi-Level Logic")
print("="*80)

# Count by group
has_email = df['Email Address'].notna()
no_email_has_address = df['Email Address'].isna() & df['Person Street'].notna()
no_email_no_address = df['Email Address'].isna() & df['Person Street'].isna()

print(f"\nGroup breakdown (input):")
print(f"  Group 1 - Has Email: {has_email.sum()} rows")
print(f"  Group 2 - No Email, Has Address: {no_email_has_address.sum()} rows")
print(f"  Group 3 - No Email, No Address: {no_email_no_address.sum()} rows")

# Count in result
has_email_result = result_multilevel['Email Address'].notna()
no_email_has_address_result = result_multilevel['Email Address'].isna() & result_multilevel['Person Street'].notna()
no_email_no_address_result = result_multilevel['Email Address'].isna() & result_multilevel['Person Street'].isna()

print(f"\nGroup breakdown (output after deduplication):")
print(f"  Group 1 - Has Email: {has_email_result.sum()} rows")
print(f"  Group 2 - No Email, Has Address: {no_email_has_address_result.sum()} rows")
print(f"  Group 3 - No Email, No Address: {no_email_no_address_result.sum()} rows")

print(f"\n{'='*80}")
print("EXPECTED BEHAVIOR:")
print("="*80)
print("""
Level 1 (Email - rows with email):
  Rows 0 & 1 are duplicates (same email john@example.com) → Keep row 0
  Rows 3 & 4 are duplicates (same email jane@example.com) → Keep row 3
  Row 9 is unique (charlie@example.com) → Keep row 9

Level 2 (Name+Address - rows without email but with address):
  Row 2 is unique (John Doe at 123 Main St, first in no-email group) → Keep row 2
  Rows 5 & 6 are duplicates (Bob Johnson at 789 Pine Rd) → Keep row 5
  Row 10 is unique (David Davis at 654 Maple Dr) → Keep row 10

Level 3 (Name+Phone - rows without email and without address):
  Rows 7 & 8 are duplicates (Alice Williams 555-4001) → Keep row 7
  Row 11 is unique (Eve Miller 555-7001) → Keep row 11

Expected output: 8 unique rows (removed 4 duplicates)

NOTE: Row 2 (John Doe, no email) is NOT a duplicate of Row 0 (John Doe, has email)
      because they're in different deduplication groups!
""")

# Validate
expected_kept = [0, 2, 3, 5, 7, 9, 10, 11]
actual_kept = sorted(result_multilevel.index.tolist())

print(f"Expected kept rows: {expected_kept}")
print(f"Actual kept rows:   {actual_kept}")

if expected_kept == actual_kept:
    print(f"\n✅ SUCCESS: Multi-level deduplication working correctly!")
    print(f"   - Removed {len(df) - len(result_multilevel)} duplicates")
    print(f"   - Kept {len(result_multilevel)} unique rows")
    print(f"   - Level 1: Deduped by email")
    print(f"   - Level 2: Deduped by name+address (for rows without email)")
    print(f"   - Level 3: Deduped by name+phone (for rows without email or address)")
else:
    print(f"\n❌ MISMATCH: Expected {expected_kept} but got {actual_kept}")

print(f"\n{'='*80}")
print("TEST COMPLETE")
print("="*80)
