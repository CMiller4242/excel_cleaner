"""
File Detail Panel Component
Right pane showing selected file's data and workflow
"""

import tkinter as tk
from tkinter import ttk


class FileDetailPanel(tk.Frame):
    """
    Right pane showing selected file's data and workflow
    """

    def __init__(self, parent, app_ref=None, **kwargs):
        super().__init__(parent, bg="white", **kwargs)

        self.app = app_ref
        self.current_file = None
        self.current_tab = "original"

        self._create_widgets()

    def _create_widgets(self):
        # File info header
        self.header_frame = tk.Frame(self, bg="#0078D4", height=50)
        self.header_frame.pack(fill=tk.X)
        self.header_frame.pack_propagate(False)

        self.file_name_label = tk.Label(
            self.header_frame,
            text="📄 No file selected",
            font=('Segoe UI', 12, 'bold'),
            bg="#0078D4",
            fg="white"
        )
        self.file_name_label.pack(side=tk.LEFT, padx=15, pady=10)

        self.file_stats_label = tk.Label(
            self.header_frame,
            text="",
            font=('Segoe UI', 10),
            bg="#0078D4",
            fg="white"
        )
        self.file_stats_label.pack(side=tk.LEFT, padx=10)

        # Scrollable content area
        content_container = tk.Frame(self, bg="white")
        content_container.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(content_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas
        self.canvas = tk.Canvas(
            content_container,
            bg="white",
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)

        # Content frame
        self.content_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window(
            0, 0,
            window=self.content_frame,
            anchor="nw"
        )

        # Bind resize
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Data preview section
        self._create_data_preview()

        # Workflow section
        self._create_workflow_section()

    def _create_data_preview(self):
        preview_frame = tk.LabelFrame(
            self.content_frame,
            text="📊 DATA PREVIEW",
            font=('Segoe UI', 11, 'bold'),
            bg="white",
            fg="#333"
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Tab control
        tab_frame = tk.Frame(preview_frame, bg="white")
        tab_frame.pack(fill=tk.X, padx=10, pady=10)

        self.original_tab_btn = tk.Button(
            tab_frame,
            text="Original",
            command=lambda: self.switch_tab("original"),
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            bg="#0078D4",
            fg="white",
            cursor="hand2",
            padx=20,
            activebackground="#005A9E",
            activeforeground="white"
        )
        self.original_tab_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.results_tab_btn = tk.Button(
            tab_frame,
            text="Results",
            command=lambda: self.switch_tab("results"),
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            bg="#E1E1E1",
            fg="#333",
            cursor="hand2",
            padx=20,
            activebackground="#CCC"
        )
        self.results_tab_btn.pack(side=tk.LEFT)

        # Data grid placeholder
        self.data_grid_frame = tk.Frame(preview_frame, bg="white", height=300)
        self.data_grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        tk.Label(
            self.data_grid_frame,
            text="Select a file to view data preview",
            font=('Segoe UI', 10),
            bg="white",
            fg="#999"
        ).pack(pady=50)

    def _create_workflow_section(self):
        workflow_frame = tk.LabelFrame(
            self.content_frame,
            text="⚙ WORKFLOW",
            font=('Segoe UI', 11, 'bold'),
            bg="white",
            fg="#333"
        )
        workflow_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Operations list container
        self.operations_container = tk.Frame(workflow_frame, bg="white")
        self.operations_container.pack(fill=tk.X, padx=10, pady=10)

        # Operations count label
        self.operations_count_label = tk.Label(
            self.operations_container,
            text="(0 operations)",
            font=('Segoe UI', 10, 'bold'),
            bg="white",
            fg="#666"
        )
        self.operations_count_label.pack(anchor=tk.W, pady=(0, 10))

        # Operations list
        self.operations_frame = tk.Frame(self.operations_container, bg="white")
        self.operations_frame.pack(fill=tk.X)

        # No operations message
        self.no_ops_label = tk.Label(
            self.operations_frame,
            text="No operations in workflow",
            font=('Segoe UI', 10),
            bg="white",
            fg="#999"
        )
        self.no_ops_label.pack(pady=20)

        # Action buttons
        btn_frame = tk.Frame(workflow_frame, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(
            btn_frame,
            text="+ Add Operation",
            command=self._on_add_operation,
            font=('Segoe UI', 10, 'bold'),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            activebackground="#005A9E",
            activeforeground="white"
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            btn_frame,
            text="▶ Run Workflow",
            command=self._on_run_workflow,
            font=('Segoe UI', 10, 'bold'),
            bg="#107C10",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            activebackground="#0B5A0C",
            activeforeground="white"
        ).pack(side=tk.LEFT)

        # Quick actions
        quick_actions_frame = tk.LabelFrame(
            workflow_frame,
            text="QUICK ACTIONS",
            font=('Segoe UI', 9, 'bold'),
            bg="white"
        )
        quick_actions_frame.pack(fill=tk.X, padx=10, pady=(10, 10))

        quick_actions = [
            ("• Copy Workflow to Selected Files", self._on_copy_to_selected, "#0078D4"),
            ("• Apply Preset to Selected Files", self._on_apply_preset, "#0078D4"),
            ("• Clear Workflow", self._on_clear_workflow, "#D83B01")
        ]

        for text, command, color in quick_actions:
            tk.Button(
                quick_actions_frame,
                text=text,
                command=command,
                font=('Segoe UI', 9),
                bg="white",
                fg=color,
                relief=tk.FLAT,
                cursor="hand2",
                anchor=tk.W,
                activebackground="#F0F0F0"
            ).pack(fill=tk.X, padx=10, pady=2)

    def show_file(self, file_obj):
        """Display file details in right pane"""
        self.current_file = file_obj

        # Update header
        self.file_name_label.config(text=f"📄 File: {file_obj['name']}")

        rows = len(file_obj['df'])
        cols = len(file_obj['df'].columns)
        self.file_stats_label.config(text=f"{rows:,} rows × {cols} columns")

        # Update data preview
        self._update_data_preview(file_obj)

        # Update workflow
        self._update_workflow(file_obj)

    def _update_data_preview(self, file_obj):
        """Update data grid with file data"""
        # Clear existing
        for widget in self.data_grid_frame.winfo_children():
            widget.destroy()

        # Get the appropriate DataFrame
        if self.current_tab == "results" and 'result_df' in file_obj and file_obj['result_df'] is not None:
            df = file_obj['result_df']
        else:
            df = file_obj['df']

        # Create simple preview (first 10 rows)
        preview_text = self._format_dataframe_preview(df)

        text_widget = tk.Text(
            self.data_grid_frame,
            font=('Courier New', 9),
            bg="white",
            wrap=tk.NONE,
            height=15
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Add scrollbars
        h_scroll = tk.Scrollbar(self.data_grid_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        text_widget.config(xscrollcommand=h_scroll.set)

        text_widget.insert('1.0', preview_text)
        text_widget.config(state=tk.DISABLED)

    def _format_dataframe_preview(self, df, max_rows=10):
        """Format DataFrame as text preview"""
        if df is None or len(df) == 0:
            return "No data available"

        # Get column headers
        headers = list(df.columns)
        col_widths = [max(len(str(h)), 10) for h in headers]

        # Adjust column widths based on data
        for i, col in enumerate(df.columns):
            max_width = max(df[col].head(max_rows).astype(str).str.len().max(), col_widths[i])
            col_widths[i] = min(max_width, 30)  # Cap at 30 chars

        # Format header
        header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
        separator = "-" * len(header_line)

        lines = [header_line, separator]

        # Format data rows
        for idx, row in df.head(max_rows).iterrows():
            row_line = " | ".join(str(row[col])[:w].ljust(w) for col, w in zip(df.columns, col_widths))
            lines.append(row_line)

        if len(df) > max_rows:
            lines.append(f"\n... ({len(df) - max_rows} more rows)")

        return "\n".join(lines)

    def _update_workflow(self, file_obj):
        """Update workflow operations list"""
        # Clear existing
        for widget in self.operations_frame.winfo_children():
            widget.destroy()

        operations = file_obj.get('operations', [])

        # Update count
        self.operations_count_label.config(text=f"({len(operations)} operations)")

        if not operations:
            tk.Label(
                self.operations_frame,
                text="No operations in workflow\nAdd operations or apply a preset",
                font=('Segoe UI', 10),
                bg="white",
                fg="#999",
                justify=tk.CENTER
            ).pack(pady=20)
        else:
            # Show preset name if applied
            preset_name = file_obj.get('preset_name')
            if preset_name:
                preset_label = tk.Label(
                    self.operations_frame,
                    text=f"📋 Preset: {preset_name}",
                    font=('Segoe UI', 9, 'italic'),
                    bg="#E6F2FF",
                    fg="#0078D4",
                    anchor=tk.W,
                    padx=10,
                    pady=5
                )
                preset_label.pack(fill=tk.X, pady=(0, 10))

            # Display each operation
            for idx, op in enumerate(operations, 1):
                self._create_operation_card(op, idx, file_obj)

    def _create_operation_card(self, operation, index, file_obj):
        """Create UI card for an operation"""
        card = tk.Frame(
            self.operations_frame,
            bg="#F3F3F3",
            relief=tk.RAISED,
            borderwidth=1
        )
        card.pack(fill=tk.X, pady=5)

        # Operation header
        header = tk.Frame(card, bg="#E1E1E1")
        header.pack(fill=tk.X)

        # Get operation name and status
        op_name = operation.get('name', operation.get('operation', 'Unknown Operation'))
        enabled = operation.get('enabled', True)
        status_icon = "✓" if enabled else "○"

        tk.Label(
            header,
            text=f"{index}. {status_icon} {op_name}",
            font=('Segoe UI', 10, 'bold'),
            bg="#E1E1E1",
            fg="#333" if enabled else "#999"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # Operation type/category
        op_type = operation.get('type', operation.get('category', ''))
        if op_type:
            tk.Label(
                header,
                text=f"[{op_type}]",
                font=('Segoe UI', 8),
                bg="#E1E1E1",
                fg="#666"
            ).pack(side=tk.LEFT, padx=5)

        # Operation parameters
        params = operation.get('params', operation.get('parameters', {}))
        if params and isinstance(params, dict):
            params_frame = tk.Frame(card, bg="#F3F3F3")
            params_frame.pack(fill=tk.X, padx=10, pady=5)

            for key, value in list(params.items())[:3]:
                # Format value nicely
                if isinstance(value, list):
                    if len(value) > 3:
                        value_str = f"{len(value)} items"
                    else:
                        value_str = ", ".join(str(v) for v in value)
                else:
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."

                tk.Label(
                    params_frame,
                    text=f"  • {key}: {value_str}",
                    font=('Segoe UI', 9),
                    bg="#F3F3F3",
                    fg="#666",
                    anchor=tk.W
                ).pack(fill=tk.X)

            if len(params) > 3:
                tk.Label(
                    params_frame,
                    text=f"  ... and {len(params) - 3} more parameters",
                    font=('Segoe UI', 8, 'italic'),
                    bg="#F3F3F3",
                    fg="#999"
                ).pack(fill=tk.X)

        # Action buttons
        btn_frame = tk.Frame(card, bg="#F3F3F3")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            btn_frame,
            text="Edit",
            command=lambda: self._edit_operation(file_obj, index - 1),
            font=('Segoe UI', 8),
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            bg="#E1E1E1",
            activebackground="#CCC"
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            btn_frame,
            text="Delete",
            command=lambda: self._delete_operation(file_obj, index - 1),
            font=('Segoe UI', 8),
            relief=tk.FLAT,
            cursor="hand2",
            fg="red",
            padx=10,
            bg="#E1E1E1",
            activebackground="#CCC"
        ).pack(side=tk.LEFT, padx=(0, 5))

        toggle_text = "Disable" if enabled else "Enable"
        tk.Button(
            btn_frame,
            text=toggle_text,
            command=lambda: self._toggle_operation(file_obj, index - 1),
            font=('Segoe UI', 8),
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            bg="#E1E1E1",
            activebackground="#CCC"
        ).pack(side=tk.LEFT)

    def switch_tab(self, tab):
        """Switch between Original and Results tabs"""
        self.current_tab = tab

        if tab == "original":
            self.original_tab_btn.config(bg="#0078D4", fg="white")
            self.results_tab_btn.config(bg="#E1E1E1", fg="#333")
        else:
            self.original_tab_btn.config(bg="#E1E1E1", fg="#333")
            self.results_tab_btn.config(bg="#0078D4", fg="white")

        # Refresh data preview
        if self.current_file:
            self._update_data_preview(self.current_file)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    # Event handlers
    def _on_add_operation(self):
        """Open dialog to add an operation with file context"""
        from tkinter import messagebox

        if not self.current_file:
            messagebox.showwarning("No File", "Please select a file first")
            return

        # For now, delegate to app's operation sidebar but pass file context
        # In the future, this could show a custom operation selector dialog
        if self.app and hasattr(self.app, 'toggle_operations_sidebar'):
            self.app.toggle_operations_sidebar()
            # Store current file context for operations to use
            if hasattr(self.app, 'batch_mode_current_file'):
                self.app.batch_mode_current_file = self.current_file

    def _on_run_workflow(self):
        if self.app and self.current_file and hasattr(self.app, 'run_workflow_for_file'):
            self.app.run_workflow_for_file(self.current_file)

    def _on_copy_to_selected(self):
        if self.app and hasattr(self.app, 'copy_workflow_to_selected'):
            self.app.copy_workflow_to_selected(self.current_file['name'] if self.current_file else None)

    def _on_apply_preset(self):
        """Apply preset to selected files via file list panel"""
        if self.app and hasattr(self.app, 'file_list_panel'):
            self.app.file_list_panel.apply_preset_to_selected()

    def _on_clear_workflow(self):
        from tkinter import messagebox

        if self.current_file:
            if messagebox.askyesno("Confirm Clear", "Remove all operations from this workflow?"):
                self.current_file['operations'] = []
                self.current_file.pop('preset_name', None)  # Remove preset name if any
                self._update_workflow(self.current_file)

    def _edit_operation(self, file_obj, op_index):
        """Edit an operation's parameters"""
        # TODO: Open operation edit dialog
        from tkinter import messagebox
        messagebox.showinfo("Edit Operation", "Operation editing coming soon!\n\nFor now, delete and re-add the operation.")

    def _delete_operation(self, file_obj, op_index):
        """Delete an operation from workflow"""
        from tkinter import messagebox

        if messagebox.askyesno("Confirm Delete", "Remove this operation from workflow?"):
            file_obj['operations'].pop(op_index)
            self._update_workflow(file_obj)

    def _toggle_operation(self, file_obj, op_index):
        """Enable/disable an operation"""
        operation = file_obj['operations'][op_index]
        operation['enabled'] = not operation.get('enabled', True)
        self._update_workflow(file_obj)
