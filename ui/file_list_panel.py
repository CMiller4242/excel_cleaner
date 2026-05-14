"""
File List Panel Component
Left pane showing list of loaded files with selection
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json
import os
from datetime import datetime


class FileListPanel(tk.Frame):
    """
    Left pane showing list of loaded files with selection
    """

    def __init__(self, parent, app_ref=None, **kwargs):
        super().__init__(parent, bg="#F3F3F3", width=280, **kwargs)
        self.pack_propagate(False)

        self.app = app_ref
        self.files = []
        self.selected_file = None

        self._create_widgets()

    def _create_widgets(self):
        # Header
        header = tk.Frame(self, bg="#0078D4", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="📁 FILES",
            font=('Segoe UI', 11, 'bold'),
            bg="#0078D4",
            fg="white"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.file_count_label = tk.Label(
            header,
            text="(0)",
            font=('Segoe UI', 11),
            bg="#0078D4",
            fg="white"
        )
        self.file_count_label.pack(side=tk.LEFT)

        # File list container (scrollable)
        list_container = tk.Frame(self, bg="#F3F3F3")
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas for scrolling
        self.canvas = tk.Canvas(
            list_container,
            bg="#F3F3F3",
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)

        # Frame inside canvas
        self.files_frame = tk.Frame(self.canvas, bg="#F3F3F3")
        self.canvas_window = self.canvas.create_window(
            0, 0,
            window=self.files_frame,
            anchor="nw"
        )

        # Bind resize
        self.files_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Add Files button
        add_btn = tk.Button(
            self,
            text="+ Add Files",
            command=self._on_add_files,
            bg="#0078D4",
            fg="white",
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#005A9E",
            activeforeground="white"
        )
        add_btn.pack(fill=tk.X, padx=10, pady=5)

        # Select All/None buttons
        select_frame = tk.Frame(self, bg="#F3F3F3")
        select_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            select_frame,
            text="Select All",
            command=self.select_all,
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            cursor="hand2",
            bg="#E1E1E1",
            activebackground="#CCC"
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            select_frame,
            text="Select None",
            command=self.select_none,
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            cursor="hand2",
            bg="#E1E1E1",
            activebackground="#CCC"
        ).pack(side=tk.LEFT)

        # Actions section
        self._create_actions_section()

    def _create_actions_section(self):
        actions_frame = tk.LabelFrame(
            self,
            text="📋 ACTIONS",
            font=('Segoe UI', 10, 'bold'),
            bg="#F3F3F3",
            fg="#333"
        )
        actions_frame.pack(fill=tk.X, padx=10, pady=10)

        # Apply Preset
        tk.Label(
            actions_frame,
            text="Apply Preset to Selected:",
            font=('Segoe UI', 9),
            bg="#F3F3F3"
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))

        self.preset_combo = ttk.Combobox(
            actions_frame,
            state="readonly",
            font=('Segoe UI', 9)
        )
        self.preset_combo.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.preset_combo.bind('<<ComboboxSelected>>', self._on_apply_preset_to_selected)

        # Copy Workflow
        tk.Label(
            actions_frame,
            text="Copy Workflow:",
            font=('Segoe UI', 9),
            bg="#F3F3F3"
        ).pack(anchor=tk.W, padx=10, pady=(5, 5))

        copy_frame = tk.Frame(actions_frame, bg="#F3F3F3")
        copy_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(copy_frame, text="From:", bg="#F3F3F3", font=('Segoe UI', 8)).pack(anchor=tk.W)
        self.copy_from_combo = ttk.Combobox(
            copy_frame,
            state="readonly",
            font=('Segoe UI', 9)
        )
        self.copy_from_combo.pack(fill=tk.X, pady=(0, 5))

        tk.Button(
            copy_frame,
            text="Copy to Selected",
            command=self._on_copy_workflow,
            font=('Segoe UI', 9),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#005A9E",
            activeforeground="white"
        ).pack(fill=tk.X)

        # Change Header Selected button
        tk.Button(
            self,
            text="📋 Change Header Selected",
            command=self._on_change_header_selected,
            font=('Segoe UI', 10, 'bold'),
            bg="#5C4033",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            height=2,
            activebackground="#4A2E25",
            activeforeground="white"
        ).pack(fill=tk.X, padx=10, pady=(5, 5))

        # Smart Format Selected button
        tk.Button(
            self,
            text="✨ Smart Format Selected",
            command=self._on_smart_format_selected,
            font=('Segoe UI', 10, 'bold'),
            bg="#6B2FAE",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            height=2,
            activebackground="#5A1F9A",
            activeforeground="white"
        ).pack(fill=tk.X, padx=10, pady=(5, 5))

        # Rename Files button
        tk.Button(
            self,
            text="🏷️ Rename Files",
            command=self._show_rename_dialog,
            font=('Segoe UI', 10, 'bold'),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            height=2,
            activebackground="#005A9E",
            activeforeground="white"
        ).pack(fill=tk.X, padx=10, pady=(10, 5))

        # Process All button
        tk.Button(
            self,
            text="🔄 Process All Files",
            command=self._on_process_all,
            font=('Segoe UI', 10, 'bold'),
            bg="#107C10",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            height=2,
            activebackground="#0B5A0C",
            activeforeground="white"
        ).pack(fill=tk.X, padx=10, pady=(5, 10))

        # Export dropdown
        export_btn = tk.Menubutton(
            self,
            text="💾 Export All ▼",
            font=('Segoe UI', 10, 'bold'),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#005A9E",
            activeforeground="white"
        )
        export_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

        export_menu = tk.Menu(export_btn, tearoff=0)
        export_btn.config(menu=export_menu)

        export_menu.add_command(label="📦 Export as ZIP", command=lambda: self._on_export("zip"))
        export_menu.add_command(label="📄 Export Individual Files", command=lambda: self._on_export("individual"))
        export_menu.add_command(label="📋 Export as Combined File", command=lambda: self._on_export("combined"))

    def add_file(self, file_obj):
        """Add a file to the list"""
        self.files.append(file_obj)
        self._create_file_item(file_obj)
        self._update_file_count()
        self._update_combos()

        # Auto-select first file
        if len(self.files) == 1:
            self.select_file(file_obj)

    def _create_file_item(self, file_obj):
        """Create UI element for a file"""
        item_frame = tk.Frame(
            self.files_frame,
            bg="white",
            relief=tk.RIDGE,
            borderwidth=1
        )
        item_frame.pack(fill=tk.X, pady=2)

        # Main content area
        content_frame = tk.Frame(item_frame, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left side: checkbox and file info
        left_frame = tk.Frame(content_frame, bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Checkbox
        var = tk.BooleanVar(value=False)
        file_obj['selected_var'] = var

        cb = tk.Checkbutton(
            left_frame,
            variable=var,
            bg="white",
            command=lambda: self._on_checkbox_change(file_obj)
        )
        cb.pack(side=tk.LEFT, padx=(0, 5))

        # File info
        info_frame = tk.Frame(left_frame, bg="white")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Filename (clickable)
        name_label = tk.Label(
            info_frame,
            text=file_obj['name'],
            font=('Segoe UI', 10, 'bold'),
            bg="white",
            fg="#0078D4",
            cursor="hand2",
            anchor=tk.W
        )
        name_label.pack(fill=tk.X)
        name_label.bind("<Button-1>", lambda e: self.select_file(file_obj))

        # Row count
        rows = len(file_obj['df'])
        cols = len(file_obj['df'].columns)
        info_label = tk.Label(
            info_frame,
            text=f"{rows:,} rows × {cols} columns",
            font=('Segoe UI', 8),
            bg="white",
            fg="#666",
            anchor=tk.W
        )
        info_label.pack(fill=tk.X)

        # Right side: action buttons
        btn_frame = tk.Frame(content_frame, bg="white")
        btn_frame.pack(side=tk.RIGHT)

        # Preview button
        preview_btn = tk.Button(
            btn_frame,
            text="👁",
            command=lambda: self._on_preview(file_obj),
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            cursor="hand2",
            width=2,
            bg="white"
        )
        preview_btn.pack(side=tk.LEFT, padx=2)

        # Remove button
        remove_btn = tk.Button(
            btn_frame,
            text="🗑",
            command=lambda: self._on_remove(file_obj),
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            cursor="hand2",
            width=2,
            fg="red",
            bg="white"
        )
        remove_btn.pack(side=tk.LEFT, padx=2)

        # Store reference
        file_obj['ui_frame'] = item_frame
        file_obj['name_label'] = name_label

    def select_file(self, file_obj):
        """Select a file and show in right pane"""
        # Deselect previous
        if self.selected_file:
            self._deselect_visual(self.selected_file)

        # Select new
        self.selected_file = file_obj
        self._select_visual(file_obj)

        # Notify app
        if self.app and hasattr(self.app, '_on_file_selected'):
            self.app._on_file_selected(file_obj)

    def _select_visual(self, file_obj):
        """Apply selection visual styling"""
        frame = file_obj['ui_frame']
        frame.config(bg="#E6F2FF")
        for widget in self._get_all_children(frame):
            if isinstance(widget, (tk.Frame, tk.Label, tk.Checkbutton)):
                try:
                    widget.config(bg="#E6F2FF")
                except:
                    pass

    def _deselect_visual(self, file_obj):
        """Remove selection visual styling"""
        frame = file_obj['ui_frame']
        frame.config(bg="white")
        for widget in self._get_all_children(frame):
            if isinstance(widget, (tk.Frame, tk.Label, tk.Checkbutton)):
                try:
                    widget.config(bg="white")
                except:
                    pass

    def _get_all_children(self, widget):
        """Recursively get all child widgets"""
        children = widget.winfo_children()
        all_children = list(children)
        for child in children:
            all_children.extend(self._get_all_children(child))
        return all_children

    def get_selected_files(self):
        """Get list of checked files"""
        return [f for f in self.files if f['selected_var'].get()]

    def select_all(self):
        """Check all files"""
        for file_obj in self.files:
            file_obj['selected_var'].set(True)

    def select_none(self):
        """Uncheck all files"""
        for file_obj in self.files:
            file_obj['selected_var'].set(False)

    def remove_file(self, file_obj):
        """Remove a file from the list"""
        if file_obj in self.files:
            self.files.remove(file_obj)
            file_obj['ui_frame'].destroy()
            self._update_file_count()
            self._update_combos()

            # Select another file if this was selected
            if self.selected_file == file_obj:
                self.selected_file = None
                if self.files:
                    self.select_file(self.files[0])

    def _update_file_count(self):
        self.file_count_label.config(text=f"({len(self.files)})")

    def _update_combos(self):
        """Update combo boxes with file names"""
        file_names = [f['name'] for f in self.files]
        self.copy_from_combo['values'] = file_names

    def _find_preset_file(self, preset_name):
        """Find preset file by name"""
        preset_dirs = [
            'presets/system',
            'presets/user',
            os.path.join(os.path.expanduser('~'), '.config', 'CleanSheet', 'presets')
        ]

        for preset_dir in preset_dirs:
            if not os.path.exists(preset_dir):
                continue

            for file in os.listdir(preset_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(preset_dir, file)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if data.get('name') == preset_name:
                                return file_path
                    except Exception:
                        continue

        return None

    def populate_preset_dropdown(self):
        """Load available presets into dropdown"""
        presets = []

        preset_dirs = [
            'presets/system',
            'presets/user',
            os.path.join(os.path.expanduser('~'), '.config', 'CleanSheet', 'presets')
        ]

        for preset_dir in preset_dirs:
            if not os.path.exists(preset_dir):
                continue

            for file in os.listdir(preset_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(preset_dir, file)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            preset_name = data.get('name', file.replace('.json', ''))
                            if preset_name not in presets:
                                presets.append(preset_name)
                    except Exception:
                        continue

        self.preset_combo['values'] = sorted(presets)

    def apply_preset_to_selected(self, preset_name=None):
        """Apply selected preset to all checked files"""
        if not preset_name:
            preset_name = self.preset_combo.get()

        if not preset_name:
            messagebox.showwarning("No Preset", "Please select a preset first")
            return

        selected_files = self.get_selected_files()

        if not selected_files:
            messagebox.showwarning("No Files", "Please select files to apply preset to")
            return

        # Load preset operations
        preset_path = self._find_preset_file(preset_name)
        if not preset_path:
            messagebox.showerror("Error", f"Preset '{preset_name}' not found")
            return

        try:
            print(f"[DEBUG] Loading preset: {preset_name}")
            print(f"[DEBUG] Preset file: {preset_path}")

            with open(preset_path, 'r') as f:
                preset_data = json.load(f)

            operations = preset_data.get('operations', [])

            print(f"[DEBUG] Raw operations loaded: {len(operations)} operations")

            if not operations:
                messagebox.showwarning("Empty Preset", "This preset has no operations")
                return

            # CRITICAL FIX: Normalize operations to new format
            # This converts old preset format (operation_id) to new format (class, name, type)
            from operations.registry import get_registry
            registry = get_registry()

            print(f"[DEBUG] Normalizing {len(operations)} operations...")
            normalized_operations = []
            for idx, op in enumerate(operations):
                print(f"[DEBUG] Normalizing operation {idx+1}: {op.get('operation_id', op.get('class', 'Unknown'))}")
                normalized_op = registry.normalize_operation(op)
                normalized_operations.append(normalized_op)
                print(f"[DEBUG] Result: {normalized_op.get('name')} ({normalized_op.get('class')})")

            operations = normalized_operations
            print(f"[DEBUG] Normalization complete. {len(operations)} operations ready")

            # Apply to each selected file
            for file_obj in selected_files:
                # CRITICAL: Store normalized operations in file object
                file_obj['operations'] = [op.copy() for op in operations]
                file_obj['preset_name'] = preset_name
                print(f"[DEBUG] Applied preset to '{file_obj['name']}' - now has {len(file_obj['operations'])} operations")

            # CRITICAL FIX: Refresh the UI to show operations
            # If there's a currently selected file, refresh its detail view
            if self.selected_file and self.selected_file in selected_files:
                print(f"[DEBUG] Refreshing UI for selected file: {self.selected_file['name']}")
                if self.app and hasattr(self.app, '_on_file_selected'):
                    self.app._on_file_selected(self.selected_file)
                elif self.app and hasattr(self.app, 'file_detail_panel'):
                    # Alternative: directly call file detail panel
                    self.app.file_detail_panel.show_file(self.selected_file)
                print(f"[DEBUG] UI refresh completed")
            else:
                print(f"[DEBUG] No file currently selected or selected file not in preset application")

            messagebox.showinfo(
                "Success",
                f"Loaded preset '{preset_name}' with {len(operations)} operation(s)\nApplied to {len(selected_files)} file(s)"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply preset:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    # Event handlers
    def _on_add_files(self):
        if self.app and hasattr(self.app, 'load_multiple_files'):
            self.app.load_multiple_files()

    def _on_preview(self, file_obj):
        self.select_file(file_obj)

    def _on_remove(self, file_obj):
        self.remove_file(file_obj)

    def _on_checkbox_change(self, file_obj):
        pass  # Could add visual feedback for selection

    def _on_apply_preset_to_selected(self, event=None):
        # Call the new direct method instead of delegating to app
        self.apply_preset_to_selected()

    def _on_copy_workflow(self):
        if self.app and hasattr(self.app, 'copy_workflow_to_selected'):
            source_name = self.copy_from_combo.get()
            if source_name:
                self.app.copy_workflow_to_selected(source_name)

    def _on_process_all(self):
        if self.app and hasattr(self.app, 'process_batch_files'):
            self.app.process_batch_files()

    def _on_smart_format_selected(self):
        """Launch Smart Format for all checked files."""
        if self.app and hasattr(self.app, 'launch_smart_format_for_selected_batch_files'):
            self.app.launch_smart_format_for_selected_batch_files()

    def _on_change_header_selected(self):
        """Add Set Header Row operation to all checked files."""
        if self.app and hasattr(self.app, 'change_header_for_selected_batch_files'):
            self.app.change_header_for_selected_batch_files()

    def _on_export(self, export_type=None):
        """Show export dialog and export processed files"""

        selected_files = self.get_selected_files()

        if not selected_files:
            messagebox.showwarning(
                "No Files Selected",
                "Please select files to export"
            )
            return

        # Check if files have been processed
        unprocessed = [f['name'] for f in selected_files if 'result_df' not in f]

        if unprocessed:
            if not messagebox.askyesno(
                "Unprocessed Files",
                f"{len(unprocessed)} file(s) haven't been processed yet:\n" +
                "\n".join(unprocessed[:3]) +
                ("\n..." if len(unprocessed) > 3 else "") +
                "\n\nExport original data for these files?"
            ):
                return

        # Show export options dialog
        self._show_export_dialog(selected_files, export_type)

    def _show_export_dialog(self, selected_files, default_type=None):
        """Show comprehensive export options dialog"""

        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Export Files")
        dialog.geometry("600x550")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Header
        header = tk.Frame(dialog, bg="#0078D4", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Export Files",
            font=("Segoe UI", 14, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=10)

        tk.Label(
            header,
            text=f"Exporting {len(selected_files)} file(s)",
            font=("Segoe UI", 10),
            bg="#0078D4",
            fg="white"
        ).pack()

        # Content
        content = tk.Frame(dialog, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # File format selection
        tk.Label(
            content,
            text="1. Select file format:",
            font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(anchor=tk.W, pady=(0, 10))

        format_var = tk.StringVar(value="txt")

        format_frame = tk.Frame(content, bg="white")
        format_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Radiobutton(
            format_frame,
            text="TXT (Comma-delimited) - For external programs",
            variable=format_var,
            value="txt",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, pady=3)

        tk.Radiobutton(
            format_frame,
            text="XLSX (Excel) - Preserves formatting",
            variable=format_var,
            value="xlsx",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, pady=3)

        tk.Radiobutton(
            format_frame,
            text="CSV (Comma-separated) - Universal format",
            variable=format_var,
            value="csv",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, pady=3)

        # Export method selection
        tk.Label(
            content,
            text="2. Select export method:",
            font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(anchor=tk.W, pady=(10, 10))

        method_var = tk.StringVar(value=default_type if default_type else "individual")

        method_frame = tk.Frame(content, bg="white")
        method_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Radiobutton(
            method_frame,
            text="Individual files - Save each file separately",
            variable=method_var,
            value="individual",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, pady=3)

        tk.Radiobutton(
            method_frame,
            text="ZIP archive - All files in one .zip",
            variable=method_var,
            value="zip",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, pady=3)

        tk.Radiobutton(
            method_frame,
            text="Combined file - Merge all into one file",
            variable=method_var,
            value="combined",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, pady=3)

        # File naming options
        tk.Label(
            content,
            text="3. File naming:",
            font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(anchor=tk.W, pady=(10, 10))

        naming_var = tk.StringVar(value="original")

        naming_frame = tk.Frame(content, bg="white")
        naming_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Radiobutton(
            naming_frame,
            text="Keep original filenames",
            variable=naming_var,
            value="original",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, pady=3)

        tk.Radiobutton(
            naming_frame,
            text="Add timestamp (filename_2025-12-04)",
            variable=naming_var,
            value="timestamp",
            font=("Segoe UI", 10),
            bg="white"
        ).pack(anchor=tk.W, pady=3)

        # Summary
        summary_frame = tk.Frame(content, bg="#F0F0F0", relief=tk.RIDGE, borderwidth=1)
        summary_frame.pack(fill=tk.X, pady=(15, 0))

        summary_label = tk.Label(
            summary_frame,
            text=f"Ready to export {len(selected_files)} file(s) as TXT (individual files)",
            font=("Segoe UI", 9),
            bg="#F0F0F0",
            fg="#333",
            wraplength=500
        )
        summary_label.pack(padx=10, pady=10)

        def update_summary(*args):
            fmt = format_var.get().upper()
            method = method_var.get()
            method_text = {
                'individual': 'individual files',
                'zip': 'ZIP archive',
                'combined': 'single combined file'
            }[method]

            summary_label.config(
                text=f"Ready to export {len(selected_files)} file(s) as {fmt} ({method_text})"
            )

        format_var.trace('w', update_summary)
        method_var.trace('w', update_summary)

        # Buttons
        button_frame = tk.Frame(dialog, bg="white")
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        def on_export():
            """Execute the export"""
            file_format = format_var.get()
            export_method = method_var.get()
            naming_style = naming_var.get()

            dialog.destroy()

            # Execute export based on method
            if export_method == "individual":
                self._export_individual_files(selected_files, file_format, naming_style)
            elif export_method == "zip":
                self._export_as_zip(selected_files, file_format, naming_style)
            else:
                self._export_combined_file(selected_files, file_format, naming_style)

        tk.Button(
            button_frame,
            text="Export",
            command=on_export,
            font=("Segoe UI", 10, "bold"),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=30,
            pady=10
        ).pack(side=tk.RIGHT, padx=(10, 0))

        tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            cursor="hand2",
            padx=30,
            pady=10
        ).pack(side=tk.RIGHT)

    def _export_individual_files(self, files, file_format, naming_style):
        """Export each file separately to a chosen folder"""
        from tkinter import filedialog
        from datetime import datetime

        # Ask for output folder
        output_dir = filedialog.askdirectory(title="Select Output Folder")

        if not output_dir:
            return

        try:
            exported_count = 0

            for file_obj in files:
                # Get DataFrame (processed or original)
                df = file_obj.get('result_df', file_obj['df'])

                # Generate filename
                base_name = os.path.splitext(file_obj['name'])[0]

                if naming_style == 'timestamp':
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    filename = f"{base_name}_{timestamp}.{file_format}"
                else:
                    filename = f"{base_name}.{file_format}"

                output_path = os.path.join(output_dir, filename)

                # Export based on format
                if file_format == 'txt':
                    # TXT files should be comma-delimited (CSV format with .txt extension)
                    df.to_csv(output_path, sep=',', index=False, quoting=1)  # QUOTE_ALL
                elif file_format == 'xlsx':
                    df.to_excel(output_path, index=False)
                else:  # csv
                    df.to_csv(output_path, index=False)

                exported_count += 1

            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {exported_count} file(s) to:\n{output_dir}"
            )

        except Exception as e:
            messagebox.showerror("Export Failed", f"Error during export:\n{str(e)}")

    def _export_as_zip(self, files, file_format, naming_style):
        """Export all files as a ZIP archive"""
        from tkinter import filedialog
        from datetime import datetime
        import zipfile
        import io

        # Ask for ZIP save location
        default_name = f"CleanSheet_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        zip_path = filedialog.asksaveasfilename(
            title="Save ZIP Archive",
            defaultextension=".zip",
            initialfile=default_name,
            filetypes=[("ZIP files", "*.zip")]
        )

        if not zip_path:
            return

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_obj in files:
                    # Get DataFrame
                    df = file_obj.get('result_df', file_obj['df'])

                    # Generate filename
                    base_name = os.path.splitext(file_obj['name'])[0]

                    if naming_style == 'timestamp':
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                        filename = f"{base_name}_{timestamp}.{file_format}"
                    else:
                        filename = f"{base_name}.{file_format}"

                    # Export to bytes
                    buffer = io.BytesIO()

                    if file_format == 'txt':
                        # TXT files should be comma-delimited (CSV format with .txt extension)
                        content = df.to_csv(sep=',', index=False, quoting=1)  # QUOTE_ALL
                        buffer.write(content.encode('utf-8'))
                    elif file_format == 'xlsx':
                        df.to_excel(buffer, index=False, engine='openpyxl')
                    else:  # csv
                        content = df.to_csv(index=False)
                        buffer.write(content.encode('utf-8'))

                    # Add to ZIP
                    zipf.writestr(filename, buffer.getvalue())

            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {len(files)} file(s) to ZIP:\n{zip_path}"
            )

        except Exception as e:
            messagebox.showerror("Export Failed", f"Error creating ZIP:\n{str(e)}")

    def _export_combined_file(self, files, file_format, naming_style):
        """Combine all files into one and export"""
        from tkinter import filedialog
        from datetime import datetime
        import pandas as pd

        # Ask for save location
        default_name = f"Combined_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}"

        filetypes = {
            'txt': [("Text files", "*.txt")],
            'xlsx': [("Excel files", "*.xlsx")],
            'csv': [("CSV files", "*.csv")]
        }

        save_path = filedialog.asksaveasfilename(
            title="Save Combined File",
            defaultextension=f".{file_format}",
            initialfile=default_name,
            filetypes=filetypes[file_format]
        )

        if not save_path:
            return

        try:
            # Combine all dataframes
            dfs = []
            for file_obj in files:
                df = file_obj.get('result_df', file_obj['df']).copy()
                # Add source filename column
                df.insert(0, 'Source_File', file_obj['name'])
                dfs.append(df)

            combined_df = pd.concat(dfs, ignore_index=True)

            # Export
            if file_format == 'txt':
                # TXT files should be comma-delimited (CSV format with .txt extension)
                combined_df.to_csv(save_path, sep=',', index=False, quoting=1)  # QUOTE_ALL
            elif file_format == 'xlsx':
                combined_df.to_excel(save_path, index=False)
            else:  # csv
                combined_df.to_csv(save_path, index=False)

            messagebox.showinfo(
                "Export Complete",
                f"Successfully combined and exported {len(files)} file(s) to:\n{save_path}\n\n"
                f"Total rows: {len(combined_df):,}"
            )

        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting combined file:\n{str(e)}")

    def _show_rename_dialog(self):
        """Show advanced batch rename dialog with batch cards"""

        if not self.files:
            messagebox.showwarning("No Files", "Please load files first")
            return

        # Create dialog
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Batch Rename Files")
        dialog.geometry("1000x800")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Store batch data
        batches = []  # List of batch dictionaries
        batch_counter = [1]  # Counter for batch numbering
        current_edit_batch = [None]  # Track if editing existing batch

        # Store original names for reverting
        original_names = {f['name']: f['name'] for f in self.files}

        # Add selection state to files
        for f in self.files:
            if 'rename_selected' not in f:
                f['rename_selected'] = tk.BooleanVar(value=False)
            else:
                f['rename_selected'].set(False)

        # Header
        header = tk.Frame(dialog, bg="#0078D4", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Batch Rename Files",
            font=("Segoe UI", 14, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=10)

        stats_label = tk.Label(
            header,
            text=f"{len(self.files)} files loaded | 0 batches created | 0 files renamed",
            font=("Segoe UI", 10),
            bg="#0078D4",
            fg="white"
        )
        stats_label.pack()

        def update_stats():
            """Update statistics in header"""
            total_renamed = sum(len(b['files']) for b in batches)
            stats_label.config(
                text=f"{len(self.files)} files loaded | {len(batches)} batches created | {total_renamed} files renamed"
            )

        # Main content area with scrolling
        content_container = tk.Frame(dialog, bg="white")
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

        # Store reference to file selection widgets and pattern variables
        file_checkboxes = {}  # file_obj -> checkbox widget
        batch_cards_container = [None]  # Will hold batch cards frame
        unrenamed_section_container = [None]  # Will hold unrenamed files section
        selected_count_label = [None]  # Label showing selected file count

        # Pattern configuration variables
        pattern_var = tk.StringVar(value="custom")
        custom_name_var = tk.StringVar(value="File")
        start_num_var = tk.StringVar(value="1")
        digits_var = tk.StringVar(value="3")
        prefix_var = tk.StringVar(value="")
        suffix_var = tk.StringVar(value="")
        find_var = tk.StringVar(value="")
        replace_var = tk.StringVar(value="")

        # ========== HELPER FUNCTIONS ==========

        def generate_batch_name(pattern_type, selected_files):
            """Generate a descriptive batch name based on pattern"""
            if pattern_type == "custom":
                custom_name = custom_name_var.get() or "File"
                return f"Batch {batch_counter[0]}: {custom_name}_###"
            elif pattern_type == "prefix":
                prefix = prefix_var.get() or "[prefix]"
                return f"Batch {batch_counter[0]}: Add prefix '{prefix}'"
            elif pattern_type == "suffix":
                suffix = suffix_var.get() or "[suffix]"
                return f"Batch {batch_counter[0]}: Add suffix '{suffix}'"
            elif pattern_type == "replace":
                find_text = find_var.get() or "[find]"
                replace_text = replace_var.get() or "[replace]"
                return f"Batch {batch_counter[0]}: Replace '{find_text}' with '{replace_text}'"
            return f"Batch {batch_counter[0]}"

        def generate_new_name(batch, file_obj, index_in_batch):
            """Generate new filename based on batch pattern"""
            current_name = file_obj.get('pending_name', file_obj['name'])
            base_name = os.path.splitext(current_name)[0]
            extension = os.path.splitext(current_name)[1]

            pattern = batch['pattern']

            if pattern == "custom":
                custom_name = batch['custom_name']
                start_num = batch['start_num']
                digits = batch['digits']
                num = str(start_num + index_in_batch).zfill(digits)
                return f"{custom_name}_{num}{extension}"

            elif pattern == "prefix":
                prefix = batch['prefix']
                return f"{prefix}{current_name}"

            elif pattern == "suffix":
                suffix = batch['suffix']
                return f"{base_name}{suffix}{extension}"

            elif pattern == "replace":
                find_text = batch['find_text']
                replace_text = batch['replace_text']
                if find_text:
                    return current_name.replace(find_text, replace_text)
                return current_name

            return current_name

        def apply_or_update_batch():
            """Create new batch or update existing batch being edited"""
            selected_files = [f for f in self.files if f.get('rename_selected', tk.BooleanVar()).get()]

            if not selected_files:
                messagebox.showwarning("No Selection", "Please select files to add to batch")
                return

            pattern = pattern_var.get()

            # Create batch data structure
            batch_data = {
                'id': current_edit_batch[0]['id'] if current_edit_batch[0] else batch_counter[0],
                'pattern': pattern,
                'custom_name': custom_name_var.get() or "File",
                'start_num': int(start_num_var.get() or 1),
                'digits': int(digits_var.get() or 3),
                'prefix': prefix_var.get(),
                'suffix': suffix_var.get(),
                'find_text': find_var.get(),
                'replace_text': replace_var.get(),
                'files': [],
                'expanded': tk.BooleanVar(value=True),
                'name': tk.StringVar()
            }

            # If editing, remove old batch
            if current_edit_batch[0]:
                old_batch = current_edit_batch[0]
                # Remove files from old batch
                for f in old_batch['files']:
                    f['current_batch'] = None
                batches.remove(old_batch)
                current_edit_batch[0] = None

            # Process files and generate new names
            for idx, file_obj in enumerate(selected_files):
                # Remove from any previous batch
                if 'current_batch' in file_obj and file_obj['current_batch']:
                    prev_batch = file_obj['current_batch']
                    if file_obj in prev_batch['files']:
                        prev_batch['files'].remove(file_obj)

                # Generate new name
                new_name = generate_new_name(batch_data, file_obj, idx)

                # Add to batch
                batch_data['files'].append(file_obj)
                file_obj['current_batch'] = batch_data
                file_obj['pending_name'] = new_name

                # Deselect file after adding to batch
                file_obj['rename_selected'].set(False)

            # Set batch name
            batch_data['name'].set(generate_batch_name(pattern, selected_files))

            # Add batch to list
            batches.append(batch_data)
            batch_counter[0] += 1

            # Refresh UI
            update_file_selection_display()
            create_batch_cards()
            update_unrenamed_section()
            update_stats()

        def create_batch_cards():
            """Render all batch cards"""
            # Clear existing cards
            if batch_cards_container[0]:
                batch_cards_container[0].destroy()

            # Create container
            cards_frame = tk.LabelFrame(
                content,
                text=f"Rename Batches ({len(batches)})",
                font=("Segoe UI", 11, "bold"),
                bg="white",
                fg="#333"
            )
            cards_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
            batch_cards_container[0] = cards_frame

            if not batches:
                tk.Label(
                    cards_frame,
                    text="No batches created yet. Select files and configure pattern above.",
                    font=("Segoe UI", 9),
                    bg="white",
                    fg="#999",
                    pady=20
                ).pack()
                return

            # Create card for each batch
            for batch in batches:
                create_batch_card(cards_frame, batch)

        def create_batch_card(parent, batch):
            """Render a single batch card"""
            card = tk.Frame(parent, bg="#F8F8F8", relief=tk.RIDGE, borderwidth=1)
            card.pack(fill=tk.X, padx=10, pady=5)

            # Header
            header = tk.Frame(card, bg="#E1E1E1")
            header.pack(fill=tk.X)

            # Expand/collapse button
            expand_btn = tk.Button(
                header,
                text="▼" if batch['expanded'].get() else "▶",
                command=lambda: toggle_batch_expand(batch),
                font=("Segoe UI", 10),
                bg="#E1E1E1",
                relief=tk.FLAT,
                cursor="hand2",
                width=3
            )
            expand_btn.pack(side=tk.LEFT, padx=5, pady=5)

            # Batch name (editable)
            name_entry = tk.Entry(
                header,
                textvariable=batch['name'],
                font=("Segoe UI", 10, "bold"),
                bg="#E1E1E1",
                relief=tk.FLAT,
                fg="#0078D4"
            )
            name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)

            # File count
            tk.Label(
                header,
                text=f"({len(batch['files'])} files)",
                font=("Segoe UI", 9),
                bg="#E1E1E1",
                fg="#666"
            ).pack(side=tk.LEFT, padx=10)

            # Action buttons
            btn_frame = tk.Frame(header, bg="#E1E1E1")
            btn_frame.pack(side=tk.RIGHT, padx=5)

            # Move up button
            if batches.index(batch) > 0:
                tk.Button(
                    btn_frame,
                    text="↑",
                    command=lambda: move_batch_up(batch),
                    font=("Segoe UI", 9),
                    bg="#E1E1E1",
                    relief=tk.FLAT,
                    cursor="hand2",
                    width=2
                ).pack(side=tk.LEFT, padx=2)

            # Move down button
            if batches.index(batch) < len(batches) - 1:
                tk.Button(
                    btn_frame,
                    text="↓",
                    command=lambda: move_batch_down(batch),
                    font=("Segoe UI", 9),
                    bg="#E1E1E1",
                    relief=tk.FLAT,
                    cursor="hand2",
                    width=2
                ).pack(side=tk.LEFT, padx=2)

            # Edit button
            tk.Button(
                btn_frame,
                text="Edit",
                command=lambda: edit_batch(batch),
                font=("Segoe UI", 9),
                bg="#0078D4",
                fg="white",
                relief=tk.FLAT,
                cursor="hand2",
                padx=8
            ).pack(side=tk.LEFT, padx=2)

            # Delete button
            tk.Button(
                btn_frame,
                text="Delete",
                command=lambda: delete_batch(batch),
                font=("Segoe UI", 9),
                bg="#D13438",
                fg="white",
                relief=tk.FLAT,
                cursor="hand2",
                padx=8
            ).pack(side=tk.LEFT, padx=2)

            # Expanded content: show renamed files
            if batch['expanded'].get():
                files_frame = tk.Frame(card, bg="white")
                files_frame.pack(fill=tk.X, padx=10, pady=10)

                for idx, file_obj in enumerate(batch['files']):
                    file_row = tk.Frame(files_frame, bg="white")
                    file_row.pack(fill=tk.X, pady=2)

                    # Original name
                    tk.Label(
                        file_row,
                        text=f"{file_obj['name']} →",
                        font=("Segoe UI", 8),
                        bg="white",
                        fg="#666",
                        anchor=tk.W,
                        width=35
                    ).pack(side=tk.LEFT)

                    # New name
                    tk.Label(
                        file_row,
                        text=file_obj.get('pending_name', file_obj['name']),
                        font=("Segoe UI", 8, "bold"),
                        bg="white",
                        fg="#0078D4",
                        anchor=tk.W
                    ).pack(side=tk.LEFT, fill=tk.X, expand=True)

                    # Reset button
                    tk.Button(
                        file_row,
                        text="Reset",
                        command=lambda f=file_obj, b=batch: reset_file_from_batch(f, b),
                        font=("Segoe UI", 7),
                        bg="#E1E1E1",
                        relief=tk.FLAT,
                        cursor="hand2",
                        padx=5
                    ).pack(side=tk.RIGHT)

        def toggle_batch_expand(batch):
            """Expand or collapse batch card"""
            batch['expanded'].set(not batch['expanded'].get())
            create_batch_cards()

        def edit_batch(batch):
            """Load batch into editor for modification"""
            current_edit_batch[0] = batch

            # Load batch settings
            pattern_var.set(batch['pattern'])
            custom_name_var.set(batch['custom_name'])
            start_num_var.set(str(batch['start_num']))
            digits_var.set(str(batch['digits']))
            prefix_var.set(batch['prefix'])
            suffix_var.set(batch['suffix'])
            find_var.set(batch['find_text'])
            replace_var.set(batch['replace_text'])

            # Select batch files
            for f in self.files:
                f['rename_selected'].set(f in batch['files'])

            update_file_selection_display()
            messagebox.showinfo("Edit Mode", f"Loaded batch for editing: {batch['name'].get()}\n\nModify settings and click 'Apply/Update Batch' to save changes.")

        def delete_batch(batch):
            """Remove a batch and restore original names"""
            if not messagebox.askyesno("Delete Batch", f"Delete batch '{batch['name'].get()}'?\n\nFiles will return to unrenamed state."):
                return

            # Remove files from batch
            for file_obj in batch['files']:
                file_obj['current_batch'] = None
                if 'pending_name' in file_obj:
                    del file_obj['pending_name']

            batches.remove(batch)
            current_edit_batch[0] = None

            # Refresh UI
            update_file_selection_display()
            create_batch_cards()
            update_unrenamed_section()
            update_stats()

        def reset_file_from_batch(file_obj, batch):
            """Remove a single file from a batch"""
            if file_obj in batch['files']:
                batch['files'].remove(file_obj)
                file_obj['current_batch'] = None
                if 'pending_name' in file_obj:
                    del file_obj['pending_name']

                # If batch is now empty, remove it
                if not batch['files']:
                    batches.remove(batch)

                # Refresh UI
                update_file_selection_display()
                create_batch_cards()
                update_unrenamed_section()
                update_stats()

        def move_batch_up(batch):
            """Move batch up in order"""
            idx = batches.index(batch)
            if idx > 0:
                batches[idx], batches[idx-1] = batches[idx-1], batches[idx]
                create_batch_cards()

        def move_batch_down(batch):
            """Move batch down in order"""
            idx = batches.index(batch)
            if idx < len(batches) - 1:
                batches[idx], batches[idx+1] = batches[idx+1], batches[idx]
                create_batch_cards()

        def update_unrenamed_section():
            """Update display of files not in any batch"""
            # Clear existing section
            if unrenamed_section_container[0]:
                unrenamed_section_container[0].destroy()

            # Get unrenamed files
            unrenamed_files = [f for f in self.files if not f.get('current_batch')]

            if not unrenamed_files:
                return

            # Create section
            unrenamed_frame = tk.LabelFrame(
                content,
                text=f"Unrenamed Files ({len(unrenamed_files)})",
                font=("Segoe UI", 11, "bold"),
                bg="white",
                fg="#666"
            )
            unrenamed_frame.pack(fill=tk.X, padx=20, pady=(5, 10))
            unrenamed_section_container[0] = unrenamed_frame

            # Expandable list
            for file_obj in unrenamed_files[:10]:  # Show first 10
                tk.Label(
                    unrenamed_frame,
                    text=f"• {file_obj['name']}",
                    font=("Segoe UI", 8),
                    bg="white",
                    fg="#666",
                    anchor=tk.W
                ).pack(fill=tk.X, padx=10, pady=1)

            if len(unrenamed_files) > 10:
                tk.Label(
                    unrenamed_frame,
                    text=f"... and {len(unrenamed_files) - 10} more",
                    font=("Segoe UI", 8, "italic"),
                    bg="white",
                    fg="#999",
                    anchor=tk.W
                ).pack(fill=tk.X, padx=10, pady=3)

        def undo_last_batch():
            """Remove the most recently created batch"""
            if not batches:
                messagebox.showinfo("No Batches", "No batches to undo")
                return

            last_batch = batches[-1]
            delete_batch(last_batch)

        def reset_all_batches():
            """Clear all batches and restore original names"""
            if not batches:
                messagebox.showinfo("No Batches", "No batches to reset")
                return

            if not messagebox.askyesno("Reset All", f"Remove all {len(batches)} batches?\n\nAll files will return to original names."):
                return

            # Clear all batches
            for batch in batches[:]:
                for file_obj in batch['files']:
                    file_obj['current_batch'] = None
                    if 'pending_name' in file_obj:
                        del file_obj['pending_name']

            batches.clear()
            batch_counter[0] = 1
            current_edit_batch[0] = None

            # Refresh UI
            update_file_selection_display()
            create_batch_cards()
            update_unrenamed_section()
            update_stats()

        def show_export_preview():
            """Show preview dialog with all rename changes"""
            if not batches:
                messagebox.showinfo("No Changes", "No rename batches to preview")
                return

            # Create preview dialog
            preview_dialog = tk.Toplevel(dialog)
            preview_dialog.title("Preview All Changes")
            preview_dialog.geometry("800x600")
            preview_dialog.transient(dialog)
            preview_dialog.grab_set()

            # Header
            header = tk.Frame(preview_dialog, bg="#0078D4", height=60)
            header.pack(fill=tk.X)
            header.pack_propagate(False)

            tk.Label(
                header,
                text="Preview All Changes",
                font=("Segoe UI", 14, "bold"),
                bg="#0078D4",
                fg="white"
            ).pack(pady=10)

            total_renamed = sum(len(b['files']) for b in batches)
            tk.Label(
                header,
                text=f"{total_renamed} files will be renamed across {len(batches)} batches",
                font=("Segoe UI", 10),
                bg="#0078D4",
                fg="white"
            ).pack()

            # Content with scrolling
            preview_canvas = tk.Canvas(preview_dialog, bg="white", highlightthickness=0)
            preview_scrollbar = tk.Scrollbar(preview_dialog, orient="vertical", command=preview_canvas.yview)
            preview_content = tk.Frame(preview_canvas, bg="white")

            preview_canvas.configure(yscrollcommand=preview_scrollbar.set)
            preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            preview_canvas_window = preview_canvas.create_window((0, 0), window=preview_content, anchor="nw")
            preview_content.bind("<Configure>", lambda e: preview_canvas.configure(scrollregion=preview_canvas.bbox("all")))
            preview_canvas.bind("<Configure>", lambda e: preview_canvas.itemconfig(preview_canvas_window, width=e.width))

            # Show each batch
            for batch_idx, batch in enumerate(batches):
                batch_frame = tk.LabelFrame(
                    preview_content,
                    text=batch['name'].get(),
                    font=("Segoe UI", 10, "bold"),
                    bg="white",
                    fg="#0078D4"
                )
                batch_frame.pack(fill=tk.X, padx=20, pady=10)

                for file_obj in batch['files']:
                    file_row = tk.Frame(batch_frame, bg="white")
                    file_row.pack(fill=tk.X, padx=10, pady=2)

                    tk.Label(
                        file_row,
                        text=original_names[file_obj['name']],
                        font=("Segoe UI", 9),
                        bg="white",
                        fg="#666",
                        anchor=tk.W,
                        width=40
                    ).pack(side=tk.LEFT)

                    tk.Label(
                        file_row,
                        text="→",
                        font=("Segoe UI", 9),
                        bg="white",
                        fg="#999"
                    ).pack(side=tk.LEFT, padx=5)

                    tk.Label(
                        file_row,
                        text=file_obj.get('pending_name', file_obj['name']),
                        font=("Segoe UI", 9, "bold"),
                        bg="white",
                        fg="#0078D4",
                        anchor=tk.W
                    ).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Close button
            tk.Button(
                preview_dialog,
                text="Close",
                command=preview_dialog.destroy,
                font=("Segoe UI", 10),
                bg="#0078D4",
                fg="white",
                relief=tk.FLAT,
                cursor="hand2",
                padx=30,
                pady=10
            ).pack(pady=20)

        def save_all_changes():
            """Commit all rename changes"""
            if not batches:
                messagebox.showinfo("No Changes", "No rename batches to save")
                return

            total_renamed = sum(len(b['files']) for b in batches)

            if not messagebox.askyesno(
                "Confirm Save",
                f"Apply all rename changes?\n\n{total_renamed} files will be renamed across {len(batches)} batches.\n\nThis cannot be undone."
            ):
                return

            # Apply all changes
            for batch in batches:
                for file_obj in batch['files']:
                    if 'pending_name' in file_obj:
                        file_obj['name'] = file_obj['pending_name']
                        # Update UI label
                        if 'name_label' in file_obj:
                            file_obj['name_label'].config(text=file_obj['name'])

            dialog.destroy()
            messagebox.showinfo("Success", f"Successfully renamed {total_renamed} file(s)")

        def cancel_all():
            """Close dialog without saving"""
            if batches:
                if not messagebox.askyesno("Cancel", f"Discard {len(batches)} batches without saving?"):
                    return

            # Clear all pending changes
            for file_obj in self.files:
                if 'current_batch' in file_obj:
                    file_obj['current_batch'] = None
                if 'pending_name' in file_obj:
                    del file_obj['pending_name']

            dialog.destroy()

        def update_file_selection_display():
            """Update file list to show batch membership status"""
            for widget in files_list_frame.winfo_children():
                widget.destroy()

            for file_obj in self.files:
                file_frame = tk.Frame(files_list_frame, bg="white")
                file_frame.pack(fill=tk.X, pady=2)

                # Checkbox
                cb = tk.Checkbutton(
                    file_frame,
                    variable=file_obj['rename_selected'],
                    bg="white",
                    command=lambda: update_selected_count_display()
                )
                cb.pack(side=tk.LEFT, padx=(5, 5))

                # File name with batch status
                if file_obj.get('current_batch'):
                    text = f"{file_obj['name']} [In Batch]"
                    fg = "#999"
                else:
                    text = file_obj['name']
                    fg = "#000"

                tk.Label(
                    file_frame,
                    text=text,
                    font=("Segoe UI", 9),
                    bg="white",
                    fg=fg,
                    anchor=tk.W
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)

            files_list_frame.update_idletasks()
            files_canvas.configure(scrollregion=files_canvas.bbox("all"))

        def update_selected_count_display():
            """Update the count of selected files"""
            if selected_count_label[0]:
                count = sum(1 for f in self.files if f.get('rename_selected', tk.BooleanVar()).get())
                selected_count_label[0].config(text=f"{count} file(s) selected")

        # ========== SECTION 1: FILE SELECTION & PATTERN CONFIGURATION ==========

        main_config_frame = tk.Frame(content, bg="white")
        main_config_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        # Left side: File selection
        left_panel = tk.LabelFrame(
            main_config_frame,
            text="Select Files",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        )
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Select buttons
        select_buttons = tk.Frame(left_panel, bg="white")
        select_buttons.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(
            select_buttons,
            text="Select All",
            command=lambda: [f['rename_selected'].set(True) for f in self.files] or update_selected_count_display(),
            font=("Segoe UI", 8),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=2
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            select_buttons,
            text="Deselect All",
            command=lambda: [f['rename_selected'].set(False) for f in self.files] or update_selected_count_display(),
            font=("Segoe UI", 8),
            bg="#E1E1E1",
            fg="#333",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=2
        ).pack(side=tk.LEFT)

        count_label = tk.Label(
            select_buttons,
            text="0 file(s) selected",
            font=("Segoe UI", 8),
            bg="white",
            fg="#666"
        )
        count_label.pack(side=tk.RIGHT, padx=5)
        selected_count_label[0] = count_label

        # File list with checkboxes
        files_canvas = tk.Canvas(left_panel, bg="white", height=200, highlightthickness=0)
        files_scrollbar = tk.Scrollbar(left_panel, orient="vertical", command=files_canvas.yview)
        files_list_frame = tk.Frame(files_canvas, bg="white")

        files_canvas.configure(yscrollcommand=files_scrollbar.set)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        files_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        files_canvas_window = files_canvas.create_window((0, 0), window=files_list_frame, anchor="nw")
        files_canvas.bind('<Configure>', lambda e: files_canvas.itemconfig(files_canvas_window, width=e.width))

        # Right side: Pattern configuration
        right_panel = tk.LabelFrame(
            main_config_frame,
            text="Configure Pattern",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        )
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Pattern options
        tk.Radiobutton(
            right_panel,
            text="Custom name + number:",
            variable=pattern_var,
            value="custom",
            font=("Segoe UI", 9),
            bg="white"
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        tk.Entry(right_panel, textvariable=custom_name_var, font=("Segoe UI", 9), width=20).grid(row=0, column=1, padx=5, pady=3)

        tk.Label(right_panel, text="Start:", font=("Segoe UI", 8), bg="white").grid(row=1, column=0, sticky=tk.E, padx=5)
        tk.Entry(right_panel, textvariable=start_num_var, font=("Segoe UI", 9), width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(right_panel, text="Digits:", font=("Segoe UI", 8), bg="white").grid(row=2, column=0, sticky=tk.E, padx=5)
        tk.Spinbox(right_panel, from_=1, to=5, textvariable=digits_var, font=("Segoe UI", 9), width=8).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Radiobutton(
            right_panel,
            text="Add prefix:",
            variable=pattern_var,
            value="prefix",
            font=("Segoe UI", 9),
            bg="white"
        ).grid(row=3, column=0, sticky=tk.W, padx=5, pady=3)
        tk.Entry(right_panel, textvariable=prefix_var, font=("Segoe UI", 9), width=20).grid(row=3, column=1, padx=5, pady=3)

        tk.Radiobutton(
            right_panel,
            text="Add suffix:",
            variable=pattern_var,
            value="suffix",
            font=("Segoe UI", 9),
            bg="white"
        ).grid(row=4, column=0, sticky=tk.W, padx=5, pady=3)
        tk.Entry(right_panel, textvariable=suffix_var, font=("Segoe UI", 9), width=20).grid(row=4, column=1, padx=5, pady=3)

        tk.Radiobutton(
            right_panel,
            text="Find/Replace:",
            variable=pattern_var,
            value="replace",
            font=("Segoe UI", 9),
            bg="white"
        ).grid(row=5, column=0, sticky=tk.W, padx=5, pady=3)

        replace_inputs = tk.Frame(right_panel, bg="white")
        replace_inputs.grid(row=5, column=1, sticky=tk.W, padx=5, pady=3)
        tk.Label(replace_inputs, text="Find:", font=("Segoe UI", 8), bg="white").pack(side=tk.LEFT)
        tk.Entry(replace_inputs, textvariable=find_var, font=("Segoe UI", 8), width=10).pack(side=tk.LEFT, padx=2)
        tk.Label(replace_inputs, text="→", font=("Segoe UI", 8), bg="white").pack(side=tk.LEFT)
        tk.Entry(replace_inputs, textvariable=replace_var, font=("Segoe UI", 8), width=10).pack(side=tk.LEFT, padx=2)

        # Apply button
        tk.Button(
            right_panel,
            text="Apply / Update Batch",
            command=apply_or_update_batch,
            font=("Segoe UI", 10, "bold"),
            bg="#107C10",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        ).grid(row=6, column=0, columnspan=2, pady=10)

        # ========== SECTION 2: BATCH CARDS ==========
        # (Will be created dynamically by create_batch_cards())

        # ========== SECTION 3: UNRENAMED FILES ==========
        # (Will be created dynamically by update_unrenamed_section())

        # ========== ACTION BUTTONS ==========
        actions_frame = tk.Frame(content, bg="white")
        actions_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(
            actions_frame,
            text="Undo Last Batch",
            command=undo_last_batch,
            font=("Segoe UI", 9),
            bg="#E1E1E1",
            fg="#333",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            actions_frame,
            text="Reset All",
            command=reset_all_batches,
            font=("Segoe UI", 9),
            bg="#E1E1E1",
            fg="#D13438",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            actions_frame,
            text="Preview Export",
            command=show_export_preview,
            font=("Segoe UI", 9),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT)

        # ========== BOTTOM BUTTONS ==========
        bottom_frame = tk.Frame(dialog, bg="white", height=70)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        bottom_frame.pack_propagate(False)

        button_container = tk.Frame(bottom_frame, bg="white")
        button_container.pack(expand=True)

        tk.Button(
            button_container,
            text="Save All Changes",
            command=save_all_changes,
            font=("Segoe UI", 11, "bold"),
            bg="#107C10",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=40,
            pady=12
        ).pack(side=tk.RIGHT, padx=(10, 0))

        tk.Button(
            button_container,
            text="Cancel All",
            command=cancel_all,
            font=("Segoe UI", 11),
            bg="#E1E1E1",
            fg="#333",
            relief=tk.FLAT,
            cursor="hand2",
            padx=40,
            pady=12
        ).pack(side=tk.RIGHT)

        # ========== INITIALIZE ==========
        update_file_selection_display()
        create_batch_cards()
        update_unrenamed_section()
        update_selected_count_display()
