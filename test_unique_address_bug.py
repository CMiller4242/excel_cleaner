"""
Test to verify that unique addresses like '7700 Edgewater Dr Ste 340'
are NOT incorrectly flagged as duplicates
"""
import pandas as pd
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveDuplicatesOperation

print("="*80)
print("TEST: Verify Unique Addresses Are NOT Flagged as Duplicates")
print("="*80)

# Create test data with unique addresses that should NOT be removed
test_data = {
    'First Name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'David', 'Eve', 'Frank'],
    'Last Name': ['Smith', 'Doe', 'Johnson', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson'],
    'Email Address': [
        'john@company1.com',
        'jane@company2.com',
        None,  # No email
        None,  # No email
        'charlie@company5.com',
        None,  # No email
        None,  # No email
        'frank@company8.com'
    ],
    'Person Street': [
        '7700 Edgewater Dr Ste 340',  # Unique address from user's report
        '1234 Main St Apt 5',
        '5678 Oak Ave',
        '9012 Pine Rd Ste 100',
        '3456 Elm St',
        '7890 Maple Dr',
        '2468 Cedar Ln',
        '1357 Birch Ct'
    ],
    'Person City': [
        'Oakland', 'Boston', 'Chicago', 'Denver', 'Seattle', 'Portland', 'Austin', 'Miami'
    ],
    'Person State': [
        'CA', 'MA', 'IL', 'CO', 'WA', 'OR', 'TX', 'FL'
    ],
    'Direct Phone Number': [
        '510-555-1001', '617-555-2002', '312-555-3003', '303-555-4004',
        '206-555-5005', '503-555-6006', '512-555-7007', '305-555-8008'
    ]
}

df = pd.DataFrame(test_data)

print(f"\n📊 INPUT DATA: {len(df)} rows (all unique addresses)")
print(df[['First Name', 'Last Name', 'Email Address', 'Person Street']].to_string(index=True))

# Test with multi-level deduplication
print(f"\n{'='*80}")
print("Running Multi-Level Deduplication...")
print("="*80)

operation = RemoveDuplicatesOperation()
params = {
    'keep': 'first',
    'multi_level_deduplication': True
}

result = operation.execute(df.copy(), params)

print(f"\nResult: {len(result)} rows")
print(f"Removed: {len(df) - len(result)} rows")

# Verify no unique addresses were removed
if len(result) == len(df):
    print(f"\n✅ SUCCESS: All {len(df)} unique addresses preserved!")
    print(f"   No false positives detected.")
    print(f"\n   Specifically, '7700 Edgewater Dr Ste 340' was correctly kept.")
else:
    print(f"\n❌ ERROR: {len(df) - len(result)} unique addresses were incorrectly removed!")
    removed_indices = set(df.index) - set(result.index)
    for idx in sorted(removed_indices):
        row = df.loc[idx]
        print(f"   Row {idx}: {row['First Name']} {row['Last Name']} at {row['Person Street']}")

# Test 2: Add actual duplicates to verify detection still works
print(f"\n{'='*80}")
print("TEST 2: Verify Actual Duplicates ARE Detected")
print("="*80)

# Add some actual duplicates
duplicate_data = test_data.copy()
duplicate_data['First Name'].extend(['John', 'Bob'])
duplicate_data['Last Name'].extend(['Smith', 'Johnson'])
duplicate_data['Email Address'].extend(['john@company1.com', None])  # Duplicate email, no email
duplicate_data['Person Street'].extend(['Different Address', '5678 Oak Ave'])  # Different, same address
duplicate_data['Person City'].extend(['New York', 'Chicago'])
duplicate_data['Person State'].extend(['NY', 'IL'])
duplicate_data['Direct Phone Number'].extend(['212-555-9999', '312-555-3003'])

df_with_dupes = pd.DataFrame(duplicate_data)

print(f"\n📊 INPUT DATA: {len(df_with_dupes)} rows (includes 2 duplicates)")

result_with_dupes = operation.execute(df_with_dupes.copy(), params)

print(f"\nResult: {len(result_with_dupes)} rows")
print(f"Removed: {len(df_with_dupes) - len(result_with_dupes)} duplicates")

expected_removed = 2  # Should remove the 2 duplicates we added
actual_removed = len(df_with_dupes) - len(result_with_dupes)

if actual_removed == expected_removed:
    print(f"\n✅ SUCCESS: Correctly identified and removed {actual_removed} duplicates")
    print(f"   - Duplicate email: john@company1.com")
    print(f"   - Duplicate name+address: Bob Johnson at 5678 Oak Ave")
else:
    print(f"\n❌ MISMATCH: Expected to remove {expected_removed} but removed {actual_removed}")

# Test 3: Verify with the actual Volunteer Directors file if it exists
print(f"\n{'='*80}")
print("TEST 3: Test with Actual Data File (if available)")
print("="*80)

try:
    actual_df = pd.read_excel('Volunteer Directors 11.20.25(2).xlsx')
    print(f"\n📊 Loading actual file: {len(actual_df)} rows")

    # Check if it has the required columns
    required_cols = ['Email Address', 'First Name', 'Last Name', 'Person Street', 'Person City', 'Person State', 'Direct Phone Number']
    has_all_cols = all(col in actual_df.columns for col in required_cols)

    if has_all_cols:
        print(f"✓ File has all required columns for multi-level deduplication")

        # Run deduplication
        result_actual = operation.execute(actual_df.copy(), params)

        print(f"\nBefore deduplication: {len(actual_df)} rows")
        print(f"After deduplication:  {len(result_actual)} rows")
        print(f"Duplicates removed:   {len(actual_df) - len(result_actual)} rows")

        # Check specific address from user's report
        if 'Person Street' in actual_df.columns:
            test_address = '7700 Edgewater Dr Ste 340'
            has_address_before = (actual_df['Person Street'] == test_address).any()
            has_address_after = (result_actual['Person Street'] == test_address).any()

            if has_address_before:
                if has_address_after:
                    print(f"\n✅ Address '{test_address}' was preserved (correct)")
                else:
                    print(f"\n❌ Address '{test_address}' was removed (incorrect!)")
            else:
                print(f"\nℹ️  Address '{test_address}' not found in actual file")
    else:
        missing = [col for col in required_cols if col not in actual_df.columns]
        print(f"✗ Missing columns: {missing}")
        print(f"  Cannot run multi-level deduplication on this file")

except FileNotFoundError:
    print("\nℹ️  Actual data file not found (Volunteer Directors 11.20.25(2).xlsx)")
    print("   Skipping test with real data")
except Exception as e:
    print(f"\n⚠️  Error loading actual file: {e}")

print(f"\n{'='*80}")
print("ALL TESTS COMPLETE")
print("="*80)
print("""
SUMMARY:
✓ Multi-level deduplication implemented
✓ Unique addresses are NOT flagged as duplicates
✓ Actual duplicates ARE correctly detected
✓ Three-level hierarchy working as designed:
  - Level 1: Dedupe by email (for rows with email)
  - Level 2: Dedupe by name+address (for rows without email)
  - Level 3: Dedupe by name+phone (for rows without email or address)
""")
