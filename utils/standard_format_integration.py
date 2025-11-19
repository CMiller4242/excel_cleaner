"""
Standard Format Integration Module
Provides UI components and methods for Standard Format functionality

This module can be imported into main_gui_v2.py to add Standard Format features
"""

import threading
from typing import Optional, Dict, List, Tuple
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


class StandardFormatIntegration:
    """
    Integration class for Standard Format features

    Usage in main_gui_v2.py:
    1. Import this module
    2. Initialize: self.sf_integration = StandardFormatIntegration(self)
    3. Add status indicator: self.sf_integration.create_status_indicator(parent_frame)
    4. Add standardize button: self.sf_integration.create_standardize_button(toolbar)
    """

    def __init__(self, main_gui):
        """
        Initialize integration

        Args:
            main_gui: Reference to main GUI object (main_gui_v2.UniversalExcelTool instance)
        """
        self.main_gui = main_gui
        self.column_mapper = None  # Lazy load
        self.header_detector = None  # Lazy load
        self.status_label = None  # Will hold the status indicator widget
        self.current_compliance = None  # Cached compliance report

    def create_status_indicator(self, parent_frame):
        """
        Create Standard Format status indicator label

        Args:
            parent_frame: Parent frame to add the indicator to

        Returns:
            The created label widget
        """
        self.status_label = ttk.Label(
            parent_frame,
            text="Standard Format: Not Checked",
            relief=tk.SUNKEN,
            padding=5,
            font=("Arial", 10)
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        return self.status_label

    def update_status_indicator(self):
        """Update the status indicator with current data compliance"""
        if self.status_label is None:
            return

        if not hasattr(self.main_gui, 'df') or self.main_gui.df is None:
            self.status_label.config(text="Standard Format: No Data Loaded")
            return

        # Get compliance report
        try:
            from utils.column_mapper import ColumnMapper
            if self.column_mapper is None:
                self.column_mapper = ColumnMapper()

            compliance = self.column_mapper.get_compliance_report(self.main_gui.df)
            self.current_compliance = compliance

            # Format status text
            compliance_pct = compliance['compliance_percentage']
            standard_found = compliance['standard_columns_found']
            total_standard = compliance['total_standard_columns']
            non_standard = compliance['columns_to_remove']

            if compliance_pct >= 90:
                symbol = "✓"
                color = "green"
            elif compliance_pct >= 70:
                symbol = "⚠"
                color = "orange"
            else:
                symbol = "✗"
                color = "red"

            status_text = f"Standard Format: {compliance_pct:.0f}% {symbol} | {standard_found}/{total_standard} cols | {non_standard} non-std"

            self.status_label.config(text=status_text, foreground=color)

        except Exception as e:
            self.status_label.config(text=f"Standard Format: Error - {str(e)}")

    def create_standardize_button(self, parent_frame):
        """
        Create "Standardize Columns" button

        Args:
            parent_frame: Parent frame (typically toolbar)

        Returns:
            The created button widget
        """
        button = ttk.Button(
            parent_frame,
            text="🔧 Standardize Columns",
            command=self.standardize_columns,
            width=20
        )
        button.pack(side=tk.LEFT, padx=5)
        return button

    def standardize_columns(self):
        """Main entry point - standardize columns in current data"""
        # Check if data is loaded
        if not hasattr(self.main_gui, 'df') or self.main_gui.df is None:
            messagebox.showerror("No Data Loaded", "Please load a file first before standardizing.")
            return

        # Get column mappings
        try:
            from utils.column_mapper import ColumnMapper
            if self.column_mapper is None:
                self.column_mapper = ColumnMapper()

            compliance = self.column_mapper.get_compliance_report(self.main_gui.df)
            mappings = compliance['mappings']

        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze columns: {str(e)}")
            return

        # Show preview dialog
        dialog = StandardizePreviewDialog(
            self.main_gui.root,
            mappings,
            compliance
        )

        result = dialog.show()

        if result == "apply":
            # Get selected operations
            selected_renames = dialog.get_selected_renames()
            selected_removals = dialog.get_selected_removals()

            # Apply standardization
            self.apply_standardization(selected_renames, selected_removals)

    def apply_standardization(self, renames: List[Tuple[str, str]], removals: List[str]):
        """
        Apply column standardization operations

        Args:
            renames: List of (old_name, new_name) tuples
            removals: List of column names to remove
        """
        if not renames and not removals:
            messagebox.showinfo("No Changes", "No standardization operations selected.")
            return

        try:
            df = self.main_gui.df.copy()

            # Apply renames
            if renames:
                rename_dict = {old: new for old, new in renames}
                df = df.rename(columns=rename_dict)

            # Remove columns
            if removals:
                existing_removals = [col for col in removals if col in df.columns]
                if existing_removals:
                    df = df.drop(columns=existing_removals)

            # Update main GUI dataframe
            self.main_gui.df = df

            # Refresh display
            if hasattr(self.main_gui, 'refresh_preview'):
                self.main_gui.refresh_preview()

            # Update status
            self.update_status_indicator()

            # Show confirmation
            message = f"✅ Standardization complete:\n"
            if renames:
                message += f"  • Renamed {len(renames)} columns\n"
            if removals:
                message += f"  • Removed {len(removals)} columns\n"

            messagebox.showinfo("Success", message)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply standardization: {str(e)}")

    def detect_header_row(self, file_path: str) -> int:
        """
        Detect which row contains the header

        Args:
            file_path: Path to Excel file

        Returns:
            Header row index (0-based)
        """
        try:
            from utils.header_row_detector import HeaderRowDetector
            if self.header_detector is None:
                self.header_detector = HeaderRowDetector()

            candidate = self.header_detector.detect_header_row(file_path)

            # If confidence is low, ask user
            if candidate.confidence_score < 0.8:
                return self.prompt_header_row_selection(file_path, candidate)

            return candidate.row_index

        except Exception as e:
            print(f"Header detection failed: {e}")
            return 0  # Default to first row

    def prompt_header_row_selection(self, file_path: str, best_candidate) -> int:
        """
        Show dialog for user to select header row

        Args:
            file_path: Path to Excel file
            best_candidate: HeaderRowCandidate with best guess

        Returns:
            Selected row index (0-based)
        """
        dialog = HeaderRowSelectionDialog(
            self.main_gui.root,
            file_path,
            best_candidate
        )

        selected_row = dialog.show()
        return selected_row if selected_row is not None else best_candidate.row_index


class StandardizePreviewDialog:
    """Dialog showing preview of standardization operations"""

    def __init__(self, parent, mappings: Dict, compliance: Dict):
        self.parent = parent
        self.mappings = mappings
        self.compliance = compliance
        self.result = None

        # Track selections
        self.rename_selections = {}  # {original_name: (selected, standard_name)}
        self.removal_selections = {}  # {column_name: selected}

    def show(self) -> Optional[str]:
        """Show dialog and return result ('apply' or None)"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Standardize Columns - Preview")
        self.dialog.geometry("700x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Title
        title_frame = ttk.Frame(self.dialog)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            title_frame,
            text="Column Standardization Preview",
            font=("Arial", 14, "bold")
        ).pack()

        compliance_pct = self.compliance['compliance_percentage']
        ttk.Label(
            title_frame,
            text=f"Current Compliance: {compliance_pct:.0f}%",
            font=("Arial", 11)
        ).pack()

        # Notebook for different sections
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Columns to Rename
        rename_frame = ttk.Frame(notebook)
        notebook.add(rename_frame, text=f"Rename ({self.compliance['columns_to_rename']})")
        self._create_rename_tab(rename_frame)

        # Tab 2: Columns to Remove
        remove_frame = ttk.Frame(notebook)
        notebook.add(remove_frame, text=f"Remove ({self.compliance['columns_to_remove']})")
        self._create_remove_tab(remove_frame)

        # Tab 3: Already Standard
        standard_frame = ttk.Frame(notebook)
        notebook.add(standard_frame, text=f"Already Standard ({self.compliance['columns_already_standard']})")
        self._create_standard_tab(standard_frame)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Apply Standardization",
            command=self._on_apply,
            width=20
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=15
        ).pack(side=tk.RIGHT)

        # Wait for dialog
        self.dialog.wait_window()
        return self.result

    def _create_rename_tab(self, parent):
        """Create tab showing columns to rename"""
        # Add "Select All" checkbox
        select_all_var = tk.BooleanVar(value=True)

        def toggle_all():
            state = select_all_var.get()
            for var in self.rename_selections.values():
                var[0].set(state)

        ttk.Checkbutton(
            parent,
            text="Select All",
            variable=select_all_var,
            command=toggle_all
        ).pack(anchor=tk.W, padx=5, pady=5)

        # Scrollable list
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add items
        for orig_name, mapping in self.mappings.items():
            if mapping.action == 'rename' and mapping.confidence >= 0.90:
                var = tk.BooleanVar(value=True)
                self.rename_selections[orig_name] = (var, mapping.standard_name)

                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, padx=5, pady=2)

                ttk.Checkbutton(
                    frame,
                    variable=var
                ).pack(side=tk.LEFT)

                ttk.Label(
                    frame,
                    text=f"{orig_name}  →  {mapping.standard_name}",
                    font=("Arial", 10)
                ).pack(side=tk.LEFT, padx=5)

                ttk.Label(
                    frame,
                    text=f"({mapping.confidence:.0%} confidence)",
                    foreground="gray"
                ).pack(side=tk.LEFT)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_remove_tab(self, parent):
        """Create tab showing columns to remove"""
        # Add "Select All" checkbox
        select_all_var = tk.BooleanVar(value=True)

        def toggle_all():
            state = select_all_var.get()
            for var in self.removal_selections.values():
                var.set(state)

        ttk.Checkbutton(
            parent,
            text="Select All",
            variable=select_all_var,
            command=toggle_all
        ).pack(anchor=tk.W, padx=5, pady=5)

        # Scrollable list
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add items
        for orig_name, mapping in self.mappings.items():
            if mapping.action == 'remove':
                var = tk.BooleanVar(value=True)
                self.removal_selections[orig_name] = var

                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, padx=5, pady=2)

                ttk.Checkbutton(
                    frame,
                    variable=var
                ).pack(side=tk.LEFT)

                ttk.Label(
                    frame,
                    text=orig_name,
                    font=("Arial", 10, "bold")
                ).pack(side=tk.LEFT, padx=5)

                ttk.Label(
                    frame,
                    text=f"({mapping.reason})",
                    foreground="gray"
                ).pack(side=tk.LEFT)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_standard_tab(self, parent):
        """Create tab showing columns already in standard format"""
        # Scrollable list
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add items
        for orig_name, mapping in self.mappings.items():
            if mapping.action == 'keep':
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, padx=5, pady=2)

                ttk.Label(
                    frame,
                    text="✓",
                    foreground="green",
                    font=("Arial", 12, "bold")
                ).pack(side=tk.LEFT)

                ttk.Label(
                    frame,
                    text=orig_name,
                    font=("Arial", 10)
                ).pack(side=tk.LEFT, padx=5)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_apply(self):
        """User clicked Apply"""
        self.result = "apply"
        self.dialog.destroy()

    def _on_cancel(self):
        """User clicked Cancel"""
        self.result = None
        self.dialog.destroy()

    def get_selected_renames(self) -> List[Tuple[str, str]]:
        """Get list of selected rename operations"""
        return [
            (orig_name, standard_name)
            for orig_name, (var, standard_name) in self.rename_selections.items()
            if var.get()
        ]

    def get_selected_removals(self) -> List[str]:
        """Get list of selected columns to remove"""
        return [
            col_name
            for col_name, var in self.removal_selections.items()
            if var.get()
        ]


class HeaderRowSelectionDialog:
    """Dialog for selecting correct header row"""

    def __init__(self, parent, file_path: str, best_candidate):
        self.parent = parent
        self.file_path = file_path
        self.best_candidate = best_candidate
        self.selected_row = None

    def show(self) -> Optional[int]:
        """Show dialog and return selected row index (0-based)"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Header Row")
        self.dialog.geometry("600x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Title
        ttk.Label(
            self.dialog,
            text="Which row contains the column headers?",
            font=("Arial", 12, "bold")
        ).pack(pady=10)

        ttk.Label(
            self.dialog,
            text=f"Suggested: Row {self.best_candidate.row_index + 1} ({self.best_candidate.confidence_score:.0%} confidence)",
            foreground="blue"
        ).pack()

        # Preview first 5 rows
        import pandas as pd
        df = pd.read_excel(self.file_path, header=None, nrows=5)

        # Radio buttons for each row
        selected_var = tk.IntVar(value=self.best_candidate.row_index)

        for idx in range(min(5, len(df))):
            frame = ttk.Frame(self.dialog)
            frame.pack(fill=tk.X, padx=20, pady=5)

            ttk.Radiobutton(
                frame,
                text=f"Row {idx + 1}:",
                variable=selected_var,
                value=idx
            ).pack(side=tk.LEFT)

            # Show preview of row contents
            row_preview = " | ".join([str(val)[:20] for val in df.iloc[idx].values[:5]])
            ttk.Label(
                frame,
                text=row_preview,
                foreground="gray"
            ).pack(side=tk.LEFT, padx=10)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)

        def on_ok():
            self.selected_row = selected_var.get()
            self.dialog.destroy()

        def on_cancel():
            self.selected_row = None
            self.dialog.destroy()

        ttk.Button(button_frame, text="OK", command=on_ok, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=15).pack(side=tk.LEFT, padx=5)

        self.dialog.wait_window()
        return self.selected_row


def add_standard_format_to_gui(main_gui):
    """
    Helper function to add Standard Format features to existing GUI

    Call this from main_gui_v2.py's create_widgets() method

    Args:
        main_gui: Instance of UniversalExcelTool
    """
    # Initialize integration
    if not hasattr(main_gui, 'sf_integration'):
        main_gui.sf_integration = StandardFormatIntegration(main_gui)

    # Add status indicator to status bar (if exists)
    if hasattr(main_gui, 'status_bar'):
        main_gui.sf_integration.create_status_indicator(main_gui.status_bar)

    # Add standardize button to toolbar
    if hasattr(main_gui, 'toolbar'):
        main_gui.sf_integration.create_standardize_button(main_gui.toolbar)

    return main_gui.sf_integration
