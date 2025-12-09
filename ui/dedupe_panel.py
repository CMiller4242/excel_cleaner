"""
Comparison Mode UI Panel
Provides interface for two-file comparison processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from dedupe.dedupe_engine import DeduplicationEngine, export_results
from datetime import datetime
import os

class DedupePanel(tk.Frame):
    """
    UI panel for two-file comparison mode
    """

    def __init__(self, parent):
        super().__init__(parent, bg="white")

        # Master file (file1) variables
        self.file1_path = None
        self.file1_df = None
        self.file1_sheets = []
        self.file1_sheet_var = tk.StringVar()
        self.file1_display_name = tk.StringVar()
        self.file1_sheet_confirmed = False

        # Secondary files (list of dictionaries for multi-file support)
        self.secondary_files = []
        # Start with one default secondary file
        self._add_secondary_file_data()

        self.column_mapping = {}
        self.results = None

        # Field enabled states (for mapping toggles)
        self.field_enabled = {
            'email': tk.BooleanVar(value=True),  # Always required
            'phone': tk.BooleanVar(value=True),
            'name': tk.BooleanVar(value=True),
            'company': tk.BooleanVar(value=True),
            'city': tk.BooleanVar(value=True),
            'state': tk.BooleanVar(value=True)
        }

        # Store combobox widgets for enable/disable
        self.field_combos = {}

        # Container for secondary file UI blocks
        self.secondary_files_container = None

        self._create_widgets()

    def _add_secondary_file_data(self):
        """Add a new secondary file data structure"""
        file_data = {
            'index': len(self.secondary_files),
            'path': None,
            'df': None,
            'sheets': [],
            'sheet_var': tk.StringVar(),
            'display_name_var': tk.StringVar(),
            'sheet_confirmed': False,
            'widgets': {}  # Store widget references for this file
        }
        self.secondary_files.append(file_data)
        return file_data

    def _create_widgets(self):
        """Create UI components"""

        # Header
        header = tk.Frame(self, bg="#0078D4", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Comparison Mode",
            font=("Segoe UI", 16, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=10)

        tk.Label(
            header,
            text="Compare files to identify overlap, differences, new entries, and existing matches using tiered matching (Email → Phone+Name → Company+Location).",
            font=("Segoe UI", 10),
            bg="#0078D4",
            fg="white"
        ).pack()

        # Main content with scroll
        content_container = tk.Frame(self, bg="white")
        content_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(content_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg="white")

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        # FILE SELECTION SECTION
        self._create_file_selection(content)

        # COLUMN MAPPING SECTION
        self.mapping_section = tk.LabelFrame(
            content,
            text="2. Map Columns",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#0078D4"
        )
        self.mapping_section.pack(fill=tk.X, padx=30, pady=(20, 10))

        tk.Label(
            self.mapping_section,
            text="Column mapping will appear after files are loaded",
            font=("Segoe UI", 10),
            bg="white",
            fg="#999"
        ).pack(pady=20)

        # ACTION BUTTONS
        action_frame = tk.Frame(content, bg="white")
        action_frame.pack(fill=tk.X, padx=30, pady=(20, 10))

        self.run_button = tk.Button(
            action_frame,
            text="▶ Run Comparison",
            command=self._run_deduplication,
            font=("Segoe UI", 12, "bold"),
            bg="#107C10",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=40,
            pady=15,
            state=tk.DISABLED
        )
        self.run_button.pack()

        # PROGRESS / LOGGING AREA
        log_frame = tk.LabelFrame(
            content,
            text="Progress Log",
            font=("Segoe UI", 11, "bold"),
            bg="white"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(10, 30))

        self.log_text = tk.Text(
            log_frame,
            font=("Consolas", 9),
            bg="#F8F8F8",
            fg="#333",
            height=15,
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        log_scroll = tk.Scrollbar(self.log_text, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scroll.set)

    def _create_file_selection(self, parent):
        """Create file selection section"""
        file_section = tk.LabelFrame(
            parent,
            text="1. Select Files",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#0078D4"
        )
        file_section.pack(fill=tk.X, padx=30, pady=(20, 10))

        # Master file
        master_frame = tk.Frame(file_section, bg="white")
        master_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

        tk.Label(
            master_frame,
            text="Master File (Priority):",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor=tk.W, pady=(0, 5))

        file1_input_frame = tk.Frame(master_frame, bg="white")
        file1_input_frame.pack(fill=tk.X)

        self.file1_entry = tk.Entry(
            file1_input_frame,
            font=("Segoe UI", 10),
            state="readonly"
        )
        self.file1_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        tk.Button(
            file1_input_frame,
            text="Browse...",
            command=lambda: self._load_file(1),
            font=("Segoe UI", 9),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT)

        self.file1_status = tk.Label(
            master_frame,
            text="",
            font=("Segoe UI", 8),
            bg="white",
            fg="#666"
        )
        self.file1_status.pack(anchor=tk.W, pady=(3, 0))

        # Sheet selection for File 1
        self.file1_sheet_frame = tk.Frame(master_frame, bg="white")
        # Initially hidden, shown after file load

        tk.Label(
            self.file1_sheet_frame,
            text="Select Sheet:",
            font=("Segoe UI", 9),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.file1_sheet_combo = ttk.Combobox(
            self.file1_sheet_frame,
            textvariable=self.file1_sheet_var,
            state="readonly",
            width=25,
            font=("Segoe UI", 9)
        )
        self.file1_sheet_combo.pack(side=tk.LEFT)
        self.file1_sheet_combo.bind('<<ComboboxSelected>>', lambda e: self._on_sheet_selected())

        # Confirm button for File 1
        self.file1_confirm_frame = tk.Frame(master_frame, bg="white")
        # Initially hidden, shown after file load

        self.file1_confirm_button = tk.Button(
            self.file1_confirm_frame,
            text="Confirm Sheet Selection",
            command=lambda: self._confirm_sheet(1),
            font=("Segoe UI", 9),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5,
            state=tk.DISABLED
        )
        self.file1_confirm_button.pack(side=tk.LEFT, padx=(0, 10))

        self.file1_confirm_status = tk.Label(
            self.file1_confirm_frame,
            text="",
            font=("Segoe UI", 8),
            bg="white",
            fg="#107C10"
        )
        self.file1_confirm_status.pack(side=tk.LEFT)

        # Display name for File 1
        self.file1_name_frame = tk.Frame(master_frame, bg="white")
        # Initially hidden, shown after file load

        tk.Label(
            self.file1_name_frame,
            text="Display Name (optional):",
            font=("Segoe UI", 9),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.file1_name_entry = tk.Entry(
            self.file1_name_frame,
            textvariable=self.file1_display_name,
            font=("Segoe UI", 9),
            width=40
        )
        self.file1_name_entry.pack(side=tk.LEFT)

        # Secondary files section
        secondary_section_frame = tk.Frame(file_section, bg="white")
        secondary_section_frame.pack(fill=tk.X, padx=15, pady=(10, 15))

        # Header with Add File button
        secondary_header = tk.Frame(secondary_section_frame, bg="white")
        secondary_header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            secondary_header,
            text="Secondary Files (Up to 10 total):",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(side=tk.LEFT)

        tk.Button(
            secondary_header,
            text="+ Add File",
            command=self._add_secondary_file_ui,
            font=("Segoe UI", 9),
            bg="#107C10",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=3
        ).pack(side=tk.LEFT, padx=(15, 0))

        # Container for secondary file blocks
        self.secondary_files_container = tk.Frame(secondary_section_frame, bg="white")
        self.secondary_files_container.pack(fill=tk.X)

        # Create first secondary file block
        self._create_secondary_file_block(0)

    def _create_secondary_file_block(self, file_index):
        """Create a UI block for a secondary file"""
        if file_index >= len(self.secondary_files):
            return

        file_data = self.secondary_files[file_index]

        # Main block frame with border
        block_frame = tk.Frame(self.secondary_files_container, bg="white", relief=tk.RIDGE, bd=1)
        block_frame.pack(fill=tk.X, pady=(0, 10))

        # Header with file number and remove button
        header_frame = tk.Frame(block_frame, bg="#F0F0F0")
        header_frame.pack(fill=tk.X)

        tk.Label(
            header_frame,
            text=f"Secondary File #{file_index + 1}:",
            font=("Segoe UI", 9, "bold"),
            bg="#F0F0F0"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # Only show remove button if more than 1 secondary file
        if len(self.secondary_files) > 1:
            remove_btn = tk.Button(
                header_frame,
                text="✕ Remove File",
                command=lambda: self._remove_secondary_file(file_index),
                font=("Segoe UI", 8),
                bg="#D13438",
                fg="white",
                relief=tk.FLAT,
                cursor="hand2",
                padx=10,
                pady=2
            )
            remove_btn.pack(side=tk.RIGHT, padx=10, pady=5)
            file_data['widgets']['remove_button'] = remove_btn

        # Content frame
        content_frame = tk.Frame(block_frame, bg="white")
        content_frame.pack(fill=tk.X, padx=15, pady=10)

        # File picker
        file_input_frame = tk.Frame(content_frame, bg="white")
        file_input_frame.pack(fill=tk.X)

        file_entry = tk.Entry(
            file_input_frame,
            font=("Segoe UI", 10),
            state="readonly"
        )
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        file_data['widgets']['file_entry'] = file_entry

        browse_btn = tk.Button(
            file_input_frame,
            text="Browse...",
            command=lambda: self._load_secondary_file(file_index),
            font=("Segoe UI", 9),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=5
        )
        browse_btn.pack(side=tk.LEFT)
        file_data['widgets']['browse_button'] = browse_btn

        # Status label
        status_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 8),
            bg="white",
            fg="#666"
        )
        status_label.pack(anchor=tk.W, pady=(3, 0))
        file_data['widgets']['status_label'] = status_label

        # Sheet selection frame
        sheet_frame = tk.Frame(content_frame, bg="white")
        file_data['widgets']['sheet_frame'] = sheet_frame

        tk.Label(
            sheet_frame,
            text="Select Sheet:",
            font=("Segoe UI", 9),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        sheet_combo = ttk.Combobox(
            sheet_frame,
            textvariable=file_data['sheet_var'],
            state="readonly",
            width=25,
            font=("Segoe UI", 9)
        )
        sheet_combo.pack(side=tk.LEFT)
        sheet_combo.bind('<<ComboboxSelected>>', lambda e, idx=file_index: self._on_secondary_sheet_selected(idx))
        file_data['widgets']['sheet_combo'] = sheet_combo

        # Confirm button frame
        confirm_frame = tk.Frame(content_frame, bg="white")
        file_data['widgets']['confirm_frame'] = confirm_frame

        confirm_button = tk.Button(
            confirm_frame,
            text="Confirm Sheet Selection",
            command=lambda: self._confirm_secondary_sheet(file_index),
            font=("Segoe UI", 9),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5,
            state=tk.DISABLED
        )
        confirm_button.pack(side=tk.LEFT, padx=(0, 10))
        file_data['widgets']['confirm_button'] = confirm_button

        confirm_status = tk.Label(
            confirm_frame,
            text="",
            font=("Segoe UI", 8),
            bg="white",
            fg="#107C10"
        )
        confirm_status.pack(side=tk.LEFT)
        file_data['widgets']['confirm_status'] = confirm_status

        # Display name frame
        name_frame = tk.Frame(content_frame, bg="white")
        file_data['widgets']['name_frame'] = name_frame

        tk.Label(
            name_frame,
            text="Display Name (optional):",
            font=("Segoe UI", 9),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        name_entry = tk.Entry(
            name_frame,
            textvariable=file_data['display_name_var'],
            font=("Segoe UI", 9),
            width=40
        )
        name_entry.pack(side=tk.LEFT)
        file_data['widgets']['name_entry'] = name_entry

        # Store block frame reference
        file_data['widgets']['block_frame'] = block_frame

    def _add_secondary_file_ui(self):
        """Add a new secondary file block to the UI"""
        if len(self.secondary_files) >= 10:
            messagebox.showinfo(
                "Maximum Files Reached",
                "You can compare up to 10 files at a time."
            )
            return

        # Add new file data
        file_data = self._add_secondary_file_data()

        # Create UI block
        self._create_secondary_file_block(file_data['index'])

        # Update remove buttons visibility
        self._update_remove_buttons()

    def _remove_secondary_file(self, file_index):
        """Remove a secondary file block"""
        if len(self.secondary_files) <= 1:
            messagebox.showwarning(
                "Cannot Remove",
                "At least one secondary file is required for comparison."
            )
            return

        file_data = self.secondary_files[file_index]

        # Destroy the UI block
        if 'block_frame' in file_data['widgets']:
            file_data['widgets']['block_frame'].destroy()

        # Remove from list
        self.secondary_files.pop(file_index)

        # Update indices
        for i, fd in enumerate(self.secondary_files):
            fd['index'] = i

        # Recreate all blocks to update numbering
        for widget in self.secondary_files_container.winfo_children():
            widget.destroy()

        for i in range(len(self.secondary_files)):
            self._create_secondary_file_block(i)

        # Check if mapping needs update
        self._check_ready_for_mapping()

    def _update_remove_buttons(self):
        """Update visibility of remove buttons based on file count"""
        show_remove = len(self.secondary_files) > 1

        for file_data in self.secondary_files:
            if 'remove_button' in file_data['widgets']:
                if show_remove:
                    file_data['widgets']['remove_button'].pack(side=tk.RIGHT, padx=10, pady=5)
                else:
                    file_data['widgets']['remove_button'].pack_forget()

    def _load_secondary_file(self, file_index):
        """Load a secondary file"""
        file_path = filedialog.askopenfilename(
            title=f"Select Secondary File #{file_index + 1}",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            file_data = self.secondary_files[file_index]

            # Detect sheets in file
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            # Extract filename without extension for display name
            filename = os.path.basename(file_path)
            display_name = os.path.splitext(filename)[0]

            # Reset confirm state
            file_data['sheet_confirmed'] = False
            file_data['widgets']['confirm_status'].config(text="")

            # Store file info
            file_data['path'] = file_path
            file_data['sheets'] = sheet_names

            # Update file entry
            file_entry = file_data['widgets']['file_entry']
            file_entry.config(state="normal")
            file_entry.delete(0, tk.END)
            file_entry.insert(0, filename)
            file_entry.config(state="readonly")

            # Set display name
            file_data['display_name_var'].set(display_name)

            # Handle sheet selection
            if len(sheet_names) == 1:
                # Single sheet - auto-select
                file_data['sheet_var'].set(sheet_names[0])
                file_data['widgets']['sheet_combo']['values'] = sheet_names
                file_data['widgets']['sheet_combo'].config(state="readonly")
                # Load the sheet immediately
                file_data['df'] = pd.read_excel(file_path, sheet_name=sheet_names[0])
                file_data['widgets']['status_label'].config(
                    text=f"✓ Loaded: {len(file_data['df'])} rows × {len(file_data['df'].columns)} columns",
                    fg="#107C10"
                )
                self._log(f"Secondary file #{file_index + 1} loaded: {filename} (sheet: {sheet_names[0]}, {len(file_data['df'])} rows)")
                # Enable confirm button for single sheet
                file_data['widgets']['confirm_button'].config(
                    state=tk.NORMAL,
                    bg="#0078D4",
                    cursor="hand2"
                )
            else:
                # Multiple sheets - require selection
                file_data['widgets']['sheet_combo']['values'] = sheet_names
                file_data['widgets']['sheet_combo'].config(state="readonly")
                file_data['sheet_var'].set('')  # No default selection
                file_data['df'] = None
                file_data['widgets']['status_label'].config(
                    text=f"✓ File loaded with {len(sheet_names)} sheets - please select a sheet",
                    fg="#0078D4"
                )
                self._log(f"Secondary file #{file_index + 1} loaded: {filename} ({len(sheet_names)} sheets)")
                # Disable confirm button until sheet is selected
                file_data['widgets']['confirm_button'].config(
                    state=tk.DISABLED,
                    bg="#0078D4"
                )

            # Show sheet, confirm, and display name UI
            file_data['widgets']['sheet_frame'].pack(fill=tk.X, pady=(5, 0))
            file_data['widgets']['confirm_frame'].pack(fill=tk.X, pady=(5, 0))
            file_data['widgets']['name_frame'].pack(fill=tk.X, pady=(5, 0))

            # Check if we can enable column mapping
            self._check_ready_for_mapping()

        except Exception as e:
            messagebox.showerror("Error Loading File", f"Failed to load file:\n{str(e)}")

    def _on_secondary_sheet_selected(self, file_index):
        """Handle sheet selection for a secondary file"""
        file_data = self.secondary_files[file_index]

        if file_data['path'] and file_data['sheet_var'].get():
            try:
                sheet_name = file_data['sheet_var'].get()
                file_data['df'] = pd.read_excel(file_data['path'], sheet_name=sheet_name)
                file_data['widgets']['status_label'].config(
                    text=f"✓ Loaded: {len(file_data['df'])} rows × {len(file_data['df'].columns)} columns",
                    fg="#107C10"
                )
                self._log(f"Secondary file #{file_index + 1} sheet loaded: {sheet_name} ({len(file_data['df'])} rows)")

                # Reset confirmation status when sheet changes
                if file_data['sheet_confirmed']:
                    file_data['sheet_confirmed'] = False
                    file_data['widgets']['confirm_status'].config(text="")
                    self._log(f"Secondary file #{file_index + 1} sheet changed - please confirm selection again")

                # Enable confirm button after sheet is loaded
                file_data['widgets']['confirm_button'].config(
                    state=tk.NORMAL,
                    bg="#0078D4",
                    cursor="hand2"
                )
            except Exception as e:
                messagebox.showerror("Error Loading Sheet", f"Failed to load sheet:\n{str(e)}")
                return

        # Check if we can enable column mapping
        self._check_ready_for_mapping()

    def _confirm_secondary_sheet(self, file_index):
        """Confirm the sheet selection for a secondary file"""
        file_data = self.secondary_files[file_index]

        if not file_data['sheet_var'].get():
            messagebox.showwarning("No Sheet Selected", "Please select a sheet first")
            return

        # Mark sheet as confirmed
        file_data['sheet_confirmed'] = True

        # Show confirmation message
        file_data['widgets']['confirm_status'].config(text="✓ Sheet confirmed")
        self._log(f"Secondary file #{file_index + 1} sheet confirmed: {file_data['sheet_var'].get()}")

        # Check if we can enable column mapping now
        self._check_ready_for_mapping()

    def _load_file(self, file_num):
        """Load a file and update UI"""
        file_path = filedialog.askopenfilename(
            title=f"Select {'Master' if file_num == 1 else 'Secondary'} File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            # Detect sheets in file
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            # Extract filename without extension for display name
            filename = os.path.basename(file_path)
            display_name = os.path.splitext(filename)[0]

            if file_num == 1:
                # Reset confirm state
                self.file1_sheet_confirmed = False
                self.file1_confirm_status.config(text="")

                # Store sheet info
                self.file1_path = file_path
                self.file1_sheets = sheet_names

                # Update file entry
                self.file1_entry.config(state="normal")
                self.file1_entry.delete(0, tk.END)
                self.file1_entry.insert(0, filename)
                self.file1_entry.config(state="readonly")

                # Set display name
                self.file1_display_name.set(display_name)

                # Handle sheet selection
                if len(sheet_names) == 1:
                    # Single sheet - auto-select but keep dropdown enabled
                    self.file1_sheet_var.set(sheet_names[0])
                    self.file1_sheet_combo['values'] = sheet_names
                    self.file1_sheet_combo.config(state="readonly")
                    # Load the sheet immediately
                    self.file1_df = pd.read_excel(file_path, sheet_name=sheet_names[0])
                    self.file1_status.config(
                        text=f"✓ Loaded: {len(self.file1_df)} rows × {len(self.file1_df.columns)} columns",
                        fg="#107C10"
                    )
                    self._log(f"Master file loaded: {filename} (sheet: {sheet_names[0]}, {len(self.file1_df)} rows)")
                    # Enable confirm button for single sheet
                    self.file1_confirm_button.config(
                        state=tk.NORMAL,
                        bg="#0078D4",
                        cursor="hand2"
                    )
                else:
                    # Multiple sheets - require selection
                    self.file1_sheet_combo['values'] = sheet_names
                    self.file1_sheet_combo.config(state="readonly")
                    self.file1_sheet_var.set('')  # No default selection
                    self.file1_df = None
                    self.file1_status.config(
                        text=f"✓ File loaded with {len(sheet_names)} sheets - please select a sheet",
                        fg="#0078D4"
                    )
                    self._log(f"Master file loaded: {filename} ({len(sheet_names)} sheets)")
                    # Disable confirm button until sheet is selected
                    self.file1_confirm_button.config(
                        state=tk.DISABLED,
                        bg="#0078D4"
                    )

                # Show sheet, confirm, and display name UI
                self.file1_sheet_frame.pack(fill=tk.X, pady=(5, 0))
                self.file1_confirm_frame.pack(fill=tk.X, pady=(5, 0))
                self.file1_name_frame.pack(fill=tk.X, pady=(5, 0))

            else:
                # Reset confirm state
                self.file2_sheet_confirmed = False
                self.file2_confirm_status.config(text="")

                # Store sheet info
                self.file2_path = file_path
                self.file2_sheets = sheet_names

                # Update file entry
                self.file2_entry.config(state="normal")
                self.file2_entry.delete(0, tk.END)
                self.file2_entry.insert(0, filename)
                self.file2_entry.config(state="readonly")

                # Set display name
                self.file2_display_name.set(display_name)

                # Handle sheet selection
                if len(sheet_names) == 1:
                    # Single sheet - auto-select but keep dropdown enabled
                    self.file2_sheet_var.set(sheet_names[0])
                    self.file2_sheet_combo['values'] = sheet_names
                    self.file2_sheet_combo.config(state="readonly")
                    # Load the sheet immediately
                    self.file2_df = pd.read_excel(file_path, sheet_name=sheet_names[0])
                    self.file2_status.config(
                        text=f"✓ Loaded: {len(self.file2_df)} rows × {len(self.file2_df.columns)} columns",
                        fg="#107C10"
                    )
                    self._log(f"Secondary file loaded: {filename} (sheet: {sheet_names[0]}, {len(self.file2_df)} rows)")
                    # Enable confirm button for single sheet
                    self.file2_confirm_button.config(
                        state=tk.NORMAL,
                        bg="#0078D4",
                        cursor="hand2"
                    )
                else:
                    # Multiple sheets - require selection
                    self.file2_sheet_combo['values'] = sheet_names
                    self.file2_sheet_combo.config(state="readonly")
                    self.file2_sheet_var.set('')  # No default selection
                    self.file2_df = None
                    self.file2_status.config(
                        text=f"✓ File loaded with {len(sheet_names)} sheets - please select a sheet",
                        fg="#0078D4"
                    )
                    self._log(f"Secondary file loaded: {filename} ({len(sheet_names)} sheets)")
                    # Disable confirm button until sheet is selected
                    self.file2_confirm_button.config(
                        state=tk.DISABLED,
                        bg="#0078D4"
                    )

                # Show sheet, confirm, and display name UI
                self.file2_sheet_frame.pack(fill=tk.X, pady=(5, 0))
                self.file2_confirm_frame.pack(fill=tk.X, pady=(5, 0))
                self.file2_name_frame.pack(fill=tk.X, pady=(5, 0))

            # Check if we can enable column mapping
            self._check_ready_for_mapping()

        except Exception as e:
            messagebox.showerror("Error Loading File", f"Failed to load file:\n{str(e)}")

    def _on_sheet_selected(self):
        """Handle sheet selection from dropdown"""
        # Load File 1 sheet if selected
        if self.file1_path and self.file1_sheet_var.get():
            try:
                sheet_name = self.file1_sheet_var.get()
                self.file1_df = pd.read_excel(self.file1_path, sheet_name=sheet_name)
                self.file1_status.config(
                    text=f"✓ Loaded: {len(self.file1_df)} rows × {len(self.file1_df.columns)} columns",
                    fg="#107C10"
                )
                self._log(f"Master file sheet loaded: {sheet_name} ({len(self.file1_df)} rows)")

                # Reset confirmation status when sheet changes
                if self.file1_sheet_confirmed:
                    self.file1_sheet_confirmed = False
                    self.file1_confirm_status.config(text="")
                    self._log(f"Master file sheet changed - please confirm selection again")

                # Enable confirm button after sheet is loaded
                self.file1_confirm_button.config(
                    state=tk.NORMAL,
                    bg="#0078D4",
                    cursor="hand2"
                )
            except Exception as e:
                messagebox.showerror("Error Loading Sheet", f"Failed to load sheet:\n{str(e)}")
                return

        # Load File 2 sheet if selected
        if self.file2_path and self.file2_sheet_var.get():
            try:
                sheet_name = self.file2_sheet_var.get()
                self.file2_df = pd.read_excel(self.file2_path, sheet_name=sheet_name)
                self.file2_status.config(
                    text=f"✓ Loaded: {len(self.file2_df)} rows × {len(self.file2_df.columns)} columns",
                    fg="#107C10"
                )
                self._log(f"Secondary file sheet loaded: {sheet_name} ({len(self.file2_df)} rows)")

                # Reset confirmation status when sheet changes
                if self.file2_sheet_confirmed:
                    self.file2_sheet_confirmed = False
                    self.file2_confirm_status.config(text="")
                    self._log(f"Secondary file sheet changed - please confirm selection again")

                # Enable confirm button after sheet is loaded
                self.file2_confirm_button.config(
                    state=tk.NORMAL,
                    bg="#0078D4",
                    cursor="hand2"
                )
            except Exception as e:
                messagebox.showerror("Error Loading Sheet", f"Failed to load sheet:\n{str(e)}")
                return

        # Check if we can enable column mapping
        self._check_ready_for_mapping()

    def _confirm_sheet(self, file_num):
        """Confirm the sheet selection for a file"""
        if file_num == 1:
            if not self.file1_sheet_var.get():
                messagebox.showwarning("No Sheet Selected", "Please select a sheet first")
                return

            # Mark sheet as confirmed
            self.file1_sheet_confirmed = True

            # Show confirmation message
            self.file1_confirm_status.config(text="✓ Sheet confirmed")
            self._log(f"Master file sheet confirmed: {self.file1_sheet_var.get()}")

        else:
            if not self.file2_sheet_var.get():
                messagebox.showwarning("No Sheet Selected", "Please select a sheet first")
                return

            # Mark sheet as confirmed
            self.file2_sheet_confirmed = True

            # Show confirmation message
            self.file2_confirm_status.config(text="✓ Sheet confirmed")
            self._log(f"Secondary file sheet confirmed: {self.file2_sheet_var.get()}")

        # Check if we can enable column mapping now
        self._check_ready_for_mapping()

    def _check_ready_for_mapping(self):
        """Check if master and ALL secondary files are loaded and sheets confirmed"""
        # Check master file
        if self.file1_df is None or not self.file1_sheet_confirmed:
            self._hide_column_mapping("Master file not ready")
            return

        # Check all secondary files
        all_secondary_ready = True
        for file_data in self.secondary_files:
            if file_data['df'] is None or not file_data['sheet_confirmed']:
                all_secondary_ready = False
                break

        if all_secondary_ready:
            self._create_column_mapping_ui()
            self.run_button.config(state=tk.NORMAL)
        else:
            self._hide_column_mapping("All secondary files must be loaded and confirmed")

    def _hide_column_mapping(self, message):
        """Hide column mapping with a message"""
        for widget in self.mapping_section.winfo_children():
            widget.destroy()
        tk.Label(
            self.mapping_section,
            text=f"Column mapping will appear after all files are loaded and sheets are confirmed.\n{message}",
            font=("Segoe UI", 10),
            bg="white",
            fg="#999"
        ).pack(pady=20)
        self.run_button.config(state=tk.DISABLED)

    def _create_column_mapping_ui(self):
        """Create column mapping interface"""
        # Clear existing
        for widget in self.mapping_section.winfo_children():
            widget.destroy()

        tk.Label(
            self.mapping_section,
            text="Map the columns from each file to the matching fields:",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, padx=15, pady=(15, 10))

        # Create mapping grid
        mapping_grid = tk.Frame(self.mapping_section, bg="white")
        mapping_grid.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Headers
        tk.Label(mapping_grid, text="Enable", font=("Segoe UI", 9, "bold"), bg="white", width=8).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(mapping_grid, text="Field", font=("Segoe UI", 9, "bold"), bg="white", width=15, anchor=tk.W).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        tk.Label(mapping_grid, text="Master File Column", font=("Segoe UI", 9, "bold"), bg="white", width=25).grid(row=0, column=2, padx=5, pady=5)
        tk.Label(mapping_grid, text="Secondary File Column", font=("Segoe UI", 9, "bold"), bg="white", width=25).grid(row=0, column=3, padx=5, pady=5)

        # Column dropdowns
        self.column_combos = {}
        self.field_combos = {}

        fields = [
            ('Email', 'email'),
            ('Phone', 'phone'),
            ('Contact Name', 'name'),
            ('Company', 'company'),
            ('City', 'city'),
            ('State', 'state')
        ]

        file1_cols = ['(None)'] + list(self.file1_df.columns)
        # Use first secondary file for mapping
        file2_cols = ['(None)'] + list(self.secondary_files[0]['df'].columns)

        for idx, (label, key) in enumerate(fields, start=1):
            # Enable checkbox
            is_email = (key == 'email')
            checkbox = tk.Checkbutton(
                mapping_grid,
                variable=self.field_enabled[key],
                command=lambda k=key: self._on_field_toggle(k),
                bg="white",
                state=tk.DISABLED if is_email else tk.NORMAL
            )
            checkbox.grid(row=idx, column=0, padx=5, pady=3)

            # Field label
            tk.Label(
                mapping_grid,
                text=f"{label}:",
                font=("Segoe UI", 9),
                bg="white",
                anchor=tk.W
            ).grid(row=idx, column=1, padx=5, pady=3, sticky=tk.W)

            # File 1 dropdown
            file1_var = tk.StringVar(value='(None)')
            file1_combo = ttk.Combobox(
                mapping_grid,
                textvariable=file1_var,
                values=file1_cols,
                state="readonly",
                width=23
            )
            file1_combo.grid(row=idx, column=2, padx=5, pady=3)
            self.column_combos[f'file1_{key}'] = file1_var

            # Try to auto-detect
            for col in self.file1_df.columns:
                if key.lower() in col.lower():
                    file1_var.set(col)
                    break

            # File 2 dropdown
            file2_var = tk.StringVar(value='(None)')
            file2_combo = ttk.Combobox(
                mapping_grid,
                textvariable=file2_var,
                values=file2_cols,
                state="readonly",
                width=23
            )
            file2_combo.grid(row=idx, column=3, padx=5, pady=3)
            self.column_combos[f'file2_{key}'] = file2_var

            # Store combo references for enable/disable
            self.field_combos[key] = (file1_combo, file2_combo)

            # Try to auto-detect
            for col in self.file2_df.columns:
                if key.lower() in col.lower():
                    file2_var.set(col)
                    break

        # Note
        tk.Label(
            self.mapping_section,
            text="Note: Email is required. Other fields improve matching accuracy. Uncheck fields to exclude them from matching.",
            font=("Segoe UI", 8),
            bg="white",
            fg="#666"
        ).pack(anchor=tk.W, padx=15, pady=(0, 10))

    def _on_field_toggle(self, field_key):
        """Handle field enable/disable toggle"""
        enabled = self.field_enabled[field_key].get()

        if field_key in self.field_combos:
            file1_combo, file2_combo = self.field_combos[field_key]
            new_state = "readonly" if enabled else "disabled"
            file1_combo.config(state=new_state)
            file2_combo.config(state=new_state)

    def _run_deduplication(self):
        """Run the comparison process"""
        # Validate column mapping
        mapping = {}
        for key, var in self.column_combos.items():
            value = var.get()
            if value != '(None)':
                mapping[key] = value

        # Check required fields
        if 'file1_email' not in mapping or 'file2_email' not in mapping:
            messagebox.showwarning(
                "Missing Required Field",
                "Email column mapping is required for both files"
            )
            return

        # Clear log
        self.log_text.delete('1.0', tk.END)
        self._log("Initializing comparison engine...")

        # Disable button during processing
        self.run_button.config(state=tk.DISABLED, text="Processing...")
        self.update()

        try:
            # Get master file display name
            file1_display = self.file1_display_name.get().strip() or os.path.splitext(os.path.basename(self.file1_path))[0]

            # Gather all secondary files data
            secondary_files_data = []
            for file_data in self.secondary_files:
                display_name = file_data['display_name_var'].get().strip() or \
                              os.path.splitext(os.path.basename(file_data['path']))[0]
                secondary_files_data.append({
                    'path': file_data['path'],
                    'sheet': file_data['sheet_var'].get(),
                    'display_name': display_name
                })

            # Get field enabled states
            enabled_fields = {key: var.get() for key, var in self.field_enabled.items()}

            # Check for large dataset
            total_rows = len(self.file1_df)
            for file_data in self.secondary_files:
                total_rows += len(file_data['df'])

            if total_rows > 100000:
                self._log(f"⚠ Large dataset detected ({total_rows:,} total rows). Processing may take several minutes...")

            # Run multi-file comparison
            engine = DeduplicationEngine(progress_callback=self._log)
            self.results = engine.run_multi(
                self.file1_path,
                secondary_files_data,
                mapping,
                sheet1=self.file1_sheet_var.get(),
                display_name1=file1_display,
                enabled_fields=enabled_fields
            )

            # Export results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"Comparison_Results_{timestamp}.xlsx"

            output_path = filedialog.asksaveasfilename(
                title="Save Comparison Results",
                defaultextension=".xlsx",
                initialfile=output_filename,
                filetypes=[("Excel files", "*.xlsx")]
            )

            if output_path:
                self._log(f"\nExporting results to: {output_path}")
                export_results(self.results, output_path)
                self._log("✓ Export complete!")

                messagebox.showinfo(
                    "Comparison Complete",
                    f"Results saved to:\n{output_path}\n\n"
                    f"Overlapping records: {engine.stats['total_duplicates']}\n"
                    f"Unique records: {engine.stats['unique_count']}"
                )
            else:
                self._log("\nExport cancelled by user")

        except Exception as e:
            self._log(f"\n❌ ERROR: {str(e)}")
            messagebox.showerror("Comparison Failed", f"An error occurred:\n{str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            self.run_button.config(state=tk.NORMAL, text="▶ Run Comparison")

    def _log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.update()
