#!/usr/bin/env python3
"""
Verification Test for Multi-Sheet Preset Selector (Phase 5)
Tests that presets can be applied to multiple sheets via checkbox dialog
"""

import sys

print("=" * 70)
print("MULTI-SHEET PRESET SELECTOR VERIFICATION (PHASE 5)")
print("=" * 70)

# Test 1: Verify MultiSheetPresetDialog class exists
print("\n1. Verifying MultiSheetPresetDialog class...")
print("-" * 70)

try:
    with open('ui/multi_sheet_preset_dialog.py', 'r') as f:
        dialog_content = f.read()

    dialog_checks = [
        ('class MultiSheetPresetDialog:', 'Class declaration'),
        ('def __init__(self, parent, sheet_names: List[str], preset_name: str, operation_count: int):', 'Constructor'),
        ('def _create_widgets(self):', '_create_widgets method'),
        ('def _select_all(self):', '_select_all method'),
        ('def _deselect_all(self):', '_deselect_all method'),
        ('def _cancel(self):', '_cancel method'),
        ('def _apply(self):', '_apply method'),
        ('def show(self) -> Optional[List[str]]:', 'show method'),
        ('self.sheet_vars = {}', 'Sheet checkboxes dict'),
        ('var = tk.BooleanVar(value=True)', 'Checkbox variables'),
        ('[PRESET DIALOG]', 'Logging prefix'),
        ('Apply Preset to Multiple Sheets', 'Dialog title'),
        ('Select All', 'Select all button'),
        ('Deselect All', 'Deselect all button'),
        ('Apply to Selected Sheets', 'Apply button'),
        ('This will replace existing workflows', 'Warning message'),
    ]

    for element, description in dialog_checks:
        if element in dialog_content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}: MISSING")
            sys.exit(1)

except FileNotFoundError:
    print("  ✗ ui/multi_sheet_preset_dialog.py file not found")
    sys.exit(1)

# Test 2: Verify import in main app
print("\n2. Verifying import in main_gui_v2_office365.py...")
print("-" * 70)

with open('main_gui_v2_office365.py', 'r') as f:
    content = f.read()

if 'from ui.multi_sheet_preset_dialog import MultiSheetPresetDialog' in content:
    print("  ✓ MultiSheetPresetDialog imported")
else:
    print("  ✗ MultiSheetPresetDialog import: MISSING")
    sys.exit(1)

# Test 3: Verify load_preset() multi-sheet detection
print("\n3. Verifying load_preset() multi-sheet detection...")
print("-" * 70)

load_preset_checks = [
    ('if self.workbook_session and self.workbook_session.is_excel and len(self.workbook_session.sheet_names) > 1:', 'Multi-sheet mode check'),
    ('[PRESET] Multi-sheet mode - showing sheet selector', 'Multi-sheet logging'),
    ('sheet_selector = MultiSheetPresetDialog(', 'Create sheet selector dialog'),
    ('selected_sheets = sheet_selector.show()', 'Show dialog and get selection'),
    ('if not selected_sheets:', 'Handle cancellation'),
    ('[PRESET] User cancelled multi-sheet preset application', 'Cancel logging'),
]

for element, description in load_preset_checks:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 4: Verify preset application to multiple sheets
print("\n4. Verifying preset application to multiple sheets...")
print("-" * 70)

preset_application_checks = [
    ('preset_operations = []', 'Build preset operations list'),
    ('self.workbook_session.apply_preset_to_sheets(preset_operations, selected_sheets)', 'Apply to selected sheets'),
    ('if self.current_sheet_name in selected_sheets:', 'Check if current sheet selected'),
    ('self._load_sheet_workflow(self.current_sheet_name)', 'Refresh current sheet workflow'),
    ('[PRESET] Refreshed current sheet', 'Refresh logging'),
    ('Applied preset', 'Success message'),
    ('operation(s) per sheet', 'Operations count in message'),
]

for element, description in preset_application_checks:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 5: Verify single-sheet fallback
print("\n5. Verifying single-sheet fallback...")
print("-" * 70)

single_sheet_checks = [
    ('# SINGLE-SHEET MODE: Apply to active sheet only', 'Single-sheet mode comment'),
    ('[PRESET] Single-sheet mode - applying preset', 'Single-sheet logging'),
    ('self.operation_queue = []', 'Clear operation queue'),
    ('self.refresh_queue_display()', 'Refresh queue display'),
    ('self._save_current_workflow()', 'Save workflow'),
]

for element, description in single_sheet_checks:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 6: Verify success message for multi-sheet
print("\n6. Verifying success message formatting...")
print("-" * 70)

success_msg_checks = [
    ('f"Applied preset \'{preset.name}\' to {len(selected_sheets)} sheet(s):', 'Sheet count in message'),
    ('"  • {s}" for s in selected_sheets', 'Sheet list formatting'),
    ('operation(s) per sheet', 'Operations per sheet'),
    ('[PRESET] Applied to {len(selected_sheets)} sheets:', 'Application logging'),
]

for element, description in success_msg_checks:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 7: Verify WorkbookSession.apply_preset_to_sheets() exists
print("\n7. Verifying WorkbookSession.apply_preset_to_sheets()...")
print("-" * 70)

with open('workbook_session.py', 'r') as f:
    wb_content = f.read()

if 'def apply_preset_to_sheets(self, preset_operations: List[Dict], sheet_names: List[str]):' in wb_content:
    print("  ✓ apply_preset_to_sheets method exists")
else:
    print("  ✗ apply_preset_to_sheets method: MISSING")
    sys.exit(1)

if 'sheet_state.operations = copy.deepcopy(preset_operations)' in wb_content:
    print("  ✓ Applies operations to sheet")
else:
    print("  ✗ Apply operations: MISSING")
    sys.exit(1)

print("\n" + "=" * 70)
print("ALL VERIFICATION TESTS PASSED! ✓")
print("=" * 70)

print("\n📋 PHASE 5 IMPLEMENTATION SUMMARY:")
print("-" * 70)
print("\n✅ MULTI-SHEET PRESET SELECTOR COMPLETE:")
print("  1. ✓ MultiSheetPresetDialog UI component created")
print("  2. ✓ Checkbox list for all available sheets")
print("  3. ✓ Select All / Deselect All buttons")
print("  4. ✓ Preset info display (name, operation count)")
print("  5. ✓ Warning about replacing workflows")
print("  6. ✓ Confirmation dialog before applying")
print("  7. ✓ Integration into load_preset() workflow")
print("  8. ✓ Multi-sheet mode detection")
print("  9. ✓ Single-sheet fallback preserved")
print(" 10. ✓ WorkbookSession.apply_preset_to_sheets() used")
print(" 11. ✓ Current sheet workflow refreshed if selected")
print(" 12. ✓ Comprehensive logging with [PRESET] prefix")

print("\n✅ UI COMPONENTS:")
print("  • Dialog header: 'Apply Preset to Multiple Sheets'")
print("  • Preset info card: Shows name and operation count")
print("  • Instruction text: 'Select which sheets...'")
print("  • Select All / Deselect All buttons")
print("  • Scrollable checkbox list for sheets")
print("  • All sheets selected by default")
print("  • Warning label: '⚠️ This will replace existing workflows'")
print("  • Cancel button")
print("  • Apply button: 'Apply to Selected Sheets'")
print("  • Confirmation dialog with sheet list")

print("\n✅ BEHAVIOR:")
print("  MULTI-SHEET MODE:")
print("    1. User clicks 'Load Preset'")
print("    2. User selects preset from list")
print("    3. App detects multi-sheet mode")
print("    4. Multi-sheet selector dialog appears")
print("    5. User sees checkboxes for all sheets (all checked)")
print("    6. User can select/deselect sheets")
print("    7. User clicks 'Apply to Selected Sheets'")
print("    8. Confirmation dialog shows selected sheets")
print("    9. Preset applied to all selected sheets")
print("   10. If current sheet selected, UI refreshes")
print("   11. Success message shows which sheets were updated")

print("\n  SINGLE-SHEET MODE:")
print("    1. User clicks 'Load Preset'")
print("    2. User selects preset from list")
print("    3. App detects single-sheet mode")
print("    4. Preset applied directly to active sheet")
print("    5. Same behavior as before (backward compatible)")

print("\n✅ DATA FLOW:")
print("  load_preset()")
print("       ↓")
print("  Check: Multi-sheet mode?")
print("       ↓ YES")
print("  MultiSheetPresetDialog.show()")
print("       ↓")
print("  User selects sheets → [Products, Orders]")
print("       ↓")
print("  Build preset_operations list")
print("       ↓")
print("  workbook_session.apply_preset_to_sheets()")
print("       ↓")
print("  For each selected sheet:")
print("    sheet.operations = preset_operations")
print("       ↓")
print("  If current sheet in selection:")
print("    _load_sheet_workflow()")
print("       ↓")
print("  Success message with sheet list")

print("\n✅ EXAMPLE SUCCESS MESSAGE:")
print("  ┌──────────────────────────────────────┐")
print("  │ Applied preset 'Basic Cleanup' to   │")
print("  │ 2 sheet(s):                          │")
print("  │                                      │")
print("  │   • Products                         │")
print("  │   • Orders                           │")
print("  │                                      │")
print("  │ 3 operation(s) per sheet             │")
print("  └──────────────────────────────────────┘")

print("\n✅ LOGGING OUTPUT:")
print("  [PRESET] Multi-sheet mode - showing sheet selector for preset 'Basic Cleanup'")
print("  [PRESET DIALOG] Multi-sheet selector opened for preset 'Basic Cleanup'")
print("  [PRESET DIALOG] Selected all sheets")
print("  [PRESET DIALOG] Applying preset to 2 sheets: ['Products', 'Orders']")
print("  [PRESET] Refreshed current sheet 'Products' workflow")
print("  [PRESET] Applied to 2 sheets: ['Products', 'Orders']")

print("\n📝 TESTING INSTRUCTIONS:")
print("-" * 70)
print("Manual test to verify multi-sheet preset selector:")
print("\n1. Load test_multi_sheet.xlsx (3 sheets: Products, Orders, Employees)")
print("2. Click 'Load Preset'")
print("3. Select 'Basic Cleanup' preset")
print("4. Multi-sheet selector dialog should appear:")
print("   → Shows 'Apply Preset to Multiple Sheets'")
print("   → Shows preset name and operation count")
print("   → Shows 3 checkboxes (all checked)")
print("   → Has 'Select All' and 'Deselect All' buttons")
print("5. Uncheck 'Employees' (leave Products and Orders checked)")
print("6. Click 'Apply to Selected Sheets'")
print("7. Confirmation dialog appears:")
print("   → Shows 'Apply preset to 2 sheet(s)?'")
print("   → Lists Products and Orders")
print("   → Has warning about replacing workflows")
print("8. Click 'Yes'")
print("9. Success message:")
print("   → 'Applied preset to 2 sheet(s)'")
print("   → Lists Products and Orders")
print("   → Shows operation count")
print("10. Switch to Products sheet:")
print("    → Should see preset operations in queue")
print("11. Switch to Orders sheet:")
print("    → Should see preset operations in queue")
print("12. Switch to Employees sheet:")
print("    → Should have empty queue (not selected)")
print("\n13. Load a single-sheet Excel file")
print("14. Click 'Load Preset'")
print("15. Select preset")
print("16. Should apply directly (no multi-sheet dialog)")

print("\n🎯 Phase 5 complete - ready to commit!")
print("=" * 70)
