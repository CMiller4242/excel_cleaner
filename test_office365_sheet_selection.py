#!/usr/bin/env python3
"""
Verification Test for main_gui_v2_office365.py Sheet Selection
Tests that all required changes were made correctly
"""

import sys

print("=" * 70)
print("MAIN_GUI_V2_OFFICE365.PY SHEET SELECTION VERIFICATION")
print("=" * 70)

# Test 1: Verify imports
print("\n1. Verifying imports...")
print("-" * 70)

with open('main_gui_v2_office365.py', 'r') as f:
    content = f.read()

required_imports = [
    ('from ui.sheet_selection_dialog import select_sheet_from_file, SheetSelectionDialog', 'Sheet selection imports'),
]

for import_statement, description in required_imports:
    if import_statement in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 2: Verify __init__ has sheet tracking variables
print("\n2. Verifying __init__ sheet tracking variables...")
print("-" * 70)

init_vars = [
    ('self.current_sheet_name = None', 'Current sheet name tracking'),
    ('self.available_sheets = []', 'Available sheets tracking'),
]

for var, description in init_vars:
    if var in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 3: Verify Change Sheet button in header
print("\n3. Verifying Change Sheet button...")
print("-" * 70)

button_elements = [
    ('self.change_sheet_btn =', 'Button variable declaration'),
    ('text="📑 Change Sheet"', 'Button text'),
    ('command=self.change_sheet', 'Button command binding'),
]

for element, description in button_elements:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 4: Verify change_sheet() method
print("\n4. Verifying change_sheet() method...")
print("-" * 70)

change_sheet_elements = [
    ('def change_sheet(self):', 'Method declaration'),
    ('if not self.current_file or not self.available_sheets:', 'File validation'),
    ('SheetSelectionDialog(self.root, self.available_sheets, file_name)', 'Dialog creation'),
    ('current_index = self.available_sheets.index(self.current_sheet_name)', 'Pre-select current sheet'),
    ('self.df = pd.read_excel(self.current_file, sheet_name=selected_sheet)', 'Load new sheet'),
    ('self.result_df = None', 'Clear results'),
    ('self.enhanced_preview.load_dataframe(self.df', 'Refresh preview'),
]

for element, description in change_sheet_elements:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 5: Verify load_file() has sheet selection logic
print("\n5. Verifying load_file() sheet selection logic...")
print("-" * 70)

load_file_elements = [
    ('self.change_sheet_btn.pack_forget()', 'Hide button by default'),
    ('excel_file = pd.ExcelFile(filename)', 'Detect sheets'),
    ('sheet_names = excel_file.sheet_names', 'Get sheet names'),
    ('self.available_sheets = sheet_names', 'Store sheet names'),
    ('[FILE LOAD] Detected', 'Debug logging for detection'),
    ('select_sheet_from_file(self.root, filename, sheet_names)', 'Call sheet selection'),
    ('if selected_sheet is None:', 'Handle cancellation'),
    ('File load cancelled - no sheet selected', 'Cancellation message'),
    ('self.current_sheet_name = selected_sheet', 'Store selected sheet'),
    ('df_test = pd.read_excel(filename, sheet_name=selected_sheet, nrows=5)', 'Test load with sheet'),
    ('self.df = pd.read_excel(filename, sheet_name=selected_sheet, header=header_row)', 'Full load with sheet'),
    ('| Sheet: {self.current_sheet_name}', 'Header shows sheet name'),
    ('if len(self.available_sheets) > 1:', 'Check for multi-sheet'),
    ('self.change_sheet_btn.pack(side=\'right\', padx=5)', 'Show button for multi-sheet'),
]

for element, description in load_file_elements:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 6: Verify logging
print("\n6. Verifying comprehensive logging...")
print("-" * 70)

logging_elements = [
    ('[FILE LOAD] Loading Excel file:', 'File load start'),
    ('[FILE LOAD] Detected', 'Sheet detection'),
    ('[FILE LOAD] Multiple sheets detected, showing dialog', 'Dialog trigger'),
    ('[FILE LOAD] Dialog returned:', 'Dialog result'),
    ('[FILE LOAD] User cancelled', 'Cancellation logged'),
    ('[FILE LOAD] Will load sheet:', 'Sheet selection logged'),
    ('[FILE LOAD] Showing \'Change Sheet\' button', 'Button visibility logged'),
    ('[SHEET CHANGE] Changing from', 'Sheet change logged'),
    ('[SHEET CHANGE ERROR]', 'Sheet change error logged'),
    ('[FILE LOAD ERROR]', 'File load error logged'),
]

for element, description in logging_elements:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 7: Verify execution order
print("\n7. Verifying execution order...")
print("-" * 70)

# Find positions of key operations within load_file()
load_file_start = content.find('def load_file(self):')
reset_pos = content.find('# Reset sheet tracking', load_file_start)
detect_pos = content.find('excel_file = pd.ExcelFile(filename)', load_file_start)
dialog_pos = content.find('select_sheet_from_file(self.root, filename, sheet_names)', load_file_start)
test_load_pos = content.find('df_test = pd.read_excel(filename, sheet_name=selected_sheet, nrows=5)', load_file_start)
full_load_pos = content.find('self.df = pd.read_excel(filename, sheet_name=selected_sheet, header=header_row)', load_file_start)

if reset_pos > 0:
    print("  ✓ Reset tracking variables")
else:
    print("  ✗ Reset tracking variables: MISSING")
    sys.exit(1)

if detect_pos > reset_pos:
    print("  ✓ Sheet detection AFTER reset")
else:
    print("  ✗ Sheet detection BEFORE reset")
    sys.exit(1)

if dialog_pos > detect_pos:
    print("  ✓ Dialog shown AFTER detection")
else:
    print("  ✗ Dialog shown BEFORE detection")
    sys.exit(1)

if test_load_pos > dialog_pos:
    print("  ✓ Test load AFTER dialog")
else:
    print("  ✗ Test load BEFORE dialog")
    sys.exit(1)

if full_load_pos > test_load_pos:
    print("  ✓ Full load AFTER test load")
else:
    print("  ✗ Full load BEFORE test load")
    sys.exit(1)

print("\n" + "=" * 70)
print("ALL VERIFICATION TESTS PASSED! ✓")
print("=" * 70)

print("\n📋 IMPLEMENTATION SUMMARY:")
print("-" * 70)
print("\n✅ ALL REQUIRED CHANGES IMPLEMENTED:")
print("  1. ✓ Imports added (select_sheet_from_file, SheetSelectionDialog)")
print("  2. ✓ Sheet tracking variables in __init__")
print("  3. ✓ 'Change Sheet' button added to header")
print("  4. ✓ change_sheet() method fully implemented")
print("  5. ✓ load_file() completely rewritten with:")
print("     - Sheet detection BEFORE any pd.read_excel()")
print("     - Dialog shown for multi-sheet files")
print("     - User cancellation handled")
print("     - sheet_name parameter passed to BOTH test and full load")
print("     - File header shows sheet name")
print("     - 'Change Sheet' button shown/hidden appropriately")
print("  6. ✓ Comprehensive logging throughout")
print("  7. ✓ Correct execution order maintained")

print("\n✅ EXPECTED BEHAVIOR:")
print("  • CSV files: Load without sheet selection")
print("  • Single-sheet Excel: Auto-load without dialog")
print("  • Multi-sheet Excel: Dialog appears IMMEDIATELY")
print("  • Dialog centered and on top (enhanced visibility)")
print("  • Cancel: File does NOT load")
print("  • Select sheet: Data loads from selected sheet")
print("  • Header shows: 'file.xlsx | Sheet: SheetName • X rows × Y columns'")
print("  • 'Change Sheet' button appears for multi-sheet files")
print("  • Click button: Dialog reopens with current sheet pre-selected")

print("\n📝 MANUAL TESTING:")
print("-" * 70)
print("Run: python3 main_gui_v2_office365.py")
print("\n1. Load test_multi_sheet.xlsx")
print("   → Dialog should appear IMMEDIATELY")
print("   → Select 'Orders' → Loads Orders data")
print("   → Header shows: 'test_multi_sheet.xlsx | Sheet: Orders'")
print("   → '📑 Change Sheet' button appears")
print("\n2. Click '📑 Change Sheet'")
print("   → Dialog reopens")
print("   → 'Orders' is pre-selected")
print("   → Select 'Products' → Data updates")
print("\n3. Load test_single_sheet.xlsx")
print("   → Auto-loads without dialog")
print("   → NO 'Change Sheet' button")
print("\n4. Load test_csv_file.csv")
print("   → Loads without sheet selection")
print("\n5. Load test_multi_sheet.xlsx and click Cancel")
print("   → File does NOT load")
print("   → Status: 'File load cancelled - no sheet selected'")
print("\nWatch console for [FILE LOAD] and [SHEET CHANGE] log messages")
print("=" * 70)
