"""
Auto-complete Combobox Widget
Provides real-time type-to-search functionality for column selection
"""

import tkinter as tk
from tkinter import ttk


class AutocompleteCombobox(ttk.Combobox):
    """
    Combobox with real-time autocomplete functionality.

    Features:
    - Type to filter options in real-time
    - Arrow keys to navigate suggestions
    - Enter to select first match
    - Case-insensitive matching
    - Matches anywhere in the text
    """

    def __init__(self, parent, values=None, **kwargs):
        # CRITICAL: Remove state parameter if present, we'll set it ourselves
        kwargs.pop('state', None)

        super().__init__(parent, **kwargs)

        # CRITICAL: Set state to 'normal' to allow typing
        self.configure(state='normal')

        self._all_values = values if values else []
        self._filtered_values = self._all_values.copy()

        # Set initial values
        self['values'] = self._all_values

        # Bind events for real-time filtering
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<Return>', self._on_return)
        self.bind('<<ComboboxSelected>>', self._on_selected)

    def set_values(self, values):
        """Update the list of available values"""
        self._all_values = values if values else []
        self._filtered_values = self._all_values.copy()
        self['values'] = self._all_values

    def set_completion_list(self, values):
        """Alias for set_values for compatibility"""
        self.set_values(values)

    def _on_keyrelease(self, event):
        """Filter values in real-time as user types"""
        # Ignore special navigation keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Home', 'End',
                           'Tab', 'Escape', 'Shift_L', 'Shift_R',
                           'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
                           'Caps_Lock', 'Num_Lock', 'Scroll_Lock', 'Return'):
            return

        # Get current text in the entry
        current_text = self.get().strip()

        # DEBUG: Print filtering info (can be removed in production)
        print(f"[DEBUG] Search text: '{current_text}'")
        print(f"[DEBUG] Total values: {len(self._all_values)}")

        if not current_text:
            # If empty, show all values
            self._filtered_values = self._all_values.copy()
            self['values'] = self._filtered_values
            print(f"[DEBUG] Empty search - showing all {len(self._filtered_values)} values")
            return

        # Filter values that contain the typed text (case-insensitive)
        search_text = current_text.lower()
        self._filtered_values = [
            value for value in self._all_values
            if search_text in value.lower()
        ]

        # DEBUG: Print filtered results
        print(f"[DEBUG] Filtered to: {len(self._filtered_values)} values")
        if self._filtered_values:
            print(f"[DEBUG] First 3 matches: {self._filtered_values[:3]}")
        else:
            print(f"[DEBUG] No matches found")

        # Update the dropdown with filtered values
        self['values'] = self._filtered_values

        # CRITICAL: Open dropdown to show filtered results
        if self._filtered_values:
            # Save cursor position
            cursor_pos = self.index(tk.INSERT)

            # Open dropdown
            try:
                self.event_generate('<Down>')
                # Restore cursor position
                self.icursor(cursor_pos)
            except:
                pass

    def _on_return(self, event):
        """Select first filtered value when Enter is pressed"""
        if self._filtered_values:
            # Set to first match
            self.set(self._filtered_values[0])
            # Clear selection and move cursor to end
            self.selection_clear()
            self.icursor(tk.END)
            # Close dropdown
            self.event_generate('<Escape>')
            return 'break'  # Prevent default Enter behavior

    def _on_selected(self, event):
        """Handle selection from dropdown"""
        # Selection made, cursor to end
        self.icursor(tk.END)


class AutocompleteEntry(ttk.Entry):
    """
    Alternative: Entry widget with popup suggestion list
    (More reliable than Combobox on some systems)
    """

    def __init__(self, parent, values=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._all_values = values if values else []
        self._listbox = None
        self._listbox_window = None

        # Bind events
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._hide_listbox)
        self.bind('<Return>', self._on_return)
        self.bind('<Down>', self._on_down)
        self.bind('<Up>', self._on_up)
        self.bind('<Escape>', self._hide_listbox)

    def set_completion_list(self, values):
        """Update the list of available values"""
        self._all_values = values if values else []

    def set_values(self, values):
        """Alias for set_completion_list"""
        self.set_completion_list(values)

    def _on_keyrelease(self, event):
        """Show filtered suggestions as user types"""
        # Ignore special keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Home', 'End',
                           'Return', 'Tab', 'Escape', 'Shift_L', 'Shift_R',
                           'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            return

        current_text = self.get().strip().lower()

        if not current_text:
            self._hide_listbox()
            return

        # Filter values
        filtered = [
            value for value in self._all_values
            if current_text in value.lower()
        ]

        if filtered:
            self._show_listbox(filtered)
        else:
            self._hide_listbox()

    def _show_listbox(self, values):
        """Show popup listbox with suggestions"""
        if self._listbox_window:
            self._listbox.delete(0, tk.END)
        else:
            # Create popup window
            self._listbox_window = tk.Toplevel(self)
            self._listbox_window.wm_overrideredirect(True)

            # Create listbox
            self._listbox = tk.Listbox(
                self._listbox_window,
                height=min(8, len(values)),
                font=self['font']
            )
            self._listbox.pack()

            # Bind selection
            self._listbox.bind('<Button-1>', self._on_listbox_select)
            self._listbox.bind('<Return>', self._on_listbox_select)

        # Populate listbox
        for value in values[:15]:  # Limit to 15 suggestions
            self._listbox.insert(tk.END, value)

        # Position below entry
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = self.winfo_width()

        self._listbox_window.geometry(f"{width}x{self._listbox.winfo_reqheight()}+{x}+{y}")

        # Select first item
        if self._listbox.size() > 0:
            self._listbox.selection_set(0)
            self._listbox.activate(0)

    def _hide_listbox(self, event=None):
        """Hide popup listbox"""
        if self._listbox_window:
            self._listbox_window.destroy()
            self._listbox_window = None
            self._listbox = None

    def _on_listbox_select(self, event):
        """Handle selection from listbox"""
        if self._listbox and self._listbox.curselection():
            selected = self._listbox.get(self._listbox.curselection()[0])
            self.delete(0, tk.END)
            self.insert(0, selected)
            self._hide_listbox()
            self.icursor(tk.END)

    def _on_return(self, event):
        """Select first suggestion on Enter"""
        if self._listbox and self._listbox.size() > 0:
            selected = self._listbox.get(0)
            self.delete(0, tk.END)
            self.insert(0, selected)
            self._hide_listbox()
            return 'break'

    def _on_down(self, event):
        """Navigate down in suggestion list"""
        if self._listbox:
            current = self._listbox.curselection()
            if current:
                next_idx = current[0] + 1
                if next_idx < self._listbox.size():
                    self._listbox.selection_clear(0, tk.END)
                    self._listbox.selection_set(next_idx)
                    self._listbox.activate(next_idx)
                    self._listbox.see(next_idx)
            return 'break'

    def _on_up(self, event):
        """Navigate up in suggestion list"""
        if self._listbox:
            current = self._listbox.curselection()
            if current and current[0] > 0:
                prev_idx = current[0] - 1
                self._listbox.selection_clear(0, tk.END)
                self._listbox.selection_set(prev_idx)
                self._listbox.activate(prev_idx)
                self._listbox.see(prev_idx)
            return 'break'


# Test code
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Autocomplete Test")
    root.geometry("600x400")

    test_columns = [
        "A: Company Name",
        "B: Contact Name",
        "C: Email",
        "D: Phone",
        "E: Amount",
        "F: Person Street",
        "G: Person City",
        "H: Person State",
        "I: Person Zip Code",
        "J: Company Street",
        "K: Company City"
    ]

    ttk.Label(root, text="Test Autocomplete Combobox",
              font=('Arial', 14, 'bold')).pack(pady=20)

    ttk.Label(root, text="Type 'per' to see Person columns only:",
              font=('Arial', 11)).pack(pady=5)

    combo = AutocompleteCombobox(root, values=test_columns, width=50)
    combo.pack(pady=10)

    ttk.Label(root, text="Type 'company' to see Company columns only:",
              font=('Arial', 11)).pack(pady=5)

    ttk.Label(root, text="💡 Type to filter • Use arrows to navigate • Enter to select",
              font=('Arial', 9), foreground='gray').pack(pady=5)

    def show_selection():
        print(f"Selected: {combo.get()}")

    ttk.Button(root, text="Show Selection", command=show_selection).pack(pady=20)

    root.mainloop()
