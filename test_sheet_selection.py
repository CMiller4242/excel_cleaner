#!/usr/bin/env python3
"""
Test script for sheet selection feature
Creates test files and verifies sheet selection functionality
"""

import pandas as pd
import sys
from pathlib import Path

print("=" * 60)
print("Sheet Selection Feature Test")
print("=" * 60)

# Test 1: Create single-sheet Excel file
print("\n1. Creating single-sheet Excel file...")
single_sheet_data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'Los Angeles', 'Chicago']
}
single_sheet_df = pd.DataFrame(single_sheet_data)
single_sheet_file = 'test_single_sheet.xlsx'
single_sheet_df.to_excel(single_sheet_file, sheet_name='Sheet1', index=False)
print(f"   ✓ Created: {single_sheet_file} (1 sheet)")

# Test 2: Create multi-sheet Excel file
print("\n2. Creating multi-sheet Excel file...")
multi_sheet_file = 'test_multi_sheet.xlsx'

sheet1_data = {
    'Product': ['Laptop', 'Mouse', 'Keyboard'],
    'Price': [999, 25, 75],
    'Stock': [50, 200, 150]
}
sheet1_df = pd.DataFrame(sheet1_data)

sheet2_data = {
    'Order_ID': [1001, 1002, 1003],
    'Customer': ['John', 'Jane', 'Bob'],
    'Total': [1099, 50, 75]
}
sheet2_df = pd.DataFrame(sheet2_data)

sheet3_data = {
    'Employee': ['Alice', 'Bob', 'Charlie'],
    'Department': ['IT', 'Sales', 'HR'],
    'Salary': [70000, 60000, 55000]
}
sheet3_df = pd.DataFrame(sheet3_data)

with pd.ExcelWriter(multi_sheet_file, engine='openpyxl') as writer:
    sheet1_df.to_excel(writer, sheet_name='Products', index=False)
    sheet2_df.to_excel(writer, sheet_name='Orders', index=False)
    sheet3_df.to_excel(writer, sheet_name='Employees', index=False)

print(f"   ✓ Created: {multi_sheet_file} (3 sheets: Products, Orders, Employees)")

# Test 3: Create CSV file
print("\n3. Creating CSV file...")
csv_data = {
    'Item': ['Apple', 'Banana', 'Orange'],
    'Quantity': [10, 20, 15],
    'Price': [1.5, 0.75, 2.0]
}
csv_df = pd.DataFrame(csv_data)
csv_file = 'test_csv_file.csv'
csv_df.to_csv(csv_file, index=False)
print(f"   ✓ Created: {csv_file}")

# Verify files
print("\n" + "=" * 60)
print("Verification:")
print("=" * 60)

# Verify single-sheet file
excel_file = pd.ExcelFile(single_sheet_file)
print(f"\n✓ {single_sheet_file}")
print(f"  Sheets: {excel_file.sheet_names}")
print(f"  Expected behavior: Load automatically (1 sheet)")

# Verify multi-sheet file
excel_file = pd.ExcelFile(multi_sheet_file)
print(f"\n✓ {multi_sheet_file}")
print(f"  Sheets: {excel_file.sheet_names}")
print(f"  Expected behavior: Show sheet selection dialog")

# Verify CSV file
print(f"\n✓ {csv_file}")
print(f"  Expected behavior: Load without sheet selection")

print("\n" + "=" * 60)
print("Test Files Created Successfully!")
print("=" * 60)
print("\nManual Testing Instructions:")
print("1. Run: python3 main_gui_v2.py")
print("2. Click 'Open File' and select test_single_sheet.xlsx")
print("   → Should load automatically without dialog")
print("3. Click 'Open File' and select test_multi_sheet.xlsx")
print("   → Should show sheet selection dialog")
print("   → Try selecting different sheets")
print("4. Click 'Open File' and select test_csv_file.csv")
print("   → Should load without sheet selection")
print("5. Verify file header shows sheet name for Excel files")
print("=" * 60)
