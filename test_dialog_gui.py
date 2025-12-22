#!/usr/bin/env python3
"""
GUI Test for Sheet Selection Dialog
Tests the actual dialog appearance and behavior
"""

import tkinter as tk
from tkinter import messagebox
import sys
sys.path.insert(0, '.')

from ui.sheet_selection_dialog import SheetSelectionDialog, select_sheet_from_file

def test_dialog_standalone():
    """Test the dialog as standalone"""
    root = tk.Tk()
    root.title("Dialog Test")
    root.geometry("400x300")

    def show_dialog():
        sheet_names = ['Products', 'Orders', 'Employees', 'Summary']
        dialog = SheetSelectionDialog(root, sheet_names, "test_file.xlsx")
        result = dialog.show()

        if result:
            messagebox.showinfo("Result", f"Selected sheet: {result}")
        else:
            messagebox.showinfo("Result", "Cancelled")

    tk.Button(
        root,
        text="Show Sheet Selection Dialog",
        command=show_dialog,
        font=("Segoe UI", 12),
        padx=20,
        pady=10
    ).pack(pady=50)

    root.mainloop()

def test_convenience_function():
    """Test the select_sheet_from_file convenience function"""
    root = tk.Tk()
    root.title("Convenience Function Test")
    root.geometry("400x300")

    def test_multi_sheet():
        result = select_sheet_from_file(root, "test_multi_sheet.xlsx")
        if result:
            messagebox.showinfo("Result", f"Selected sheet: {result}")
        else:
            messagebox.showinfo("Result", "Cancelled or error")

    def test_single_sheet():
        result = select_sheet_from_file(root, "test_single_sheet.xlsx")
        if result:
            messagebox.showinfo("Result", f"Auto-selected sheet: {result}")
        else:
            messagebox.showinfo("Result", "Error")

    tk.Label(
        root,
        text="Test Sheet Selection Functions",
        font=("Segoe UI", 14, "bold")
    ).pack(pady=20)

    tk.Button(
        root,
        text="Test Multi-Sheet File (3 sheets)",
        command=test_multi_sheet,
        font=("Segoe UI", 11),
        padx=20,
        pady=10
    ).pack(pady=10)

    tk.Button(
        root,
        text="Test Single-Sheet File (1 sheet)",
        command=test_single_sheet,
        font=("Segoe UI", 11),
        padx=20,
        pady=10
    ).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    print("=" * 60)
    print("Sheet Selection Dialog GUI Test")
    print("=" * 60)
    print("\nChoose test:")
    print("1. Standalone dialog test")
    print("2. Convenience function test (requires test files)")
    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        test_dialog_standalone()
    elif choice == "2":
        test_convenience_function()
    else:
        print("Invalid choice")
