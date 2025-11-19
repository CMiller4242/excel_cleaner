# Preset System Integration Guide

## Quick Start

This guide shows how to integrate the preset system with the operation queue in your GUI.

## Prerequisites

- Operation queue must be accessible
- Operation queue should have either:
  - An `add_operation(operation_id, parameters)` method, OR
  - An `append(operation_dict)` method

## Integration Steps

### Step 1: Import Integration Module

```python
from utils.preset_queue_integration import (
    PresetQueueIntegration,
    add_preset_operations_to_queue,
    get_operations_from_preset
)
from utils.preset_manager import PresetManager
```

### Step 2: Initialize Integration in Your GUI

```python
class UniversalExcelToolGUI:
    def __init__(self):
        # ... existing init code ...

        # Initialize preset integration
        self.preset_integration = PresetQueueIntegration(self.operation_queue)
        self.preset_manager = PresetManager()
```

### Step 3: Add "Load Preset" Menu/Button

```python
def create_preset_menu(self):
    """Add preset menu to GUI"""
    preset_menu = tk.Menu(self.menu_bar, tearoff=0)
    self.menu_bar.add_cascade(label="Presets", menu=preset_menu)

    # List available presets
    presets = self.preset_manager.list_presets()

    for preset_info in presets:
        preset_menu.add_command(
            label=preset_info['name'],
            command=lambda p=preset_info: self.load_preset(p['id'])
        )

    preset_menu.add_separator()
    preset_menu.add_command(
        label="Refresh Presets",
        command=self.refresh_preset_menu
    )
```

### Step 4: Implement Load Preset Handler

```python
def load_preset(self, preset_id: str):
    """
    Load a preset and add all operations to queue

    Args:
        preset_id: Preset identifier (e.g., 'zoominfo_healthcare_evs')
    """
    # Show loading indicator
    self.status_label.config(text=f"Loading preset...")
    self.update_idletasks()

    # Load preset to queue
    success, message, operations = self.preset_integration.load_preset_to_queue(preset_id)

    if success:
        # Show success message
        messagebox.showinfo(
            "Preset Loaded",
            f"{message}\n\n{len(operations)} operations added to queue."
        )

        # Refresh operation queue UI
        self.refresh_operation_queue_display()

    else:
        # Show error
        messagebox.showerror("Error Loading Preset", message)

    # Update status
    self.status_label.config(text="Ready")
```

### Step 5: Integrate with Data Quality Analyzer

When analyzer detects a ZoomInfo file (or other preset-supported file):

```python
def handle_analyzer_preset_suggestion(self, detection_result: Dict):
    """
    Handle when analyzer suggests a preset

    Args:
        detection_result: Dict from detect_and_suggest_preset()
    """
    preset_name = detection_result['preset_name']
    preset_id = detection_result['preset_id']
    confidence = detection_result['confidence']

    # Ask user if they want to load the preset
    response = messagebox.askyesno(
        f"{detection_result['file_type']} File Detected",
        f"This appears to be a {detection_result['file_type']} export.\n\n"
        f"Would you like to load the '{preset_name}' preset?\n\n"
        f"Detection confidence: {confidence:.0%}\n"
        f"Operations: {len(detection_result['preset_data']['operations'])}"
    )

    if response:
        # User clicked Yes - load the preset
        self.load_preset(preset_id)
```

### Step 6: Add Preset Button to Toolbar

```python
def create_toolbar(self):
    """Create toolbar with preset button"""
    # ... existing toolbar code ...

    # Add Preset button
    preset_button = ttk.Button(
        self.toolbar,
        text="📋 Load Preset",
        command=self.show_preset_selector
    )
    preset_button.pack(side=tk.LEFT, padx=5)
```

```python
def show_preset_selector(self):
    """Show dialog to select and load a preset"""
    # Create dialog
    dialog = tk.Toplevel(self.root)
    dialog.title("Load Preset")
    dialog.geometry("500x400")

    # Title
    ttk.Label(
        dialog,
        text="Select a Preset to Load",
        font=("Arial", 12, "bold")
    ).pack(pady=10)

    # List of presets
    listbox_frame = ttk.Frame(dialog)
    listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    scrollbar = ttk.Scrollbar(listbox_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    # Populate listbox
    presets = self.preset_manager.list_presets()
    preset_map = {}

    for idx, preset_info in enumerate(presets):
        display_text = f"{preset_info['name']} ({preset_info['operation_count']} operations)"
        listbox.insert(tk.END, display_text)
        preset_map[idx] = preset_info['id']

    # Buttons
    button_frame = ttk.Frame(dialog)
    button_frame.pack(fill=tk.X, padx=10, pady=10)

    def load_selected():
        selection = listbox.curselection()
        if selection:
            preset_id = preset_map[selection[0]]
            dialog.destroy()
            self.load_preset(preset_id)

    ttk.Button(
        button_frame,
        text="Load",
        command=load_selected
    ).pack(side=tk.RIGHT, padx=5)

    ttk.Button(
        button_frame,
        text="Cancel",
        command=dialog.destroy
    ).pack(side=tk.RIGHT)
```

## Alternative: Simple Function Call

If you just want to add a preset to the queue without all the UI:

```python
# Simple approach - just add operations to queue
success, message = add_preset_operations_to_queue(
    'zoominfo_healthcare_evs',
    self.operation_queue
)

if success:
    print(message)  # "Successfully added 9 operations to queue"
    self.refresh_operation_queue_display()
else:
    print(f"Error: {message}")
```

## Getting Operations Without Adding to Queue

If you want to preview operations before adding:

```python
operations, errors = get_operations_from_preset('zoominfo_healthcare_evs')

if operations:
    # Show preview dialog
    preview_text = "\n".join([
        f"{idx + 1}. {op['operation_id']}: {op['description']}"
        for idx, op in enumerate(operations)
    ])

    # Ask user to confirm
    response = messagebox.askyesno(
        "Load Preset?",
        f"This will add {len(operations)} operations:\n\n{preview_text}\n\nContinue?"
    )

    if response:
        # User confirmed - add to queue
        for op in operations:
            self.operation_queue.add_operation(op['operation_id'], op['parameters'])
        self.refresh_operation_queue_display()

if errors:
    messagebox.showwarning("Preset Errors", "\n".join(errors))
```

## Logging

All preset operations are logged. To see logs:

```python
import logging

# Enable debug logging for preset system
logging.basicConfig(level=logging.DEBUG)

# Or configure specific loggers
logging.getLogger("PresetManager").setLevel(logging.DEBUG)
logging.getLogger("PresetLoader").setLevel(logging.DEBUG)
logging.getLogger("PresetQueueIntegration").setLevel(logging.DEBUG)
```

Log output example:
```
INFO:PresetManager:PresetManager initialized with directory: /path/to/presets/system
DEBUG:PresetManager:Scanning preset directory: /path/to/presets/system
DEBUG:PresetManager:Found 3 preset files
DEBUG:PresetManager:Loaded preset: ZoomInfo - Healthcare/EVS Export (9 operations)
INFO:PresetManager:Loaded 3 presets
INFO:PresetLoader:Loading 9 operations from preset 'ZoomInfo - Healthcare/EVS Export'
DEBUG:PresetLoader:Processing operation 1: clean_remove_blank_rows
DEBUG:PresetLoader:Added operation 1: clean_remove_blank_rows
INFO:PresetLoader:Successfully validated 9 of 9 operations
INFO:PresetQueueIntegration:Loaded 9 valid operations from preset
INFO:PresetQueueIntegration:Successfully added 9 operations to queue
```

## Error Handling

The integration provides detailed error messages:

```python
success, message, operations = self.preset_integration.load_preset_to_queue(preset_id)

if not success:
    # Common errors:
    # - "Preset file not found: {preset_id}"
    # - "Failed to load preset: {preset_id}"
    # - "Preset has N invalid operations: ..."
    # - "No valid operations found in preset"
    # - "Error adding operations to queue: {error}"

    print(f"Error: {message}")
```

## Testing Integration

Test your integration:

```python
def test_preset_integration(self):
    """Test preset loading"""
    # List presets
    presets = self.preset_manager.list_presets()
    print(f"Found {len(presets)} presets:")
    for p in presets:
        print(f"  - {p['name']} ({p['id']})")

    # Load a preset
    preset_id = 'zoominfo_healthcare_evs'
    success, message, ops = self.preset_integration.load_preset_to_queue(preset_id)

    if success:
        print(f"✓ {message}")
        print(f"Operations in queue: {len(self.operation_queue)}")
    else:
        print(f"✗ {message}")
```

## Complete Example

Full example of integrating preset system:

```python
# In your GUI class __init__:
def __init__(self):
    # ... existing init ...

    # Initialize preset system
    self.preset_integration = PresetQueueIntegration(self.operation_queue)
    self.preset_manager = PresetManager()

    # Create preset menu
    self.create_preset_menu()

# Create preset menu
def create_preset_menu(self):
    preset_menu = tk.Menu(self.menu_bar, tearoff=0)
    self.menu_bar.add_cascade(label="Presets", menu=preset_menu)

    presets = self.preset_manager.list_presets()
    for preset_info in presets:
        preset_menu.add_command(
            label=preset_info['name'],
            command=lambda p=preset_info['id']: self.load_preset(p)
        )

# Load preset handler
def load_preset(self, preset_id: str):
    success, message, operations = self.preset_integration.load_preset_to_queue(preset_id)

    if success:
        messagebox.showinfo("Success", message)
        self.refresh_operation_queue_display()
    else:
        messagebox.showerror("Error", message)

# Integrate with analyzer
def on_analyze_complete(self, analysis_report):
    # ... existing analyzer code ...

    # Check for preset suggestions
    detection = detect_and_suggest_preset(self.df)
    if detection:
        self.handle_preset_suggestion(detection)

def handle_preset_suggestion(self, detection):
    response = messagebox.askyesno(
        "Preset Detected",
        f"Detected: {detection['preset_name']}\n"
        f"Confidence: {detection['confidence']:.0%}\n\n"
        f"Load this preset?"
    )

    if response:
        self.load_preset(detection['preset_id'])
```

## Troubleshooting

**Preset not found:**
- Check preset directory: `/path/to/excel_cleaner/presets/system/`
- Ensure preset JSON file exists: `zoominfo_healthcare_evs.json`
- Check file permissions

**Operations not added to queue:**
- Verify operation queue has `add_operation` or `append` method
- Check logs for detailed error messages
- Ensure operation IDs in preset match registered operations

**Preset doesn't appear in menu:**
- Call `self.preset_manager.list_presets()` to see what's found
- Check preset JSON is valid
- Refresh preset menu

## Next Steps

- Add preset editor UI (see `utils/preset_editor_ui.py`)
- Allow users to create custom presets
- Add preset preview before loading
- Implement preset export/import
