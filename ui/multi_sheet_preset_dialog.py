"""
Multi-Sheet Preset Selector Dialog

Allows users to select which sheets to apply a preset to in multi-sheet mode.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import logging


class MultiSheetPresetDialog:
    """Dialog for selecting which sheets to apply a preset to"""

    def __init__(self, parent, sheet_names: List[str], preset_name: str, operation_count: int):
        """
        Initialize multi-sheet preset selector dialog

        Args:
            parent: Parent window
            sheet_names: List of available sheet names
            preset_name: Name of the preset being applied
            operation_count: Number of operations in the preset
        """
        self.result = None
        self.sheet_names = sheet_names
        self.preset_name = preset_name
        self.operation_count = operation_count

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Apply Preset to Sheets")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self._create_widgets()

        logging.info(f"[PRESET DIALOG] Multi-sheet selector opened for preset '{preset_name}'")

    def _create_widgets(self):
        """Create dialog widgets"""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill='x', padx=20, pady=15)

        ttk.Label(
            header_frame,
            text="Apply Preset to Multiple Sheets",
            font=('Segoe UI', 14, 'bold'),
            foreground='#0078D4'
        ).pack(anchor='w')

        # Preset info
        info_frame = ttk.Frame(self.dialog, style='Card.TFrame', relief='solid', borderwidth=1)
        info_frame.pack(fill='x', padx=20, pady=(0, 15))

        ttk.Label(
            info_frame,
            text=f"📋 Preset: {self.preset_name}",
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor='w', padx=15, pady=(10, 5))

        ttk.Label(
            info_frame,
            text=f"⚙️ {self.operation_count} operation{'s' if self.operation_count != 1 else ''}",
            font=('Segoe UI', 10),
            foreground='#666666'
        ).pack(anchor='w', padx=15, pady=(0, 10))

        # Instruction
        ttk.Label(
            self.dialog,
            text="Select which sheets to apply this preset to:",
            font=('Segoe UI', 10)
        ).pack(anchor='w', padx=20, pady=(0, 10))

        # Sheet selection area
        selection_frame = ttk.Frame(self.dialog, style='Card.TFrame', relief='solid', borderwidth=1)
        selection_frame.pack(fill='both', expand=True, padx=20, pady=(0, 15))

        # Select All / Deselect All buttons
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="✓ Select All",
            command=self._select_all,
            width=12
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame,
            text="✗ Deselect All",
            command=self._deselect_all,
            width=12
        ).pack(side='left', padx=5)

        # Sheet checkboxes in scrollable frame
        canvas = tk.Canvas(selection_frame, bg='#FFFFFF', highlightthickness=0)
        scrollbar = ttk.Scrollbar(selection_frame, orient='vertical', command=canvas.yview)
        self.checkbox_frame = ttk.Frame(canvas, style='Card.TFrame')

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=(0, 10))

        canvas_window = canvas.create_window((0, 0), window=self.checkbox_frame, anchor='nw')

        # Create checkbox for each sheet
        self.sheet_vars = {}
        for i, sheet_name in enumerate(self.sheet_names):
            var = tk.BooleanVar(value=True)  # Default: all selected
            self.sheet_vars[sheet_name] = var

            cb = ttk.Checkbutton(
                self.checkbox_frame,
                text=f"  {sheet_name}",
                variable=var,
                style='Sheet.TCheckbutton'
            )
            cb.pack(anchor='w', padx=10, pady=5, fill='x')

        # Update scroll region
        self.checkbox_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox('all'))

        # Bind canvas resize
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))

        self.checkbox_frame.bind('<Configure>', on_frame_configure)

        # Warning label
        self.warning_label = ttk.Label(
            self.dialog,
            text="⚠️ This will replace existing workflows on selected sheets",
            font=('Segoe UI', 9),
            foreground='#D83B01'  # Office 365 red
        )
        self.warning_label.pack(padx=20, pady=(0, 10))

        # Button frame
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=20, pady=(0, 15))

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self._cancel,
            width=15
        ).pack(side='left', padx=5)

        ttk.Button(
            btn_frame,
            text="Apply to Selected Sheets",
            command=self._apply,
            style='Accent.TButton',
            width=25
        ).pack(side='right', padx=5)

    def _select_all(self):
        """Select all sheets"""
        for var in self.sheet_vars.values():
            var.set(True)
        logging.info("[PRESET DIALOG] Selected all sheets")

    def _deselect_all(self):
        """Deselect all sheets"""
        for var in self.sheet_vars.values():
            var.set(False)
        logging.info("[PRESET DIALOG] Deselected all sheets")

    def _cancel(self):
        """Cancel and close dialog"""
        logging.info("[PRESET DIALOG] User cancelled")
        self.result = None
        self.dialog.destroy()

    def _apply(self):
        """Apply preset to selected sheets"""
        # Get selected sheets
        selected = [name for name, var in self.sheet_vars.items() if var.get()]

        if not selected:
            messagebox.showwarning(
                "No Sheets Selected",
                "Please select at least one sheet to apply the preset to.",
                parent=self.dialog
            )
            return

        # Confirm
        sheet_list = "\n".join([f"  • {name}" for name in selected])
        confirm = messagebox.askyesno(
            "Confirm Apply Preset",
            f"Apply preset '{self.preset_name}' to {len(selected)} sheet(s)?\n\n"
            f"{sheet_list}\n\n"
            f"⚠️ This will replace existing workflows on these sheets.",
            parent=self.dialog
        )

        if not confirm:
            return

        self.result = selected
        logging.info(f"[PRESET DIALOG] Applying preset to {len(selected)} sheets: {selected}")
        self.dialog.destroy()

    def show(self) -> Optional[List[str]]:
        """
        Show dialog and return selected sheet names

        Returns:
            List of selected sheet names, or None if cancelled
        """
        self.dialog.wait_window()
        return self.result


# Example usage and testing
if __name__ == "__main__":
    def test_dialog():
        root = tk.Tk()
        root.title("Test Parent Window")
        root.geometry("800x600")

        def show_selector():
            test_sheets = ['Products', 'Orders', 'Employees', 'Customers', 'Inventory']
            dialog = MultiSheetPresetDialog(root, test_sheets, "Basic Cleanup", 3)
            selected = dialog.show()

            if selected:
                print(f"Selected sheets: {selected}")
                messagebox.showinfo("Result", f"Selected {len(selected)} sheets:\n" + "\n".join(selected))
            else:
                print("Cancelled")
                messagebox.showinfo("Result", "Cancelled")

        ttk.Button(
            root,
            text="Open Multi-Sheet Preset Selector",
            command=show_selector
        ).pack(pady=20)

        root.mainloop()

    test_dialog()
