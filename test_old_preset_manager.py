#!/usr/bin/env python3
"""
Test the OLD preset manager (presets/preset_manager.py)
to see what it loads and identify any errors
"""

from presets.preset_manager import PresetManager, Preset
from pathlib import Path

print("=" * 80)
print("TESTING OLD PRESET MANAGER (presets/preset_manager.py)")
print("=" * 80)

# Create preset manager instance
manager = PresetManager()

print(f"\nPreset directories:")
print(f"  System dir: {manager.system_dir}")
print(f"  User dir: {manager.user_dir}")

print(f"\nSystem directory exists: {manager.system_dir.exists()}")
print(f"User directory exists: {manager.user_dir.exists()}")

# List JSON files in system directory
system_files = list(manager.system_dir.glob("*.json"))
print(f"\nJSON files in system directory: {len(system_files)}")
for f in system_files:
    print(f"  - {f.name}")

# Try to load presets
print("\n" + "=" * 80)
print("LOADING PRESETS")
print("=" * 80)

presets = manager.list_presets()

print(f"\nTotal presets loaded: {len(presets)}")
for preset in presets:
    print(f"\n  Preset: {preset.name}")
    print(f"    ID: {preset.id}")
    print(f"    Category: {preset.category}")
    print(f"    System: {preset.is_system}")
    print(f"    Operations: {len(preset.operations)}")

# Specifically check for ZoomInfo preset
print("\n" + "=" * 80)
print("CHECKING FOR ZOOMINFO PRESET")
print("=" * 80)

zoominfo_preset = None
for preset in presets:
    if 'zoominfo' in preset.id.lower():
        zoominfo_preset = preset
        break

if zoominfo_preset:
    print(f"\n✓ ZoomInfo preset FOUND:")
    print(f"  Name: {zoominfo_preset.name}")
    print(f"  ID: {zoominfo_preset.id}")
    print(f"  Category: {zoominfo_preset.category}")
    print(f"  Operations: {len(zoominfo_preset.operations)}")
else:
    print(f"\n✗ ZoomInfo preset NOT FOUND")
    print(f"  Available preset IDs:")
    for preset in presets:
        print(f"    - {preset.id}")

# Try to manually load the ZoomInfo preset file
print("\n" + "=" * 80)
print("MANUALLY LOADING ZOOMINFO FILE")
print("=" * 80)

zoominfo_file = manager.system_dir / "zoominfo_healthcare_evs.json"
print(f"\nFile path: {zoominfo_file}")
print(f"File exists: {zoominfo_file.exists()}")

if zoominfo_file.exists():
    try:
        print("\nAttempting to load...")
        preset = manager._load_preset_file(zoominfo_file, is_system=True)
        print(f"✓ Successfully loaded!")
        print(f"  Name: {preset.name}")
        print(f"  Operations: {len(preset.operations)}")
    except Exception as e:
        print(f"✗ ERROR loading file:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
