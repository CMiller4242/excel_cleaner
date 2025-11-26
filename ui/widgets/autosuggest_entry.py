"""
Auto-Suggest Entry - Entry widget with integrated autocomplete
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable
from ui.widgets.suggestion_engine import ContextualSuggestionEngine
from ui.widgets.suggestion_dropdown import SuggestionDropdown


class AutoSuggestEntry(ttk.Entry):
    """
    Entry widget with production-grade autocomplete.

    Features:
    - Real-time suggestions as you type
    - Keyboard navigation (↑↓ Enter Escape)
    - Mouse selection
    - Contextual awareness (recent/frequent values)
    - Non-intrusive UI
    - High performance
    """

    def __init__(self, parent, values: List[str] = None, **kwargs):
        """
        Initialize auto-suggest entry.

        Args:
            parent: Parent widget
            values: List of all possible values for suggestions
            **kwargs: Additional Entry widget arguments
        """
        super().__init__(parent, **kwargs)

        # Initialize suggestion engine
        self.engine = ContextualSuggestionEngine(values if values else [])

        # Initialize dropdown
        self.dropdown = SuggestionDropdown(self, self._on_suggestion_selected)

        # Configuration
        self.min_chars = 1  # Minimum characters before showing suggestions
        self.max_suggestions = 15
        self.debounce_ms = 50  # Delay before showing suggestions (reduces flicker)

        # State
        self._last_query = ""
        self._debounce_id = None

        # Bind events
        self.bind('<KeyRelease>', self._on_key_release)
        self.bind('<KeyPress>', self._on_key_press)
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<Button-1>', self._on_click)

    def set_values(self, values: List[str]):
        """Update the list of available values"""
        self.engine.update_values(values)

    def _on_key_release(self, event):
        """Handle key release - show suggestions"""
        # Ignore navigation keys
        if event.keysym in ('Up', 'Down', 'Return', 'Escape',
                           'Left', 'Right', 'Home', 'End',
                           'Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                           'Alt_L', 'Alt_R', 'Tab'):
            return

        # Cancel previous debounce
        if self._debounce_id:
            self.after_cancel(self._debounce_id)

        # Schedule suggestion update (debounced)
        self._debounce_id = self.after(self.debounce_ms, self._update_suggestions)

    def _on_key_press(self, event):
        """Handle key press - navigation"""
        if event.keysym == 'Down':
            if self.dropdown.navigate_down():
                return 'break'

        elif event.keysym == 'Up':
            if self.dropdown.navigate_up():
                return 'break'

        elif event.keysym == 'Return':
            if self.dropdown.select_current():
                return 'break'

        elif event.keysym == 'Escape':
            if self.dropdown.is_visible():
                self.dropdown.hide()
                return 'break'

    def _on_focus_out(self, event):
        """Hide dropdown when focus is lost"""
        # Delay slightly to allow clicking on dropdown
        self.after(200, self._check_hide_dropdown)

    def _on_click(self, event):
        """Show dropdown on click if empty"""
        if not self.get().strip():
            self._update_suggestions()

    def _check_hide_dropdown(self):
        """Check if dropdown should be hidden"""
        # Hide if neither entry nor dropdown has focus
        if not self.focus_get() and not self.dropdown.is_visible():
            self.dropdown.hide()

    def _update_suggestions(self):
        """Update and show suggestions based on current text"""
        query = self.get().strip()

        # Don't update if query hasn't changed
        if query == self._last_query:
            return

        self._last_query = query

        # Check minimum character requirement
        if query and len(query) < self.min_chars:
            self.dropdown.hide()
            return

        # Get suggestions from engine
        suggestions = self.engine.get_suggestions(query, self.max_suggestions)

        # Show dropdown
        if suggestions:
            self.dropdown.show(suggestions)
        else:
            self.dropdown.hide()

    def _on_suggestion_selected(self, value: str):
        """Handle suggestion selection"""
        # Update entry
        self.delete(0, tk.END)
        self.insert(0, value)

        # Record selection for contextual awareness
        self.engine.record_selection(value)

        # Move cursor to end
        self.icursor(tk.END)

        # Hide dropdown
        self.dropdown.hide()

        # Trigger any bindings on the entry
        self.event_generate('<<AutoSuggestSelected>>')

    def destroy(self):
        """Clean up"""
        self.dropdown.destroy()
        super().destroy()
