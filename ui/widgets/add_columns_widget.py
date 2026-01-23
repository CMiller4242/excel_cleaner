"""
Add Columns Widget - Dynamic add/remove rows for adding multiple columns
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict


class AddColumnsWidget(ttk.Frame):
    """
    Widget for adding multiple columns at once with dynamic add/remove rows.

    Each row has:
    - Text field for column name
    - Dropdown for default type (blank, value)
    - Text field for value (conditional on type)
    - Dropdown for on_exists behavior (skip, overwrite, rename)
    - Add button (➕) to add new row
    - Delete button (🗑️) to remove row
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.column_rows = []

        # Header row
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(header_frame, text="Column Name", width=20, font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        ttk.Label(header_frame, text="Type", width=12, font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        ttk.Label(header_frame, text="Default Value", width=20, font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        ttk.Label(header_frame, text="If Exists", width=12, font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)

        # Scrollable container for column rows
        self.canvas = tk.Canvas(self, height=300)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.rows_container = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.rows_container, anchor='nw')

        # Bind canvas resize
        self.rows_container.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # Add initial row
        self.add_column_row()

    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def add_column_row(self, name: str = "", default_type: str = "blank", value: str = "", on_exists: str = "skip"):
        """Add a new column definition row"""
        row_frame = ttk.Frame(self.rows_container)
        row_frame.pack(fill='x', pady=5)

        # Column Name entry
        name_entry = ttk.Entry(row_frame, font=('Segoe UI', 11), width=20)
        name_entry.pack(side='left', padx=5)
        if name:
            name_entry.insert(0, name)

        # Type dropdown
        type_combo = ttk.Combobox(
            row_frame,
            values=['blank', 'value'],
            width=12,
            state='readonly',
            font=('Segoe UI', 11)
        )
        type_combo.set(default_type)
        type_combo.pack(side='left', padx=5)

        # Value entry (enabled only when type is 'value')
        value_entry = ttk.Entry(row_frame, font=('Segoe UI', 11), width=20)
        value_entry.pack(side='left', padx=5)
        if value:
            value_entry.insert(0, value)

        # Enable/disable value entry based on type
        def on_type_change(event=None):
            if type_combo.get() == 'value':
                value_entry.config(state='normal')
            else:
                value_entry.config(state='disabled')
                value_entry.delete(0, tk.END)

        type_combo.bind('<<ComboboxSelected>>', on_type_change)
        on_type_change()  # Initialize state

        # On Exists dropdown
        on_exists_combo = ttk.Combobox(
            row_frame,
            values=['skip', 'overwrite', 'rename'],
            width=12,
            state='readonly',
            font=('Segoe UI', 11)
        )
        on_exists_combo.set(on_exists)
        on_exists_combo.pack(side='left', padx=5)

        # Buttons frame
        buttons_frame = ttk.Frame(row_frame)
        buttons_frame.pack(side='left', padx=10)

        # Add button (➕)
        add_btn = ttk.Button(
            buttons_frame,
            text="➕",
            command=self.add_column_row,
            width=3
        )
        add_btn.pack(side='left', padx=2)

        # Delete button (🗑️)
        delete_btn = ttk.Button(
            buttons_frame,
            text="🗑️",
            command=lambda: self.remove_column_row(row_frame),
            width=3
        )
        delete_btn.pack(side='left', padx=2)

        # Store row info
        row_info = {
            'frame': row_frame,
            'name_entry': name_entry,
            'type_combo': type_combo,
            'value_entry': value_entry,
            'on_exists_combo': on_exists_combo,
            'delete_btn': delete_btn
        }
        self.column_rows.append(row_info)

        # Update delete button visibility
        self._update_delete_buttons()

        # Update scroll region
        self._on_frame_configure()

    def remove_column_row(self, row_frame):
        """Remove a column definition row"""
        # Find and remove from list
        for i, row_info in enumerate(self.column_rows):
            if row_info['frame'] == row_frame:
                row_frame.destroy()
                self.column_rows.pop(i)
                break

        # Update delete button visibility
        self._update_delete_buttons()

        # Update scroll region
        self._on_frame_configure()

    def _update_delete_buttons(self):
        """Show/hide delete buttons based on row count"""
        show_delete = len(self.column_rows) > 1

        for row_info in self.column_rows:
            if show_delete:
                row_info['delete_btn'].config(state='normal')
            else:
                row_info['delete_btn'].config(state='disabled')

    def get_columns(self) -> List[Dict]:
        """
        Get column definitions from all rows.

        Returns:
            List of dicts with column specifications
        """
        columns = []

        for row_info in self.column_rows:
            name = row_info['name_entry'].get().strip()
            default_type = row_info['type_combo'].get()
            value = row_info['value_entry'].get().strip()
            on_exists = row_info['on_exists_combo'].get()

            # Skip rows with empty names
            if not name:
                continue

            col_spec = {
                'name': name,
                'default_type': default_type,
                'on_exists': on_exists
            }

            # Add value only if type is 'value' and value is not empty
            if default_type == 'value':
                col_spec['value'] = value

            columns.append(col_spec)

        return columns

    def set_columns(self, columns: List[Dict]):
        """
        Set column definitions (for edit mode).

        Args:
            columns: List of dicts with column specifications
        """
        # Clear existing rows
        for row_info in self.column_rows[:]:
            row_info['frame'].destroy()
        self.column_rows.clear()

        # Add rows for each column definition
        if not columns:
            self.add_column_row()
        else:
            for col in columns:
                self.add_column_row(
                    name=col.get('name', ''),
                    default_type=col.get('default_type', 'blank'),
                    value=col.get('value', ''),
                    on_exists=col.get('on_exists', 'skip')
                )

    def validate(self) -> tuple[bool, str]:
        """
        Validate the column definitions.

        Returns:
            (is_valid, error_message)
        """
        columns = self.get_columns()

        if not columns:
            return False, "Please add at least one column definition."

        # Check for duplicate names
        names = [col['name'] for col in columns]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            return False, f"Duplicate column names found: {', '.join(set(duplicates))}"

        # Check for empty values when type is 'value'
        for col in columns:
            if col['default_type'] == 'value' and 'value' not in col:
                return False, f"Column '{col['name']}': Please specify a default value."

        return True, ""
