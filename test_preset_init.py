#!/usr/bin/env python3
"""
Test script for preset initialization
"""

import logging
from utils.preset_initializer import (
    initialize_preset_directory,
    ensure_zoominfo_healthcare_preset,
    get_user_preset_directory,
    list_available_system_presets
)
from utils.preset_manager import PresetManager

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

def main():
    print("=" * 80)
    print("PRESET INITIALIZATION TEST")
    print("=" * 80)
    print()

    # Step 1: List system presets
    print("Step 1: Listing system presets...")
    system_presets = list_available_system_presets()
    print(f"Found {len(system_presets)} system presets:")
    for preset in system_presets:
        print(f"  - {preset}")
    print()

    # Step 2: Initialize preset directory
    print("Step 2: Initializing user preset directory...")
    success, message, copied_files = initialize_preset_directory(force_overwrite=False)

    if success:
        print(f"✓ {message}")
        if copied_files:
            print(f"Copied files: {', '.join(copied_files)}")
    else:
        print(f"✗ {message}")
        return False
    print()

    # Step 3: Ensure ZoomInfo Healthcare preset exists
    print("Step 3: Ensuring ZoomInfo Healthcare preset exists...")
    if ensure_zoominfo_healthcare_preset():
        print("✓ ZoomInfo Healthcare preset is ready")
    else:
        print("✗ Failed to ensure ZoomInfo Healthcare preset")
        return False
    print()

    # Step 4: Initialize PresetManager
    print("Step 4: Initializing PresetManager...")
    try:
        manager = PresetManager()
        print(f"✓ PresetManager initialized successfully")
        print(f"Preset directory: {manager.preset_directory}")
    except Exception as e:
        print(f"✗ Failed to initialize PresetManager: {e}")
        return False
    print()

    # Step 5: List available presets
    print("Step 5: Listing available presets...")
    presets = manager.list_presets()
    print(f"Found {len(presets)} presets:")
    for preset in presets:
        print(f"  - {preset['name']} (ID: {preset['id']}, Operations: {preset['operation_count']})")
    print()

    # Step 6: Load ZoomInfo Healthcare preset
    print("Step 6: Loading ZoomInfo Healthcare preset...")
    preset = manager.load_preset('zoominfo_healthcare_evs')

    if preset:
        print(f"✓ Loaded preset: {preset['name']}")
        print(f"  Category: {preset.get('category', 'N/A')}")
        print(f"  Description: {preset.get('description', 'N/A')}")
        print(f"  Operations: {len(preset.get('operations', []))}")

        # List operations
        print("\n  Operations:")
        for idx, op in enumerate(preset.get('operations', []), 1):
            enabled = "✓" if op.get('enabled', True) else "✗"
            print(f"    {enabled} {idx}. {op.get('operation_id')} - {op.get('description', '')}")
    else:
        print("✗ Failed to load preset")
        return False
    print()

    # Step 7: Get user preset directory path
    print("Step 7: User preset directory location...")
    user_dir = get_user_preset_directory()
    print(f"User presets stored at: {user_dir}")
    print()

    print("=" * 80)
    print("✓ ALL TESTS PASSED")
    print("=" * 80)
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
