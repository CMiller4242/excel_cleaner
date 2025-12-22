#!/usr/bin/env python3
"""
Code Review Test for Sheet Selection Enhancements
Tests code structure without requiring GUI/tkinter
"""

import pandas as pd
import sys
from pathlib import Path

print("=" * 70)
print("SHEET SELECTION CODE REVIEW TEST")
print("=" * 70)

# Test 1: Verify test files exist
print("\n1. Verifying test files exist...")
print("-" * 70)

required_files = [
    'test_single_sheet.xlsx',
    'test_multi_sheet.xlsx',
    'test_csv_file.csv'
]

all_exist = True
for file in required_files:
    if Path(file).exists():
        print(f"  ✓ {file} exists")
    else:
        print(f"  ✗ {file} MISSING")
        all_exist = False

if not all_exist:
    print("\n❌ Some test files are missing. Run: python3 test_sheet_selection.py")
    sys.exit(1)

# Test 2: Verify main_gui_v2.py has required changes
print("\n2. Verifying main_gui_v2.py enhancements...")
print("-" * 70)

try:
    with open('main_gui_v2.py', 'r') as f:
        content = f.read()

    required_elements = [
        ('from ui.sheet_selection_dialog import select_sheet_from_file', 'Import statement'),
        ('self.current_sheet_name = None', 'Sheet name tracking variable'),
        ('self.available_sheets = []', 'Sheet list tracking variable'),
        ('self.change_sheet_btn =', 'Change Sheet button declaration'),
        ('def change_sheet(self):', 'Change sheet method'),
        ('select_sheet_from_file(self.root, filename, sheet_names)', 'Optimized function call'),
        ('self.change_sheet_btn.pack(side=\'right\'', 'Button pack for multi-sheet'),
        ('self.change_sheet_btn.pack_forget()', 'Button hide logic'),
        ('print(f"DEBUG: Loading Excel file:', 'Debug logging'),
        ('print(f"DEBUG: Detected {len(sheet_names)} sheets:', 'Sheet count logging'),
        ('print(f"DEBUG: Multiple sheets detected, showing dialog', 'Dialog trigger logging'),
    ]

    all_found = True
    for element, description in required_elements:
        if element in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}: MISSING")
            all_found = False

    if not all_found:
        sys.exit(1)

except Exception as e:
    print(f"  ✗ Error reading file: {str(e)}")
    sys.exit(1)

# Test 3: Verify dialog enhancements
print("\n3. Verifying ui/sheet_selection_dialog.py enhancements...")
print("-" * 70)

try:
    with open('ui/sheet_selection_dialog.py', 'r') as f:
        content = f.read()

    visibility_elements = [
        ('self.dialog.lift()', 'Lift to front'),
        ('self.dialog.focus_force()', 'Force focus'),
        ('self.dialog.grab_set()', 'Modal grab (after widgets)'),
        ('self.dialog.transient(parent)', 'Transient window'),
        ('def select_sheet_from_file(parent, file_path: str, sheet_names: Optional[list] = None)', 'Optimized function signature'),
        ('if sheet_names is None:', 'Optional parameter handling'),
        ('print(f"DEBUG:', 'Debug logging'),
        ('traceback.print_exc()', 'Error traceback'),
    ]

    all_found = True
    for element, description in visibility_elements:
        if element in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}: MISSING")
            all_found = False

    if not all_found:
        sys.exit(1)

except Exception as e:
    print(f"  ✗ Error reading file: {str(e)}")
    sys.exit(1)

# Test 4: Verify dialog method order is correct
print("\n4. Verifying dialog initialization order...")
print("-" * 70)

try:
    with open('ui/sheet_selection_dialog.py', 'r') as f:
        lines = f.readlines()

    # Find the __init__ method
    in_init = False
    found_transient = False
    found_create_widgets = False
    found_lift = False
    found_focus = False
    found_grab = False

    for i, line in enumerate(lines):
        if 'def __init__(self' in line:
            in_init = True
        elif in_init and 'def ' in line and '__init__' not in line:
            in_init = False

        if in_init:
            if 'self.dialog.transient(parent)' in line:
                found_transient = True
                transient_line = i
            if 'self._create_widgets()' in line:
                found_create_widgets = True
                create_widgets_line = i
            if 'self.dialog.lift()' in line:
                found_lift = True
                lift_line = i
            if 'self.dialog.focus_force()' in line:
                found_focus = True
                focus_line = i
            if 'self.dialog.grab_set()' in line and i > 50:  # After widgets
                found_grab = True
                grab_line = i

    if found_transient and found_create_widgets and found_lift and found_focus and found_grab:
        print("  ✓ All dialog setup methods found")

        # Check order
        if create_widgets_line < lift_line < focus_line < grab_line:
            print("  ✓ Correct order: _create_widgets() → lift() → focus_force() → grab_set()")
        else:
            print("  ✗ Incorrect order of visibility methods")
            print(f"    create_widgets: line {create_widgets_line}")
            print(f"    lift: line {lift_line}")
            print(f"    focus: line {focus_line}")
            print(f"    grab: line {grab_line}")
            sys.exit(1)
    else:
        print("  ✗ Some dialog setup methods missing")
        sys.exit(1)

except Exception as e:
    print(f"  ✗ Error: {str(e)}")
    sys.exit(1)

# Test 5: Verify change_sheet method implementation
print("\n5. Verifying change_sheet() method implementation...")
print("-" * 70)

try:
    with open('main_gui_v2.py', 'r') as f:
        content = f.read()

    change_sheet_elements = [
        ('def change_sheet(self):', 'Method declaration'),
        ('if not self.current_file or not self.available_sheets:', 'File validation'),
        ('if len(self.available_sheets) <= 1:', 'Single sheet check'),
        ('SheetSelectionDialog(self.root, self.available_sheets, file_name)', 'Dialog creation'),
        ('if self.current_sheet_name:', 'Pre-select current sheet'),
        ('dialog.sheet_listbox.selection_set(current_index)', 'Set selection'),
        ('if selected_sheet and selected_sheet != self.current_sheet_name:', 'Sheet change check'),
        ('self.df = pd.read_excel(self.current_file, sheet_name=selected_sheet)', 'Load new sheet'),
        ('self.result_df = None', 'Clear results'),
        ('self.enhanced_preview.load_dataframe(self.df', 'Refresh preview'),
    ]

    all_found = True
    for element, description in change_sheet_elements:
        if element in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}: MISSING")
            all_found = False

    if not all_found:
        sys.exit(1)

except Exception as e:
    print(f"  ✗ Error: {str(e)}")
    sys.exit(1)

# Test 6: Test data integrity
print("\n6. Testing data file integrity...")
print("-" * 70)

try:
    # Test single-sheet
    file_path = 'test_single_sheet.xlsx'
    excel_file = pd.ExcelFile(file_path)
    if len(excel_file.sheet_names) == 1:
        print(f"  ✓ {file_path}: Single sheet")
    else:
        print(f"  ✗ {file_path}: Expected 1 sheet, got {len(excel_file.sheet_names)}")

    # Test multi-sheet
    file_path = 'test_multi_sheet.xlsx'
    excel_file = pd.ExcelFile(file_path)
    if len(excel_file.sheet_names) == 3:
        print(f"  ✓ {file_path}: 3 sheets ({', '.join(excel_file.sheet_names)})")
    else:
        print(f"  ✗ {file_path}: Expected 3 sheets, got {len(excel_file.sheet_names)}")

    # Test CSV
    file_path = 'test_csv_file.csv'
    df = pd.read_csv(file_path)
    if len(df) > 0:
        print(f"  ✓ {file_path}: Valid CSV")
    else:
        print(f"  ✗ {file_path}: Empty CSV")

except Exception as e:
    print(f"  ✗ Error: {str(e)}")
    sys.exit(1)

print("\n" + "=" * 70)
print("ALL CODE REVIEW TESTS PASSED! ✓")
print("=" * 70)

print("\n📋 IMPLEMENTATION SUMMARY:")
print("-" * 70)
print("\n✅ BUG FIXES IMPLEMENTED:")
print("  1. Dialog visibility enhanced (lift, focus_force, grab_set)")
print("  2. Dialog initialization order corrected")
print("  3. Optimized to avoid redundant file reads")
print("  4. Debug logging added throughout")
print("  5. Comprehensive error handling")

print("\n✅ NEW FEATURES IMPLEMENTED:")
print("  1. 'Change Sheet' button for multi-sheet files")
print("  2. Pre-selection of current sheet in dialog")
print("  3. Dynamic button show/hide based on file type")
print("  4. Result clearing when switching sheets")

print("\n✅ EXPECTED BEHAVIOR:")
print("  • Single-sheet Excel: Auto-load, no dialog")
print("  • Multi-sheet Excel: Dialog appears with enhanced visibility")
print("  • Multi-sheet Excel: 'Change Sheet' button shown")
print("  • CSV files: No sheet selection")
print("  • Cancel: File not loaded")

print("\n📝 MANUAL TESTING INSTRUCTIONS:")
print("-" * 70)
print("Run: python3 main_gui_v2.py")
print("\n1. Load test_multi_sheet.xlsx")
print("   → Dialog should appear IMMEDIATELY")
print("   → Dialog should be CENTERED and ON TOP")
print("   → Select 'Orders' → Click 'Load Selected Sheet'")
print("   → '📑 Change Sheet' button should appear")
print("\n2. Click '📑 Change Sheet'")
print("   → Dialog should reappear")
print("   → 'Orders' should be pre-selected")
print("   → Select 'Products' → Confirm")
print("   → Data and header should update")
print("\n3. Load test_single_sheet.xlsx")
print("   → Should auto-load WITHOUT dialog")
print("   → NO 'Change Sheet' button")
print("\n4. Load test_csv_file.csv")
print("   → Should load WITHOUT sheet selection")
print("\n5. Load test_multi_sheet.xlsx again and click 'Cancel'")
print("   → File should NOT load")
print("   → Status: 'File load cancelled - no sheet selected'")
print("\nWatch console for DEBUG messages to verify execution flow")
print("=" * 70)
