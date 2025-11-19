# New Features Documentation

## Feature 1: Multi-Sheet Export System

### Overview
The Universal Excel Tool now exports results as a comprehensive multi-sheet workbook instead of a single sheet. This preserves all data and provides complete transparency about what operations did.

### Three-Sheet Structure

#### Sheet 1: "Original"
- **Contents**: The raw, unmodified input file data
- **Purpose**: Reference the starting point of your data transformations
- **Columns**: All original columns from the input file

#### Sheet 2: "Results"
- **Contents**: The final processed data after all operations are applied
- **Purpose**: Your cleaned, transformed, ready-to-use data
- **Columns**: Columns after transformations (renamed, reordered, concatenated, etc.)

#### Sheet 3: "Removed"
- **Contents**: All rows that were deleted during operations
- **Purpose**: Audit trail for data quality and compliance
- **Columns**: All original columns PLUS metadata columns:
  - `_Removed_By`: Name of the operation that removed this row
  - `_Operation_ID`: Technical ID of the operation
  - `_Step`: Which step in the queue removed this row (1, 2, 3, etc.)

### Which Operations Track Removed Rows?

The following operations automatically track removed rows:
- **Remove Blank Rows**: Tracks completely empty rows
- **Remove Rows Containing**: Tracks rows with specified text
- **Remove Rows If**: Tracks rows matching conditions (blank, not blank, equals, contains, etc.)
- **Remove Excluded States**: Tracks rows with AK, HI, PR, VI states
- **Remove Duplicates**: Tracks duplicate rows
- Any other operation that reduces row count

### How It Works

#### During Execution
1. Load your data file
2. Build your operation queue
3. Click "Execute Queue"
4. The executor:
   - Takes a snapshot before each operation
   - Compares indices after each operation
   - Identifies which rows were removed
   - Stores removed rows with operation metadata

#### During Save
1. Click "Save Results"
2. Choose Excel format (.xlsx)
3. The tool exports three sheets:
   - Original: Your input data
   - Results: Your processed data
   - Removed: All deleted rows with metadata

**Note**: CSV format only saves the Results sheet (CSV doesn't support multiple sheets)

### Example Workflow

**Input**: ZoomInfo Healthcare export (1,577 rows, 73 columns)

**Operations**:
1. Remove Blank Rows → Removes 5 rows
2. Remove Non-Standard Columns → Keeps 10 columns
3. Combine First + Last Name → Creates "Contact" column
4. Split Address → Creates "Address 1" and "Address 2"
5. Rename Columns → Standardizes names
6. Convert State Names → OH, IL, etc.
7. Remove Excluded States → Removes 127 rows (AK, HI, PR, VI)
8. Remove Blank Address 1 → Removes 43 rows
9. Reorder Columns → Final order

**Export Results**:
- **Original Sheet**: 1,577 rows × 73 columns
- **Results Sheet**: 1,402 rows × 10 columns
- **Removed Sheet**: 175 rows × 76 columns (73 original + 3 metadata)

**Removed Sheet Example**:
```
Company Name | Person Street | Person City | ... | _Removed_By | _Operation_ID | _Step
ABC Corp     | (blank)       | Chicago     | ... | Remove Blank Address 1 | data_remove_rows_if | 8
XYZ Inc      | 123 Main St   | Honolulu    | ... | Remove Excluded States | remove_excluded_states | 7
```

### Success Message

After saving, you'll see a message like:
```
Workbook saved to: output.xlsx

Sheets:
• Original: 1,577 rows
• Results: 1,402 rows
• Removed: 175 rows
```

### Benefits

1. **Data Integrity**: No data is ever lost - it's just organized
2. **Audit Trail**: See exactly what was removed and why
3. **Compliance**: Prove you didn't arbitrarily delete data
4. **Debugging**: Understand why certain rows were filtered out
5. **Recovery**: Can recover removed rows if needed
6. **Reporting**: Show stakeholders the full picture

### Use Cases

#### Use Case 1: Compliance Audit
**Scenario**: Your boss asks "Why did we go from 1,577 records to 1,402?"

**Answer**: Open the "Removed" sheet and filter by `_Removed_By`:
- 127 rows removed by "Remove Excluded States" (AK, HI, PR, VI)
- 43 rows removed by "Remove Blank Address 1"
- 5 rows removed by "Remove Blank Rows"
- Total: 175 rows removed

#### Use Case 2: Data Quality Review
**Scenario**: You want to see which records were filtered out by state

**Solution**: Filter "Removed" sheet where `_Removed_By` = "Remove Excluded States", then examine those records

#### Use Case 3: Mistake Recovery
**Scenario**: Oops! You removed rows you didn't mean to

**Solution**: Copy the rows from the "Removed" sheet and paste them back into "Results"

### Technical Details

#### Memory Impact
- Minimal: We only store removed rows, not every intermediate state
- For a 10,000 row file with 20% removal, memory increase is ~20%

#### Performance
- Negligible: Index comparison is very fast in pandas
- Adds ~5-10ms per operation that removes rows
- Total overhead for typical workflow: <100ms

#### CSV Export
- When saving as CSV, only the Results sheet is exported
- You'll see a note: "CSV format only saves Results sheet"
- Use Excel format to preserve all sheets

---

## Feature 2: Preset Overwrite Feature

### Overview
You can now update existing presets instead of being forced to create new ones every time. This makes preset management much more convenient.

### How It Works

#### Saving a New Preset
1. Build your operation queue
2. Click "Save as Preset"
3. Enter a unique name (e.g., "My Custom Workflow")
4. Enter a description
5. Click "Save"
6. Success message: "Preset 'My Custom Workflow' saved!"

#### Updating an Existing Preset
1. Build your operation queue
2. Click "Save as Preset"
3. Enter the SAME name as an existing preset (e.g., "My Custom Workflow")
4. **Confirmation Dialog Appears**:
   ```
   Preset Exists

   A preset named 'My Custom Workflow' already exists.

   Do you want to overwrite it?

   • Yes = Overwrite existing preset
   • No = Enter a different name
   • Cancel = Cancel save
   ```
5. Click your choice:
   - **Yes**: Overwrites the preset with new operations
   - **No**: Clears the name field so you can enter a different name
   - **Cancel**: Closes the dialog without saving

#### After Overwriting
- Success message: "Preset 'My Custom Workflow' updated successfully!"
- The preset file is updated with new operations
- The `created_at` timestamp is preserved (shows when originally created)
- The `updated_at` timestamp is set to now (shows when last modified)
- All operation definitions are replaced with your current queue

### Example Workflow

#### Initial Save
```
1. Create operations:
   - Remove Blank Rows
   - Trim Whitespace
   - Remove Duplicates

2. Save as "Quick Clean"

3. Result: Quick Clean preset created
```

#### Update Preset
```
1. Create different operations:
   - Remove Blank Rows
   - Trim Whitespace
   - Remove Duplicates
   - Standardize Phone Numbers  ← NEW!
   - Standardize Email Format   ← NEW!

2. Save as "Quick Clean" (same name)

3. Dialog appears asking to overwrite

4. Click "Yes"

5. Result: Quick Clean preset now has 5 operations instead of 3
```

### Benefits

1. **Iterative Development**: Refine presets as you improve your workflow
2. **No Clutter**: Don't end up with "Quick Clean v2", "Quick Clean v3", etc.
3. **Easy Updates**: Fix mistakes or add improvements to existing presets
4. **Version Control**: `created_at` and `updated_at` timestamps track history
5. **Safety**: Confirmation dialog prevents accidental overwrites

### Use Cases

#### Use Case 1: Fixing a Preset
**Scenario**: You discover your "ZoomInfo Import" preset is missing a step

**Solution**:
1. Load the preset
2. Add the missing operation
3. Save with same name "ZoomInfo Import"
4. Confirm overwrite
5. Preset is fixed for future use

#### Use Case 2: Seasonal Updates
**Scenario**: Your mailing list workflow changes for holiday campaigns

**Solution**:
1. Load "Holiday Mailing List" preset
2. Modify operations for this year's campaign
3. Save with same name
4. Overwrite with updated workflow

#### Use Case 3: A/B Testing Workflows
**Scenario**: Testing two different cleaning approaches

**Solution**:
1. Try approach A, save as "Test Workflow"
2. Try approach B, save as "Test Workflow" → overwrite
3. Compare results
4. Save final version with production name

### Technical Details

#### What Gets Preserved
- `id`: Preset identifier (based on name)
- `created_at`: Original creation timestamp
- File location: Same file in presets directory

#### What Gets Updated
- `name`: Can be updated
- `description`: Can be updated
- `operations`: Completely replaced with new queue
- `updated_at`: Set to current timestamp

#### File Structure
Before overwrite:
```json
{
  "id": "quick_clean",
  "name": "Quick Clean",
  "description": "Basic cleaning",
  "operations": [...3 operations...],
  "created_at": "2025-01-01T10:00:00",
  "updated_at": "2025-01-01T10:00:00"
}
```

After overwrite:
```json
{
  "id": "quick_clean",
  "name": "Quick Clean",
  "description": "Enhanced cleaning",
  "operations": [...5 operations...],
  "created_at": "2025-01-01T10:00:00",  ← PRESERVED
  "updated_at": "2025-01-19T15:30:00"   ← UPDATED
}
```

#### System Presets
- System presets (like "ZoomInfo - Healthcare/EVS Export") cannot be overwritten
- They are read-only and stored in `presets/system/`
- Only user presets in `presets/user/` can be overwritten

### Dialog Options Explained

#### Yes (Overwrite)
- Replaces existing preset with current operations
- Preserves created_at timestamp
- Updates updated_at timestamp
- Shows success message: "Preset updated successfully!"

#### No (Different Name)
- Clears the name field
- Keeps the dialog open
- Allows you to enter a different preset name
- Shows info message: "Please enter a different preset name"

#### Cancel
- Closes the dialog
- Does not save anything
- Returns to main application

---

## Frequently Asked Questions

### Multi-Sheet Export

**Q: Can I export just the Results sheet?**
A: Yes! Save as CSV format, which only exports the Results sheet.

**Q: What if no rows were removed?**
A: The "Removed" sheet won't be created. You'll see:
- Original sheet
- Results sheet

**Q: Can I see which specific operation removed each row?**
A: Yes! Sort the "Removed" sheet by `_Step` column to see removals in order, or filter by `_Removed_By` to see rows removed by a specific operation.

**Q: Do the removed rows include all columns from the original file?**
A: Yes! The "Removed" sheet has all original columns plus 3 metadata columns (_Removed_By, _Operation_ID, _Step).

**Q: What if I add columns during processing (like "Contact" from concatenation)?**
A: Removed rows show the state they were in when removed. So if removed before concatenation, they won't have the "Contact" column.

### Preset Overwrite

**Q: Can I overwrite system presets like "ZoomInfo - Healthcare/EVS"?**
A: No, system presets are read-only. The overwrite feature only works for user-created presets.

**Q: What happens if I click "No" when asked to overwrite?**
A: The dialog stays open, the name field is cleared, and you can enter a different name.

**Q: Can I see when a preset was last updated?**
A: Yes, preset files have `created_at` and `updated_at` timestamps. These will be visible if you load the preset JSON file.

**Q: If I overwrite a preset, can I undo it?**
A: No, the old operations are permanently replaced. Make sure you want to overwrite before confirming.

**Q: Does overwriting change the preset ID?**
A: No, the preset ID (based on the name) stays the same.

---

## Tips and Best Practices

### Multi-Sheet Export
1. **Always use Excel format** if you want all three sheets
2. **Review the Removed sheet** before deleting the workbook
3. **Filter removed rows by operation** to understand your data quality
4. **Export intermediate results** if you want to see data at different stages
5. **Archive removed rows** for compliance and audit purposes

### Preset Overwrite
1. **Use consistent naming** for presets you plan to update frequently
2. **Test before overwriting** - make sure your new operations work first
3. **Document changes** in the description field when overwriting
4. **Back up important presets** by exporting the JSON file
5. **Use versioning for major changes** (e.g., "Import v1", "Import v2") instead of overwriting

---

## Troubleshooting

### Multi-Sheet Export Issues

**Problem**: Removed sheet is empty
**Solution**: This means no rows were removed by any operations. Check that you have operations that filter/remove data.

**Problem**: Can't see metadata columns in Excel
**Solution**: Scroll to the right - they're the last 3 columns (_Removed_By, _Operation_ID, _Step)

**Problem**: CSV only has Results
**Solution**: Expected behavior - use Excel format for multi-sheet export

### Preset Overwrite Issues

**Problem**: Dialog doesn't appear when entering existing name
**Solution**: Make sure you're entering the exact same name (case-insensitive). The system matches on preset ID, which is the name in lowercase with underscores.

**Problem**: Can't overwrite a preset
**Solution**: Check if it's a system preset - they're read-only. Only user presets can be overwritten.

**Problem**: Overwrite succeeded but preset didn't change
**Solution**: Reload the preset to see changes. The preset manager caches presets, so you may need to restart the application to see updates.
