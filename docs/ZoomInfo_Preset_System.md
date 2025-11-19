# ZoomInfo Preset System Documentation

## Overview

The ZoomInfo Preset System provides automated, editable workflows for transforming ZoomInfo exports into standardized mailing list formats. It includes intelligent file detection, customizable operation sequences, and interactive UI for reviewing and modifying transformations.

## Key Features

- **Auto-Detection**: Automatically identifies ZoomInfo files and suggests appropriate presets
- **Editable Operations**: Users can modify any operation parameter before execution
- **Interactive UI**: Preview and edit operations with visual feedback
- **Tested Transformations**: Pre-configured sequences tested with real ZoomInfo exports
- **Extensible Framework**: Easy to add new presets for other file types (LinkedIn, SugarCRM, etc.)

---

## ZoomInfo Healthcare/EVS Preset

### Purpose

Transforms ZoomInfo Healthcare/EVS exports (typically 73 columns, 1000+ rows) into a clean 10-column standard mailing list format.

### File Characteristics

- **Expected Columns**: First Name, Last Name, Job Title, Direct Phone Number, Email Address, Person Street, Person City, Person State, Person Zip Code, Company Name, ZoomInfo Contact ID
- **Typical Size**: 1,500-2,000 rows, 73 columns
- **Key Indicator**: Contains "ZoomInfo Contact ID" and "Person Street" columns

### Transformation Sequence

#### Phase 1: Clean Empty Data
```
Operation: Remove Blank Rows
- Removes rows where all cells are empty
- Editable: No (required operation)
```

#### Phase 2: Combine Names
```
Operation: Concatenate Columns
- Combines: First Name + Last Name → Contact
- Separator: space
- Removes: First Name, Last Name columns
- Editable: Yes (can change separator)
```

#### Phase 3: Split Addresses
```
Operation: Split Address Column
- Source: Person Street
- Detects suite keywords: Ste, Suite, Unit, Apt, Bldg, Floor
- Creates: Address 1 (street) + Address 2 (suite/unit)
- Logic: Finds LAST occurrence of suite keyword
- Editable: Yes (can modify suite keywords)

Examples:
  "400 W Illinois Ave Ste 950" →
    Address 1: "400 W Illinois Ave"
    Address 2: "Ste 950"

  "3715 Northside Pkwy NW Bldg 300 Ste 110" →
    Address 1: "3715 Northside Pkwy NW"
    Address 2: "Bldg 300 Ste 110"

  "251 Stenton Ave" →
    Address 1: "251 Stenton Ave"
    Address 2: "" (blank)
```

#### Phase 4: Rename Columns
```
Operations: Rename Column (x7)
- Person City → City
- Person State → State
- Person Zip Code → Zip
- Job Title → Title
- Direct Phone Number → Phone
- Email Address → Email
- Company Name → Company
- Editable: Yes (can modify target names)
```

#### Phase 5: Convert State Names
```
Operation: Convert State Names to Codes
- Converts: "Ohio" → "OH", "Illinois" → "IL", etc.
- Handles: Full names, abbreviations, case-insensitive
- Leaves existing 2-letter codes unchanged
- Editable: Yes (can enable flag_unconverted)

Examples:
  "Ohio" → "OH"
  "Virgin Islands" → "VI"
  "IL" → "IL" (unchanged)
  "Calif." → "CA"
```

#### Phase 6: Remove Excluded States
```
Operation: Remove Excluded States
- Removes: Alaska (AK), Hawaii (HI), Puerto Rico (PR), Virgin Islands (VI)
- Reason: Mainland-only mailing campaigns
- Editable: Yes (can modify exclusion list)
```

#### Phase 7: Remove Invalid Rows
```
Operation: Remove Rows If Blank
- Removes: Any row with blank Address 1
- Ensures: All output has valid street address
- Editable: Yes (can change condition)
```

#### Phase 8: Remove Non-Standard Columns
```
Operation: Remove Columns
- Removes: 63 non-standard columns including:
  * ZoomInfo IDs and URLs
  * Industry codes (SIC, NAICS)
  * Company metadata (revenue, employees, funding)
  * Social media links
  * Query metadata
- Editable: Yes (can modify list)
- Required: No (can skip if you want to keep some columns)
```

#### Phase 9: Reorder to Standard Format
```
Operation: Reorder Columns
- Final order:
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
- Editable: Yes (can change order)
```

### Expected Results

- **Input**: 1,577 rows × 73 columns
- **Output**: ~1,400 rows × 10 columns
- **Row Reduction**: ~10-15% (due to excluded states and blank addresses)
- **All States**: 2-letter codes only
- **All Addresses**: Split into street + suite
- **No**: Alaska, Hawaii, PR, VI, or blank addresses

---

## Using the Preset System

### Method 1: Auto-Detection (Recommended)

1. **Load File**
   ```python
   # In your application
   df = pd.read_excel("EVS_export.xlsx")
   ```

2. **Analyze Data Quality**
   - Click "Analyze Data Quality"
   - System automatically detects ZoomInfo file
   - Shows alert: "ZoomInfo File Detected - Preset Available"

3. **Load Suggested Preset**
   - Click "Load Preset" button in the alert
   - Preset Editor opens with all 15 operations

4. **Review & Edit Operations**
   - Each operation shows:
     - ✓ or ⊗ (enabled/disabled)
     - Operation name and description
     - Current parameters
     - [Edit] and [Skip] buttons
   - Edit any operation to modify parameters
   - Skip non-required operations if needed

5. **Run Operations**
   - Click "Run All" (enables all operations)
   - Or "Run Selected" (runs only checked operations)
   - All operations execute in sequence

### Method 2: Manual Preset Loading

```python
from utils.preset_manager import PresetManager

# Load preset
manager = PresetManager()
preset_data = manager.load_preset("zoominfo_healthcare_evs")

# Show editor
from utils.preset_editor_ui import show_preset_editor
operations = show_preset_editor(root, preset_data, df)

if operations:
    # Execute operations...
    for op in operations:
        df = execute_operation(df, op)
```

### Method 3: Programmatic Detection

```python
from utils.preset_manager import detect_and_suggest_preset

# Detect file type
detection = detect_and_suggest_preset(df)

if detection:
    print(f"File type: {detection['file_type']}")
    print(f"Suggested preset: {detection['preset_name']}")
    print(f"Confidence: {detection['confidence']:.0%}")

    # Load preset
    preset_data = detection['preset_data']
    # ... continue with preset execution
```

---

## Editing Operations

### Edit Dialog Interface

When you click **[Edit]** on an operation, a dialog opens showing:

1. **Operation Name & Description**
2. **Parameter Inputs**
   - Column dropdowns for column parameters
   - Text inputs for strings
   - Checkboxes for booleans
   - Comma-separated lists for arrays
3. **Preview** (for some operations)
4. **Apply / Cancel** buttons

### Example: Edit Split Address

```
┌─────────────────────────────────────────────┐
│ Edit: Split Address Column                 │
├─────────────────────────────────────────────┤
│ source_column: [Person Street ▼]            │
│                                             │
│ suite_keywords:                             │
│ [Ste,Suite,Unit,Apt,Bldg,Floor]            │
│                                             │
│ address1_column: [Address 1]               │
│                                             │
│ address2_column: [Address 2]               │
│                                             │
│ remove_original: ☑                          │
│                                             │
│ [ Apply ] [ Cancel ]                       │
└─────────────────────────────────────────────┘
```

**Common Modifications:**
- Add more suite keywords: "Ste,Suite,Unit,Apt,Bldg,Floor,Rm,Room"
- Change source column if file has different name
- Change output column names
- Disable remove_original to keep original column

### Example: Edit Remove Excluded States

```
┌─────────────────────────────────────────────┐
│ Edit: Remove Excluded States               │
├─────────────────────────────────────────────┤
│ column: [State ▼]                           │
│                                             │
│ excluded_states:                            │
│ [AK,HI,PR,VI]                              │
│                                             │
│ [ Apply ] [ Cancel ]                       │
└─────────────────────────────────────────────┘
```

**Common Modifications:**
- Add more states: "AK,HI,PR,VI,GU,AS,MP" (all territories)
- Remove a state: "AK,HI,PR" (keep Virgin Islands)
- Change to different exclusions based on campaign

---

## Technical Implementation

### New Operations

#### 1. `zoominfo_split_address`

**Purpose**: Split full address into street + suite/unit

**Parameters**:
- `source_column` (str): Column containing full address
- `suite_keywords` (list): Keywords to detect (Ste, Suite, Unit, etc.)
- `address1_column` (str): Output column for street
- `address2_column` (str): Output column for suite/unit
- `remove_original` (bool): Remove source column after split

**Logic**:
1. Find LAST occurrence of any suite keyword (case-insensitive)
2. Split at that point
3. Address 1 = everything before suite keyword (trimmed)
4. Address 2 = suite keyword + everything after (trimmed)
5. If no suite keyword found: Address 1 = full address, Address 2 = blank

**Edge Cases Handled**:
- Multiple suite keywords: "Bldg 300 Ste 110" → Address 2 contains both
- Directionals: "1330 Maryland Ave SW" → SW stays in Address 1
- No suite: "251 Stenton Ave" → Address 2 is blank
- Case insensitive: "ste", "STE", "Ste" all work

#### 2. `zoominfo_state_converter`

**Purpose**: Convert state names to 2-letter codes

**Parameters**:
- `column` (str): Column containing state names/codes
- `flag_unconverted` (bool): Create flag column for unconverted values

**State Mapping**:
- 50 states + DC
- Full names: "Ohio" → "OH"
- Abbreviations: "Ill." → "IL", "Calif." → "CA"
- Case-insensitive: "ohio" → "OH"
- Already 2-letter: "IL" → "IL" (unchanged)
- Territories: "Puerto Rico" → "PR", "Virgin Islands" → "VI"

**Returns**:
- Updates column with 2-letter codes
- Optional: Creates `{column}_Converted` flag column

#### 3. `remove_excluded_states`

**Purpose**: Remove rows with specific state codes

**Parameters**:
- `column` (str): Column containing state codes
- `excluded_states` (list): State codes to remove

**Default Exclusions**: AK, HI, PR, VI

**Logic**:
- Case-insensitive matching
- Removes entire row if state matches any in exclusion list
- Resets index after removal

#### 4. `data_reorder_columns`

**Purpose**: Reorder columns to specific sequence

**Parameters**:
- `column_order` (list): Ordered list of column names
- `keep_unlisted` (bool): Keep unlisted columns at end (default: False)

**Logic**:
- Reorders existing columns to match specified order
- Ignores columns in list that don't exist
- Optionally keeps unlisted columns at the end

---

## Preset Manager API

### PresetManager Class

```python
from utils.preset_manager import PresetManager

manager = PresetManager()

# List all presets
presets = manager.list_presets()
# Returns: [{'id': 'zoominfo_healthcare_evs', 'name': '...', ...}]

# List by category
zoominfo_presets = manager.list_presets(category="ZoomInfo")

# Load specific preset
preset_data = manager.load_preset("zoominfo_healthcare_evs")

# Save preset
success = manager.save_preset(preset_data, "my_custom_preset")

# Detect file type
file_type, preset_id, confidence = manager.detect_file_type(df)

# Validate columns
validation = manager.validate_preset_columns("zoominfo_healthcare_evs", df)
# Returns: {
#   'valid': bool,
#   'missing_columns': list,
#   'extra_columns': list,
#   'confidence': float
# }
```

### PresetEditor Class

```python
from utils.preset_manager import PresetEditor

# Create editor
editor = PresetEditor(preset_data)

# Get operations
operations = editor.get_operations()

# Update operation parameters
editor.update_operation(index=2, parameters={'column': 'NewColumn'})

# Enable/disable operation
editor.enable_operation(index=3, enabled=False)

# Remove operation
editor.remove_operation(index=5)

# Add operation
editor.add_operation({'operation_id': '...', ...}, index=10)

# Get updated preset
updated_preset = editor.get_preset_data()
```

---

## Creating New Presets

### Step 1: Define Preset JSON

```json
{
  "id": "my_custom_preset",
  "name": "My Custom Preset",
  "description": "Description of what this preset does",
  "category": "Custom",
  "version": "1.0",
  "expected_columns": [
    "Column1",
    "Column2"
  ],
  "operations": [
    {
      "operation_id": "clean_remove_blank_rows",
      "parameters": {},
      "order": 0,
      "enabled": true,
      "description": "Remove empty rows",
      "editable": false,
      "required": true
    }
  ],
  "expected_output": {
    "columns": 10,
    "column_names": ["Col1", "Col2", ...]
  }
}
```

### Step 2: Save Preset

```python
# Save to presets/system/ directory
manager = PresetManager()
manager.save_preset(preset_data, "my_custom_preset")
```

### Step 3: Add Detection Logic (Optional)

Edit `utils/preset_manager.py`:

```python
def detect_file_type(self, df: pd.DataFrame):
    # Add your detection logic
    if self._detect_my_file_type(df):
        return "MyFileType", "my_custom_preset", 0.95

    # ... existing detection code
```

---

## Testing

### Test Preset with Sample Data

```python
import pandas as pd
from utils.preset_manager import PresetManager
from utils.preset_editor_ui import show_preset_editor

# Load test data
df = pd.read_excel("test_file.xlsx")

# Load preset
manager = PresetManager()
preset = manager.load_preset("zoominfo_healthcare_evs")

# Validate columns
validation = manager.validate_preset_columns("zoominfo_healthcare_evs", df)
print(f"Valid: {validation['valid']}")
print(f"Missing: {validation['missing_columns']}")
print(f"Confidence: {validation['confidence']:.0%}")

# Show editor (manual testing)
operations = show_preset_editor(root, preset, df)

if operations:
    # Execute operations...
    print(f"Would execute {len(operations)} operations")
```

### Edge Case Testing

**Address Splitting**:
```python
test_addresses = [
    "400 W Illinois Ave Ste 950",
    "3715 Northside Pkwy NW Bldg 300 Ste 110",
    "251 Stenton Ave",
    "1330 Maryland Ave SW"
]

# Test each address
for addr in test_addresses:
    df = pd.DataFrame({'Person Street': [addr]})
    # Execute split operation...
    # Verify Address 1 and Address 2
```

**State Conversion**:
```python
test_states = ["Ohio", "Illinois", "IL", "Virgin Islands", "Alaska", "Calif."]

for state in test_states:
    df = pd.DataFrame({'State': [state]})
    # Execute convert operation...
    # Verify conversion
```

---

## Integration with Main GUI

### Add to File Loading

```python
# In main_gui_v2.py load_file() method

def load_file(self):
    # ... load file ...

    # Auto-detect and suggest preset
    from utils.preset_manager import detect_and_suggest_preset

    detection = detect_and_suggest_preset(self.df)

    if detection:
        result = messagebox.askyesno(
            f"{detection['file_type']} File Detected",
            f"This appears to be a {detection['file_type']} export.\n\n"
            f"Would you like to load the '{detection['preset_name']}' preset?\n\n"
            f"Detection confidence: {detection['confidence']:.0%}"
        )

        if result:
            self.load_preset(detection['preset_id'])
```

### Add Preset Menu

```python
# In main_gui_v2.py create_menu() method

def create_menu(self):
    # ... existing menu ...

    # Add Presets menu
    preset_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Presets", menu=preset_menu)

    # List presets
    manager = PresetManager()
    presets = manager.list_presets()

    for preset in presets:
        preset_menu.add_command(
            label=preset['name'],
            command=lambda p=preset: self.load_preset(p['id'])
        )
```

---

## Future Enhancements

### Additional Presets Planned

1. **ZoomInfo - Standard Export** (FOOD_PROC style)
2. **LinkedIn Sales Navigator Export**
3. **SugarCRM Contact Export**
4. **Salesforce Report Export**
5. **HubSpot Contact Export**

### Planned Features

- **Preview Mode**: Show before/after comparison before executing
- **Undo**: Ability to undo preset execution
- **Batch Processing**: Apply preset to multiple files
- **Custom Templates**: Save user-modified presets as templates
- **Operation Library**: Browse and add individual operations
- **Macro Recording**: Record manual operations and save as preset

---

## Troubleshooting

### Preset Not Detected

**Cause**: File doesn't have required indicator columns

**Solution**:
1. Manually load preset: File → Presets → ZoomInfo Healthcare/EVS
2. Review expected columns in preset JSON
3. Edit preset to match your file's columns

### Operation Fails

**Cause**: Column name doesn't match

**Solution**:
1. Click [Edit] on the failing operation
2. Update column parameter to match your file
3. Click Apply and run again

### Wrong Columns Removed

**Cause**: Remove Columns operation removes columns you want to keep

**Solution**:
1. Click [Edit] on "Remove Non-Standard Columns"
2. Remove column names from the list that you want to keep
3. Or click [Skip] to skip this operation entirely

### State Not Converting

**Cause**: State name not in mapping

**Solution**:
1. Contact support to add state to mapping
2. Or manually rename before applying preset

---

## Support

For questions, issues, or feature requests:
- GitHub Issues: [github.com/user/excel_cleaner/issues](https://github.com/user/excel_cleaner/issues)
- Documentation: /docs/ZoomInfo_Preset_System.md
- Examples: /examples/zoominfo_examples/

---

## Version History

### v1.0 (2025-11-19)
- Initial release
- ZoomInfo Healthcare/EVS preset
- Auto-detection system
- Interactive preset editor
- 4 new operations: split_address, state_converter, remove_excluded_states, reorder_columns
- Integration with Data Quality Analyzer
