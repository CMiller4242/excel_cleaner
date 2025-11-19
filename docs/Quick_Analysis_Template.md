# Quick Analysis Template
## Excel File Transformation Analysis - Copy & Fill

**File:** _________________________________

**Analyst:** _________________________________

**Date:** _________________________________

---

## 1. File Overview (5 min)

### Sheets Present

| Sheet Name | Rows | Columns | Purpose/Stage |
|------------|------|---------|---------------|
|            |      |         |               |
|            |      |         |               |
|            |      |         |               |
|            |      |         |               |

### Data Flow
```
[Sheet 1: ___________] (___rows)
    ↓
[Sheet 2: ___________] (___rows)
    ↓
[Sheet 3: ___________] (___rows)
    ↓
[Sheet 4: ___________] (___rows)
```

**Total Reduction:** _____ → _____ rows (___%)

---

## 2. Column Mapping (15-20 min)

### Raw → Working → Final Mapping

| Raw Column Name | Working Column | Transformations | Final Column | Notes |
|-----------------|----------------|-----------------|--------------|-------|
|                 |                |                 |              |       |
|                 |                |                 |              |       |
|                 |                |                 |              |       |
|                 |                |                 |              |       |
|                 |                |                 |              |       |
|                 |                |                 |              |       |
|                 |                |                 |              |       |
|                 |                |                 |              |       |
|                 |                |                 |              |       |
|                 |                |                 |              |       |

### Columns Dropped

| Column Name | Stage Dropped | Reason |
|-------------|---------------|--------|
|             |               |        |
|             |               |        |
|             |               |        |

### Columns Added

| Column Name | Stage Added | Formula/Logic |
|-------------|-------------|---------------|
|             |             |               |
|             |             |               |
|             |             |               |

---

## 3. Transformations Observed (10 min)

### Text Operations Used

- [ ] UPPER() - Columns: _______________________
- [ ] LOWER() - Columns: _______________________
- [ ] PROPER() - Columns: _______________________
- [ ] TRIM() - Columns: _______________________
- [ ] CONCATENATE() - Columns: _______________________
- [ ] SUBSTITUTE() - Find: _______ Replace: _______ Columns: _______
- [ ] LEFT() - Columns: _______ Characters: _____
- [ ] RIGHT() - Columns: _______ Characters: _____
- [ ] MID() - Columns: _______ Start: _____ Length: _____
- [ ] Other: _______________________________________________

### Phone Number Formatting

**Input Format(s):** ___________________________________________

**Output Format:** ___________________________________________

**Formula/Logic:** ___________________________________________

### Address Handling

- [ ] Split full address into components
- [ ] Combine address components
- [ ] Standardize abbreviations (St→Street, etc.)
- [ ] Remove special characters
- [ ] Other: _______________________________________________

---

## 4. Validation & Filtering (10-15 min)

### Row Reduction Analysis

**Starting Rows:** _____
**Ending Rows:** _____
**Removed:** _____ (___%)

### Estimated Removal Reasons

| Reason | Estimated Count | Validation Method |
|--------|----------------|-------------------|
| Blank email | | |
| Invalid email format | | |
| Duplicate email | | |
| Blank company | | |
| Blank name | | |
| PO Box address | | |
| Invalid phone | | |
| Other: _________ | | |

### Validation Formulas Found

```excel
[Copy any validation formulas found in the file here]




```

### Deduplication

- [ ] Duplicates removed
- **Column used for dedup:** _______________________
- **Keep first or last?** _______________________

---

## 5. Comparison to Tool Capabilities (10 min)

### Operations We CAN Replicate

✓ Operation: _______________________________________________
✓ Operation: _______________________________________________
✓ Operation: _______________________________________________
✓ Operation: _______________________________________________
✓ Operation: _______________________________________________

### Operations We CANNOT Replicate (Missing)

✗ Operation: _______________________________________________
✗ Operation: _______________________________________________
✗ Operation: _______________________________________________

### Priority Gap Fixes

1. **HIGH Priority:** _______________________________________________
2. **HIGH Priority:** _______________________________________________
3. **MEDIUM Priority:** _______________________________________________

---

## 6. Recommended Preset Configuration (15 min)

### Operation Sequence

**Phase 1: Cleaning**
1. Remove Blank Rows
2. Trim Whitespace: [columns: _________________]
3. Remove Columns: [columns: _________________]

**Phase 2: Formatting**
4. PROPER case: [columns: _________________]
5. UPPER case: [columns: _________________]
6. LOWER case: [columns: _________________]
7. _________________________________________________
8. _________________________________________________

**Phase 3: Validation**
9. Validate Email: [column: _________________]
10. Flag If Contains: [column: _______ text: _______]
11. _________________________________________________

**Phase 4: Deduplication**
12. Remove Duplicates: [column: _________________]

**Phase 5: Filtering (Manual or Future)**
- Remove rows where: _________________________________
- Remove rows where: _________________________________
- Remove rows where: _________________________________

**Phase 6: Final**
13. Sort by: [column: _________________]
14. _________________________________________________

---

## 7. Quality Metrics (5 min)

| Metric | Value |
|--------|-------|
| Starting Row Count | |
| Ending Row Count | |
| Reduction Rate (%) | |
| Email Validation Pass Rate | |
| Duplicate Records Removed | |
| PO Boxes Removed | |
| Invalid Data Removed | |
| Final Quality Score | % |

---

## 8. Notes & Observations

### Patterns Noticed
_______________________________________________
_______________________________________________
_______________________________________________

### Edge Cases
_______________________________________________
_______________________________________________
_______________________________________________

### Recommendations
_______________________________________________
_______________________________________________
_______________________________________________

---

## 9. Action Items

- [ ] Create preset configuration: "_____________________"
- [ ] Add missing operations: _______________________
- [ ] Test preset on sample data
- [ ] Document final workflow
- [ ] Train team on standardized process
- [ ] Other: _______________________________________________

---

## 10. Summary

**Can we automate this workflow with current tool?** YES / NO / PARTIALLY

**If NO or PARTIALLY, what's needed?**
_______________________________________________
_______________________________________________
_______________________________________________

**Estimated time savings:**
- Manual process: _____ minutes
- Automated process: _____ minutes
- **Savings: _____ minutes per file**

**Recommended next steps:**
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

**Analysis completed by:** _____________________
**Date:** _____________________
**Review status:** DRAFT / REVIEWED / APPROVED
