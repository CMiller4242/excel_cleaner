"""
Diagnostic script to verify the RemoveDuplicatesOperation metadata
"""
import sys
# Clear any cached imports to ensure we get the latest code
if 'operations.data_ops' in sys.modules:
    del sys.modules['operations.data_ops']
if 'operations.registry' in sys.modules:
    del sys.modules['operations.registry']

# Now import fresh
from operations.registry import registry

print("="*80)
print("DIAGNOSTIC: RemoveDuplicatesOperation Metadata")
print("="*80)

# Get the operation
operation = registry.get_by_id('data_remove_duplicates')

if not operation:
    print("❌ ERROR: Operation 'data_remove_duplicates' not found in registry!")
    print(f"Available operations: {list(registry.operations.keys())}")
    sys.exit(1)

print(f"\n✓ Operation found: {operation.metadata.name}")
print(f"  ID: {operation.metadata.id}")
print(f"  Category: {operation.metadata.category}")

print(f"\nParameters:")
for i, param in enumerate(operation.metadata.parameters, 1):
    print(f"\n  {i}. {param.name}")
    print(f"     Type: {param.type}")
    print(f"     Description: {param.description[:80]}..." if len(param.description) > 80 else f"     Description: {param.description}")
    if hasattr(param, 'default'):
        print(f"     Default: {param.default}")
    if hasattr(param, 'required'):
        print(f"     Required: {param.required}")
    if hasattr(param, 'choices') and param.choices:
        print(f"     Choices: {param.choices}")

# Check specifically for multi_level_deduplication
print(f"\n{'='*80}")
print("Checking for 'multi_level_deduplication' parameter:")
print("="*80)

param_names = [p.name for p in operation.metadata.parameters]
print(f"\nAll parameter names: {param_names}")

if 'multi_level_deduplication' in param_names:
    print(f"\n✅ SUCCESS: 'multi_level_deduplication' parameter IS present in metadata")

    # Find the parameter
    multi_level_param = next(p for p in operation.metadata.parameters if p.name == 'multi_level_deduplication')
    print(f"\n   Details:")
    print(f"   - Name: {multi_level_param.name}")
    print(f"   - Type: {multi_level_param.type}")
    print(f"   - Description: {multi_level_param.description}")
    print(f"   - Default: {multi_level_param.default}")
    print(f"   - Required: {multi_level_param.required}")

    print(f"\n   This parameter SHOULD appear in the UI as a checkbox.")
    print(f"   Label: {multi_level_param.description}")
    print(f"   Default state: {'Checked' if multi_level_param.default else 'Unchecked'}")
else:
    print(f"\n❌ ERROR: 'multi_level_deduplication' parameter NOT FOUND in metadata")
    print(f"   The code may not have been reloaded properly.")

print(f"\n{'='*80}")
print("TROUBLESHOOTING:")
print("="*80)
print("""
If the parameter IS present in metadata but NOT in UI:

1. Check if the GUI application is still running
   - Close ALL windows of the application
   - Kill the process completely (not just minimize)

2. Python module caching:
   - Python caches imported modules in memory
   - The GUI may be using an old cached version
   - Solution: Restart the Python process completely

3. Try this:
   - Find the main GUI process: ps aux | grep main_gui
   - Kill it: kill -9 <PID>
   - Start the GUI fresh

4. If still not working:
   - Check if there's a __pycache__ directory
   - Delete it: rm -rf operations/__pycache__
   - Restart the application

5. Verify the GUI is loading from the correct location:
   - Check which Python is running: which python3
   - Check sys.path in the GUI to ensure it's loading from /home/user/excel_cleaner
""")

print(f"\n{'='*80}")
print("FILE VERIFICATION:")
print("="*80)

# Read the actual file to verify the code is there
with open('operations/data_ops.py', 'r') as f:
    content = f.read()

if 'multi_level_deduplication' in content:
    print(f"✓ 'multi_level_deduplication' found in operations/data_ops.py file")

    # Count occurrences
    count = content.count('multi_level_deduplication')
    print(f"  Appears {count} times in the file")

    # Find in metadata section
    if "name='multi_level_deduplication'" in content:
        print(f"  ✓ Found in Parameter definition")
    if "type='boolean'" in content:
        print(f"  ✓ Boolean type parameter exists")
    if "default=True" in content and 'multi_level_deduplication' in content:
        print(f"  ✓ Default value set")
else:
    print(f"❌ 'multi_level_deduplication' NOT found in operations/data_ops.py file")
    print(f"   The file may not have been saved properly")

print(f"\n{'='*80}")
