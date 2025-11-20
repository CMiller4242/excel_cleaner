# CRITICAL QUESTION: What Should "is_blank" Check for Addresses?

## Current Finding

When running "Remove Rows If (Person Street is_blank)":

**Current Behavior:**
- Checks ONLY "Person Street" column
- Keeps: 782 rows (those with Person Street data)
- Removes: 1,255 rows (those without Person Street data)
  - But 1,245 of these have **Company Street Address** data!

## Possible Solutions

### Option 1: Check BOTH Person Street AND Company Street Address

**Logic:** Only remove if BOTH columns are blank

**Result:**
- Keep: 2,027 rows (has address in Person OR Company column)
- Remove: 10 rows (blank in BOTH columns)

### Option 2: Current Behavior is Correct

**Logic:** User specifically selected "Person Street", so only check that column

**Result:**
- Keep: 782 rows (only those with Person Street)
- Remove: 1,255 rows (even if they have Company Street)

### Option 3: Let User Choose

Add a parameter "Check Related Columns" that when enabled:
- For address columns, checks Person Street OR Company Street Address
- For email columns, checks all email fields
- Etc.

## Your Numbers vs Reality

You mentioned:
- Expected to keep: 1,450-1,550 valid addresses
- Expected to remove: 500-550 blank rows

My findings:
- Person Street only: Keep 782, Remove 1,255
- Both columns: Keep 2,027, Remove 10

**Your expected numbers (1,450-1,550) are between these two values.**

## Questions:

1. **Which columns should "is_blank" check?**
   - Just the selected column (Person Street)?
   - Both Person Street AND Company Street Address?
   - Something else?

2. **What defines a "valid address" for your use case?**
   - Must have Person Street data?
   - Can have either Person OR Company address?
   - Must have specific type of address (no PO Boxes)?

3. **Is there a different file or different data you're working with?**
   - I only see "Volunteer Directors 11.20.25.xlsx"
   - Does your GUI show different numbers?

## What I Need

Please clarify EXACTLY what you want the operation to do:

```
When I run "Remove Rows If (Person Street is_blank)":
- Check [ ] Person Street only
- Check [ ] Person Street AND Company Street Address
- Check [ ] Something else: _________________

Keep a row if:
- [ ] It has data in Person Street
- [ ] It has data in Person Street OR Company Street Address
- [ ] It has a valid physical address (not PO Box)
- [ ] Something else: _________________
```

Once I know exactly what you want, I can implement the correct fix.
