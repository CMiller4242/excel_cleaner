"""
Sheet Selection Dialog Component
Reusable dialog for selecting sheets from multi-sheet Excel files
Office 365 UI styling
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Optional


class SheetSelectionDialog:
    """
    Modal dialog for selecting a sheet from an Excel file with multiple sheets.

    Features:
    - Lists all available sheets
    - Allows single sheet selection
    - Office 365 styling
    - Scrollable for files with many sheets
    - Returns selected sheet name or None if cancelled
    """

    def __init__(self, parent, sheet_names: list, file_name: str = "Excel File"):
        """
        Initialize the sheet selection dialog.

        Args:
            parent: Parent tkinter window
            sheet_names: List of sheet names to display
            file_name: Name of the file (for display purposes)
        """
        self.parent = parent
        self.sheet_names = sheet_names
        self.file_name = file_name
        self.selected_sheet = None
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Sheet to Load")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")

        # Make dialog modal
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog UI components"""
        # Main frame
        main_frame = tk.Frame(self.dialog, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = tk.Frame(main_frame, bg="#0078D4", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="Select Sheet to Load",
            font=("Segoe UI", 14, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=20)

        # Content frame
        content_frame = tk.Frame(main_frame, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # File info
        info_text = f"File: {self.file_name}"
        tk.Label(
            content_frame,
            text=info_text,
            font=("Segoe UI", 10),
            bg="white",
            fg="#333333"
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            content_frame,
            text=f"This file contains {len(self.sheet_names)} sheets. Please select one:",
            font=("Segoe UI", 9),
            bg="white",
            fg="#666666"
        ).pack(anchor="w", pady=(0, 15))

        # Sheet list frame with scrollbar
        list_frame = tk.Frame(content_frame, bg="white")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox for sheets
        self.sheet_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=0
        )
        self.sheet_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sheet_listbox.yview)

        # Populate sheet list
        for sheet in self.sheet_names:
            self.sheet_listbox.insert(tk.END, f"• {sheet}")

        # Select first sheet by default
        if self.sheet_names:
            self.sheet_listbox.selection_set(0)
            self.selected_sheet = self.sheet_names[0]

        # Bind selection event
        self.sheet_listbox.bind('<<ListboxSelect>>', self._on_sheet_select)

        # Double-click to confirm
        self.sheet_listbox.bind('<Double-Button-1>', lambda e: self._on_confirm())

        # Buttons frame
        btn_frame = tk.Frame(content_frame, bg="white")
        btn_frame.pack(fill=tk.X)

        # Cancel button
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#333333",
            relief=tk.SOLID,
            borderwidth=1,
            cursor="hand2",
            padx=20,
            pady=8,
            width=12
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Load button
        self.load_btn = tk.Button(
            btn_frame,
            text="Load Selected Sheet",
            command=self._on_confirm,
            font=("Segoe UI", 10, "bold"),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            width=18
        )
        self.load_btn.pack(side=tk.RIGHT)

        # Hover effects
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(bg="#F0F0F0"))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(bg="#FFFFFF"))

        self.load_btn.bind("<Enter>", lambda e: self.load_btn.config(bg="#005A9E"))
        self.load_btn.bind("<Leave>", lambda e: self.load_btn.config(bg="#0078D4"))

    def _on_sheet_select(self, event):
        """Handle sheet selection from listbox"""
        selection = self.sheet_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_sheet = self.sheet_names[index]

    def _on_confirm(self):
        """Handle confirm button click"""
        if not self.selected_sheet:
            messagebox.showwarning(
                "No Sheet Selected",
                "Please select a sheet to load.",
                parent=self.dialog
            )
            return

        self.result = self.selected_sheet
        self.dialog.destroy()

    def _on_cancel(self):
        """Handle cancel button or window close"""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[str]:
        """
        Show the dialog and return the selected sheet name.

        Returns:
            Selected sheet name, or None if cancelled
        """
        # Wait for dialog to close
        self.dialog.wait_window()
        return self.result


def select_sheet_from_file(parent, file_path: str) -> Optional[str]:
    """
    Convenience function to show sheet selection dialog for an Excel file.

    Args:
        parent: Parent tkinter window
        file_path: Path to Excel file

    Returns:
        Selected sheet name, or None if cancelled or error
    """
    try:
        # Get sheet names from file
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names

        # If only one sheet, return it directly
        if len(sheet_names) == 1:
            return sheet_names[0]

        # Show dialog for multiple sheets
        import os
        file_name = os.path.basename(file_path)
        dialog = SheetSelectionDialog(parent, sheet_names, file_name)
        return dialog.show()

    except Exception as e:
        messagebox.showerror(
            "Error",
            f"Failed to read Excel file:\n{str(e)}",
            parent=parent
        )
        return None
