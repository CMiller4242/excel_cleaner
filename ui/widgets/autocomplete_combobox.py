"""
Autocomplete Combobox Widget
Type-to-filter dropdown with keyboard navigation
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable


class AutocompleteCombobox(ttk.Combobox):
    """
    Enhanced combobox with autocomplete/type-to-filter functionality

    Features:
    - Type to filter dropdown list in real-time
    - Case-insensitive matching
    - Keyboard navigation (arrows, Enter)
    - Visual hints for users
    - Automatic dropdown management
    """

    def __init__(self, parent, values: List[str] = None, placeholder: str = "Type to search...",
                 match_anywhere: bool = True, on_select: Optional[Callable] = None, **kwargs):
        """
        Initialize autocomplete combobox

        Args:
            parent: Parent widget
            values: List of items to display
            placeholder: Placeholder text when empty
            match_anywhere: If True, match anywhere in string; if False, match from start only
            on_select: Optional callback when item is selected
            **kwargs: Additional ttk.Combobox arguments
        """
        super().__init__(parent, **kwargs)

        self._all_values = values or []
        self._filtered_values = self._all_values.copy()
        self.placeholder = placeholder
        self.match_anywhere = match_anywhere
        self.on_select_callback = on_select

        # Configure combobox
        self['values'] = self._all_values
        self['state'] = 'normal'  # Allow typing

        # Bind events
        self.bind('<KeyRelease>', self._on_key_release)
        self.bind('<<ComboboxSelected>>', self._on_select)
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)

        # Show placeholder if empty
        if not self.get():
            self._show_placeholder()

    def _show_placeholder(self):
        """Show placeholder text"""
        self.delete(0, tk.END)
        self.insert(0, self.placeholder)
        self.config(foreground='gray')

    def _hide_placeholder(self):
        """Hide placeholder text"""
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(foreground='black')

    def _on_focus_in(self, event):
        """Handle focus in event"""
        self._hide_placeholder()

    def _on_focus_out(self, event):
        """Handle focus out event"""
        if not self.get():
            self._show_placeholder()

    def _on_key_release(self, event):
        """Handle key release for filtering"""
        # Ignore special keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Tab',
                            'Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                            'Alt_L', 'Alt_R', 'Escape'):
            return

        # Get current text
        current_text = self.get()

        # If placeholder or empty, show all
        if not current_text or current_text == self.placeholder:
            self._filtered_values = self._all_values.copy()
            self['values'] = self._filtered_values
            return

        # Filter values based on current text
        search_text = current_text.lower()

        if self.match_anywhere:
            # Match anywhere in the string
            self._filtered_values = [
                val for val in self._all_values
                if search_text in val.lower()
            ]
        else:
            # Match from start only
            self._filtered_values = [
                val for val in self._all_values
                if val.lower().startswith(search_text)
            ]

        # Update dropdown values
        self['values'] = self._filtered_values

        # Show dropdown if there are matches
        if self._filtered_values:
            self.event_generate('<Down>')

    def _on_select(self, event):
        """Handle selection event"""
        selected = self.get()

        # Hide placeholder style
        self.config(foreground='black')

        # Call callback if provided
        if self.on_select_callback:
            try:
                self.on_select_callback(selected)
            except Exception as e:
                print(f"Error in selection callback: {e}")

    def set_values(self, values: List[str]):
        """
        Update the list of available values

        Args:
            values: New list of items
        """
        self._all_values = values
        self._filtered_values = values.copy()
        self['values'] = self._filtered_values

    def get_values(self) -> List[str]:
        """Get current list of all available values"""
        return self._all_values.copy()

    def clear(self):
        """Clear the selection and show placeholder"""
        self.delete(0, tk.END)
        self._show_placeholder()

    def set_selection(self, value: str):
        """
        Set the selected value

        Args:
            value: Value to select
        """
        if value in self._all_values:
            self.delete(0, tk.END)
            self.insert(0, value)
            self.config(foreground='black')

    def is_valid_selection(self) -> bool:
        """Check if current value is a valid selection from the list"""
        current = self.get()
        return current in self._all_values and current != self.placeholder


# Test/demo code
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Autocomplete Combobox Test")
    root.geometry("400x300")

    # Sample data
    operations = [
        "Remove Duplicates",
        "Remove Empty Rows",
        "Remove Empty Columns",
        "Trim Whitespace",
        "Convert to Uppercase",
        "Convert to Lowercase",
        "Replace Values",
        "Fill Missing Values",
        "Sort by Column",
        "Filter Rows",
        "Rename Column",
        "Delete Column",
        "Add Column",
        "Merge Columns",
        "Split Column"
    ]

    columns = [
        "A - Customer ID",
        "B - Company Name",
        "C - Contact Name",
        "D - Email",
        "E - Phone",
        "F - Address",
        "G - City",
        "H - State",
        "I - Zip Code",
        "J - Amount"
    ]

    # Create UI
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Autocomplete Combobox Demo",
              font=('Segoe UI', 14, 'bold')).pack(pady=10)

    # Operation selector
    ttk.Label(frame, text="Select Operation:", font=('Segoe UI', 10)).pack(pady=(10, 5))

    def on_operation_select(value):
        print(f"Selected operation: {value}")

    op_combo = AutocompleteCombobox(
        frame,
        values=operations,
        placeholder="Type to search operations...",
        width=40,
        on_select=on_operation_select
    )
    op_combo.pack(pady=5)

    # Column selector
    ttk.Label(frame, text="Select Column:", font=('Segoe UI', 10)).pack(pady=(20, 5))

    def on_column_select(value):
        print(f"Selected column: {value}")

    col_combo = AutocompleteCombobox(
        frame,
        values=columns,
        placeholder="Type to search columns...",
        width=40,
        on_select=on_column_select
    )
    col_combo.pack(pady=5)

    # Test buttons
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=20)

    ttk.Button(btn_frame, text="Clear Operation",
               command=op_combo.clear).pack(side='left', padx=5)
    ttk.Button(btn_frame, text="Clear Column",
               command=col_combo.clear).pack(side='left', padx=5)

    # Status label
    status_label = ttk.Label(frame, text="Try typing to filter the list!",
                            font=('Segoe UI', 9), foreground='gray')
    status_label.pack(pady=10)

    root.mainloop()
