"""
Suggestion Dropdown - Popup list for autocomplete suggestions
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional


class SuggestionDropdown:
    """
    Lightweight dropdown widget for showing autocomplete suggestions.

    Features:
    - Appears below the entry field
    - Keyboard navigation (↑↓, Enter, Escape)
    - Mouse click selection
    - Auto-dismiss on focus loss
    - Smooth scrolling for long lists
    """

    def __init__(self, parent_entry: tk.Entry, on_select: Callable[[str], None]):
        """
        Initialize suggestion dropdown.

        Args:
            parent_entry: The entry widget to attach to
            on_select: Callback when suggestion is selected
        """
        self.parent = parent_entry
        self.on_select = on_select

        self.window: Optional[tk.Toplevel] = None
        self.listbox: Optional[tk.Listbox] = None
        self.suggestions: List[str] = []

        self.visible = False
        self.selected_index = 0

    def show(self, suggestions: List[str]):
        """
        Show dropdown with suggestions.

        Args:
            suggestions: List of suggestions to display
        """
        if not suggestions:
            self.hide()
            return

        self.suggestions = suggestions

        # Create or update window
        if not self.window or not self.window.winfo_exists():
            self._create_window()

        # Update listbox
        self.listbox.delete(0, tk.END)
        for suggestion in suggestions:
            self.listbox.insert(tk.END, suggestion)

        # Position window
        self._position_window()

        # Select first item
        self.selected_index = 0
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(0)
        self.listbox.see(0)

        # Show window
        self.window.deiconify()
        self.visible = True

    def hide(self):
        """Hide the dropdown"""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()
        self.visible = False

    def is_visible(self) -> bool:
        """Check if dropdown is currently visible"""
        return self.visible and self.window and self.window.winfo_exists()

    def navigate_down(self) -> bool:
        """Navigate to next suggestion. Returns True if handled."""
        if not self.is_visible() or not self.suggestions:
            return False

        self.selected_index = min(self.selected_index + 1, len(self.suggestions) - 1)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.selected_index)
        self.listbox.see(self.selected_index)
        return True

    def navigate_up(self) -> bool:
        """Navigate to previous suggestion. Returns True if handled."""
        if not self.is_visible() or not self.suggestions:
            return False

        self.selected_index = max(self.selected_index - 1, 0)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.selected_index)
        self.listbox.see(self.selected_index)
        return True

    def select_current(self) -> bool:
        """Select currently highlighted suggestion. Returns True if handled."""
        if not self.is_visible() or not self.suggestions:
            return False

        if 0 <= self.selected_index < len(self.suggestions):
            selected = self.suggestions[self.selected_index]
            self.on_select(selected)
            self.hide()
            return True

        return False

    def _create_window(self):
        """Create the popup window and listbox"""
        self.window = tk.Toplevel(self.parent)
        self.window.wm_overrideredirect(True)
        self.window.withdraw()

        # Create listbox with scrollbar
        frame = ttk.Frame(self.window)
        frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self.listbox = tk.Listbox(
            frame,
            height=8,
            font=('Segoe UI', 10),
            activestyle='none',
            selectmode='single',
            yscrollcommand=scrollbar.set,
            borderwidth=1,
            relief='solid',
            highlightthickness=0
        )
        self.listbox.pack(side='left', fill='both', expand=True)

        scrollbar.config(command=self.listbox.yview)

        # Bind click event
        self.listbox.bind('<Button-1>', self._on_click)
        self.listbox.bind('<Double-Button-1>', self._on_double_click)

        # Bind focus out
        self.window.bind('<FocusOut>', lambda e: self.hide())

    def _position_window(self):
        """Position dropdown below the entry field"""
        # Update to get accurate dimensions
        self.parent.update_idletasks()

        # Get parent position
        x = self.parent.winfo_rootx()
        y = self.parent.winfo_rooty() + self.parent.winfo_height()
        width = self.parent.winfo_width()

        # Calculate height (max 8 items)
        item_height = 20  # Approximate height per item
        max_height = min(len(self.suggestions), 8) * item_height + 4

        # Set geometry
        self.window.geometry(f"{width}x{max_height}+{x}+{y}")

    def _on_click(self, event):
        """Handle mouse click on listbox"""
        index = self.listbox.nearest(event.y)
        if 0 <= index < len(self.suggestions):
            self.selected_index = index
            # Don't select immediately on single click, wait for double-click

    def _on_double_click(self, event):
        """Handle double-click on listbox"""
        index = self.listbox.nearest(event.y)
        if 0 <= index < len(self.suggestions):
            selected = self.suggestions[index]
            self.on_select(selected)
            self.hide()

    def destroy(self):
        """Clean up the dropdown"""
        if self.window:
            self.window.destroy()
            self.window = None
        self.listbox = None
