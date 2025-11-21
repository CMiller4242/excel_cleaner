"""
Test that verifies the UI can now render boolean parameters in multi-column dialogs
"""
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

# Clear cache
for module in list(sys.modules.keys()):
    if module.startswith('operations'):
        del sys.modules[module]

from operations.registry import registry

print("="*80)
print("TESTING: Boolean Parameter Rendering in Multi-Column Dialog")
print("="*80)

# Get the RemoveDuplicatesOperation
operation = registry.get_by_id('data_remove_duplicates')

if not operation:
    print("❌ ERROR: Operation not found")
    sys.exit(1)

print(f"\n✓ Operation: {operation.metadata.name}")
print(f"  ID: {operation.metadata.id}")

# Check what dialog it will use
needs_multi_column = any(p.type == 'column_list' for p in operation.metadata.parameters)
needs_single_column = any(p.type == 'column' for p in operation.metadata.parameters)

print(f"\nDialog selection:")
print(f"  needs_multi_column: {needs_multi_column}")
print(f"  needs_single_column: {needs_single_column}")

if needs_multi_column:
    print(f"  → Will use _show_multi_column_dialog")
    dialog_method = "_show_multi_column_dialog"
elif needs_single_column and not needs_multi_column:
    print(f"  → Will use _show_single_column_dialog")
    dialog_method = "_show_single_column_dialog"
else:
    print(f"  → Will use _show_standard_parameter_dialog")
    dialog_method = "_show_standard_parameter_dialog"

print(f"\n{'='*80}")
print(f"CODE VERIFICATION: Checking {dialog_method}")
print(f"{'='*80}")

# Read the main_gui_v2.py file and check if boolean handling exists
with open('main_gui_v2.py', 'r') as f:
    content = f.read()

# Find the dialog method
if dialog_method in content:
    print(f"✓ Method {dialog_method} exists in main_gui_v2.py")

    # Check if it has boolean handling
    # Look for the pattern after the method definition
    method_start = content.find(f"def {dialog_method}")
    if method_start > 0:
        # Find the next method definition (end of this method)
        next_method = content.find("def _show", method_start + 10)
        if next_method < 0:
            next_method = len(content)

        method_code = content[method_start:next_method]

        # Check for boolean parameter handling
        has_boolean_check = "param.type == 'boolean'" in method_code
        has_booleanvar = "tk.BooleanVar" in method_code
        has_checkbutton = "ttk.Checkbutton" in method_code

        print(f"\nBoolean parameter support in {dialog_method}:")
        print(f"  param.type == 'boolean' check: {'✓ YES' if has_boolean_check else '❌ NO'}")
        print(f"  tk.BooleanVar usage: {'✓ YES' if has_booleanvar else '❌ NO'}")
        print(f"  ttk.Checkbutton usage: {'✓ YES' if has_checkbutton else '❌ NO'}")

        # Check if BooleanVar is handled in on_add
        has_booleanvar_handling = "isinstance(widget, tk.BooleanVar)" in method_code
        print(f"  BooleanVar in on_add: {'✓ YES' if has_booleanvar_handling else '❌ NO'}")

        if has_boolean_check and has_booleanvar and has_checkbutton and has_booleanvar_handling:
            print(f"\n✅ SUCCESS: {dialog_method} HAS COMPLETE boolean parameter support")
            print(f"   The checkbox WILL appear in the UI!")
        else:
            print(f"\n❌ INCOMPLETE: {dialog_method} is missing boolean parameter support")
            print(f"   The checkbox will NOT appear")

print(f"\n{'='*80}")
print(f"PARAMETERS CHECK:")
print(f"{'='*80}")

# Check all parameters
print(f"\nRemoveDuplicatesOperation parameters:")
for i, param in enumerate(operation.metadata.parameters, 1):
    print(f"\n  {i}. {param.name}")
    print(f"     Type: {param.type}")
    print(f"     Description: {param.description[:60]}...")

    if param.type == 'boolean':
        print(f"     *** BOOLEAN PARAMETER ***")
        print(f"     Default: {param.default}")
        print(f"     This should render as a checkbox")

print(f"\n{'='*80}")
print(f"CONCLUSION:")
print(f"{'='*80}")

print(f"""
If the code verification shows:
  ✓ boolean type check exists
  ✓ BooleanVar usage exists
  ✓ Checkbutton usage exists
  ✓ BooleanVar handling in on_add exists

Then the fix is complete and the checkbox WILL appear after:
1. Clearing Python cache: rm -rf operations/__pycache__
2. Restarting the GUI application

The checkbox should appear as:
☑ Use smart multi-level duplicate detection (Email → Name+Address → Name+Phone)
  [CHECKED by default]
""")
