"""
File List Panel Component
Left pane showing list of loaded files with selection
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json
import os


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
        ).pack(fill=tk.X, padx=10, pady=10)

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
            with open(preset_path, 'r') as f:
                preset_data = json.load(f)

            operations = preset_data.get('operations', [])

            if not operations:
                messagebox.showwarning("Empty Preset", "This preset has no operations")
                return

            # Apply to each selected file
            for file_obj in selected_files:
                # CRITICAL: Store operations in file object
                file_obj['operations'] = operations.copy()
                file_obj['preset_name'] = preset_name

            messagebox.showinfo(
                "Success",
                f"Applied preset '{preset_name}' to {len(selected_files)} file(s)"
            )

            # If a file is currently selected, refresh its detail view
            if self.selected_file and self.selected_file in selected_files:
                if self.app and hasattr(self.app, '_on_file_selected'):
                    self.app._on_file_selected(self.selected_file)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply preset:\n{str(e)}")

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
            text="TXT (Tab-delimited) - For external programs",
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
                    df.to_csv(output_path, sep='\t', index=False)
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
                        content = df.to_csv(sep='\t', index=False)
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
                combined_df.to_csv(save_path, sep='\t', index=False)
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
