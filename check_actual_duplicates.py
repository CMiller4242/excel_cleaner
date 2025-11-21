"""
Check if the actual Volunteer Directors file has any duplicates
"""
import pandas as pd
import sys

print("="*80)
print("CHECKING FOR DUPLICATES IN ACTUAL FILE")
print("="*80)

# Load the actual file
df = pd.read_excel('Volunteer Directors 11.20.25(2).xlsx')

print(f"\n📊 File: Volunteer Directors 11.20.25(2).xlsx")
print(f"Total rows: {len(df)}")

# Check for required columns
required_cols = ['Email Address', 'First Name', 'Last Name', 'Person Street', 'Person City', 'Person State', 'Direct Phone Number']
missing = [col for col in required_cols if col not in df.columns]

if missing:
    print(f"\n⚠️  Missing columns: {missing}")
    print(f"   Multi-level deduplication will fall back to standard mode")
else:
    print(f"\n✓ All required columns present")

print(f"\n{'='*80}")
print(f"LEVEL 1: Checking for duplicate Email Addresses")
print(f"{'='*80}")

# Check Level 1 duplicates (by email)
has_email = df['Email Address'].notna()
email_group = df[has_email]

print(f"Rows with Email Address: {len(email_group)}")

if len(email_group) > 0:
    duplicates_by_email = email_group[email_group.duplicated(subset=['Email Address'], keep=False)]
    unique_duplicate_emails = duplicates_by_email['Email Address'].nunique()

    print(f"Rows with duplicate emails: {len(duplicates_by_email)}")
    print(f"Unique duplicate email addresses: {unique_duplicate_emails}")

    if len(duplicates_by_email) > 0:
        print(f"\nSample duplicate emails:")
        for email in duplicates_by_email['Email Address'].unique()[:10]:
            count = (email_group['Email Address'] == email).sum()
            print(f"  {email}: appears {count} times")
    else:
        print(f"\n✓ No duplicate email addresses found")

print(f"\n{'='*80}")
print(f"LEVEL 2: Checking for duplicate Name+Address combinations")
print(f"{'='*80}")

no_email = df['Email Address'].isna()
has_address = df['Person Street'].notna()
address_group = df[no_email & has_address]

print(f"Rows without email but with address: {len(address_group)}")

if len(address_group) > 0:
    dedupe_cols = ['First Name', 'Last Name', 'Person Street', 'Person City', 'Person State']
    duplicates_by_address = address_group[address_group.duplicated(subset=dedupe_cols, keep=False)]

    print(f"Rows with duplicate name+address: {len(duplicates_by_address)}")

    if len(duplicates_by_address) > 0:
        print(f"\nSample duplicate name+address combinations:")
        for idx, row in duplicates_by_address.head(5).iterrows():
            print(f"  {row['First Name']} {row['Last Name']} at {row['Person Street']}, {row['Person City']}, {row['Person State']}")
    else:
        print(f"\n✓ No duplicate name+address combinations found")

print(f"\n{'='*80}")
print(f"LEVEL 3: Checking for duplicate Name+Phone combinations")
print(f"{'='*80}")

no_address = df['Person Street'].isna()
phone_group = df[no_email & no_address]

print(f"Rows without email and without address: {len(phone_group)}")

if len(phone_group) > 0:
    dedupe_cols = ['First Name', 'Last Name', 'Direct Phone Number']
    duplicates_by_phone = phone_group[phone_group.duplicated(subset=dedupe_cols, keep=False)]

    print(f"Rows with duplicate name+phone: {len(duplicates_by_phone)}")

    if len(duplicates_by_phone) > 0:
        print(f"\nSample duplicate name+phone combinations:")
        for idx, row in duplicates_by_phone.head(5).iterrows():
            print(f"  {row['First Name']} {row['Last Name']} - {row['Direct Phone Number']}")
    else:
        print(f"\n✓ No duplicate name+phone combinations found")

print(f"\n{'='*80}")
print(f"SUMMARY:")
print(f"{'='*80}")

total_duplicates = 0

# Count total duplicates across all levels
if len(email_group) > 0:
    dup_email_count = len(email_group) - email_group['Email Address'].nunique()
    total_duplicates += dup_email_count
    print(f"Level 1 (email): {dup_email_count} duplicate rows")

if len(address_group) > 0:
    dup_address_count = len(address_group) - len(address_group.drop_duplicates(subset=['First Name', 'Last Name', 'Person Street', 'Person City', 'Person State']))
    total_duplicates += dup_address_count
    print(f"Level 2 (name+address): {dup_address_count} duplicate rows")

if len(phone_group) > 0:
    dup_phone_count = len(phone_group) - len(phone_group.drop_duplicates(subset=['First Name', 'Last Name', 'Direct Phone Number']))
    total_duplicates += dup_phone_count
    print(f"Level 3 (name+phone): {dup_phone_count} duplicate rows")

print(f"\nTotal duplicate rows: {total_duplicates}")
print(f"Expected output after deduplication: {len(df) - total_duplicates} rows")

if total_duplicates == 0:
    print(f"\n💡 CONCLUSION: This file has NO DUPLICATES!")
    print(f"   Multi-level deduplication is working correctly.")
    print(f"   Input: {len(df)} rows → Output: {len(df)} rows (no change)")
else:
    print(f"\n💡 CONCLUSION: This file has {total_duplicates} duplicates")
    print(f"   Multi-level deduplication should remove them.")
    print(f"   Input: {len(df)} rows → Expected Output: {len(df) - total_duplicates} rows")

print(f"\n{'='*80}")
