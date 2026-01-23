# Universal Excel Tool V2.0 - Complete Operations Inventory

**Total Operations: 26**
**Last Updated:** 2026-01-23

---

## Operation Categories

1. [Text Operations](#text-operations) - 9 operations
2. [Data Operations](#data-operations) - 4 operations
3. [Cleaning Operations](#cleaning-operations) - 4 operations
4. [Math Operations](#math-operations) - 6 operations
5. [Validation Operations](#validation-operations) - 1 operation
6. [Conditional Operations](#conditional-operations) - 1 operation
7. [Date Operations](#date-operations) - 1 operation

---

## Text Operations

### 1. Convert to UPPERCASE
- **ID:** `text_uppercase`
- **Excel Equivalent:** `UPPER()`
- **Description:** Convert all text in selected columns to UPPERCASE
- **Parameters:**
  - `columns` (column_list) - Columns to convert
- **Example Use:** "acme corp" → "ACME CORP"
- **Common Use Case:** Standardize company names, state codes

### 2. Convert to lowercase
- **ID:** `text_lowercase`
- **Excel Equivalent:** `LOWER()`
- **Description:** Convert all text in selected columns to lowercase
- **Parameters:**
  - `columns` (column_list) - Columns to convert
- **Example Use:** "EMAIL@DOMAIN.COM" → "email@domain.com"
- **Common Use Case:** Standardize email addresses

### 3. Convert to Title Case
- **ID:** `text_titlecase`
- **Excel Equivalent:** `PROPER()`
- **Description:** Convert text to Title Case (First Letter Of Each Word Capitalized)
- **Parameters:**
  - `columns` (column_list) - Columns to convert
- **Example Use:** "john smith" → "John Smith"
- **Common Use Case:** Format names, addresses

### 4. Remove Extra Whitespace
- **ID:** `text_trim`
- **Excel Equivalent:** `TRIM()`
- **Description:** Remove leading, trailing, and extra spaces from text
- **Parameters:**
  - `columns` (column_list) - Columns to trim
- **Example Use:** "  John   Smith  " → "John Smith"
- **Common Use Case:** Clean imported data, fix spacing issues

### 5. Combine Columns
- **ID:** `text_concatenate`
- **Excel Equivalent:** `CONCATENATE()` or `TEXTJOIN()`
- **Description:** Join multiple columns together with a separator
- **Parameters:**
  - `columns` (column_list) - Columns to combine (in order)
  - `separator` (text, optional) - Text between values (default: space)
  - `new_column` (text) - Name for combined column
  - `remove_original` (boolean, optional) - Remove original columns (default: false)
- **Example Use:** First="John", Last="Smith" → Full Name="John Smith"
- **Common Use Case:** Create full names, complete addresses

### 6. Split Column
- **ID:** `text_split`
- **Excel Equivalent:** Text to Columns
- **Description:** Split one column into multiple columns based on a separator
- **Parameters:**
  - `column` (column) - Column to split
  - `separator` (text) - Character to split on (default: comma)
  - `new_columns` (text) - Comma-separated names for new columns
  - `remove_original` (boolean, optional) - Remove original column (default: false)
- **Example Use:** "Last, First" → Last Name="Last", First Name="First"
- **Common Use Case:** Split names, parse addresses, separate codes

### 7. Remove Special Characters
- **ID:** `text_remove_special`
- **Excel Equivalent:** `SUBSTITUTE()` or REGEX
- **Description:** Remove symbols and special characters from text
- **Parameters:**
  - `columns` (column_list) - Columns to clean
  - `keep_spaces` (boolean, optional) - Keep spaces (default: true)
  - `keep_numbers` (boolean, optional) - Keep numbers (default: true)
- **Example Use:** "123 Main St #5" → "123 Main St 5"
- **Common Use Case:** Clean addresses, product codes, phone numbers

### 8. Find and Replace
- **ID:** `text_find_replace`
- **Excel Equivalent:** Find & Replace or `SUBSTITUTE()`
- **Description:** Find specific text and replace it with something else
- **Parameters:**
  - `columns` (column_list) - Columns to search in
  - `find_text` (text) - Text to find
  - `replace_text` (text) - Text to replace with
  - `case_sensitive` (boolean, optional) - Match case exactly (default: false)
- **Example Use:** "St" → "Street"
- **Common Use Case:** Standardize abbreviations, fix typos

### 9. Add Prefix or Suffix
- **ID:** `text_add_prefix_suffix`
- **Excel Equivalent:** `CONCATENATE()` or `&`
- **Description:** Add text to the beginning or end of values
- **Parameters:**
  - `columns` (column_list) - Columns to modify
  - `prefix` (text, optional) - Text to add at beginning
  - `suffix` (text, optional) - Text to add at end
- **Example Use:** "Smith" → "Mr. Smith" or "domain" → "domain.com"
- **Common Use Case:** Add titles, domain extensions, currency symbols

---

## Data Operations

### 10. Lookup Values from Another File
- **ID:** `data_vlookup`
- **Excel Equivalent:** `VLOOKUP()`
- **Description:** Find and retrieve values from another spreadsheet based on a matching column
- **Parameters:**
  - `lookup_column` (column) - Column to match on in your data
  - `lookup_file` (file) - File to search in (CSV or Excel)
  - `lookup_file_column` (text) - Column name in lookup file to match
  - `return_column` (text) - Column to retrieve from lookup file
  - `new_column` (text) - Name for the new column
- **Example Use:** Get pricing from master price list using product code
- **Common Use Case:** Enrich data with external information

### 11. Remove Duplicate Rows
- **ID:** `data_remove_duplicates`
- **Excel Equivalent:** Remove Duplicates
- **Description:** Remove duplicate records based on one or more columns
- **Parameters:**
  - `columns` (column_list) - Columns to check (empty = check all)
  - `keep` (choice) - Which duplicate to keep: 'first' or 'last' (default: first)
- **Example Use:** Remove duplicate customers by Customer ID
- **Common Use Case:** Deduplicate contact lists, remove repeated entries

### 12. Sort Data
- **ID:** `data_sort`
- **Excel Equivalent:** Sort A-Z or Sort Z-A
- **Description:** Sort rows by one or more columns
- **Parameters:**
  - `columns` (column_list) - Columns to sort by (in priority order)
  - `ascending` (boolean) - Sort A-Z, 1-9 (default: true)
- **Example Use:** Sort by customer name alphabetically
- **Common Use Case:** Organize data, prepare for reporting

### 12.5. Add Multiple Columns
- **ID:** `data_add_multiple_columns`
- **Excel Equivalent:** Insert columns (multiple times)
- **Category:** Data - Organization
- **Description:** Add multiple new columns at once with blank or constant values (batch column creation)
- **Parameters:**
  - `columns` (add_columns_list) - List of column definitions
    - Each definition includes:
      - `name` - Column name
      - `default_type` - 'blank' or 'value'
      - `value` - Default value (if type is 'value')
      - `on_exists` - Behavior if column exists: 'skip', 'overwrite', or 'rename'
- **Example Use:**
  - Add blank columns for Status, Notes, Follow_Up
  - Add columns with default values like Country=USA, Score=0
  - Batch create template columns for data entry
- **Common Use Case:**
  - Prepare template columns for manual data entry
  - Add standardized fields to multiple datasets
  - Create placeholder columns for future processing
- **Special Behavior:**
  - New columns appended at end of DataFrame in order specified
  - Non-fatal validation: handles existing columns gracefully
  - on_exists=skip: skips and logs issue
  - on_exists=overwrite: replaces existing column values
  - on_exists=rename: auto-renames to unique name (e.g., Status_1)
  - Issues logged but don't block execution

---

## Cleaning Operations

### 13. Remove Blank Rows
- **ID:** `clean_remove_blank_rows`
- **Excel Equivalent:** Go To Special > Blanks > Delete
- **Description:** Remove rows where all cells are empty
- **Parameters:** (none)
- **Example Use:** Clean up imported data with empty rows
- **Common Use Case:** Remove spacer rows, clean CSV imports

### 14. Fill Missing Values
- **ID:** `clean_fill_missing`
- **Excel Equivalent:** Find & Replace (blank cells)
- **Description:** Replace blank cells with a specified value
- **Parameters:**
  - `columns` (column_list) - Columns to fill
  - `fill_value` (text) - Value for blank cells (default: "N/A")
- **Example Use:** Fill empty phone numbers with "N/A"
- **Common Use Case:** Handle missing data, prepare for export

### 15. Remove Columns
- **ID:** `clean_remove_columns`
- **Excel Equivalent:** Delete columns
- **Description:** Delete one or more columns from the data
- **Parameters:**
  - `columns` (column_list) - Columns to remove
- **Example Use:** Remove unnecessary ID columns
- **Common Use Case:** Clean up exports, remove internal fields

### 16. Keep Columns (Remove Everything Else)
- **ID:** `clean_keep_columns`
- **Excel Equivalent:** Hide/Delete columns (inverse)
- **Description:** Keep only selected columns and remove all others
- **Parameters:**
  - `columns_to_keep` (column_list) - Columns to keep
- **Example Use:** Keep only Name, Email, Phone from 50-column export
- **Common Use Case:** Simplify datasets with many columns, extract specific fields
- **Special Behavior:**
  - If some selected columns don't exist, operation proceeds with columns that do exist (lenient validation)
  - Preserves original DataFrame column order (not selection order)
  - More efficient than selecting dozens of columns to remove when you only want a few columns

---

## Math Operations

### 16. Add Columns
- **ID:** `math_add_columns`
- **Excel Equivalent:** `=A1+B1`
- **Description:** Add two or more columns together
- **Parameters:**
  - `columns` (column_list) - Columns to add
  - `new_column` (text) - Name for result column
- **Example Use:** Quantity + Bonus = Total
- **Common Use Case:** Sum numeric fields

### 17. Multiply Columns
- **ID:** `math_multiply`
- **Excel Equivalent:** `=A1*B1`
- **Description:** Multiply two columns (e.g., quantity × price)
- **Parameters:**
  - `column1` (column) - First column
  - `column2` (column) - Second column
  - `new_column` (text) - Name for result
- **Example Use:** Quantity × Price = Total
- **Common Use Case:** Calculate totals, products

### 18. SUM - Total of Multiple Columns (Advanced)
- **ID:** `math_sum`
- **Excel Equivalent:** `SUM(A1:E1)`
- **Description:** Add up values across multiple columns
- **Parameters:**
  - `columns` (column_list) - Columns to sum
  - `new_column` (text) - Name for result column
- **Example Use:** Total sales across regions
- **Common Use Case:** Aggregate numeric data

### 19. AVERAGE - Mean of Multiple Columns (Advanced)
- **ID:** `math_average`
- **Excel Equivalent:** `AVERAGE(A1:E1)`
- **Description:** Calculate average across columns
- **Parameters:**
  - `columns` (column_list) - Columns to average
  - `new_column` (text) - Name for result
- **Example Use:** Average score across tests
- **Common Use Case:** Calculate means, performance metrics

### 20. ROUND - Round Numbers (Advanced)
- **ID:** `math_round`
- **Excel Equivalent:** `ROUND(number, decimals)`
- **Description:** Round numbers to specified decimal places
- **Parameters:**
  - `column` (column) - Column to round
  - `decimals` (number) - Number of decimal places
  - `new_column` (text, optional) - Name for result (or overwrite)
- **Example Use:** Round currency to 2 decimals
- **Common Use Case:** Format financial data, clean calculations

### 21. Calculate Percentage (Advanced)
- **ID:** `math_percentage`
- **Excel Equivalent:** `=(A1/B1)*100`
- **Description:** Calculate what percentage one number is of another
- **Parameters:**
  - `numerator_column` (column) - Part (numerator)
  - `denominator_column` (column) - Whole (denominator)
  - `new_column` (text) - Name for percentage column
  - `multiply_by_100` (boolean) - Show as 0-100 vs 0-1 (default: true)
- **Example Use:** Calculate completion percentage
- **Common Use Case:** Progress tracking, ratios

---

## Validation Operations

### 22. Validate Email Addresses
- **ID:** `validate_email`
- **Excel Equivalent:** Complex IF formula
- **Description:** Check if email addresses are properly formatted
- **Parameters:**
  - `column` (column) - Email column
  - `flag_invalid` (boolean) - Create flag column for invalid emails (default: true)
- **Example Use:** Flag invalid customer emails
- **Common Use Case:** Email list validation, data quality checks
- **Validation Pattern:** Must contain @ and . in proper format

---

## Conditional Operations

### 23. Flag If Contains
- **ID:** `conditional_flag_contains`
- **Excel Equivalent:** `=IF(ISNUMBER(SEARCH(...)))`
- **Description:** Flag rows where a column contains specific text
- **Parameters:**
  - `column` (column) - Column to check
  - `text` (text) - Text to search for
  - `flag_column` (text) - Name for flag column (default: "Flag")
- **Example Use:** Flag companies containing "LLC", flag PO Box addresses
- **Common Use Case:** Identify patterns, filter criteria

---

## Date Operations

### 24. Format Date
- **ID:** `date_format`
- **Excel Equivalent:** `TEXT(date,"MM/DD/YYYY")`
- **Description:** Convert dates to a specific format
- **Parameters:**
  - `column` (column) - Date column
  - `format` (choice) - Date format: 'MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD' (default: MM/DD/YYYY)
- **Example Use:** Standardize all dates to MM/DD/YYYY
- **Common Use Case:** Date standardization, international formats

---

## Quick Reference by Use Case

### Mailing List Cleaning
1. Remove Blank Rows (#13)
2. Trim Whitespace (#4) - all text columns
3. Title Case (#3) - names, addresses
4. UPPERCASE (#1) - company, state
5. lowercase (#2) - emails
6. Validate Email (#22)
7. Remove Duplicates (#11) - by email
8. Flag If Contains (#23) - PO Box detection
9. Sort (#12) - alphabetical

### Data Standardization
1. Trim Whitespace (#4)
2. Find and Replace (#8) - fix abbreviations
3. Remove Special Characters (#7)
4. Format Date (#24)
5. UPPER/lower/Title Case (#1, #2, #3)

### Data Enrichment
1. VLOOKUP (#10) - add external data
2. Combine Columns (#5) - create full names/addresses
3. Add Prefix/Suffix (#9) - formatting

### Data Quality
1. Validate Email (#22)
2. Remove Duplicates (#11)
3. Flag If Contains (#23) - pattern detection
4. Fill Missing Values (#14)
5. Remove Blank Rows (#13)

---

## Missing Operations (Compared to Manual Excel Workflows)

Based on analysis of manual data cleaning workflows, these operations are commonly needed but not yet available:

| Missing Operation | Excel Equivalent | Priority | Use Case |
|-------------------|------------------|----------|----------|
| **LEFT** | `=LEFT(A1,5)` | HIGH | Extract first N characters (zip codes, area codes) |
| **RIGHT** | `=RIGHT(A1,4)` | HIGH | Extract last N characters |
| **MID** | `=MID(A1,3,5)` | HIGH | Extract middle portion of text |
| **LEN** | `=LEN(A1)` | HIGH | Get text length for validation |
| **Phone Formatter** | Custom | HIGH | Standardize phone to (XXX) XXX-XXXX |
| **Remove Rows If** | Filter + Delete | HIGH | Delete rows matching criteria |
| **State Validator** | Custom | MEDIUM | Validate 2-letter state codes |
| **Zip Code Formatter** | `=TEXT(A1,"00000")` | MEDIUM | Force 5-digit format |
| **Address Parser** | Text to Columns | MEDIUM | Split full address into parts |
| **PO Box Remover** | Filter + Delete | MEDIUM | Auto-remove PO Box addresses |
| **IF/THEN/ELSE** | `=IF()` | MEDIUM | Conditional value assignment |
| **COUNTIF** | `=COUNTIF()` | LOW | Count matching values |
| **SUMIF** | `=SUMIF()` | LOW | Conditional sum |

---

## Operation Mode Availability

### Simple Mode (14 operations)
- Text: UPPER, lower, Title, Trim, Combine, Split
- Data: Remove Duplicates, Sort, VLOOKUP
- Cleaning: Remove Blanks, Fill Missing
- Math: Add, Multiply
- (Simplified UI, basic parameters only)

### Advanced Mode (All 24 operations)
- All Simple Mode operations
- Text: Remove Special, Find/Replace, Prefix/Suffix
- Math Advanced: SUM, AVERAGE, ROUND, PERCENTAGE
- Validation: Email validation
- Conditional: Flag If Contains
- Dates: Format Date
- (Full parameter control, advanced options)

---

## Next Steps

**To enhance tool capabilities for mailing list workflows:**
1. Add LEFT/RIGHT/MID operations (HIGH priority)
2. Add LEN operation for validation (HIGH priority)
3. Create Phone Number Formatter (HIGH priority)
4. Add "Remove Rows If" conditional deletion (HIGH priority)
5. Create preset: "Standard Mailing List Cleaner"
6. Add state/zip validation operations (MEDIUM priority)

---

**Document Version:** 1.0
**Operations Count:** 24
**Last Audit:** 2025-11-18
