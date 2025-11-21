"""
Test that simulates how the GUI accesses parameters
"""
import sys

# Clear cache
for module in list(sys.modules.keys()):
    if module.startswith('operations'):
        del sys.modules[module]

# Import like the GUI does
from operations.registry import registry

print("="*80)
print("SIMULATING GUI PARAMETER ACCESS")
print("="*80)

# Get operation like the GUI does (line 349 in main_gui_v2.py)
operation = registry.get_by_id('data_remove_duplicates')

if not operation:
    print("ERROR: Operation not found")
    sys.exit(1)

print(f"\n✓ Got operation: {operation.metadata.name}")
print(f"  ID: {operation.metadata.id}")

# Simulate the parameter rendering loop (lines 436-481 in main_gui_v2.py)
print(f"\nSimulating GUI parameter rendering loop:")
print(f"{'='*80}")

param_widgets = {}

for param in operation.metadata.parameters:
    print(f"\nProcessing parameter: {param.name}")
    print(f"  Type: {param.type}")
    print(f"  Description: {param.description[:60]}...")

    if param.type == 'boolean':
        print(f"  ✓ This is a BOOLEAN parameter")
        print(f"  Default value: {param.default}")
        print(f"  Required: {getattr(param, 'required', 'N/A')}")

        # This is what the GUI does on line 467-470
        print(f"\n  GUI would create:")
        print(f"    - BooleanVar with value={param.default if param.default else False}")
        print(f"    - Checkbutton with text='{param.description}'")
        print(f"    - Initial state: {'CHECKED' if param.default else 'UNCHECKED'}")

        param_widgets[param.name] = f"BooleanVar(value={param.default})"

    elif param.type == 'column_list':
        print(f"  → Column list parameter")
        param_widgets[param.name] = "ColumnSelector"

    elif param.type == 'choice':
        print(f"  → Choice parameter")
        print(f"  Choices: {param.choices}")
        param_widgets[param.name] = f"Combobox(default={param.default})"

    else:
        print(f"  → {param.type} parameter")
        param_widgets[param.name] = "Entry widget"

print(f"\n{'='*80}")
print(f"PARAMETER WIDGETS CREATED:")
print(f"{'='*80}")

for name, widget in param_widgets.items():
    print(f"  {name}: {widget}")

# Check if multi_level_deduplication is in there
print(f"\n{'='*80}")
print(f"VERIFICATION:")
print(f"{'='*80}")

if 'multi_level_deduplication' in param_widgets:
    print(f"✅ SUCCESS: 'multi_level_deduplication' WOULD appear in GUI")
    print(f"   Widget type: {param_widgets['multi_level_deduplication']}")

    # Get the actual parameter
    multi_param = next(p for p in operation.metadata.parameters if p.name == 'multi_level_deduplication')
    print(f"\n   Checkbox would show:")
    print(f"   ☑ {multi_param.description}")
    print(f"   Default: {'CHECKED' if multi_param.default else 'UNCHECKED'}")
else:
    print(f"❌ ERROR: 'multi_level_deduplication' would NOT appear in GUI")

print(f"\n{'='*80}")
print(f"CONCLUSION:")
print(f"{'='*80}")

print("""
If the diagnostic shows the parameter IS present but the UI doesn't show it,
the issue is PYTHON MODULE CACHING.

SOLUTION:
1. Close the GUI application completely
2. Clear Python cache:
   rm -rf operations/__pycache__
3. Restart the GUI application from scratch

The GUI needs a complete restart to pick up the new code.
Simply closing the window is NOT enough - the Python process
must be killed and restarted.
""")
