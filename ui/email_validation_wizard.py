"""
Email Validation Wizard Dialog

Multi-step wizard for configuring and running Emailable email validation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
import pandas as pd


class EmailValidationWizard:
    """
    Multi-step wizard for email validation configuration.

    Steps:
    1. Select sheets to validate
    2. Choose email column for each sheet
    3. Set validation options
    """

    def __init__(self, parent, workbook_session, on_start_validation):
        """
        Initialize email validation wizard.

        Args:
            parent: Parent window
            workbook_session: WorkbookSession instance
            on_start_validation: Callback(config_dict) when user starts validation
        """
        self.parent = parent
        self.workbook_session = workbook_session
        self.on_start_validation = on_start_validation

        # Configuration
        self.selected_sheets = []  # List of sheet names
        self.sheet_column_map = {}  # {sheet_name: column_name}
        self.options = {
            'mode': 'bulk',
            'chunk_size': 10000,
            'treat_risky_as_bad': True
        }

        # Current step (0, 1, or 2)
        self.current_step = 0

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Email Validation Wizard")
        self.dialog.geometry("800x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._show_step(0)

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create wizard UI structure."""
        # Header with progress
        header_frame = tk.Frame(self.dialog, bg="#0078D4", height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        self.title_label = tk.Label(
            header_frame,
            text="Email Validation Wizard",
            font=("Segoe UI", 18, "bold"),
            bg="#0078D4",
            fg="white"
        )
        self.title_label.pack(pady=10)

        self.subtitle_label = tk.Label(
            header_frame,
            text="Step 1 of 3: Select Sheets",
            font=("Segoe UI", 11),
            bg="#0078D4",
            fg="white"
        )
        self.subtitle_label.pack()

        # Content area (will hold step frames)
        self.content_frame = tk.Frame(self.dialog, padx=20, pady=20)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Create step frames (hidden initially)
        self.step_frames = []
        self.step_frames.append(self._create_step1())
        self.step_frames.append(self._create_step2())
        self.step_frames.append(self._create_step3())

        # Navigation buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        self.back_button = tk.Button(
            button_frame,
            text="< Back",
            command=self._go_back,
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            state=tk.DISABLED
        )
        self.back_button.pack(side=tk.LEFT, padx=(0, 10))

        self.next_button = tk.Button(
            button_frame,
            text="Next >",
            command=self._go_next,
            bg="#0078D4",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8
        )
        self.next_button.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            font=("Segoe UI", 10),
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)

    def _create_step1(self):
        """Create Step 1: Sheet Selection."""
        frame = tk.Frame(self.content_frame)

        tk.Label(
            frame,
            text="Select sheets to validate:",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W, pady=(10, 10))

        tk.Label(
            frame,
            text="Choose one or more sheets that contain email addresses to validate.",
            font=("Segoe UI", 10),
            fg="gray"
        ).pack(anchor=tk.W, pady=(0, 20))

        # Sheet selection area with scrollbar
        list_frame = tk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sheet_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.MULTIPLE,
            font=("Segoe UI", 11),
            yscrollcommand=scrollbar.set,
            height=15
        )
        self.sheet_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sheet_listbox.yview)

        # Populate with visible sheets
        visible_sheets = self.workbook_session.get_visible_sheets()
        for sheet_name in visible_sheets:
            self.sheet_listbox.insert(tk.END, sheet_name)

        # Select first sheet by default
        if visible_sheets:
            self.sheet_listbox.selection_set(0)

        # Select/Deselect All buttons
        button_row = tk.Frame(frame)
        button_row.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            button_row,
            text="Select All",
            command=self._select_all_sheets,
            font=("Segoe UI", 9),
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            button_row,
            text="Deselect All",
            command=self._deselect_all_sheets,
            font=("Segoe UI", 9),
            padx=10,
            pady=5
        ).pack(side=tk.LEFT)

        return frame

    def _create_step2(self):
        """Create Step 2: Column Mapping."""
        frame = tk.Frame(self.content_frame)

        tk.Label(
            frame,
            text="Select email column for each sheet:",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W, pady=(10, 10))

        tk.Label(
            frame,
            text="Choose the column containing email addresses for each selected sheet.",
            font=("Segoe UI", 10),
            fg="gray"
        ).pack(anchor=tk.W, pady=(0, 20))

        # Scrollable frame for sheet column mappings
        canvas_frame = tk.Frame(frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame, bg="white")
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.column_mapping_frame = tk.Frame(canvas, bg="white")

        self.column_mapping_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.column_mapping_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.column_mapping_widgets = {}  # {sheet_name: combobox_widget}

        return frame

    def _create_step3(self):
        """Create Step 3: Options."""
        frame = tk.Frame(self.content_frame)

        tk.Label(
            frame,
            text="Validation Options:",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W, pady=(10, 10))

        tk.Label(
            frame,
            text="Configure how the email validation will be performed.",
            font=("Segoe UI", 10),
            fg="gray"
        ).pack(anchor=tk.W, pady=(0, 20))

        # Mode selection
        mode_frame = tk.LabelFrame(frame, text="Validation Mode", font=("Segoe UI", 10), padx=10, pady=10)
        mode_frame.pack(fill=tk.X, pady=(0, 20))

        self.mode_var = tk.StringVar(value="bulk")

        tk.Radiobutton(
            mode_frame,
            text="Bulk Mode (Recommended) - Fast batch processing for large lists",
            variable=self.mode_var,
            value="bulk",
            font=("Segoe UI", 10)
        ).pack(anchor=tk.W, pady=5)

        tk.Radiobutton(
            mode_frame,
            text="Real-time Mode - Immediate validation (slower, use for small lists)",
            variable=self.mode_var,
            value="realtime",
            font=("Segoe UI", 10)
        ).pack(anchor=tk.W, pady=5)

        # Chunk size (for bulk mode)
        chunk_frame = tk.LabelFrame(frame, text="Processing", font=("Segoe UI", 10), padx=10, pady=10)
        chunk_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            chunk_frame,
            text="Chunk Size (emails per batch):",
            font=("Segoe UI", 10)
        ).pack(anchor=tk.W, pady=(0, 5))

        self.chunk_size_var = tk.IntVar(value=10000)
        chunk_spinbox = tk.Spinbox(
            chunk_frame,
            from_=100,
            to=50000,
            increment=1000,
            textvariable=self.chunk_size_var,
            font=("Segoe UI", 10),
            width=15
        )
        chunk_spinbox.pack(anchor=tk.W)

        # Status interpretation
        status_frame = tk.LabelFrame(frame, text="Status Interpretation", font=("Segoe UI", 10), padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=(0, 20))

        self.treat_risky_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            status_frame,
            text="Treat 'Risky' and 'Undeliverable' as 'Bad' in summary counts",
            variable=self.treat_risky_var,
            font=("Segoe UI", 10)
        ).pack(anchor=tk.W, pady=5)

        return frame

    def _show_step(self, step_index):
        """Show the specified step."""
        self.current_step = step_index

        # Update subtitle
        step_titles = [
            "Step 1 of 3: Select Sheets",
            "Step 2 of 3: Choose Email Columns",
            "Step 3 of 3: Set Options"
        ]
        self.subtitle_label.config(text=step_titles[step_index])

        # Hide all step frames
        for frame in self.step_frames:
            frame.pack_forget()

        # Show current step
        self.step_frames[step_index].pack(fill=tk.BOTH, expand=True)

        # Update button states
        if step_index == 0:
            self.back_button.config(state=tk.DISABLED)
            self.next_button.config(text="Next >", command=self._go_next)
        elif step_index == 2:
            self.back_button.config(state=tk.NORMAL)
            self.next_button.config(text="Start Validation", command=self._start_validation,
                                   bg="#28a745")
        else:
            self.back_button.config(state=tk.NORMAL)
            self.next_button.config(text="Next >", command=self._go_next, bg="#0078D4")

        # Special handling for step 2 (populate column mappings)
        if step_index == 1:
            self._populate_column_mappings()

    def _go_back(self):
        """Navigate to previous step."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _go_next(self):
        """Navigate to next step."""
        if self.current_step == 0:
            # Validate sheet selection
            selected_indices = self.sheet_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning(
                    "No Sheets Selected",
                    "Please select at least one sheet to validate.",
                    parent=self.dialog
                )
                return

            self.selected_sheets = [self.sheet_listbox.get(i) for i in selected_indices]
            self._show_step(1)

        elif self.current_step == 1:
            # Validate column selection
            valid = True
            for sheet_name in self.selected_sheets:
                combobox = self.column_mapping_widgets.get(sheet_name)
                if not combobox or not combobox.get():
                    messagebox.showwarning(
                        "Missing Column Selection",
                        f"Please select an email column for sheet: {sheet_name}",
                        parent=self.dialog
                    )
                    valid = False
                    break
                self.sheet_column_map[sheet_name] = combobox.get()

            if valid:
                self._show_step(2)

    def _select_all_sheets(self):
        """Select all sheets in listbox."""
        self.sheet_listbox.selection_set(0, tk.END)

    def _deselect_all_sheets(self):
        """Deselect all sheets in listbox."""
        self.sheet_listbox.selection_clear(0, tk.END)

    def _populate_column_mappings(self):
        """Populate column selection widgets for each selected sheet."""
        # Clear existing widgets
        for widget in self.column_mapping_frame.winfo_children():
            widget.destroy()
        self.column_mapping_widgets.clear()

        # Create row for each selected sheet
        for idx, sheet_name in enumerate(self.selected_sheets):
            # Get sheet data to extract columns
            sheet_state = self.workbook_session.get_sheet(sheet_name)

            # Load sheet if not loaded
            if not sheet_state.is_loaded and sheet_state.df_original is None:
                # Need to lazy load - try to load it
                # This requires access to the file which we'll handle via callback
                columns = self._get_sheet_columns(sheet_name)
            else:
                if sheet_state.df_original is not None:
                    columns = list(sheet_state.df_original.columns)
                else:
                    columns = []

            # Sheet label
            tk.Label(
                self.column_mapping_frame,
                text=f"Sheet: {sheet_name}",
                font=("Segoe UI", 10, "bold"),
                bg="white"
            ).grid(row=idx*2, column=0, sticky=tk.W, pady=(10, 5), padx=10)

            # Column dropdown
            combo_frame = tk.Frame(self.column_mapping_frame, bg="white")
            combo_frame.grid(row=idx*2+1, column=0, sticky=tk.W, pady=(0, 10), padx=20)

            tk.Label(
                combo_frame,
                text="Email Column:",
                font=("Segoe UI", 10),
                bg="white"
            ).pack(side=tk.LEFT, padx=(0, 10))

            combobox = ttk.Combobox(
                combo_frame,
                values=columns,
                state="readonly",
                font=("Segoe UI", 10),
                width=30
            )
            combobox.pack(side=tk.LEFT)

            # Auto-select if column name contains 'email' or 'mail'
            for col in columns:
                if 'email' in col.lower() or 'mail' in col.lower():
                    combobox.set(col)
                    break

            self.column_mapping_widgets[sheet_name] = combobox

    def _get_sheet_columns(self, sheet_name):
        """Get columns for a sheet (handles lazy loading)."""
        try:
            # Read just first row to get columns
            df_sample = pd.read_excel(
                self.workbook_session.file_path,
                sheet_name=sheet_name,
                nrows=1
            )
            return list(df_sample.columns)
        except Exception as e:
            messagebox.showerror(
                "Error Loading Sheet",
                f"Failed to load columns from sheet '{sheet_name}':\n{e}",
                parent=self.dialog
            )
            return []

    def _start_validation(self):
        """Start the validation process."""
        # Gather configuration
        config = {
            'sheets': self.selected_sheets,
            'column_map': self.sheet_column_map,
            'mode': self.mode_var.get(),
            'chunk_size': self.chunk_size_var.get(),
            'treat_risky_as_bad': self.treat_risky_var.get()
        }

        # Close wizard
        self.dialog.destroy()

        # Trigger validation
        self.on_start_validation(config)

    def show(self):
        """Show the wizard dialog."""
        self.dialog.wait_window()
