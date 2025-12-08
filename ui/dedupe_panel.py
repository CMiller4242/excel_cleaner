"""
Deduplication Mode UI Panel
Provides interface for two-file deduplication processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from dedupe.dedupe_engine import DeduplicationEngine, export_results
from datetime import datetime
import os

class DedupePanel(tk.Frame):
    """
    UI panel for two-file deduplication mode
    """

    def __init__(self, parent):
        super().__init__(parent, bg="white")

        self.file1_path = None
        self.file2_path = None
        self.file1_df = None
        self.file2_df = None
        self.file1_sheets = []
        self.file2_sheets = []
        self.file1_sheet_var = tk.StringVar()
        self.file2_sheet_var = tk.StringVar()
        self.file1_display_name = tk.StringVar()
        self.file2_display_name = tk.StringVar()
        self.column_mapping = {}
        self.results = None

        self._create_widgets()

    def _create_widgets(self):
        """Create UI components"""

        # Header
        header = tk.Frame(self, bg="#0078D4", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Two-File Deduplication Mode",
            font=("Segoe UI", 16, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=10)

        tk.Label(
            header,
            text="Compare two files and remove duplicates using tiered matching (Email → Phone+Name → Company+Location)",
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
            text="▶ Run Deduplication",
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

        # Secondary file
        secondary_frame = tk.Frame(file_section, bg="white")
        secondary_frame.pack(fill=tk.X, padx=15, pady=(10, 15))

        tk.Label(
            secondary_frame,
            text="Secondary File (Check for duplicates):",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor=tk.W, pady=(0, 5))

        file2_input_frame = tk.Frame(secondary_frame, bg="white")
        file2_input_frame.pack(fill=tk.X)

        self.file2_entry = tk.Entry(
            file2_input_frame,
            font=("Segoe UI", 10),
            state="readonly"
        )
        self.file2_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        tk.Button(
            file2_input_frame,
            text="Browse...",
            command=lambda: self._load_file(2),
            font=("Segoe UI", 9),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT)

        self.file2_status = tk.Label(
            secondary_frame,
            text="",
            font=("Segoe UI", 8),
            bg="white",
            fg="#666"
        )
        self.file2_status.pack(anchor=tk.W, pady=(3, 0))

        # Sheet selection for File 2
        self.file2_sheet_frame = tk.Frame(secondary_frame, bg="white")
        # Initially hidden, shown after file load

        tk.Label(
            self.file2_sheet_frame,
            text="Select Sheet:",
            font=("Segoe UI", 9),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.file2_sheet_combo = ttk.Combobox(
            self.file2_sheet_frame,
            textvariable=self.file2_sheet_var,
            state="readonly",
            width=25,
            font=("Segoe UI", 9)
        )
        self.file2_sheet_combo.pack(side=tk.LEFT)
        self.file2_sheet_combo.bind('<<ComboboxSelected>>', lambda e: self._on_sheet_selected())

        # Display name for File 2
        self.file2_name_frame = tk.Frame(secondary_frame, bg="white")
        # Initially hidden, shown after file load

        tk.Label(
            self.file2_name_frame,
            text="Display Name (optional):",
            font=("Segoe UI", 9),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.file2_name_entry = tk.Entry(
            self.file2_name_frame,
            textvariable=self.file2_display_name,
            font=("Segoe UI", 9),
            width=40
        )
        self.file2_name_entry.pack(side=tk.LEFT)

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
                    # Single sheet - auto-select and disable dropdown
                    self.file1_sheet_var.set(sheet_names[0])
                    self.file1_sheet_combo['values'] = sheet_names
                    self.file1_sheet_combo.config(state="disabled")
                    # Load the sheet immediately
                    self.file1_df = pd.read_excel(file_path, sheet_name=sheet_names[0])
                    self.file1_status.config(
                        text=f"✓ Loaded: {len(self.file1_df)} rows × {len(self.file1_df.columns)} columns",
                        fg="#107C10"
                    )
                    self._log(f"Master file loaded: {filename} (sheet: {sheet_names[0]}, {len(self.file1_df)} rows)")
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

                # Show sheet and display name UI
                self.file1_sheet_frame.pack(fill=tk.X, pady=(5, 0))
                self.file1_name_frame.pack(fill=tk.X, pady=(5, 0))

            else:
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
                    # Single sheet - auto-select and disable dropdown
                    self.file2_sheet_var.set(sheet_names[0])
                    self.file2_sheet_combo['values'] = sheet_names
                    self.file2_sheet_combo.config(state="disabled")
                    # Load the sheet immediately
                    self.file2_df = pd.read_excel(file_path, sheet_name=sheet_names[0])
                    self.file2_status.config(
                        text=f"✓ Loaded: {len(self.file2_df)} rows × {len(self.file2_df.columns)} columns",
                        fg="#107C10"
                    )
                    self._log(f"Secondary file loaded: {filename} (sheet: {sheet_names[0]}, {len(self.file2_df)} rows)")
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

                # Show sheet and display name UI
                self.file2_sheet_frame.pack(fill=tk.X, pady=(5, 0))
                self.file2_name_frame.pack(fill=tk.X, pady=(5, 0))

            # Check if we can enable column mapping
            self._check_ready_for_mapping()

        except Exception as e:
            messagebox.showerror("Error Loading File", f"Failed to load file:\n{str(e)}")

    def _on_sheet_selected(self):
        """Handle sheet selection from dropdown"""
        # Load File 1 sheet if selected
        if self.file1_path and self.file1_sheet_var.get() and not self.file1_df:
            try:
                sheet_name = self.file1_sheet_var.get()
                self.file1_df = pd.read_excel(self.file1_path, sheet_name=sheet_name)
                self.file1_status.config(
                    text=f"✓ Loaded: {len(self.file1_df)} rows × {len(self.file1_df.columns)} columns",
                    fg="#107C10"
                )
                self._log(f"Master file sheet loaded: {sheet_name} ({len(self.file1_df)} rows)")
            except Exception as e:
                messagebox.showerror("Error Loading Sheet", f"Failed to load sheet:\n{str(e)}")
                return

        # Load File 2 sheet if selected
        if self.file2_path and self.file2_sheet_var.get() and not self.file2_df:
            try:
                sheet_name = self.file2_sheet_var.get()
                self.file2_df = pd.read_excel(self.file2_path, sheet_name=sheet_name)
                self.file2_status.config(
                    text=f"✓ Loaded: {len(self.file2_df)} rows × {len(self.file2_df.columns)} columns",
                    fg="#107C10"
                )
                self._log(f"Secondary file sheet loaded: {sheet_name} ({len(self.file2_df)} rows)")
            except Exception as e:
                messagebox.showerror("Error Loading Sheet", f"Failed to load sheet:\n{str(e)}")
                return

        # Check if we can enable column mapping
        self._check_ready_for_mapping()

    def _check_ready_for_mapping(self):
        """Check if both files are loaded with sheets selected, then enable column mapping"""
        if self.file1_df is not None and self.file2_df is not None:
            self._create_column_mapping_ui()
            self.run_button.config(state=tk.NORMAL)

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
        tk.Label(mapping_grid, text="Field", font=("Segoe UI", 9, "bold"), bg="white", width=15, anchor=tk.W).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        tk.Label(mapping_grid, text="Master File Column", font=("Segoe UI", 9, "bold"), bg="white", width=25).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(mapping_grid, text="Secondary File Column", font=("Segoe UI", 9, "bold"), bg="white", width=25).grid(row=0, column=2, padx=5, pady=5)

        # Column dropdowns
        self.column_combos = {}

        fields = [
            ('Email', 'email'),
            ('Phone', 'phone'),
            ('Contact Name', 'name'),
            ('Company', 'company'),
            ('City', 'city'),
            ('State', 'state')
        ]

        file1_cols = ['(None)'] + list(self.file1_df.columns)
        file2_cols = ['(None)'] + list(self.file2_df.columns)

        for idx, (label, key) in enumerate(fields, start=1):
            tk.Label(
                mapping_grid,
                text=f"{label}:",
                font=("Segoe UI", 9),
                bg="white",
                anchor=tk.W
            ).grid(row=idx, column=0, padx=5, pady=3, sticky=tk.W)

            # File 1 dropdown
            file1_var = tk.StringVar(value='(None)')
            file1_combo = ttk.Combobox(
                mapping_grid,
                textvariable=file1_var,
                values=file1_cols,
                state="readonly",
                width=23
            )
            file1_combo.grid(row=idx, column=1, padx=5, pady=3)
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
            file2_combo.grid(row=idx, column=2, padx=5, pady=3)
            self.column_combos[f'file2_{key}'] = file2_var

            # Try to auto-detect
            for col in self.file2_df.columns:
                if key.lower() in col.lower():
                    file2_var.set(col)
                    break

        # Note
        tk.Label(
            self.mapping_section,
            text="Note: Email is required. Other fields improve matching accuracy.",
            font=("Segoe UI", 8),
            bg="white",
            fg="#666"
        ).pack(anchor=tk.W, padx=15, pady=(0, 10))

    def _run_deduplication(self):
        """Run the deduplication process"""
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
        self._log("Initializing deduplication engine...")

        # Disable button during processing
        self.run_button.config(state=tk.DISABLED, text="Processing...")
        self.update()

        try:
            # Get display names (use filename if empty)
            file1_display = self.file1_display_name.get().strip() or os.path.splitext(os.path.basename(self.file1_path))[0]
            file2_display = self.file2_display_name.get().strip() or os.path.splitext(os.path.basename(self.file2_path))[0]

            # Run deduplication
            engine = DeduplicationEngine(progress_callback=self._log)
            self.results = engine.run(
                self.file1_path,
                self.file2_path,
                mapping,
                sheet1=self.file1_sheet_var.get(),
                sheet2=self.file2_sheet_var.get(),
                display_name1=file1_display,
                display_name2=file2_display
            )

            # Export results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"Deduplicated_Results_{timestamp}.xlsx"

            output_path = filedialog.asksaveasfilename(
                title="Save Deduplication Results",
                defaultextension=".xlsx",
                initialfile=output_filename,
                filetypes=[("Excel files", "*.xlsx")]
            )

            if output_path:
                self._log(f"\nExporting results to: {output_path}")
                export_results(self.results, output_path)
                self._log("✓ Export complete!")

                messagebox.showinfo(
                    "Deduplication Complete",
                    f"Results saved to:\n{output_path}\n\n"
                    f"Duplicates removed: {engine.stats['total_duplicates']}\n"
                    f"Unique records: {engine.stats['unique_count']}"
                )
            else:
                self._log("\nExport cancelled by user")

        except Exception as e:
            self._log(f"\n❌ ERROR: {str(e)}")
            messagebox.showerror("Deduplication Failed", f"An error occurred:\n{str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            self.run_button.config(state=tk.NORMAL, text="▶ Run Deduplication")

    def _log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.update()
