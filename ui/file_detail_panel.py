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
        """Create data preview section using tksheet (same as single file mode)"""
        preview_frame = tk.LabelFrame(
            self.content_frame,
            text="📊 DATA PREVIEW",
            font=('Segoe UI', 11, 'bold'),
            bg="white",
            fg="#333"
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Use the same EnhancedDataPreview component from single file mode
        from enhanced_preview import EnhancedDataPreview

        self.data_preview = EnhancedDataPreview(preview_frame)
        self.data_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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
        """Update data grid with file data using tksheet"""
        if not hasattr(self, 'data_preview'):
            return

        # Load original data into preview
        if file_obj.get('df') is not None and not file_obj['df'].empty:
            self.data_preview.load_dataframe(file_obj['df'], is_result=False)

        # If file has been processed, show results
        if 'result_df' in file_obj and file_obj['result_df'] is not None and not file_obj['result_df'].empty:
            self.data_preview.load_dataframe(file_obj['result_df'], is_result=True)

    def _update_workflow(self, file_obj):
        """Update workflow operations list"""
        print(f"[DEBUG] Updating workflow for {file_obj.get('name', 'Unknown')}")

        # Clear existing
        for widget in self.operations_frame.winfo_children():
            widget.destroy()

        operations = file_obj.get('operations', [])
        print(f"[DEBUG] Found {len(operations)} operations in file object")

        if operations:
            print(f"[DEBUG] First operation: {operations[0]}")

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
                print(f"[DEBUG] Displaying preset: {preset_name}")
                preset_label = tk.Frame(
                    self.operations_frame,
                    bg="#E6F2FF",
                    relief=tk.RAISED,
                    borderwidth=1
                )
                preset_label.pack(fill=tk.X, pady=(0, 10))

                tk.Label(
                    preset_label,
                    text=f"📋 Preset: {preset_name}",
                    font=('Segoe UI', 10, 'bold'),
                    bg="#E6F2FF",
                    fg="#0078D4",
                    anchor=tk.W,
                    padx=10,
                    pady=8
                ).pack(fill=tk.X)

            # Display each operation
            print(f"[DEBUG] Creating {len(operations)} operation cards")
            for idx, op in enumerate(operations, 1):
                try:
                    self._create_operation_card(op, idx, file_obj)
                except Exception as e:
                    print(f"[ERROR] Failed to create operation card {idx}: {e}")
                    import traceback
                    traceback.print_exc()

            print(f"[DEBUG] Workflow update complete")

    def _create_operation_card(self, operation, index, file_obj):
        """Create UI card for an operation"""
        # HANDLE BOTH OLD AND NEW OPERATION FORMATS
        # Old format: {'name': 'Op Name', 'parameters': {...}}
        # Preset format: {'operation_id': '...', 'parameters': {...}}
        # New format: {'class': 'ClassName', 'type': 'Category', 'parameters': {...}, 'enabled': True}

        print(f"[DEBUG] Creating card {index} for operation keys: {list(operation.keys())}")

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

        # Get operation name and status (use registry for accurate names)
        from operations.registry import get_registry
        registry = get_registry()

        op_name = registry.get_display_name(operation)
        enabled = operation.get('enabled', True)
        status_icon = "✓" if enabled else "○"

        print(f"[DEBUG] Display name: {op_name}, Enabled: {enabled}")

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

        # Operation parameters (support both 'params' and 'parameters')
        params = operation.get('params', operation.get('parameters', {}))
        if params and isinstance(params, dict):
            params_frame = tk.Frame(card, bg="#F3F3F3")
            params_frame.pack(fill=tk.X, padx=10, pady=5)

            # Show first 5 parameters
            param_items = list(params.items())[:5]
            for key, value in param_items:
                # Format value nicely
                if isinstance(value, list):
                    if len(value) > 3:
                        value_str = f"{len(value)} items"
                    else:
                        value_str = ", ".join(str(v) for v in value)
                elif isinstance(value, dict):
                    value_str = f"{len(value)} mappings"
                else:
                    value_str = str(value)
                    if len(value_str) > 60:
                        value_str = value_str[:57] + "..."

                tk.Label(
                    params_frame,
                    text=f"  • {key}: {value_str}",
                    font=('Segoe UI', 9),
                    bg="#F3F3F3",
                    fg="#666",
                    anchor=tk.W
                ).pack(fill=tk.X)

            if len(params) > 5:
                tk.Label(
                    params_frame,
                    text=f"  ... and {len(params) - 5} more parameter(s)",
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
            activebackground="#CCC",
            state=tk.NORMAL if enabled else tk.DISABLED
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

        # Show operation selector dialog
        self._show_operation_selector()

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
        from tkinter import messagebox
        from operations.registry import get_registry

        operation_config = file_obj['operations'][op_index]

        # Get operation ID from various possible keys
        operation_id = operation_config.get('class') or operation_config.get('operation_id') or operation_config.get('id')

        if not operation_id:
            # Fallback: try to find by name
            operation_name = operation_config.get('name')
            print(f"[DEBUG] No class/operation_id found, trying to find by name: {operation_name}")

        print(f"[DEBUG] Editing operation with ID: {operation_id}")

        # Get operation from registry
        registry = get_registry()
        operation = registry.get_by_id(operation_id) if operation_id else None

        if not operation and 'name' in operation_config:
            # Fallback: search by name
            operation_name = operation_config['name']
            print(f"[DEBUG] Searching by name: {operation_name}")
            for op in registry.list_all():
                if op.metadata.name == operation_name:
                    operation = op
                    break

        if not operation:
            error_msg = f"Could not find operation '{operation_id or operation_config.get('name', 'Unknown')}'"
            print(f"[ERROR] {error_msg}")
            messagebox.showerror("Operation Not Found", error_msg)
            return

        print(f"[DEBUG] Found operation: {operation.metadata.name}")

        # Get current parameters
        current_params = operation_config.get('parameters', operation_config.get('params', {}))

        # Show the appropriate dialog with current parameters
        self._configure_operation(file_obj, operation, edit_mode=True, edit_index=op_index, current_params=current_params)

    def _delete_operation(self, file_obj, op_index):
        """Delete an operation from workflow"""
        from tkinter import messagebox

        if messagebox.askyesno("Confirm Delete", "Remove this operation from workflow?"):
            file_obj['operations'].pop(op_index)

            # If we deleted all operations, clear preset name
            if not file_obj['operations']:
                file_obj.pop('preset_name', None)

            self._update_workflow(file_obj)

    def _toggle_operation(self, file_obj, op_index):
        """Enable/disable an operation"""
        operation = file_obj['operations'][op_index]
        operation['enabled'] = not operation.get('enabled', True)
        self._update_workflow(file_obj)

    # ==================== OPERATION CONFIGURATION ====================

    def _show_operation_selector(self):
        """Show dialog to select an operation to add"""
        from tkinter import messagebox
        from operations.registry import get_registry

        registry = get_registry()
        operations = registry.list_all()

        if not operations:
            messagebox.showwarning("No Operations", "No operations available")
            return

        # Create operation selector dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Operation")
        dialog.geometry("700x600")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        main_frame = tk.Frame(dialog, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        tk.Label(
            main_frame,
            text="Select an Operation",
            font=('Segoe UI', 14, 'bold'),
            bg="white"
        ).pack(pady=(0, 10))

        # Search box
        search_frame = tk.Frame(main_frame, bg="white")
        search_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            search_frame,
            text="Search:",
            font=('Segoe UI', 10),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=search_var,
            font=('Segoe UI', 10)
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Category filter
        category_frame = tk.Frame(main_frame, bg="white")
        category_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            category_frame,
            text="Category:",
            font=('Segoe UI', 10),
            bg="white"
        ).pack(side=tk.LEFT, padx=(0, 5))

        categories = ['All'] + sorted(set(op.metadata.category for op in operations))
        category_var = tk.StringVar(value='All')
        category_combo = ttk.Combobox(
            category_frame,
            textvariable=category_var,
            values=categories,
            state='readonly',
            font=('Segoe UI', 10)
        )
        category_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Operations list (scrollable)
        list_frame = tk.Frame(main_frame, bg="white")
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(
            list_frame,
            bg="white",
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas.yview)

        ops_container = tk.Frame(canvas, bg="white")
        canvas_window = canvas.create_window(0, 0, window=ops_container, anchor="nw")

        def update_operations_list(*args):
            """Filter and display operations based on search and category"""
            # Clear existing
            for widget in ops_container.winfo_children():
                widget.destroy()

            search_text = search_var.get().lower()
            category_filter = category_var.get()

            filtered_ops = []
            for op in operations:
                # Filter by category
                if category_filter != 'All' and op.metadata.category != category_filter:
                    continue

                # Filter by search
                if search_text:
                    if (search_text not in op.metadata.name.lower() and
                        search_text not in op.metadata.description.lower()):
                        continue

                filtered_ops.append(op)

            # Sort by name
            filtered_ops.sort(key=lambda x: x.metadata.name)

            # Display operations
            for op in filtered_ops:
                self._create_operation_button(ops_container, op, dialog)

            # Update scroll region
            ops_container.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox('all'))

        # Bind filters
        search_var.trace('w', update_operations_list)
        category_var.trace('w', update_operations_list)

        # Initial population
        update_operations_list()

        # Configure canvas resize
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        ops_container.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)

        # Cancel button
        tk.Button(
            main_frame,
            text="Cancel",
            command=dialog.destroy,
            font=('Segoe UI', 10),
            bg="#E1E1E1",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(pady=(10, 0))

    def _create_operation_button(self, parent, operation, dialog):
        """Create a clickable operation card"""
        card = tk.Frame(
            parent,
            bg="#F8F8F8",
            relief=tk.RAISED,
            borderwidth=1
        )
        card.pack(fill=tk.X, pady=5)

        # Make entire card clickable
        def on_click(event=None):
            dialog.destroy()
            self._configure_operation(self.current_file, operation)

        card.bind('<Button-1>', on_click)

        # Operation info
        info_frame = tk.Frame(card, bg="#F8F8F8")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        info_frame.bind('<Button-1>', on_click)

        name_label = tk.Label(
            info_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 11, 'bold'),
            bg="#F8F8F8",
            anchor=tk.W,
            cursor="hand2"
        )
        name_label.pack(fill=tk.X)
        name_label.bind('<Button-1>', on_click)

        category_label = tk.Label(
            info_frame,
            text=f"[{operation.metadata.category}]",
            font=('Segoe UI', 9),
            bg="#F8F8F8",
            fg="#666",
            anchor=tk.W,
            cursor="hand2"
        )
        category_label.pack(fill=tk.X)
        category_label.bind('<Button-1>', on_click)

        desc_label = tk.Label(
            info_frame,
            text=operation.metadata.description,
            font=('Segoe UI', 9),
            bg="#F8F8F8",
            fg="#333",
            anchor=tk.W,
            wraplength=620,
            justify=tk.LEFT,
            cursor="hand2"
        )
        desc_label.pack(fill=tk.X, pady=(5, 0))
        desc_label.bind('<Button-1>', on_click)

    def _configure_operation(self, file_obj, operation, edit_mode=False, edit_index=None, current_params=None):
        """Configure operation parameters and add/update in workflow"""
        from tkinter import messagebox

        # Validate file has data
        if file_obj.get('df') is None or file_obj['df'].empty:
            messagebox.showwarning("No Data", f"File '{file_obj['name']}' has no data to process.")
            return

        # Check if operation has a custom show_dialog() method
        if hasattr(operation, 'show_dialog') and callable(operation.show_dialog):
            # Create DataContext wrapper to pass DataFrame to operation's custom dialog
            class DataContext:
                """Temporary container to pass DataFrame to operation dialogs"""
                def __init__(self, df, app=None):
                    self.df = df
                    self.data = df
                    self.app = app

            context = DataContext(file_obj['df'], app=self.app)

            try:
                # Call operation's custom show_dialog with context and initial params
                result = operation.show_dialog(parent=context, initial_params=current_params)

                if result:
                    # Add or update operation in workflow
                    operation_config = {
                        'name': operation.metadata.name,
                        'type': operation.metadata.category,
                        'parameters': result,
                        'enabled': True
                    }

                    if edit_mode:
                        # Update existing operation
                        operation_config['enabled'] = file_obj['operations'][edit_index].get('enabled', True)
                        file_obj['operations'][edit_index] = operation_config
                    else:
                        # Add new operation
                        if 'operations' not in file_obj:
                            file_obj['operations'] = []
                        file_obj['operations'].append(operation_config)

                    self._update_workflow(file_obj)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to configure operation:\n{str(e)}")
            return

        # Get columns with Excel-style letters
        columns = self._get_columns_with_letters(file_obj['df'])

        # Determine dialog type based on parameters
        needs_column_rename = any(p.type == 'column_rename_list' for p in operation.metadata.parameters)
        needs_single_column = any(p.type == 'column' for p in operation.metadata.parameters)
        needs_multi_column = any(p.type == 'column_list' for p in operation.metadata.parameters)

        if needs_column_rename:
            self._show_column_rename_dialog(file_obj, operation, columns, edit_mode, edit_index, current_params)
        elif needs_single_column and not needs_multi_column:
            self._show_single_column_dialog(file_obj, operation, columns, edit_mode, edit_index, current_params)
        elif needs_multi_column:
            self._show_multi_column_dialog(file_obj, operation, columns, edit_mode, edit_index, current_params)
        else:
            self._show_standard_parameter_dialog(file_obj, operation, edit_mode, edit_index, current_params)

    def _get_columns_with_letters(self, df):
        """Get column list with Excel-style letters"""
        def excel_column_letter(n):
            """Convert column number to Excel letter (1 -> A, 26 -> Z, 27 -> AA)"""
            result = ""
            while n > 0:
                n -= 1
                result = chr(65 + (n % 26)) + result
                n //= 26
            return result

        columns = []
        for i, col in enumerate(df.columns, 1):
            letter = excel_column_letter(i)
            columns.append(f"{letter}: {col}")
        return columns

    def _show_single_column_dialog(self, file_obj, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Show dialog for operations with single column parameter"""
        from smart_column_selector import ColumnSelector

        dialog = tk.Toplevel(self)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x500")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        main_frame = tk.Frame(dialog, bg="white", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        tk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold'),
            bg="white"
        ).pack(pady=(0, 10))

        tk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=550,
            font=('Segoe UI', 11),
            bg="white"
        ).pack(pady=(0, 5))

        tk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Segoe UI', 10),
            fg="gray",
            bg="white"
        ).pack(pady=(0, 20))

        param_widgets = {}

        # Process each parameter
        for param in operation.metadata.parameters:
            param_frame = tk.Frame(main_frame, bg="white")
            param_frame.pack(fill=tk.X, pady=10)

            label_text = param.description
            if param.required:
                label_text += " *"

            # Get current value if in edit mode
            current_value = current_params.get(param.name) if current_params else None

            if param.type == 'column':
                # Use ColumnSelector
                selector = ColumnSelector(param_frame, columns, label_text)
                selector.pack(fill=tk.X)
                # Pre-fill if editing
                if current_value:
                    selector.set_value(current_value)
                param_widgets[param.name] = selector

            elif param.type == 'text':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = tk.Entry(param_frame, font=('Segoe UI', 12))
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'number':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = tk.Entry(param_frame, font=('Segoe UI', 12))
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'boolean':
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else (param.default if param.default else False)
                var = tk.BooleanVar(value=value_to_set)
                widget = tk.Checkbutton(param_frame, text=label_text, variable=var, bg="white")
                widget.pack(anchor=tk.W, pady=2)
                param_widgets[param.name] = var

            elif param.type == 'choice':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = ttk.Combobox(param_frame, values=param.choices,
                                     font=('Segoe UI', 12), state='readonly')
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.set(value_to_set)
                elif param.choices:
                    widget.set(param.choices[0])
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

        def on_submit():
            params = {}
            for param in operation.metadata.parameters:
                widget = param_widgets.get(param.name)
                if widget:
                    if isinstance(widget, tk.BooleanVar):
                        params[param.name] = widget.get()
                    elif isinstance(widget, ColumnSelector):
                        params[param.name] = widget.get_value()
                    elif isinstance(widget, (tk.Entry, ttk.Combobox)):
                        value = widget.get()
                        if param.type == 'number':
                            try:
                                value = float(value)
                            except:
                                value = 0
                        params[param.name] = value

            if edit_mode:
                # Update existing operation
                file_obj['operations'][edit_index] = {
                    'name': operation.metadata.name,
                    'type': operation.metadata.category,
                    'parameters': params,
                    'enabled': file_obj['operations'][edit_index].get('enabled', True)
                }
            else:
                # Add new operation
                operation_config = {
                    'name': operation.metadata.name,
                    'type': operation.metadata.category,
                    'parameters': params,
                    'enabled': True
                }

                if 'operations' not in file_obj:
                    file_obj['operations'] = []

                file_obj['operations'].append(operation_config)

            self._update_workflow(file_obj)
            dialog.destroy()

        # Buttons
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            font=('Segoe UI', 10),
            bg="#E1E1E1",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

        button_text = "✓ Update" if edit_mode else "✓ Add to Workflow"
        tk.Button(
            btn_frame,
            text=button_text,
            command=on_submit,
            font=('Segoe UI', 10, 'bold'),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            activebackground="#005A9E",
            activeforeground="white"
        ).pack(side=tk.RIGHT, padx=5)

    def _show_multi_column_dialog(self, file_obj, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Show dialog for operations with multi-column parameter"""
        from smart_column_selector import MultiColumnSelector

        dialog = tk.Toplevel(self)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x600")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        main_frame = tk.Frame(dialog, bg="white", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        tk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold'),
            bg="white"
        ).pack(pady=(0, 10))

        tk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=550,
            font=('Segoe UI', 11),
            bg="white"
        ).pack(pady=(0, 5))

        tk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Segoe UI', 10),
            fg="gray",
            bg="white"
        ).pack(pady=(0, 20))

        param_widgets = {}

        # Process each parameter
        for param in operation.metadata.parameters:
            param_frame = tk.Frame(main_frame, bg="white")
            param_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            label_text = param.description
            if param.required:
                label_text += " *"

            # Get current value if in edit mode
            current_value = current_params.get(param.name) if current_params else None

            if param.type == 'column_list':
                # Use MultiColumnSelector
                selector = MultiColumnSelector(param_frame, columns, label_text, max_height=200)
                selector.pack(fill=tk.BOTH, expand=True)
                # Pre-fill if editing
                if current_value and isinstance(current_value, list):
                    for col_value in current_value:
                        # Find matching column and select it
                        for col in columns:
                            if col_value in col or col.endswith(col_value):
                                if col in selector.selected_vars:
                                    selector.selected_vars[col].set(True)
                                    if col not in selector.selection_order:
                                        selector.selection_order.append(col)
                                break
                param_widgets[param.name] = selector

            elif param.type == 'text':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = tk.Entry(param_frame, font=('Segoe UI', 12))
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'number':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = tk.Entry(param_frame, font=('Segoe UI', 12))
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'boolean':
                value_to_set = current_value if current_value is not None else (param.default if param.default else False)
                var = tk.BooleanVar(value=value_to_set)
                widget = tk.Checkbutton(param_frame, text=label_text, variable=var, bg="white")
                widget.pack(anchor=tk.W, pady=2)
                param_widgets[param.name] = var

            elif param.type == 'choice':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = ttk.Combobox(param_frame, values=param.choices,
                                     font=('Segoe UI', 12), state='readonly')
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.set(value_to_set)
                elif param.choices:
                    widget.set(param.choices[0])
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

        def on_submit():
            params = {}
            for param in operation.metadata.parameters:
                widget = param_widgets.get(param.name)
                if widget:
                    if isinstance(widget, tk.BooleanVar):
                        params[param.name] = widget.get()
                    elif isinstance(widget, MultiColumnSelector):
                        # Get selected columns (cleaned of Excel letters)
                        selected = []
                        for col in widget.selection_order:
                            if ':' in col:
                                selected.append(col.split(':', 1)[1].strip())
                            else:
                                selected.append(col)
                        params[param.name] = selected
                    elif isinstance(widget, (tk.Entry, ttk.Combobox)):
                        value = widget.get()
                        if param.type == 'number':
                            try:
                                value = float(value)
                            except:
                                value = 0
                        params[param.name] = value

            if edit_mode:
                # Update existing operation
                file_obj['operations'][edit_index] = {
                    'name': operation.metadata.name,
                    'type': operation.metadata.category,
                    'parameters': params,
                    'enabled': file_obj['operations'][edit_index].get('enabled', True)
                }
            else:
                # Add new operation
                operation_config = {
                    'name': operation.metadata.name,
                    'type': operation.metadata.category,
                    'parameters': params,
                    'enabled': True
                }

                if 'operations' not in file_obj:
                    file_obj['operations'] = []

                file_obj['operations'].append(operation_config)

            self._update_workflow(file_obj)
            dialog.destroy()

        # Buttons
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            font=('Segoe UI', 10),
            bg="#E1E1E1",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

        button_text = "✓ Update" if edit_mode else "✓ Add to Workflow"
        tk.Button(
            btn_frame,
            text=button_text,
            command=on_submit,
            font=('Segoe UI', 10, 'bold'),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            activebackground="#005A9E",
            activeforeground="white"
        ).pack(side=tk.RIGHT, padx=5)

    def _show_standard_parameter_dialog(self, file_obj, operation, edit_mode=False, edit_index=None, current_params=None):
        """Show dialog for operations without column parameters"""
        from tkinter import messagebox

        dialog = tk.Toplevel(self)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x400")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        main_frame = tk.Frame(dialog, bg="white", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        tk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold'),
            bg="white"
        ).pack(pady=(0, 10))

        tk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=550,
            font=('Segoe UI', 11),
            bg="white"
        ).pack(pady=(0, 5))

        tk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Segoe UI', 10),
            fg="gray",
            bg="white"
        ).pack(pady=(0, 20))

        param_widgets = {}

        # Process each parameter
        for param in operation.metadata.parameters:
            param_frame = tk.Frame(main_frame, bg="white")
            param_frame.pack(fill=tk.X, pady=10)

            label_text = param.description
            if param.required:
                label_text += " *"

            # Get current value if in edit mode
            current_value = current_params.get(param.name) if current_params else None

            if param.type == 'text':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = tk.Entry(param_frame, font=('Segoe UI', 12))
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'number':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = tk.Entry(param_frame, font=('Segoe UI', 12))
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'boolean':
                value_to_set = current_value if current_value is not None else (param.default if param.default else False)
                var = tk.BooleanVar(value=value_to_set)
                widget = tk.Checkbutton(param_frame, text=label_text, variable=var, bg="white")
                widget.pack(anchor=tk.W, pady=2)
                param_widgets[param.name] = var

            elif param.type == 'choice':
                tk.Label(param_frame, text=label_text, font=('Segoe UI', 11, 'bold'), bg="white").pack(anchor=tk.W)
                widget = ttk.Combobox(param_frame, values=param.choices,
                                     font=('Segoe UI', 12), state='readonly')
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.set(value_to_set)
                elif param.choices:
                    widget.set(param.choices[0])
                widget.pack(fill=tk.X, pady=2)
                param_widgets[param.name] = widget

        def on_submit():
            params = {}
            for param in operation.metadata.parameters:
                widget = param_widgets.get(param.name)
                if widget:
                    if isinstance(widget, tk.BooleanVar):
                        params[param.name] = widget.get()
                    elif isinstance(widget, (tk.Entry, ttk.Combobox)):
                        value = widget.get()
                        if param.type == 'number':
                            try:
                                value = float(value)
                            except:
                                value = 0
                        params[param.name] = value

            if edit_mode:
                # Update existing operation
                file_obj['operations'][edit_index] = {
                    'name': operation.metadata.name,
                    'type': operation.metadata.category,
                    'parameters': params,
                    'enabled': file_obj['operations'][edit_index].get('enabled', True)
                }
            else:
                # Add new operation
                operation_config = {
                    'name': operation.metadata.name,
                    'type': operation.metadata.category,
                    'parameters': params,
                    'enabled': True
                }

                if 'operations' not in file_obj:
                    file_obj['operations'] = []

                file_obj['operations'].append(operation_config)

            self._update_workflow(file_obj)
            dialog.destroy()

        # Buttons
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            font=('Segoe UI', 10),
            bg="#E1E1E1",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

        button_text = "✓ Update" if edit_mode else "✓ Add to Workflow"
        tk.Button(
            btn_frame,
            text=button_text,
            command=on_submit,
            font=('Segoe UI', 10, 'bold'),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            activebackground="#005A9E",
            activeforeground="white"
        ).pack(side=tk.RIGHT, padx=5)

    def _show_column_rename_dialog(self, file_obj, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Show dialog for renaming multiple columns"""
        from tkinter import messagebox

        # Strip Excel letters from columns to get actual column names
        actual_columns = []
        for col in columns:
            if ':' in col:
                actual_columns.append(col.split(':', 1)[1].strip())
            else:
                actual_columns.append(col)

        dialog = tk.Toplevel(self)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("750x600")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        main_frame = tk.Frame(dialog, bg="white", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        tk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold'),
            bg="white"
        ).pack(pady=(0, 10))

        tk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=700,
            font=('Segoe UI', 11),
            bg="white"
        ).pack(pady=(0, 5))

        tk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Segoe UI', 10),
            fg="gray",
            bg="white"
        ).pack(pady=(0, 20))

        # Instructions
        tk.Label(
            main_frame,
            text="Select columns to rename and enter new names:",
            font=('Segoe UI', 10),
            bg="white"
        ).pack(anchor=tk.W, pady=(0, 10))

        # Scrollable frame for column mappings
        canvas_frame = tk.Frame(main_frame, bg="white")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Store mapping rows
        mapping_rows = []

        def create_mapping_row(old_name=None, new_name=""):
            """Create a row for column mapping"""
            row_frame = tk.Frame(scrollable_frame, bg="white")
            row_frame.pack(fill=tk.X, pady=5)

            # Old column name (dropdown)
            tk.Label(
                row_frame,
                text="Old:",
                font=('Segoe UI', 9),
                bg="white",
                width=5
            ).pack(side=tk.LEFT, padx=(0, 5))

            old_var = tk.StringVar(value=old_name if old_name else "")
            old_combo = ttk.Combobox(
                row_frame,
                textvariable=old_var,
                values=actual_columns,
                state="readonly",
                width=28,
                font=('Segoe UI', 9)
            )
            old_combo.pack(side=tk.LEFT, padx=(0, 15))

            # Arrow
            tk.Label(
                row_frame,
                text="→",
                font=('Segoe UI', 12),
                bg="white"
            ).pack(side=tk.LEFT, padx=(0, 15))

            # New column name (text entry)
            tk.Label(
                row_frame,
                text="New:",
                font=('Segoe UI', 9),
                bg="white",
                width=5
            ).pack(side=tk.LEFT, padx=(0, 5))

            new_var = tk.StringVar(value=new_name)
            new_entry = tk.Entry(
                row_frame,
                textvariable=new_var,
                width=30,
                font=('Segoe UI', 9)
            )
            new_entry.pack(side=tk.LEFT, padx=(0, 10))

            # Remove button
            remove_btn = tk.Button(
                row_frame,
                text="✕",
                command=lambda: remove_row(row_frame),
                font=('Segoe UI', 10, 'bold'),
                fg="red",
                bg="white",
                relief=tk.FLAT,
                cursor="hand2",
                width=3
            )
            remove_btn.pack(side=tk.LEFT)

            mapping_rows.append({
                'frame': row_frame,
                'old_var': old_var,
                'new_var': new_var
            })

            return row_frame

        def remove_row(row_frame):
            """Remove a mapping row"""
            for i, row in enumerate(mapping_rows):
                if row['frame'] == row_frame:
                    row_frame.destroy()
                    mapping_rows.pop(i)
                    break

        def add_row():
            """Add a new mapping row"""
            create_mapping_row()
            canvas.update_idletasks()
            canvas.yview_moveto(1.0)  # Scroll to bottom

        # Load initial mappings if editing
        if current_params and 'column_mappings' in current_params:
            for mapping in current_params['column_mappings']:
                create_mapping_row(
                    old_name=mapping.get('old_name', ''),
                    new_name=mapping.get('new_name', '')
                )
        else:
            # Create 3 empty rows by default
            for _ in range(3):
                create_mapping_row()

        # Add/Remove buttons
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            btn_frame,
            text="+ Add Row",
            command=add_row,
            font=('Segoe UI', 9),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            btn_frame,
            text=f"Available columns: {len(actual_columns)}",
            font=('Segoe UI', 9),
            bg="white",
            fg="#666"
        ).pack(side=tk.LEFT)

        def on_submit():
            """Validate and save mappings"""
            mappings = []

            for row in mapping_rows:
                old_name = row['old_var'].get()
                new_name = row['new_var'].get().strip()

                # Skip empty rows
                if not old_name or not new_name:
                    continue

                # Check for duplicates
                if old_name == new_name:
                    messagebox.showwarning(
                        "Invalid Mapping",
                        f"Column '{old_name}' has the same old and new name.\n\n"
                        "Please change the new name or remove this row."
                    )
                    return

                mappings.append({
                    'old_name': old_name,
                    'new_name': new_name
                })

            if not mappings:
                messagebox.showwarning(
                    "No Mappings",
                    "Please add at least one column mapping before saving."
                )
                return

            # Check for duplicate new names
            new_names = [m['new_name'] for m in mappings]
            if len(new_names) != len(set(new_names)):
                messagebox.showwarning(
                    "Duplicate Names",
                    "Cannot use the same new name for multiple columns.\n\n"
                    "Please ensure all new names are unique."
                )
                return

            params = {'column_mappings': mappings}

            if edit_mode:
                # Update existing operation
                file_obj['operations'][edit_index] = {
                    'name': operation.metadata.name,
                    'type': operation.metadata.category,
                    'parameters': params,
                    'enabled': file_obj['operations'][edit_index].get('enabled', True)
                }
            else:
                # Add new operation
                operation_config = {
                    'name': operation.metadata.name,
                    'type': operation.metadata.category,
                    'parameters': params,
                    'enabled': True
                }

                if 'operations' not in file_obj:
                    file_obj['operations'] = []

                file_obj['operations'].append(operation_config)

            self._update_workflow(file_obj)
            dialog.destroy()

        # Dialog buttons
        button_frame = tk.Frame(main_frame, bg="white")
        button_frame.pack(fill=tk.X, pady=(20, 0))

        tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            font=('Segoe UI', 10),
            bg="#E1E1E1",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

        button_text = "✓ Update" if edit_mode else "✓ Add to Workflow"
        tk.Button(
            button_frame,
            text=button_text,
            command=on_submit,
            font=('Segoe UI', 10, 'bold'),
            bg="#0078D4",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            activebackground="#005A9E",
            activeforeground="white"
        ).pack(side=tk.RIGHT, padx=5)
