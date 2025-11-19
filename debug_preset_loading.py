#!/usr/bin/env python3
"""
Debug script for diagnosing preset loading issues
Tests all aspects of preset system to find why presets aren't appearing in UI
"""

import logging
import json
from pathlib import Path
from utils.preset_manager import PresetManager

# Enable ALL logging including DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s [%(name)s] %(message)s'
)

def check_directory():
    """Check 1: Verify preset directory exists"""
    print("\n" + "=" * 80)
    print("CHECK 1: PRESET DIRECTORY")
    print("=" * 80)

    user_dir = Path.home() / ".universal_excel_tool" / "presets"
    print(f"Expected location: {user_dir}")
    print(f"Directory exists: {user_dir.exists()}")

    if user_dir.exists():
        files = list(user_dir.glob("*.json"))
        print(f"JSON files found: {len(files)}")
        for f in files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")
    else:
        print("❌ DIRECTORY DOES NOT EXIST!")

    return user_dir

def check_json_validity(preset_dir):
    """Check 2: Verify each JSON file is valid"""
    print("\n" + "=" * 80)
    print("CHECK 2: JSON FILE VALIDITY")
    print("=" * 80)

    files = list(preset_dir.glob("*.json"))

    for preset_file in files:
        print(f"\n{preset_file.name}:")
        try:
            with open(preset_file, 'r') as f:
                data = json.load(f)

            preset_id = data.get('id', 'NO ID')
            preset_name = data.get('name', 'NO NAME')
            op_count = len(data.get('operations', []))

            print(f"  ✓ Valid JSON")
            print(f"  ID: {preset_id}")
            print(f"  Name: {preset_name}")
            print(f"  Operations: {op_count}")

        except json.JSONDecodeError as e:
            print(f"  ❌ INVALID JSON: {e}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

def check_preset_manager_init():
    """Check 3: Test PresetManager initialization"""
    print("\n" + "=" * 80)
    print("CHECK 3: PRESETMANAGER INITIALIZATION")
    print("=" * 80)

    try:
        print("Creating PresetManager instance...")
        manager = PresetManager()

        print(f"\n✓ PresetManager created successfully")
        print(f"Preset directory: {manager.preset_directory}")
        print(f"Cache size: {len(manager._presets_cache)} presets")

        print("\nPresets in cache:")
        for preset_id, preset_data in manager._presets_cache.items():
            print(f"  - ID: {preset_id}")
            print(f"    Name: {preset_data.get('name')}")
            print(f"    Category: {preset_data.get('category', 'N/A')}")

        return manager

    except Exception as e:
        print(f"❌ FAILED TO CREATE PRESETMANAGER: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_list_presets(manager):
    """Check 4: Test list_presets() method"""
    print("\n" + "=" * 80)
    print("CHECK 4: LIST_PRESETS() METHOD")
    print("=" * 80)

    if not manager:
        print("❌ No manager instance - skipping")
        return

    print("Calling manager.list_presets()...")
    presets = manager.list_presets()

    print(f"\nReturned {len(presets)} presets:")
    for preset in presets:
        print(f"\n  Preset:")
        print(f"    ID: {preset['id']}")
        print(f"    Name: {preset['name']}")
        print(f"    Description: {preset.get('description', 'N/A')}")
        print(f"    Category: {preset.get('category', 'N/A')}")
        print(f"    Operations: {preset['operation_count']}")
        print(f"    File: {preset['file_path']}")

def check_zoominfo_preset(manager):
    """Check 5: Specifically test ZoomInfo preset"""
    print("\n" + "=" * 80)
    print("CHECK 5: ZOOMINFO HEALTHCARE PRESET")
    print("=" * 80)

    if not manager:
        print("❌ No manager instance - skipping")
        return

    preset_id = 'zoominfo_healthcare_evs'

    print(f"Looking for preset ID: '{preset_id}'")
    print(f"Available IDs in cache: {list(manager._presets_cache.keys())}")

    if preset_id in manager._presets_cache:
        print(f"\n✓ ZoomInfo preset found in cache!")

        preset = manager.load_preset(preset_id)
        if preset:
            print(f"  Name: {preset['name']}")
            print(f"  Category: {preset.get('category')}")
            print(f"  Description: {preset.get('description')}")
            print(f"  Operations: {len(preset.get('operations', []))}")

            print("\n  Operation list:")
            for idx, op in enumerate(preset.get('operations', []), 1):
                enabled = "✓" if op.get('enabled', True) else "✗"
                print(f"    {enabled} {idx}. {op.get('operation_id')}")
        else:
            print("❌ load_preset() returned None!")
    else:
        print(f"❌ ZoomInfo preset NOT in cache!")

def check_category_filter(manager):
    """Check 6: Test category filtering"""
    print("\n" + "=" * 80)
    print("CHECK 6: CATEGORY FILTERING")
    print("=" * 80)

    if not manager:
        print("❌ No manager instance - skipping")
        return

    print("Testing manager.list_presets(category='ZoomInfo')...")
    zoominfo_presets = manager.list_presets(category='ZoomInfo')

    print(f"Found {len(zoominfo_presets)} ZoomInfo presets:")
    for preset in zoominfo_presets:
        print(f"  - {preset['name']} (ID: {preset['id']})")

    print("\nTesting manager.list_presets() (all categories)...")
    all_presets = manager.list_presets()
    print(f"Found {len(all_presets)} total presets")

    # Group by category
    by_category = {}
    for preset in all_presets:
        cat = preset.get('category', 'Uncategorized')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(preset['name'])

    print("\nPresets by category:")
    for category, names in sorted(by_category.items()):
        print(f"  {category}:")
        for name in names:
            print(f"    - {name}")

def simulate_ui_dialog(manager):
    """Check 7: Simulate what UI dialog would do"""
    print("\n" + "=" * 80)
    print("CHECK 7: SIMULATING UI 'LOAD PRESET' DIALOG")
    print("=" * 80)

    if not manager:
        print("❌ No manager instance - skipping")
        return

    print("Step 1: UI calls manager.list_presets()")
    available_presets = manager.list_presets()
    print(f"  Received {len(available_presets)} presets")

    print("\nStep 2: UI populates dialog list")
    print("  Dialog would show:")
    for preset in available_presets:
        print(f"    [{preset.get('category', 'N/A')}] {preset['name']}")

    print("\nStep 3: User selects a preset")
    if available_presets:
        selected = available_presets[0]
        print(f"  Simulating selection of: {selected['name']}")

        print("\nStep 4: UI loads selected preset")
        preset_data = manager.load_preset(selected['id'])
        if preset_data:
            print(f"  ✓ Successfully loaded: {preset_data['name']}")
            print(f"  Ready to add {len(preset_data['operations'])} operations to queue")
        else:
            print(f"  ❌ Failed to load preset!")

def main():
    """Run all diagnostic checks"""
    print("\n" + "=" * 80)
    print("PRESET LOADING DIAGNOSTIC")
    print("=" * 80)
    print("This script will test all aspects of the preset loading system")
    print("to identify why presets aren't appearing in the UI dialog")

    # Run all checks
    preset_dir = check_directory()

    if preset_dir.exists():
        check_json_validity(preset_dir)

    manager = check_preset_manager_init()
    check_list_presets(manager)
    check_zoominfo_preset(manager)
    check_category_filter(manager)
    simulate_ui_dialog(manager)

    # Final summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

    if manager and len(manager._presets_cache) > 0:
        print(f"✓ System is working - {len(manager._presets_cache)} presets loaded")
        print("\nIf presets aren't appearing in UI, the problem is in the UI code,")
        print("not the PresetManager. Check that the UI is:")
        print("  1. Creating a PresetManager instance")
        print("  2. Calling manager.list_presets()")
        print("  3. Actually populating the dialog with the returned data")
    else:
        print("❌ Problem detected - presets are not loading into cache")
        print("\nLikely causes:")
        print("  1. Preset files don't exist in user directory")
        print("  2. JSON files are invalid")
        print("  3. PresetManager initialization is failing")

if __name__ == '__main__':
    main()
