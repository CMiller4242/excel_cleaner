# UI "Load Preset" Dialog Integration Guide

## Problem Diagnosis

**✓ Backend is working correctly:**
- PresetManager loads all 6 presets including ZoomInfo Healthcare
- `list_presets()` returns correct data
- All JSON files are valid
- Cache is populated on startup

**❌ Issue is in the UI code:**
- The "Load Preset" dialog is not calling the PresetManager correctly
- OR the dialog is not displaying the returned data
- Only "Mail List Cleaner - Quick" appears (hardcoded?)

---

## Required Fix in UI Code

### Step 1: Initialize PresetManager on Application Startup

In your main application `__init__` or startup method:

```python
from utils.preset_manager import PresetManager
from utils.preset_initializer import initialize_presets_on_startup

class UniversalExcelTool:
    def __init__(self):
        # ... other initialization ...

        # Initialize preset system (creates user directory if needed)
        initialize_presets_on_startup()

        # Create PresetManager instance
        self.preset_manager = PresetManager()

        print(f"Loaded {len(self.preset_manager._presets_cache)} presets")
```

### Step 2: Fix "Load Preset" Dialog Population

**BEFORE (Broken - Hardcoded):**
```python
def show_load_preset_dialog(self):
    dialog = QDialog(self)
    dialog.setWindowTitle("Load Preset")

    # ❌ WRONG: Hardcoded preset list
    preset_list = QListWidget()
    preset_list.addItem("Mail List Cleaner - Quick")

    # ... rest of dialog
```

**AFTER (Fixed - Dynamic from PresetManager):**
```python
def show_load_preset_dialog(self):
    dialog = QDialog(self)
    dialog.setWindowTitle("Load Preset")

    # ✓ CORRECT: Load presets from PresetManager
    available_presets = self.preset_manager.list_presets()

    print(f"DEBUG: Found {len(available_presets)} presets")
    for p in available_presets:
        print(f"  - {p['name']} (Category: {p.get('category', 'N/A')})")

    # Create list widget
    preset_list = QListWidget()

    # Populate with actual presets from manager
    for preset in available_presets:
        # Create display text with category
        category = preset.get('category', 'Other')
        display_text = f"[{category}] {preset['name']}"

        # Add item to list
        item = QListWidgetItem(display_text)

        # Store preset ID in item data for later retrieval
        item.setData(Qt.UserRole, preset['id'])

        preset_list.addItem(item)

    # ... rest of dialog setup ...

    layout = QVBoxLayout()
    layout.addWidget(QLabel("Select a preset:"))
    layout.addWidget(preset_list)

    # Add buttons
    button_box = QDialogButtonBox(
        QDialogButtonBox.Ok | QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)

    dialog.setLayout(layout)

    # Show dialog and handle selection
    if dialog.exec_() == QDialog.Accepted:
        selected_item = preset_list.currentItem()
        if selected_item:
            preset_id = selected_item.data(Qt.UserRole)
            self.load_and_apply_preset(preset_id)
```

### Step 3: Load and Apply Selected Preset

```python
def load_and_apply_preset(self, preset_id: str):
    """
    Load preset and add operations to queue

    Args:
        preset_id: ID of preset to load (e.g., 'zoominfo_healthcare_evs')
    """
    print(f"Loading preset: {preset_id}")

    # Load preset data
    preset = self.preset_manager.load_preset(preset_id)

    if not preset:
        QMessageBox.warning(
            self,
            "Preset Error",
            f"Failed to load preset: {preset_id}"
        )
        return

    # Get operations from preset
    operations = preset.get('operations', [])

    if not operations:
        QMessageBox.warning(
            self,
            "Empty Preset",
            f"Preset '{preset['name']}' has no operations"
        )
        return

    # Add each operation to queue
    added_count = 0
    for operation_config in operations:
        # Skip disabled operations
        if not operation_config.get('enabled', True):
            continue

        operation_id = operation_config.get('operation_id')
        parameters = operation_config.get('parameters', {})

        # Add to operation queue
        self.operation_queue.add_operation(
            operation_id=operation_id,
            parameters=parameters
        )

        added_count += 1

    # Show success message
    QMessageBox.information(
        self,
        "Preset Loaded",
        f"Added {added_count} operations from '{preset['name']}' to queue"
    )

    # Refresh operation queue display
    self.refresh_operation_queue_display()
```

---

## Complete Working Example

Here's a complete, copy-paste ready implementation:

```python
# In your main GUI class

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QDialogButtonBox,
    QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt
from utils.preset_manager import PresetManager
from utils.preset_initializer import initialize_presets_on_startup

class YourMainWindow:
    def __init__(self):
        # ... other init code ...

        # Initialize preset system
        initialize_presets_on_startup()
        self.preset_manager = PresetManager()

    def on_load_preset_clicked(self):
        """Called when user clicks 'Load Preset' button"""
        self.show_load_preset_dialog()

    def show_load_preset_dialog(self):
        """Show dialog to select and load a preset"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Preset")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        # Main layout
        layout = QVBoxLayout()

        # Get available presets
        presets = self.preset_manager.list_presets()

        # Debug output
        print(f"Loading preset dialog with {len(presets)} presets:")
        for p in presets:
            print(f"  - [{p.get('category')}] {p['name']}")

        # Create preset list widget
        preset_list = QListWidget()

        # Group by category
        categories = {}
        for preset in presets:
            cat = preset.get('category', 'Other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(preset)

        # Add presets grouped by category
        for category in sorted(categories.keys()):
            # Add category header
            header_item = QListWidgetItem(f"━━━ {category} ━━━")
            header_item.setFlags(Qt.NoItemFlags)  # Not selectable
            header_item.setBackground(Qt.lightGray)
            preset_list.addItem(header_item)

            # Add presets in this category
            for preset in categories[category]:
                item_text = f"  {preset['name']}"
                if preset.get('description'):
                    item_text += f"\n    {preset['description']}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, preset['id'])
                item.setData(Qt.UserRole + 1, preset)  # Store full preset data
                preset_list.addItem(item)

        # Info label
        info_label = QLabel(
            "Select a preset to load its operations into the queue.\n"
            "Presets are pre-configured operation sequences for common tasks."
        )
        info_label.setWordWrap(True)

        layout.addWidget(info_label)
        layout.addWidget(QLabel("Available Presets:"))
        layout.addWidget(preset_list)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # Handle selection
        if dialog.exec_() == QDialog.Accepted:
            selected_item = preset_list.currentItem()
            if selected_item:
                preset_id = selected_item.data(Qt.UserRole)
                if preset_id:  # Skip category headers
                    self.load_and_apply_preset(preset_id)

    def load_and_apply_preset(self, preset_id: str):
        """Load preset and add operations to queue"""
        preset = self.preset_manager.load_preset(preset_id)

        if not preset:
            QMessageBox.warning(self, "Error", f"Failed to load preset: {preset_id}")
            return

        operations = preset.get('operations', [])

        # Add operations to queue
        added = 0
        for op_config in operations:
            if not op_config.get('enabled', True):
                continue

            self.operation_queue.add_operation(
                operation_id=op_config['operation_id'],
                parameters=op_config.get('parameters', {})
            )
            added += 1

        QMessageBox.information(
            self,
            "Success",
            f"Added {added} operations from '{preset['name']}' to queue"
        )

        self.refresh_operation_queue_display()
```

---

## Troubleshooting

### Issue 1: "AttributeError: 'NoneType' object has no attribute 'list_presets'"

**Cause:** PresetManager not initialized

**Fix:**
```python
# In __init__
self.preset_manager = PresetManager()

# Check it's working
print(f"PresetManager loaded {len(self.preset_manager._presets_cache)} presets")
```

### Issue 2: "Dialog is empty"

**Cause:** Not calling `list_presets()` or not populating list widget

**Fix:** Add debug logging:
```python
presets = self.preset_manager.list_presets()
print(f"DEBUG: Got {len(presets)} presets")
for p in presets:
    print(f"  - {p['name']}")
```

### Issue 3: "Only 'Mail List Cleaner' appears"

**Cause:** Hardcoded preset list in UI

**Fix:** Replace hardcoded list with dynamic loading from PresetManager

### Issue 4: "ZoomInfo preset exists but doesn't appear"

**Cause:** Category filter being applied incorrectly

**Fix:**
```python
# Get ALL presets (no filter)
presets = self.preset_manager.list_presets()

# OR filter for specific category
zoominfo_presets = self.preset_manager.list_presets(category='ZoomInfo')
```

---

## Testing Checklist

After implementing the fix, verify:

- [ ] Run the application
- [ ] Check console for "Loaded X presets" message on startup
- [ ] Click "Load Preset" button
- [ ] Verify dialog shows 6 presets:
  - [ ] Mail List Cleaner - Quick
  - [ ] ZoomInfo - Healthcare/EVS Export ← **THIS ONE**
  - [ ] Format Standard Columns
  - [ ] Standardize + Full Mailing List Clean
  - [ ] Standard Mailing List Cleaner
  - [ ] Standardize + Clean Data
- [ ] Select ZoomInfo preset
- [ ] Click OK
- [ ] Verify 9 operations added to queue
- [ ] Verify operation queue shows all 9 operations

---

## Expected Output

When working correctly, you should see:

**Console on startup:**
```
Loaded 6 presets into cache
PresetManager initialized with 6 presets
```

**Console when opening dialog:**
```
Loading preset dialog with 6 presets:
  - [Mail List] Mail List Cleaner - Quick
  - [ZoomInfo] ZoomInfo - Healthcare/EVS Export
  - [Standard Format] Format Standard Columns
  - [Standard Format] Standardize + Full Mailing List Clean
  - [Mail List] Standard Mailing List Cleaner
  - [Standard Format] Standardize + Clean Data
```

**Dialog display:**
```
━━━ Mail List ━━━
  Mail List Cleaner - Quick
    Clean customer mailing lists quickly
  Standard Mailing List Cleaner
    Complete mailing list cleaning workflow...

━━━ Standard Format ━━━
  Format Standard Columns
    Apply standard formatting to core mailing list columns
  Standardize + Full Mailing List Clean
    Complete mailing list cleaning with formatting...
  Standardize + Clean Data
    Format standard columns and remove blank/incomplete rows

━━━ ZoomInfo ━━━
  ZoomInfo - Healthcare/EVS Export
    Standardize ZoomInfo Healthcare/EVS export to standard mailing list format
```

---

## Need Help?

Run the diagnostic script to verify backend is working:

```bash
python debug_preset_loading.py
```

If all checks pass (✓), the problem is definitely in the UI code, not the backend.
