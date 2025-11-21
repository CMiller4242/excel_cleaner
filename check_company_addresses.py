"""Check for Company Street Address column"""
import pandas as pd

df = pd.read_excel('Volunteer Directors 11.20.25(2).xlsx')

print("="*80)
print("CHECKING FOR ALTERNATE ADDRESS COLUMNS")
print("="*80)
print(f"\nTotal rows: {len(df)}")
print(f"\nColumns in DataFrame:")
address_cols = [col for col in df.columns if 'street' in col.lower() or 'address' in col.lower()]
print(f"  Address-related columns: {address_cols}")

if 'Person Street' in df.columns and 'Company Street Address' in df.columns:
    person_street = df['Person Street']
    company_street = df['Company Street Address']

    print(f"\n{'='*80}")
    print("PERSON STREET vs COMPANY STREET ADDRESS ANALYSIS")
    print(f"{'='*80}")

    print(f"\nPerson Street:")
    print(f"  Non-blank: {person_street.notna().sum()}")
    print(f"  Blank (NaN): {person_street.isna().sum()}")

    print(f"\nCompany Street Address:")
    print(f"  Non-blank: {company_street.notna().sum()}")
    print(f"  Blank (NaN): {company_street.isna().sum()}")

    # Check rows where Person Street is blank BUT Company Street Address is not
    person_blank = person_street.isna()
    company_not_blank = company_street.notna()

    rows_with_company_but_no_person = df[person_blank & company_not_blank]

    print(f"\n{'='*80}")
    print("CRITICAL FINDING:")
    print(f"{'='*80}")
    print(f"\nRows where Person Street is BLANK but Company Street Address has data:")
    print(f"  Count: {len(rows_with_company_but_no_person)}")

    if len(rows_with_company_but_no_person) > 0:
        print(f"\n  THIS IS THE ISSUE!")
        print(f"  These rows have valid addresses in Company Street Address")
        print(f"  But would be REMOVED because Person Street is blank!")
        print(f"\n  Sample Company Street Address values:")
        for idx, val in rows_with_company_but_no_person['Company Street Address'].head(20).items():
            print(f"    Row {idx}: '{val}'")

        print(f"\n{'='*80}")
        print("CONCLUSION:")
        print(f"{'='*80}")
        print(f"When checking 'Person Street is_blank':")
        print(f"  - Removes {person_blank.sum()} rows with blank Person Street")
        print(f"  - Of which {len(rows_with_company_but_no_person)} have valid Company addresses!")
        print(f"  - These {len(rows_with_company_but_no_person)} addresses appear in the Removed sheet")
        print(f"  - User sees valid addresses in Removed sheet and thinks it's a bug!")

    # Check the inverse - Person Street has data but Company is blank
    person_not_blank = person_street.notna()
    company_blank = company_street.isna()

    rows_with_person_but_no_company = df[person_not_blank & company_blank]
    print(f"\nRows with Person Street but no Company Street Address: {len(rows_with_person_but_no_company)}")

    # Rows with BOTH
    both_not_blank = person_not_blank & company_not_blank
    print(f"Rows with BOTH Person and Company addresses: {both_not_blank.sum()}")

    # Rows with NEITHER
    both_blank = person_blank & company_blank
    print(f"Rows with NEITHER Person nor Company addresses: {both_blank.sum()}")

    print(f"\n{'='*80}")
    print("RECOMMENDATION:")
    print(f"{'='*80}")
    print(f"User probably wants to:")
    print(f"  Remove rows ONLY if BOTH Person Street AND Company Street Address are blank")
    print(f"  NOT remove rows that have an address in EITHER column")
