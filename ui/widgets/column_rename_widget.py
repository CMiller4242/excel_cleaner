"""
Column Rename Widget - Dynamic add/remove rows for renaming columns
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict


class ColumnRenameWidget(ttk.Frame):
    """
    Widget for renaming multiple columns with dynamic add/remove rows.

    Each row has:
    - Dropdown to select column to rename
    - Text field for new name
    - Add button (➕) to add new row
    - Delete button (🗑️) to remove row
    """

    def __init__(self, parent, columns: List[str]):
        super().__init__(parent)

        self.columns = columns if columns else []
        self.rename_rows = []

        # Container for rename rows
        self.rows_container = ttk.Frame(self)
        self.rows_container.pack(fill='both', expand=True)

        # Add initial row
        self.add_rename_row()

    def add_rename_row(self, old_name: str = "", new_name: str = ""):
        """Add a new rename row"""
        row_frame = ttk.Frame(self.rows_container)
        row_frame.pack(fill='x', pady=5)

        # Dropdown for selecting column to rename
        col_label = ttk.Label(row_frame, text="Column:", width=8)
        col_label.pack(side='left', padx=(0, 5))

        # Use FilterCombobox if available, otherwise use regular Combobox
        try:
            from ui.widgets.filter_combobox import FilterCombobox
            col_combo = FilterCombobox(
                row_frame,
                values=self.columns,
                width=30
            )
        except ImportError:
            col_combo = ttk.Combobox(
                row_frame,
                values=self.columns,
                width=30,
                font=('Segoe UI', 11)
            )

        col_combo.pack(side='left', padx=5)

        if old_name:
            col_combo.set(old_name)

        # Arrow separator
        ttk.Label(row_frame, text="→", font=('Segoe UI', 12)).pack(side='left', padx=5)

        # Text field for new name
        new_name_label = ttk.Label(row_frame, text="Rename to:", width=10)
        new_name_label.pack(side='left', padx=(0, 5))

        new_name_entry = ttk.Entry(row_frame, font=('Segoe UI', 11), width=30)
        new_name_entry.pack(side='left', padx=5)

        if new_name:
            new_name_entry.insert(0, new_name)

        # Buttons frame
        buttons_frame = ttk.Frame(row_frame)
        buttons_frame.pack(side='left', padx=10)

        # Add button (➕)
        add_btn = ttk.Button(
            buttons_frame,
            text="➕",
            command=self.add_rename_row,
            width=3
        )
        add_btn.pack(side='left', padx=2)

        # Delete button (🗑️) - only show if more than 1 row
        delete_btn = ttk.Button(
            buttons_frame,
            text="🗑️",
            command=lambda: self.remove_rename_row(row_frame),
            width=3
        )
        delete_btn.pack(side='left', padx=2)

        # Store row info
        row_info = {
            'frame': row_frame,
            'col_combo': col_combo,
            'new_name_entry': new_name_entry,
            'delete_btn': delete_btn
        }
        self.rename_rows.append(row_info)

        # Update delete button visibility
        self._update_delete_buttons()

    def remove_rename_row(self, row_frame):
        """Remove a rename row"""
        # Find and remove from list
        for i, row_info in enumerate(self.rename_rows):
            if row_info['frame'] == row_frame:
                row_frame.destroy()
                self.rename_rows.pop(i)
                break

        # Update delete button visibility
        self._update_delete_buttons()

    def _update_delete_buttons(self):
        """Show/hide delete buttons based on row count"""
        show_delete = len(self.rename_rows) > 1

        for row_info in self.rename_rows:
            if show_delete:
                row_info['delete_btn'].config(state='normal')
            else:
                row_info['delete_btn'].config(state='disabled')

    def get_mappings(self) -> List[Dict[str, str]]:
        """
        Get column rename mappings from all rows.

        Returns:
            List of dicts: [{'old_name': 'Col A', 'new_name': 'New Col A'}, ...]
        """
        mappings = []

        for row_info in self.rename_rows:
            old_name = row_info['col_combo'].get().strip()
            new_name = row_info['new_name_entry'].get().strip()

            # Skip empty rows
            if not old_name or not new_name:
                continue

            # Remove column letter prefix if present (e.g., "A: Column" → "Column")
            if ':' in old_name:
                old_name = old_name.split(':', 1)[1].strip()

            mappings.append({
                'old_name': old_name,
                'new_name': new_name
            })

        return mappings

    def set_mappings(self, mappings: List[Dict[str, str]]):
        """
        Set column rename mappings (for edit mode).

        Args:
            mappings: List of dicts with 'old_name' and 'new_name'
        """
        # Clear existing rows
        for row_info in self.rename_rows[:]:
            row_info['frame'].destroy()
        self.rename_rows.clear()

        # Add rows for each mapping
        if not mappings:
            self.add_rename_row()
        else:
            for mapping in mappings:
                self.add_rename_row(
                    old_name=mapping.get('old_name', ''),
                    new_name=mapping.get('new_name', '')
                )

    def update_columns(self, new_columns: List[str]):
        """Update available columns in all dropdowns"""
        self.columns = new_columns

        for row_info in self.rename_rows:
            # Update combobox values
            if hasattr(row_info['col_combo'], 'set_values'):
                # FilterCombobox
                row_info['col_combo'].set_values(new_columns)
            else:
                # Standard ttk.Combobox
                row_info['col_combo']['values'] = new_columns
