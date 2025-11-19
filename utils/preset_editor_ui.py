"""
Preset Editor UI Components
Provides UI for editing presets and operations
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Callable
import pandas as pd


class PresetEditorDialog:
    """
    Dialog for reviewing and editing preset operations before execution

    Usage:
        dialog = PresetEditorDialog(parent, preset_data, df)
        result = dialog.show()
        if result == "run_all":
            operations = dialog.get_selected_operations()
            # Execute operations...
    """

    def __init__(self, parent, preset_data: Dict, df: pd.DataFrame, operation_registry=None):
        """
        Initialize preset editor dialog

        Args:
            parent: Parent window
            preset_data: Preset configuration dict
            df: DataFrame being processed (for validation)
            operation_registry: Optional registry for looking up operations
        """
        self.parent = parent
        self.preset_data = preset_data
        self.df = df
        self.operation_registry = operation_registry
        self.result = None

        # Track operation states
        self.operations = preset_data.get('operations', [])
        self.operation_states = {}  # {index: {'enabled': bool, 'params': dict}}

        # Initialize states
        for idx, op in enumerate(self.operations):
            self.operation_states[idx] = {
                'enabled': op.get('enabled', True),
                'params': op.get('parameters', {}).copy()
            }

    def show(self) -> Optional[str]:
        """
        Show dialog and return user choice

        Returns:
            "run_all", "run_selected", or None (cancelled)
        """
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Preset: {self.preset_data.get('name', 'Unknown')}")
        self.dialog.geometry("800x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self._create_widgets()

        # Wait for dialog
        self.dialog.wait_window()
        return self.result

    def _create_widgets(self):
        """Create all dialog widgets"""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            header_frame,
            text=self.preset_data.get('name', 'Preset Editor'),
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W)

        ttk.Label(
            header_frame,
            text=self.preset_data.get('description', ''),
            font=("Arial", 10)
        ).pack(anchor=tk.W)

        ttk.Label(
            header_frame,
            text=f"{len(self.operations)} operations • Review and modify as needed",
            font=("Arial", 9),
            foreground="gray"
        ).pack(anchor=tk.W)

        # Separator
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        # Operations list (scrollable)
        self._create_operations_list()

        # Separator
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # Buttons
        self._create_buttons()

    def _create_operations_list(self):
        """Create scrollable list of operations"""
        # Container frame
        list_frame = ttk.Frame(self.dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Canvas + Scrollbar
        canvas = tk.Canvas(list_frame, bg="white")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)

        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create operation widgets
        for idx, operation in enumerate(self.operations):
            self._create_operation_widget(scrollable_frame, idx, operation)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_operation_widget(self, parent, idx: int, operation: Dict):
        """Create widget for single operation"""
        # Operation frame
        op_frame = ttk.LabelFrame(parent, text=f"Operation {idx + 1}", padding=10)
        op_frame.pack(fill=tk.X, padx=5, pady=5)

        # Top row: Checkbox + Name + Status
        top_row = ttk.Frame(op_frame)
        top_row.pack(fill=tk.X)

        # Enabled checkbox
        enabled_var = tk.BooleanVar(value=self.operation_states[idx]['enabled'])

        def toggle_enabled():
            self.operation_states[idx]['enabled'] = enabled_var.get()

        chk = ttk.Checkbutton(
            top_row,
            text="",
            variable=enabled_var,
            command=toggle_enabled
        )
        chk.pack(side=tk.LEFT)

        # Operation name
        op_name = operation.get('operation_id', 'Unknown')
        description = operation.get('description', '')

        name_label = ttk.Label(
            top_row,
            text=f"{op_name}",
            font=("Arial", 10, "bold")
        )
        name_label.pack(side=tk.LEFT, padx=5)

        # Editable indicator
        if operation.get('editable', False):
            ttk.Label(
                top_row,
                text="✏️",
                font=("Arial", 10)
            ).pack(side=tk.LEFT)

        # Status indicator
        status_text = "✓" if enabled_var.get() else "⊗"
        status_color = "green" if enabled_var.get() else "gray"
        status_label = ttk.Label(
            top_row,
            text=status_text,
            foreground=status_color,
            font=("Arial", 12, "bold")
        )
        status_label.pack(side=tk.RIGHT)

        # Update status when checkbox changes
        def update_status():
            status_label.config(
                text="✓" if enabled_var.get() else "⊗",
                foreground="green" if enabled_var.get() else "gray"
            )

        enabled_var.trace_add("write", lambda *args: update_status())

        # Description row
        if description:
            desc_label = ttk.Label(
                op_frame,
                text=description,
                font=("Arial", 9),
                foreground="gray"
            )
            desc_label.pack(fill=tk.X, pady=(5, 0))

        # Parameters preview
        params = operation.get('parameters', {})
        if params:
            params_text = self._format_parameters(params)
            params_label = ttk.Label(
                op_frame,
                text=f"Parameters: {params_text}",
                font=("Arial", 8),
                foreground="blue"
            )
            params_label.pack(fill=tk.X, pady=(2, 0))

        # Buttons row
        button_frame = ttk.Frame(op_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        if operation.get('editable', False):
            ttk.Button(
                button_frame,
                text="Edit",
                command=lambda: self._edit_operation(idx),
                width=10
            ).pack(side=tk.LEFT, padx=2)

        if not operation.get('required', False):
            ttk.Button(
                button_frame,
                text="Skip",
                command=lambda: self._skip_operation(idx, enabled_var),
                width=10
            ).pack(side=tk.LEFT, padx=2)

    def _format_parameters(self, params: Dict) -> str:
        """Format parameters for display"""
        items = []
        for key, value in params.items():
            if isinstance(value, list):
                if len(value) > 3:
                    value_str = f"{len(value)} items"
                else:
                    value_str = ', '.join(str(v) for v in value)
            elif isinstance(value, str) and len(value) > 30:
                value_str = value[:27] + "..."
            else:
                value_str = str(value)

            items.append(f"{key}={value_str}")

        return " | ".join(items[:3])  # Show first 3 params

    def _edit_operation(self, idx: int):
        """Open edit dialog for operation"""
        operation = self.operations[idx]
        current_params = self.operation_states[idx]['params']

        # Create edit dialog
        dialog = OperationEditDialog(
            self.dialog,
            operation,
            current_params,
            self.df
        )

        new_params = dialog.show()

        if new_params is not None:
            # Update parameters
            self.operation_states[idx]['params'] = new_params
            messagebox.showinfo("Success", "Operation parameters updated")

    def _skip_operation(self, idx: int, enabled_var: tk.BooleanVar):
        """Skip an operation"""
        enabled_var.set(False)
        self.operation_states[idx]['enabled'] = False

    def _create_buttons(self):
        """Create action buttons"""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # Count enabled operations
        enabled_count = sum(1 for state in self.operation_states.values() if state['enabled'])

        ttk.Label(
            button_frame,
            text=f"{enabled_count} of {len(self.operations)} operations enabled",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Run Selected",
            command=self._on_run_selected,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Run All",
            command=self._on_run_all,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

    def _on_run_all(self):
        """Enable all and run"""
        for idx in self.operation_states:
            self.operation_states[idx]['enabled'] = True
        self.result = "run_all"
        self.dialog.destroy()

    def _on_run_selected(self):
        """Run only selected operations"""
        enabled_count = sum(1 for state in self.operation_states.values() if state['enabled'])
        if enabled_count == 0:
            messagebox.showwarning("No Operations", "Please enable at least one operation.")
            return
        self.result = "run_selected"
        self.dialog.destroy()

    def _on_cancel(self):
        """Cancel"""
        self.result = None
        self.dialog.destroy()

    def get_selected_operations(self) -> List[Dict]:
        """Get list of enabled operations with updated parameters"""
        selected = []

        for idx, operation in enumerate(self.operations):
            state = self.operation_states[idx]

            if state['enabled']:
                # Create operation copy with updated params
                op_copy = operation.copy()
                op_copy['parameters'] = state['params']
                selected.append(op_copy)

        return selected


class OperationEditDialog:
    """
    Dialog for editing operation parameters

    Provides dynamic form based on operation parameters
    """

    def __init__(self, parent, operation: Dict, current_params: Dict, df: pd.DataFrame):
        """
        Initialize edit dialog

        Args:
            parent: Parent window
            operation: Operation configuration dict
            current_params: Current parameter values
            df: DataFrame (for column dropdowns, etc.)
        """
        self.parent = parent
        self.operation = operation
        self.current_params = current_params.copy()
        self.df = df
        self.result = None

        # Parameter widgets
        self.param_widgets = {}

    def show(self) -> Optional[Dict]:
        """
        Show dialog and return updated parameters

        Returns:
            Updated parameters dict or None if cancelled
        """
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Edit: {self.operation.get('operation_id', 'Operation')}")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self._create_widgets()

        self.dialog.wait_window()
        return self.result

    def _create_widgets(self):
        """Create dialog widgets"""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            header_frame,
            text=f"Edit Operation Parameters",
            font=("Arial", 12, "bold")
        ).pack(anchor=tk.W)

        ttk.Label(
            header_frame,
            text=self.operation.get('description', ''),
            font=("Arial", 9),
            foreground="gray"
        ).pack(anchor=tk.W)

        # Separator
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        # Parameters form
        form_frame = ttk.Frame(self.dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create parameter inputs
        row = 0
        for param_name, param_value in self.current_params.items():
            self._create_parameter_input(form_frame, row, param_name, param_value)
            row += 1

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Apply",
            command=self._on_apply,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

    def _create_parameter_input(self, parent, row: int, param_name: str, param_value):
        """Create input widget for parameter"""
        # Label
        ttk.Label(
            parent,
            text=f"{param_name}:",
            font=("Arial", 10)
        ).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)

        # Determine input type based on value
        if isinstance(param_value, bool):
            # Checkbox for boolean
            var = tk.BooleanVar(value=param_value)
            widget = ttk.Checkbutton(parent, variable=var)
            widget.grid(row=row, column=1, sticky=tk.W, pady=5)
            self.param_widgets[param_name] = var

        elif isinstance(param_value, list):
            # Entry for lists (comma-separated)
            var = tk.StringVar(value=', '.join(str(v) for v in param_value))
            widget = ttk.Entry(parent, textvariable=var, width=40)
            widget.grid(row=row, column=1, sticky=tk.W + tk.E, pady=5)
            self.param_widgets[param_name] = var

        elif param_name.endswith('_column') or param_name == 'column':
            # Dropdown for column selection
            var = tk.StringVar(value=str(param_value))
            widget = ttk.Combobox(
                parent,
                textvariable=var,
                values=list(self.df.columns),
                width=37
            )
            widget.grid(row=row, column=1, sticky=tk.W + tk.E, pady=5)
            self.param_widgets[param_name] = var

        elif param_name == 'columns':
            # List of columns - show multi-select or text entry
            var = tk.StringVar(value=', '.join(str(v) for v in param_value) if isinstance(param_value, list) else str(param_value))
            widget = ttk.Entry(parent, textvariable=var, width=40)
            widget.grid(row=row, column=1, sticky=tk.W + tk.E, pady=5)
            self.param_widgets[param_name] = var

        else:
            # Default: text entry
            var = tk.StringVar(value=str(param_value))
            widget = ttk.Entry(parent, textvariable=var, width=40)
            widget.grid(row=row, column=1, sticky=tk.W + tk.E, pady=5)
            self.param_widgets[param_name] = var

        parent.grid_columnconfigure(1, weight=1)

    def _on_apply(self):
        """Apply changes"""
        updated_params = {}

        for param_name, widget_var in self.param_widgets.items():
            original_value = self.current_params[param_name]

            if isinstance(original_value, bool):
                updated_params[param_name] = widget_var.get()
            elif isinstance(original_value, list):
                # Parse comma-separated list
                value_str = widget_var.get()
                if value_str.strip():
                    updated_params[param_name] = [v.strip() for v in value_str.split(',')]
                else:
                    updated_params[param_name] = []
            else:
                updated_params[param_name] = widget_var.get()

        self.result = updated_params
        self.dialog.destroy()

    def _on_cancel(self):
        """Cancel"""
        self.result = None
        self.dialog.destroy()


def show_preset_editor(parent, preset_data: Dict, df: pd.DataFrame) -> Optional[List[Dict]]:
    """
    Convenience function to show preset editor and get selected operations

    Args:
        parent: Parent window
        preset_data: Preset configuration
        df: DataFrame being processed

    Returns:
        List of selected operations with updated parameters, or None if cancelled
    """
    dialog = PresetEditorDialog(parent, preset_data, df)
    result = dialog.show()

    if result:
        return dialog.get_selected_operations()

    return None
