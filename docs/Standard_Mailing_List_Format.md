# Standard Mailing List Format Specification
## Universal Excel Tool V2.0 - Standardized Output Format

**Version:** 1.0
**Last Updated:** 2025-11-18
**Purpose:** Define a consistent, validated format for all mailing list outputs

---

## Overview

This document specifies the standardized format for cleaned mailing lists. All mailing list cleaning operations should produce output conforming to this specification.

### Goals
- **Consistency** - Same format across all campaigns and sources
- **Validation** - All data meets quality standards
- **Compatibility** - Works with CRM systems, email platforms, mailing services
- **Completeness** - Contains all necessary fields for targeting and personalization

---

## Standard Format Tiers

### Tier 1: Minimal Required (5 fields)
Absolute minimum for a functional mailing list.

### Tier 2: Standard (10 fields)
Recommended for most mailing campaigns.

### Tier 3: Enhanced (14+ fields)
Full data enrichment for advanced targeting and personalization.

---

## Tier 1: Minimal Required Fields

**Use Case:** Basic email campaigns, simple direct mail

| # | Field Name | Data Type | Format | Validation | Required | Example |
|---|------------|-----------|--------|------------|----------|---------|
| 1 | **First Name** | Text | Title Case | Not blank, trimmed | YES | John |
| 2 | **Last Name** | Text | Title Case | Not blank, trimmed | YES | Smith |
| 3 | **Company** | Text | UPPERCASE | Not blank, trimmed | YES | ACME CORPORATION |
| 4 | **Email** | Text | lowercase | Valid format, unique | YES | john.smith@acme.com |
| 5 | **Phone** | Text | (XXX) XXX-XXXX | 10 digits | YES | (555) 123-4567 |

**Validation Rules:**
- All 5 fields must be populated (not blank)
- Email must pass regex validation: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Email must be unique (no duplicates)
- Phone must contain exactly 10 numeric digits
- All text fields must be trimmed (no leading/trailing spaces)

---

## Tier 2: Standard Format (Recommended)

**Use Case:** Most B2B mailing campaigns, targeted outreach

Includes all Tier 1 fields plus:

| # | Field Name | Data Type | Format | Validation | Required | Example |
|---|------------|-----------|--------|------------|----------|---------|
| 6 | **Job Title** | Text | Title Case | Trimmed | Recommended | Vice President Of Sales |
| 7 | **Street** | Text | Title Case | Not blank, No PO Box | YES | 123 Main Street |
| 8 | **City** | Text | Title Case | Not blank | YES | Springfield |
| 9 | **State** | Text | UPPERCASE | 2-letter state code | YES | IL |
| 10 | **Zip** | Text | 5 digits | Numeric, 5 characters | YES | 62701 |

**Additional Validation Rules:**
- Street address cannot contain "PO Box", "P.O. Box", "POB" (case-insensitive)
- State must be valid 2-letter US state code
- Zip code must be exactly 5 digits (or 9 with hyphen: XXXXX-XXXX)
- City must not be blank

**Complete Standard Column Order:**
```
First Name | Last Name | Company | Job Title | Email | Phone | Street | City | State | Zip
```

---

## Tier 3: Enhanced Format (Full Data)

**Use Case:** Advanced targeting, segmentation, personalization, high-value campaigns

Includes all Tier 2 fields plus:

| # | Field Name | Data Type | Format | Purpose | Keep/Discard | Example |
|---|------------|-----------|--------|---------|--------------|---------|
| 11 | **Industry** | Text | Title Case | Segmentation | KEEP | Food Processing |
| 12 | **Company Size** | Text or Number | Various | Targeting | KEEP | 100-500 Employees |
| 13 | **Revenue** | Text or Number | Various | High-value targeting | CONDITIONAL | $10M-$50M |
| 14 | **Management Level** | Text | Title Case | Decision-maker ID | KEEP | C-Level |
| 15 | **Job Function** | Text | Title Case | Department targeting | KEEP | Sales & Marketing |
| 16 | **Website** | URL | lowercase | Research/enrichment | OPTIONAL | www.acme.com |
| 17 | **LinkedIn** | URL | As-is | Social enrichment | OPTIONAL | linkedin.com/company/acme |
| 18 | **Employees** | Number | Numeric | Sizing | CONDITIONAL | 250 |

**Field Retention Criteria:**

**ALWAYS KEEP:**
- Industry (useful for segmentation)
- Management Level (decision-maker identification)
- Job Function (department targeting)

**KEEP IF AVAILABLE & ACCURATE:**
- Company Size
- Revenue (if relatively recent and reliable)
- Employees (if from reliable source)

**OPTIONAL (Keep if useful for campaign):**
- Website
- LinkedIn URL
- Other social media

**ALWAYS DISCARD:**
- Internal IDs (ZoomInfo Contact ID, Salesforce ID, etc.)
- Last Updated timestamps
- Data Source (unless tracking multiple sources)
- Export metadata
- Confidence scores (internal to data provider)

---

## Field Specifications in Detail

### First Name
- **Format:** Title Case
- **Transformations:** `PROPER()`, `TRIM()`
- **Max Length:** 50 characters
- **Validation:** Not blank, no numbers, no special characters
- **Edge Cases:**
  - Hyphenated names OK: "Mary-Jane"
  - Apostrophes OK: "O'Brien"
  - Single letter OK: "J"

### Last Name
- **Format:** Title Case
- **Transformations:** `PROPER()`, `TRIM()`
- **Max Length:** 50 characters
- **Validation:** Not blank, no numbers
- **Edge Cases:**
  - Prefixes OK: "Van Der Berg", "De La Cruz"
  - Suffixes separate: Store "Jr.", "III" separately if possible

### Company
- **Format:** UPPERCASE
- **Transformations:** `UPPER()`, `TRIM()`
- **Max Length:** 100 characters
- **Validation:** Not blank
- **Standardizations:**
  - Keep legal suffixes: "ACME CORPORATION INC."
  - Do NOT remove "LLC", "INC", "CORP" etc.
  - Keep "&" and other punctuation
- **Edge Cases:**
  - Acronyms: "IBM", "HP" (keep as-is)
  - Numbers OK: "3M COMPANY"

### Email
- **Format:** lowercase
- **Transformations:** `LOWER()`, `TRIM()`
- **Max Length:** 100 characters
- **Validation:**
  - Must contain exactly one "@"
  - Must contain at least one "." after "@"
  - Pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
  - Must be unique in dataset
- **Invalid Patterns:**
  - Multiple @: "user@@domain.com" (REMOVE)
  - No domain: "user@" (REMOVE)
  - No TLD: "user@domain" (REMOVE)
  - Generic: "info@", "noreply@", "admin@" (FLAG for review)

### Phone
- **Format:** `(XXX) XXX-XXXX`
- **Transformations:**
  1. Remove all non-numeric: `SUBSTITUTE()` repeatedly
  2. Take rightmost 10 digits: `RIGHT(10)`
  3. Format: `="("&LEFT(3)&") "&MID(4,3)&"-"&RIGHT(4)`
- **Validation:** Must have exactly 10 digits after cleaning
- **Input Formats Accepted:**
  - `1234567890`
  - `123-456-7890`
  - `(123) 456-7890`
  - `+1-123-456-7890` (strip country code)
  - `123.456.7890`
- **Invalid:**
  - Less than 10 digits (FLAG for review or REMOVE)
  - International format other than +1 (FLAG for review)

### Job Title
- **Format:** Title Case
- **Transformations:** `PROPER()`, `TRIM()`
- **Max Length:** 100 characters
- **Validation:** Recommended but not required
- **Standardizations:**
  - "VP" → "Vice President" (optional)
  - Spell out abbreviations for clarity (optional)

### Street
- **Format:** Title Case
- **Transformations:** `PROPER()`, `TRIM()`
- **Max Length:** 100 characters
- **Validation:**
  - Not blank
  - Must NOT contain PO Box indicators
- **PO Box Patterns to REJECT:**
  - "PO Box"
  - "P.O. Box"
  - "POB"
  - "Post Office Box"
  - (Case-insensitive matching)
- **Standardizations (Optional):**
  - "St" → "Street"
  - "Ave" → "Avenue"
  - "Blvd" → "Boulevard"
  - "Ste" → "Suite"
  - "#" → "Suite"

### City
- **Format:** Title Case
- **Transformations:** `PROPER()`, `TRIM()`
- **Max Length:** 50 characters
- **Validation:** Not blank
- **Edge Cases:**
  - Hyphens OK: "Winston-Salem"
  - Multiple words OK: "San Francisco"

### State
- **Format:** UPPERCASE, 2 letters
- **Transformations:** `UPPER()`, `TRIM()`, `LEFT(2)`
- **Length:** Exactly 2 characters
- **Validation:** Must be valid US state code
- **Valid Codes:** AL, AK, AZ, AR, CA, CO, CT, DE, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY, DC
- **Handling full state names:** Convert to 2-letter code if possible

### Zip
- **Format:** 5 digits (or 9 with hyphen)
- **Transformations:**
  - Take first 5 digits only: `LEFT(5)`
  - Pad with leading zeros if needed: `TEXT(A1,"00000")`
- **Length:** 5 characters (or 10 with hyphen: "XXXXX-XXXX")
- **Validation:** Must be numeric, 5 digits
- **Input Formats:**
  - `62701` (keep as-is)
  - `62701-1234` (either keep or truncate to 5)
  - `627` (INVALID - flag for review)

---

## Data Quality Standards

### Completeness Requirements

**Tier 1 (Minimal):**
- 100% of required fields populated
- 0% blank values in required fields

**Tier 2 (Standard):**
- 100% of Tier 1 fields populated
- 90%+ of Tier 2 fields populated
- Job Title: 80%+ populated (acceptable to have some blanks)

**Tier 3 (Enhanced):**
- 100% of Tier 2 fields populated
- 70%+ of Tier 3 fields populated

### Uniqueness Requirements
- **Email:** 100% unique (no duplicates)
- **Company + Contact Name:** Allow duplicates (multiple contacts per company)
- If duplicate emails found: Keep first occurrence, flag others

### Validation Pass Rate
- **Email validation:** 100% must pass format check
- **Phone validation:** 95%+ must have 10 valid digits
- **Address validation:** 100% must have no PO Boxes (if mail campaign)

---

## Preset Configuration: "Standard Mailing List Cleaner"

### Operation Sequence

**Phase 1: Initial Cleaning (Operations 1-3)**
1. **Remove Blank Rows**
   - Operation: `clean_remove_blank_rows`
   - Parameters: (none)

2. **Trim Whitespace** (All text columns)
   - Operation: `text_trim`
   - Parameters: `columns = [ALL text columns]`

3. **Remove Columns** (Internal/Unnecessary fields)
   - Operation: `clean_remove_columns`
   - Parameters: `columns = [ZoomInfo Contact ID, Last Updated, Data Source, etc.]`

**Phase 2: Text Formatting (Operations 4-7)**
4. **PROPER Case: Names and Addresses**
   - Operation: `text_titlecase`
   - Parameters: `columns = [First Name, Last Name, Job Title, Street, City]`

5. **UPPERCASE: Company and State**
   - Operation: `text_uppercase`
   - Parameters: `columns = [Company, State]`

6. **lowercase: Email**
   - Operation: `text_lowercase`
   - Parameters: `columns = [Email]`

7. **Format Zip Code** (if operation available)
   - Operation: `LEFT(Zip, 5)` - Future enhancement
   - Parameters: `column = Zip, length = 5`

**Phase 3: Validation (Operations 8-9)**
8. **Validate Email**
   - Operation: `validate_email`
   - Parameters: `column = Email, flag_invalid = TRUE`
   - Creates: `Email_Valid` flag column

9. **Flag PO Boxes**
   - Operation: `conditional_flag_contains`
   - Parameters: `column = Street, text = "PO Box", flag_column = "PO_Box_Flag"`
   - Also run with: `text = "P.O. Box"`, `text = "POB"`

**Phase 4: Deduplication (Operation 10)**
10. **Remove Duplicates**
    - Operation: `data_remove_duplicates`
    - Parameters: `columns = [Email], keep = 'first'`

**Phase 5: Final Filtering (Manual or Future Enhancement)**
- Remove rows where `Email_Valid = FALSE`
- Remove rows where `PO_Box_Flag = TRUE`
- Remove rows where `Company` is blank
- Remove rows where `First Name` is blank
- Remove rows where `Last Name` is blank

**Phase 6: Sorting and Final Touches (Operation 11)**
11. **Sort by Company**
    - Operation: `data_sort`
    - Parameters: `columns = [Company], ascending = TRUE`

12. **Remove Flag Columns** (optional - clean up working columns)
    - Operation: `clean_remove_columns`
    - Parameters: `columns = [Email_Valid, PO_Box_Flag]` (if not needed in output)

---

## Column Order - Final Output

### Tier 1 & 2 (Standard) Output:
```
1.  First Name
2.  Last Name
3.  Company
4.  Job Title
5.  Email
6.  Phone
7.  Street
8.  City
9.  State
10. Zip
```

### Tier 3 (Enhanced) Output:
```
1.  First Name
2.  Last Name
3.  Company
4.  Job Title
5.  Email
6.  Phone
7.  Street
8.  City
9.  State
10. Zip
11. Industry
12. Company Size
13. Revenue
14. Management Level
15. Job Function
16. Website
17. LinkedIn
```

---

## Export Format Recommendations

### CSV Export
- **Encoding:** UTF-8
- **Delimiter:** Comma (,)
- **Text Qualifier:** Double quotes (")
- **Line Ending:** Windows (CRLF) or Unix (LF)
- **Header Row:** Yes, include column names

### Excel Export
- **Format:** .xlsx (not .xls)
- **Sheet Name:** "Clean_List_[Campaign]_[Date]"
- **Freeze Top Row:** Yes
- **Column Widths:** Auto-fit
- **Filters:** Enable for header row

---

## Quality Assurance Checklist

Before finalizing any mailing list, verify:

- [ ] All required fields are populated (no blanks)
- [ ] Email format validation: 100% pass rate
- [ ] Email uniqueness: No duplicates
- [ ] PO Boxes removed (if physical mail campaign)
- [ ] Phone numbers formatted consistently
- [ ] Names are in Title Case
- [ ] Company names are in UPPERCASE
- [ ] State codes are 2-letter UPPERCASE
- [ ] Zip codes are 5 digits
- [ ] Row count reduced appropriately (document reduction rate)
- [ ] Spot check 10-20 random rows for accuracy
- [ ] Column order matches standard specification
- [ ] File naming convention: `Clean_List_[Source]_[Campaign]_[Date].xlsx`

---

## Naming Conventions

### File Names
```
Clean_List_[DataSource]_[Campaign]_[YYYY-MM-DD].xlsx
```

**Examples:**
- `Clean_List_ZoomInfo_HolidayGift_2025-08-26.xlsx`
- `Clean_List_LinkedIn_Q4Outreach_2025-11-18.xlsx`
- `Clean_List_Manual_WinterPromo_2025-12-01.xlsx`

### Sheet Names (if multiple sheets in one file)
- `Clean_List_Final` - The validated, final output
- `Removed_Invalid_Email` - Records removed due to email issues
- `Removed_PO_Box` - Records removed due to PO Box addresses
- `Removed_Duplicates` - Duplicate records
- `Quality_Report` - Summary statistics

---

## Metrics to Track

For each cleaning operation, document:

| Metric | Description | Example |
|--------|-------------|---------|
| **Starting Row Count** | Rows in raw data | 188 |
| **Ending Row Count** | Rows in final output | 82 |
| **Reduction Count** | Rows removed | 106 |
| **Reduction Rate** | Percentage removed | 56.4% |
| **Blank Email Removed** | Rows with no email | 25 |
| **Invalid Email Removed** | Rows with bad email format | 18 |
| **Duplicate Email Removed** | Duplicate records | 32 |
| **PO Box Removed** | PO Box addresses | 15 |
| **Missing Required Fields** | Other mandatory fields blank | 16 |
| **Final Validation Pass Rate** | % of final rows fully valid | 100% |

---

## Example Comparison: Raw vs. Clean

### Raw Data (FOOD PROC sheet):
```
First Name: JOHN
Last Name: SMITH
Company: acme corporation inc
Email: JOHN.SMITH@ACME.COM
Phone: 5551234567
Street: 123 main st
City: SPRINGFIELD
State: il
Zip: 62701
```

### Clean Data (Standard Format):
```
First Name: John
Last Name: Smith
Company: ACME CORPORATION INC
Email: john.smith@acme.com
Phone: (555) 123-4567
Street: 123 Main St
City: Springfield
State: IL
Zip: 62701
```

---

## Future Enhancements

### Planned Additions:
1. **State Name to Code Converter** - Auto-convert "Illinois" → "IL"
2. **International Address Support** - Handle non-US addresses
3. **Phone Format Options** - Support international formats
4. **Custom Validation Rules** - User-defined validation criteria
5. **Auto-Flag Generic Emails** - Flag "info@", "sales@" addresses
6. **Company Name Normalization** - Standardize "Inc", "Inc.", "Incorporated"
7. **Title Standardization** - Map various titles to standard categories

---

## Usage Example

**Scenario:** Cleaning ZoomInfo export for holiday gift campaign

1. Load `ZOOM_FOOD_PROC-_HOLIDAY_GIFT_8-26-25.xlsx`
2. Load preset: "Standard Mailing List Cleaner"
3. Run all operations
4. Review quality metrics
5. Export as: `Clean_List_ZoomInfo_HolidayGift_2025-08-26.xlsx`
6. Result: 188 rows → 82 rows (56% reduction, all validated)

---

**Document Version:** 1.0
**Specification Level:** Tier 2 (Standard)
**Last Review:** 2025-11-18
