# Reorder Columns Dialog - User Guide

## Overview

The **Reorder Columns** operation now has a specialized, user-friendly dialog that makes it easy to arrange columns in your desired order.

## Features

### 1. Visual Column List
- See all columns currently in your loaded data
- Columns displayed with Excel-style letter prefixes (A, B, C, etc.)
- Easy-to-read format: "A: Column Name"

### 2. Reordering Controls
Four buttons to move selected columns:
- **⬆ Move Up**: Move selected column up one position
- **⬇ Move Down**: Move selected column down one position
- **⤒ Move to Top**: Move selected column to first position
- **⤓ Move to Bottom**: Move selected column to last position

### 3. Keep Unlisted Checkbox
- **Checked**: Columns not in the reordered list will be kept and appended at the end
- **Unchecked**: Only columns in the reordered list will be kept (others will be removed)

### 4. Live Preview
- See the final column order as you rearrange
- Preview updates automatically when you move columns or toggle the checkbox

## How to Use

### Basic Reordering

1. **Load your data file** containing the columns you want to reorder

2. **Select "Reorder Columns"** from the operations menu

3. **Arrange columns**:
   - Click on a column to select it
   - Click the arrow buttons to move it up/down
   - Repeat for each column you want to reposition

4. **Set keep_unlisted option**:
   - Check the box if you want to keep all columns (reordered ones first, others at end)
   - Uncheck if you only want the columns in your reordered list

5. **Preview the result** in the preview section at the bottom

6. **Click "Add to Queue"** to add the operation

### Example Use Cases

#### Example 1: Reorder All Columns

You have 10 columns and want them in a specific order:

1. Arrange all 10 columns in desired order using arrow buttons
2. **Uncheck** "Keep unlisted" (since you've arranged all of them)
3. Result: Exactly those 10 columns in your specified order

#### Example 2: Put Key Columns First

You have 20 columns but only care about putting 5 key columns first:

1. Move your 5 key columns to the top in desired order
2. **Check** "Keep unlisted"
3. Result: Your 5 key columns first, followed by the other 15 columns

#### Example 3: Standard Mailing List Format

Reorder to standard mailing list format:

```
1. Company
2. Address 1
3. Address 2
4. City
5. State
6. Zip
7. Phone
8. Contact
9. Title
10. Email
```

Steps:
1. Move "Company" to top
2. Move "Address 1" to position 2
3. Continue arranging remaining columns
4. Uncheck "Keep unlisted" (to only keep these 10)
5. Add to queue

## Parameters Generated

When you click "Add to Queue", the operation creates parameters:

```json
{
  "column_order": ["Column1", "Column2", "Column3", ...],
  "keep_unlisted": true/false
}
```

### column_order
A list of column names in the order they should appear

### keep_unlisted
- `false`: Only columns in column_order will be kept (others dropped)
- `true`: Columns in column_order appear first, remaining columns appended at end

## Tips

### Efficient Reordering
- Use "Move to Top" to quickly bring columns to the beginning
- Use "Move to Bottom" to push columns to the end
- Select and move one at a time for precise control

### Keyboard Shortcuts
While a column is selected:
- Click arrow buttons or use mouse to select and move

### Preview is Your Friend
Always check the preview before adding to queue:
- Verify column order is correct
- Ensure keep_unlisted setting matches your intent
- Preview shows exactly what your final DataFrame will look like

## Common Patterns

### Pattern 1: Standard Format Transformation
Transform non-standard column names and order to standard format:

```
Before: First Name, Last Name, Company Name, Email, Phone Number, ...
After: Company, Contact, Email, Phone, ...
```

Note: You may need to combine this with "Rename Columns" or "Concatenate" operations

### Pattern 2: Move ID Columns to End
Keep all columns but move metadata/ID columns to the end:

```
Before: ID, Record_ID, Modified_Date, Name, Email, Phone
After: Name, Email, Phone, ID, Record_ID, Modified_Date
```

1. Arrange Name, Email, Phone at top
2. Check "Keep unlisted"
3. ID columns will automatically go to end

### Pattern 3: Export Subset
Keep only specific columns for export:

```
Before: 50 columns
After: 10 columns (only the ones you want)
```

1. Arrange your 10 desired columns
2. Uncheck "Keep unlisted"
3. Other 40 columns will be dropped

## Troubleshooting

### Column Not in List
If a column you need isn't showing:
- Ensure data is loaded
- Check if column was removed by a previous operation
- Verify column name spelling

### Wrong Final Order
If preview shows unexpected order:
- Check which column is currently selected
- Verify keep_unlisted checkbox setting
- Remember: preview shows exact final result

### Too Many Columns
If you have 50+ columns:
- Use scroll bar to navigate list
- Consider using keep_unlisted=true and only arrange top columns
- Or use "Remove Columns" operation first to reduce to manageable set

## Integration with ZoomInfo Preset

The ZoomInfo Healthcare/EVS preset uses this operation as the final step:

```json
{
  "operation_id": "data_reorder_columns",
  "parameters": {
    "column_order": [
      "Company", "Address 1", "Address 2", "City",
      "State", "Zip", "Phone", "Contact", "Title", "Email"
    ],
    "keep_unlisted": false
  }
}
```

This ensures the final output has exactly 10 columns in standard mailing list format.

## Technical Details

### Operation ID
`data_reorder_columns`

### Implementation
- Operation: `ReorderColumnsOperation` in `operations/data_ops.py`
- Dialog: `_show_reorder_columns_dialog()` in `main_gui_v2.py`

### Validation
Before executing:
- Validates all columns in column_order exist
- Ignores columns that don't exist (no error)
- If keep_unlisted=False, only specified columns are kept

### Performance
- Fast operation (no data transformation, just column selection/reordering)
- Works on DataFrames of any size
- Memory efficient (no data copying beyond normal pandas operations)

---

## See Also

- **Remove Columns**: To delete unwanted columns before reordering
- **Rename Columns**: To standardize column names before reordering
- **Concatenate**: To combine columns before reordering
- **ZoomInfo Preset**: Complete workflow using reorder as final step
