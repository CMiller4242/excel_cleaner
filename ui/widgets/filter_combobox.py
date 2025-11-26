"""
FilterCombobox - Simple, reliable combobox with type-to-filter
Uses standard ttk.Combobox with real-time filtering
"""

import tkinter as tk
from tkinter import ttk


class FilterCombobox(ttk.Combobox):
    """
    Simple combobox with type-to-filter functionality.

    Advantages:
    - Uses standard ttk.Combobox (proven, reliable)
    - No complex popup windows
    - Works on all platforms
    - Lightweight and fast

    Usage:
        combo = FilterCombobox(parent, values=my_list)
        combo.pack()
    """

    def __init__(self, parent, values=None, **kwargs):
        # Force state to 'normal' to allow typing
        kwargs['state'] = 'normal'

        super().__init__(parent, **kwargs)

        # Store all values
        self._all_values = values if values else []
        self._filtered_values = self._all_values.copy()

        # Set initial values
        self['values'] = self._all_values

        # Bind filtering events
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusIn>', self._on_focus)

        # Track last query to avoid redundant filtering
        self._last_query = ""

    def set_values(self, values):
        """Update the list of available values"""
        self._all_values = values if values else []
        self._filtered_values = self._all_values.copy()
        self['values'] = self._all_values
        self._last_query = ""

    def _on_focus(self, event):
        """Show all values when focused"""
        if not self.get():
            self['values'] = self._all_values

    def _on_keyrelease(self, event):
        """Filter values as user types"""
        # Ignore navigation keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Home', 'End',
                           'Return', 'Tab', 'Escape', 'Shift_L', 'Shift_R',
                           'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            return

        # Get current text
        current_text = self.get().strip()

        # Skip if query hasn't changed
        if current_text == self._last_query:
            return

        self._last_query = current_text

        # Filter logic
        if not current_text:
            # Show all if empty
            self._filtered_values = self._all_values.copy()
        else:
            # Case-insensitive substring match
            query_lower = current_text.lower()
            self._filtered_values = [
                value for value in self._all_values
                if query_lower in value.lower()
            ]

        # Update dropdown values
        self['values'] = self._filtered_values

        # Auto-open dropdown if there are matches
        if self._filtered_values and len(self._filtered_values) < len(self._all_values):
            self.event_generate('<Down>')  # Open dropdown
            self.icursor(tk.END)  # Keep cursor at end
