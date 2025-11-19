#!/usr/bin/env python3
"""
Simulate the UI load_preset dialog behavior
to verify ZoomInfo preset will appear
"""

from presets.preset_manager import PresetManager, Preset, OperationConfig

print("=" * 80)
print("SIMULATING UI LOAD PRESET DIALOG")
print("=" * 80)

# This is what the UI does in __init__
print("\nStep 1: Creating PresetManager instance (like UI __init__)")
preset_manager = PresetManager()

# This is what the UI does in load_preset()
print("\nStep 2: Calling preset_manager.list_presets() (like UI load_preset())")
presets = preset_manager.list_presets()

print(f"\nFound {len(presets)} presets")

if not presets:
    print("❌ PROBLEM: No presets available - dialog would show 'No presets available'")
else:
    print("\n✓ Presets loaded successfully!")

    # This is what the UI displays in the listbox
    print("\nStep 3: Building listbox items (what UI shows):")
    print("-" * 80)

    preset_map = {}
    for i, preset in enumerate(presets):
        icon = "🔒" if preset.is_system else "📝"
        text = f"{icon} {preset.name} - {preset.description}"
        print(f"  [{i}] {text}")
        preset_map[i] = preset

    print("-" * 80)

    # Check if ZoomInfo is in the list
    print("\nStep 4: Checking for ZoomInfo preset:")

    zoominfo_found = False
    zoominfo_index = -1

    for i, preset in enumerate(presets):
        if 'zoominfo' in preset.id.lower():
            zoominfo_found = True
            zoominfo_index = i
            break

    if zoominfo_found:
        print(f"✓ ZoomInfo preset FOUND at index {zoominfo_index}")
        print(f"  Name: {presets[zoominfo_index].name}")
        print(f"  Description: {presets[zoominfo_index].description}")
        print(f"  Category: {presets[zoominfo_index].category}")
        print(f"  Operations: {len(presets[zoominfo_index].operations)}")

        print("\n" + "=" * 80)
        print("✓ UI DIALOG WILL SHOW ZOOMINFO PRESET")
        print("=" * 80)

        # Simulate selecting and loading it
        print("\nStep 5: Simulating user selection and load:")
        selected_preset = presets[zoominfo_index]

        print(f"\nUser selects: {selected_preset.name}")
        print(f"Loading {len(selected_preset.operations)} operations:")

        for i, op_config in enumerate(selected_preset.operations, 1):
            enabled_icon = "✓" if op_config.enabled else "✗"
            print(f"  {enabled_icon} {i}. {op_config.operation_id}")
            if op_config.description:
                print(f"      {op_config.description}")

        print(f"\n✓ Would add {len(selected_preset.operations)} operations to queue")
        print(f"✓ Would show: \"Loaded '{selected_preset.name}' with {len(selected_preset.operations)} operations\"")

    else:
        print("❌ PROBLEM: ZoomInfo preset NOT in list")
        print(f"Available presets:")
        for preset in presets:
            print(f"  - {preset.id}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
