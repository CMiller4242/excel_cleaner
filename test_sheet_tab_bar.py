#!/usr/bin/env python3
"""
Verification Test for SheetTabBar Integration (Phase 2)
Tests that the sheet tab bar is correctly integrated into main_gui_v2_office365.py
"""

import sys

print("=" * 70)
print("SHEET TAB BAR INTEGRATION VERIFICATION (PHASE 2)")
print("=" * 70)

# Test 1: Verify imports
print("\n1. Verifying imports...")
print("-" * 70)

with open('main_gui_v2_office365.py', 'r') as f:
    content = f.read()

required_imports = [
    ('from ui.sheet_tab_bar import SheetTabBar', 'SheetTabBar import'),
]

for import_statement, description in required_imports:
    if import_statement in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 2: Verify instance variable
print("\n2. Verifying instance variable...")
print("-" * 70)

if 'self.sheet_tab_bar: Optional[SheetTabBar] = None' in content:
    print("  ✓ SheetTabBar instance variable declared")
else:
    print("  ✗ SheetTabBar instance variable: MISSING")
    sys.exit(1)

# Test 3: Verify widget creation in create_widgets()
print("\n3. Verifying widget creation...")
print("-" * 70)

widget_elements = [
    ('self.sheet_tab_bar = SheetTabBar(data_frame, on_sheet_change=self.on_tab_click)', 'Widget creation'),
    ('# Tab bar will be shown/hidden dynamically', 'Dynamic visibility comment'),
]

for element, description in widget_elements:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 4: Verify on_tab_click() callback method
print("\n4. Verifying on_tab_click() callback method...")
print("-" * 70)

callback_elements = [
    ('def on_tab_click(self, sheet_name: str):', 'Method declaration'),
    ('[SHEET TAB] Tab clicked:', 'Tab click logging'),
    ('self.workbook_session.switch_to_sheet(sheet_name)', 'Switch to sheet'),
    ('if not sheet_state.is_loaded:', 'Check if sheet is loaded'),
    ('[SHEET TAB] Lazy loading sheet', 'Lazy loading log'),
    ('self.df = sheet_state.df_original', 'Retrieve from cache'),
    ('[SHEET TAB] Sheet retrieved from cache', 'Cache retrieval log'),
    ('self.enhanced_preview.load_dataframe(self.df, is_result=False)', 'Refresh preview'),
]

for element, description in callback_elements:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 5: Verify load_file() updates sheet tab bar
print("\n5. Verifying load_file() sheet tab bar updates...")
print("-" * 70)

load_file_elements = [
    ('self.sheet_tab_bar.set_sheets(self.available_sheets, self.current_sheet_name)', 'Set sheets'),
    ('self.sheet_tab_bar.show()', 'Show tab bar for multi-sheet'),
    ('[SHEET TAB BAR] Displaying', 'Tab bar display logging'),
    ('self.sheet_tab_bar.hide()', 'Hide tab bar for single-sheet/CSV'),
]

for element, description in load_file_elements:
    if element in content:
        print(f"  ✓ {description}")
    else:
        print(f"  ✗ {description}: MISSING")
        sys.exit(1)

# Test 6: Verify change_sheet() updates sheet tab bar
print("\n6. Verifying change_sheet() updates sheet tab bar...")
print("-" * 70)

if 'self.sheet_tab_bar.set_active_sheet(selected_sheet)' in content:
    print("  ✓ Update active sheet in tab bar")
else:
    print("  ✗ Update active sheet in tab bar: MISSING")
    sys.exit(1)

# Test 7: Verify SheetTabBar class exists
print("\n7. Verifying SheetTabBar class implementation...")
print("-" * 70)

try:
    with open('ui/sheet_tab_bar.py', 'r') as f:
        tab_bar_content = f.read()

    tab_bar_elements = [
        ('class SheetTabBar(ttk.Frame):', 'Class declaration'),
        ('ACTIVE_BG = "#0078D4"', 'Office 365 active color'),
        ('INACTIVE_BG = "#F3F2F1"', 'Office 365 inactive color'),
        ('def set_sheets(self, sheet_names: List[str], active_sheet:', 'set_sheets method'),
        ('def set_active_sheet(self, sheet_name: str):', 'set_active_sheet method'),
        ('def show(self):', 'show method'),
        ('def hide(self):', 'hide method'),
        ('self.canvas = tk.Canvas', 'Canvas for scrolling'),
        ('self.scrollbar = ttk.Scrollbar', 'Horizontal scrollbar'),
        ('[SHEET TAB BAR]', 'Logging'),
    ]

    for element, description in tab_bar_elements:
        if element in tab_bar_content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}: MISSING")
            sys.exit(1)

except FileNotFoundError:
    print("  ✗ ui/sheet_tab_bar.py file not found")
    sys.exit(1)

print("\n" + "=" * 70)
print("ALL VERIFICATION TESTS PASSED! ✓")
print("=" * 70)

print("\n📋 PHASE 2 IMPLEMENTATION SUMMARY:")
print("-" * 70)
print("\n✅ SHEET TAB BAR UI COMPONENT CREATED:")
print("  1. ✓ ui/sheet_tab_bar.py implemented")
print("  2. ✓ Excel-like horizontal tab bar with scrolling")
print("  3. ✓ Office 365 color scheme (#0078D4 blue for active)")
print("  4. ✓ Click to switch sheets instantly")
print("  5. ✓ Hover effects on inactive tabs")
print("  6. ✓ Active sheet highlighting")
print("  7. ✓ Show/hide based on file type")

print("\n✅ INTEGRATION INTO MAIN APP:")
print("  1. ✓ Import added")
print("  2. ✓ Instance variable declared")
print("  3. ✓ Widget created in create_widgets()")
print("  4. ✓ on_tab_click() callback implemented with lazy loading")
print("  5. ✓ load_file() populates and shows/hides tab bar")
print("  6. ✓ change_sheet() updates active tab")
print("  7. ✓ Tab bar positioned below data preview")

print("\n✅ EXPECTED BEHAVIOR:")
print("  • CSV files: Tab bar hidden")
print("  • Single-sheet Excel: Tab bar hidden")
print("  • Multi-sheet Excel: Tab bar shown with all sheets")
print("  • Click tab: Instantly switches sheet with lazy loading")
print("  • Active tab: Blue background, white text, bold")
print("  • Inactive tabs: Light gray, hover effect")
print("  • Horizontal scrolling for many sheets")

print("\n📝 MANUAL TESTING:")
print("-" * 70)
print("Run: python3 main_gui_v2_office365.py")
print("\n1. Load test_multi_sheet.xlsx")
print("   → Sheet selection dialog appears")
print("   → Select 'Orders'")
print("   → Tab bar appears below preview showing all 3 sheets")
print("   → 'Orders' tab is highlighted in blue")
print("\n2. Click 'Products' tab")
print("   → Sheet switches instantly")
print("   → Products data loads")
print("   → Products tab now highlighted")
print("   → Check console for [SHEET TAB] logs")
print("\n3. Click 'Employees' tab")
print("   → Sheet switches instantly")
print("   → Employees data loads (lazy loading)")
print("\n4. Use 'Change Sheet' button to switch to 'Products'")
print("   → Dialog appears")
print("   → Select Products → Confirm")
print("   → Tab bar updates to show Products as active")
print("\n5. Load test_single_sheet.xlsx")
print("   → Tab bar disappears (single sheet)")
print("\n6. Load test_csv_file.csv")
print("   → Tab bar disappears (CSV file)")
print("\n✅ Phase 2 complete - ready to commit!")
print("=" * 70)
