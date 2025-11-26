#!/usr/bin/env python3
"""
Quick test for FilterCombobox functionality
"""

import tkinter as tk
from tkinter import ttk
from ui.widgets.filter_combobox import FilterCombobox

def test_filter_combobox():
    """Test the FilterCombobox widget"""
    root = tk.Tk()
    root.title("FilterCombobox Test")
    root.geometry("600x400")

    # Sample columns (simulating a real Excel dataset)
    sample_columns = [
        "A: Customer ID",
        "B: Company Name",
        "C: Person Street",
        "D: Person City",
        "E: Person State",
        "F: Person Zip Code",
        "G: Company Street",
        "H: Company City",
        "I: Company State",
        "J: Email",
        "K: Phone Number",
        "L: Website"
    ]

    # Create main frame
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill='both', expand=True)

    # Title
    ttk.Label(
        main_frame,
        text="FilterCombobox Test",
        font=('Segoe UI', 16, 'bold')
    ).pack(pady=(0, 20))

    # Instructions
    instructions = ttk.Label(
        main_frame,
        text="Type to filter the dropdown:\n"
             "• Try typing 'per' to see Person columns\n"
             "• Try typing 'company' to see Company columns\n"
             "• Use arrow keys to navigate, Enter to select",
        font=('Segoe UI', 10),
        justify='left'
    )
    instructions.pack(pady=(0, 20))

    # FilterCombobox
    ttk.Label(
        main_frame,
        text="Select Column:",
        font=('Segoe UI', 11, 'bold')
    ).pack(anchor='w', pady=(0, 5))

    combo = FilterCombobox(
        main_frame,
        values=sample_columns,
        font=('Segoe UI', 11),
        width=50
    )
    combo.pack(fill='x', pady=10)

    # Status label
    status_var = tk.StringVar(value="No selection yet")
    status_label = ttk.Label(
        main_frame,
        textvariable=status_var,
        font=('Segoe UI', 10),
        foreground='green'
    )
    status_label.pack(pady=(20, 0))

    # Update status when selection changes
    def on_selection(event):
        selected = combo.get()
        if selected:
            status_var.set(f"Selected: {selected}")
            # Show filter status
            filtered_count = len(combo._filtered_values)
            total_count = len(combo._all_values)
            print(f"Selection: {selected}")
            print(f"Filtered: {filtered_count} of {total_count} columns visible")
        else:
            status_var.set("No selection yet")

    combo.bind('<<ComboboxSelected>>', on_selection)
    combo.bind('<Return>', on_selection)

    # Test info
    test_info = ttk.Label(
        main_frame,
        text=f"Total columns: {len(sample_columns)}",
        font=('Segoe UI', 9),
        foreground='gray'
    )
    test_info.pack(pady=(10, 0))

    # Close button
    ttk.Button(
        main_frame,
        text="Close",
        command=root.destroy,
        width=20
    ).pack(pady=(20, 0))

    print("FilterCombobox test started")
    print("Test the following scenarios:")
    print("1. Type 'per' - should show Person columns only")
    print("2. Type 'person s' - should show Person Street and Person State")
    print("3. Type 'company' - should show Company columns only")
    print("4. Clear text - should show all columns")
    print("5. Type 'xyz' - should show empty or no matches")

    root.mainloop()

if __name__ == "__main__":
    test_filter_combobox()
