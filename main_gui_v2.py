#!/usr/bin/env python3
"""
Universal Excel Tool V2.1+ - Enhanced Edition with Smart UI
Features:
- Enhanced data preview with auto-fit columns and expandable view
- Smart column selection with dropdowns and search
- Simple/Advanced mode toggle
- AI Assistant integration  
- Accessible design for older users
- Smart Data Quality Analyzer
- 38+ operations
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
from pathlib import Path
import sys
import os

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from operations.registry import registry
from engine.executor import OperationExecutor
from engine.validator import Validator
from presets.preset_manager import PresetManager, Preset, OperationConfig
from ui.themes.accessible_theme import AccessibleTheme
from ai_assistant.claude_assistant import ClaudeAssistant
from utils.export_helper import ExportHelper
from analysis.data_quality_integration import DataQualityIntegration
from config_manager import ConfigManager
from datetime import datetime

# Import enhanced components
from enhanced_preview import EnhancedDataPreview
from smart_column_selector import ColumnSelector, MultiColumnSelector, SmartColumnDialog
from ui.sheet_selection_dialog import select_sheet_from_file


class UniversalExcelToolV2Enhanced:
    """Enhanced main application with improved UI and smart features"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Universal Excel Automation Tool v2.1+ - Professional Edition")
        self.root.geometry("1600x900")
        
        # Data
        self.df = None
        self.result_df = None
        self.removed_df = None  # Track removed rows for multi-sheet export
        self.current_file = None
        self.operation_queue = []

        # Sheet selection tracking
        self.current_sheet_name = None  # Selected sheet name
        self.available_sheets = []  # List of all sheets in current file
        
        # Mode: simple or advanced
        self.mode = tk.StringVar(value="simple")
        
        # AI Assistant
        self.ai_assistant = None
        self.api_key = tk.StringVar(value=os.environ.get('ANTHROPIC_API_KEY', ''))
        
        # Managers
        self.preset_manager = PresetManager()
        self.executor = OperationExecutor(progress_callback=self.on_progress)
        self.config_manager = ConfigManager()

        # Data Quality Integration
        self.dq_integration = DataQualityIntegration(self)

        # Email validation cache (session only)
        self.email_validation_cache = {}  # {normalized_email: validation_result_dict}
        
        # Apply accessible theme
        AccessibleTheme.apply_theme(self.root)
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create modern, accessible interface with enhanced preview"""
        
        # Top bar with mode toggle
        top_bar = ttk.Frame(self.root, style='Card.TFrame', height=80)
        top_bar.pack(fill='x', padx=10, pady=10)
        top_bar.pack_propagate(False)
        
        # Title
        ttk.Label(top_bar, text="🤖 Universal Excel Tool v2.1+",
                 style='Title.TLabel').pack(side='left', padx=20)
        
        # Mode toggle
        mode_frame = ttk.Frame(top_bar)
        mode_frame.pack(side='right', padx=20)
        
        ttk.Label(mode_frame, text="Mode:", style='Heading.TLabel').pack(side='left', padx=5)
        
        ttk.Radiobutton(mode_frame, text="🌟 Simple (Beginners)", 
                       variable=self.mode, value="simple",
                       command=self.on_mode_change,
                       style='TButton').pack(side='left', padx=5)
        
        ttk.Radiobutton(mode_frame, text="⚡ Advanced (Power Users)",
                       variable=self.mode, value="advanced", 
                       command=self.on_mode_change,
                       style='TButton').pack(side='left', padx=5)
        
        # Main toolbar with large buttons
        self.toolbar = ttk.Frame(self.root, style='Card.TFrame')
        self.toolbar.pack(fill='x', padx=10, pady=5)
        
        btn_frame = ttk.Frame(self.toolbar)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="📁 Open File", 
                  command=self.load_file,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="📋 Load Preset",
                  command=self.load_preset,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="▶️  RUN Operations",
                  command=self.run_operations,
                  style='Success.TButton').pack(side='left', padx=15)
        
        ttk.Button(btn_frame, text="💾 Save Results",
                  command=self.save_results,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="💾 Save as Preset",
                  command=self.save_preset,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        # Data Quality Analysis Button
        ttk.Button(
            btn_frame,
            text="🔍 Analyze Data Quality",
            command=self.analyze_data_quality,
            style='Primary.TButton'
        ).pack(side='left', padx=5)

        # Settings Button
        ttk.Button(
            btn_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            style='Primary.TButton'
        ).pack(side='left', padx=5)
        
        # Status bar with large text
        self.status_var = tk.StringVar(value="Ready - Load a file to begin")
        status = ttk.Label(self.root, textvariable=self.status_var,
                          style='Heading.TLabel', relief=tk.SUNKEN)
        status.pack(side='bottom', fill='x', pady=5)
        
        # Main content area - 3 column layout
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # LEFT: Operations Browser
        left_frame = ttk.Frame(main_paned, style='Card.TFrame')
        main_paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="🔧 Operations",
                 style='Heading.TLabel').pack(pady=10)
        
        # Search box
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        ttk.Entry(search_frame, textvariable=self.search_var,
                 style='TEntry', font=('Arial', 12)).pack(side='left', fill='x', expand=True, padx=5)
        
        # Operations tree
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.ops_tree = ttk.Treeview(tree_frame, show='tree')
        ops_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.ops_tree.yview)
        self.ops_tree.configure(yscrollcommand=ops_scroll.set)
        
        self.ops_tree.pack(side='left', fill='both', expand=True)
        ops_scroll.pack(side='right', fill='y')
        
        self.ops_tree.bind('<Double-1>', self.on_operation_select)
        
        self.load_operations()
        
        # CENTER: Queue and AI Assistant
        center_frame = ttk.Frame(main_paned, style='Card.TFrame')
        main_paned.add(center_frame, weight=1)
        
        # Notebook for Queue/AI
        center_notebook = ttk.Notebook(center_frame)
        center_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Queue tab
        queue_tab = ttk.Frame(center_notebook)
        center_notebook.add(queue_tab, text="📝 Operation Queue")
        
        ttk.Label(queue_tab, text="Your Workflow:",
                 style='Heading.TLabel').pack(pady=5)
        
        # Queue listbox
        queue_list_frame = ttk.Frame(queue_tab)
        queue_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.queue_listbox = tk.Listbox(queue_list_frame,
                                        font=('Arial', 11),
                                        selectmode=tk.SINGLE,
                                        height=15)
        queue_scroll = ttk.Scrollbar(queue_list_frame, orient='vertical',
                                     command=self.queue_listbox.yview)
        self.queue_listbox.configure(yscrollcommand=queue_scroll.set)
        
        self.queue_listbox.pack(side='left', fill='both', expand=True)
        queue_scroll.pack(side='right', fill='y')

        # Double-click to edit
        self.queue_listbox.bind('<Double-Button-1>', lambda e: self.edit_operation())

        # Queue buttons
        queue_btn_frame = ttk.Frame(queue_tab)
        queue_btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(queue_btn_frame, text="↑ Move Up",
                  command=self.move_up).pack(side='left', padx=2)
        ttk.Button(queue_btn_frame, text="↓ Move Down",
                  command=self.move_down).pack(side='left', padx=2)
        ttk.Button(queue_btn_frame, text="✏️ Edit",
                  command=self.edit_operation).pack(side='left', padx=2)
        ttk.Button(queue_btn_frame, text="🗑 Remove",
                  command=self.remove_operation).pack(side='left', padx=2)
        ttk.Button(queue_btn_frame, text="Clear All",
                  command=self.clear_queue).pack(side='left', padx=2)
        
        # AI Assistant tab
        ai_tab = ttk.Frame(center_notebook)
        center_notebook.add(ai_tab, text="🤖 AI Assistant")
        
        # API Key input
        api_frame = ttk.Frame(ai_tab)
        api_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(api_frame, text="Claude API Key:",
                 style='Heading.TLabel').pack(side='left', padx=5)
        ttk.Entry(api_frame, textvariable=self.api_key,
                 show='*', width=30).pack(side='left', padx=5)
        ttk.Button(api_frame, text="Connect",
                  command=self.init_ai,
                  style='Success.TButton').pack(side='left', padx=5)
        
        # Conversation history
        ttk.Label(ai_tab, text="Conversation:",
                 style='Heading.TLabel').pack(pady=5)
        
        conv_frame = ttk.Frame(ai_tab)
        conv_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.conversation_text = scrolledtext.ScrolledText(
            conv_frame,
            font=('Arial', 11),
            wrap=tk.WORD,
            height=15
        )
        self.conversation_text.pack(fill='both', expand=True)
        
        # User input
        input_frame = ttk.Frame(ai_tab)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(input_frame, text="Your message:",
                 style='Heading.TLabel').pack(anchor='w')
        
        self.ai_input = scrolledtext.ScrolledText(
            input_frame,
            font=('Arial', 12),
            wrap=tk.WORD,
            height=4
        )
        self.ai_input.pack(fill='x', pady=5)
        
        ai_btn_frame = ttk.Frame(input_frame)
        ai_btn_frame.pack(fill='x')
        
        ttk.Button(ai_btn_frame, text="Send to AI",
                  command=self.send_ai_message,
                  style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(ai_btn_frame, text="Clear Chat",
                  command=self.clear_ai_chat).pack(side='left', padx=5)
        
        # RIGHT: Enhanced Data Preview
        right_frame = ttk.Frame(main_paned, style='Card.TFrame')
        main_paned.add(right_frame, weight=2)
        
        # File info header
        header_frame = ttk.Frame(right_frame)
        header_frame.pack(fill='x', pady=5)

        # Left side: file info label
        self.file_info_var = tk.StringVar(value="No file loaded")
        ttk.Label(header_frame, textvariable=self.file_info_var,
                 font=('Arial', 11, 'bold')).pack(side='left', pady=5, padx=10)

        # Right side: Change Sheet button (initially hidden)
        self.change_sheet_btn = ttk.Button(
            header_frame,
            text="📑 Change Sheet",
            command=self.change_sheet,
            style='Primary.TButton'
        )
        # Button will be shown/hidden dynamically based on file type
        
        # ENHANCED PREVIEW - Replace old preview with new component
        self.enhanced_preview = EnhancedDataPreview(right_frame)
        self.enhanced_preview.pack(fill='both', expand=True, padx=5, pady=5)
    
    def load_operations(self):
        """Load operations into tree"""
        self.ops_tree.delete(*self.ops_tree.get_children())
        
        # Get categories based on mode
        categories = registry.get_all_categories()
        
        if self.mode.get() == "simple":
            # Filter to simple operations only
            simple_categories = ['Text', 'Data Matching', 'Cleaning', 'Math']
            categories = [c for c in categories if c in simple_categories]
        
        for category in categories:
            cat_id = self.ops_tree.insert('', 'end', text=f"📁 {category}", open=True)
            
            operations = registry.get_by_category(category)
            for op in operations:
                self.ops_tree.insert(cat_id, 'end',
                                   text=f"  ▶ {op.metadata.name}",
                                   tags=(op.metadata.id,))
    
    def on_mode_change(self):
        """Handle mode toggle"""
        mode = self.mode.get()
        self.status_var.set(f"Switched to {mode.upper()} mode")
        self.load_operations()
    
    def on_search(self, *args):
        """Filter operations by search"""
        query = self.search_var.get().lower()
        if not query:
            self.load_operations()
            return
        
        self.ops_tree.delete(*self.ops_tree.get_children())
        
        results = registry.search(query)
        if results:
            search_node = self.ops_tree.insert('', 'end',
                                              text=f"🔍 Search Results ({len(results)})",
                                              open=True)
            for op in results:
                self.ops_tree.insert(search_node, 'end',
                                   text=f"  ▶ {op.metadata.name}",
                                   tags=(op.metadata.id,))
    
    def on_operation_select(self, event):
        """Handle operation double-click"""
        selection = self.ops_tree.selection()
        if not selection:
            return
        
        item = self.ops_tree.item(selection[0])
        tags = item.get('tags', ())
        
        if tags:
            operation_id = tags[0]
            operation = registry.get_by_id(operation_id)
            if operation:
                self.add_operation_to_queue_smart(operation)
    
    def get_column_list_with_letters(self):
        """Get column list with Excel-style letters for dropdowns"""
        if self.df is None:
            return []
        
        columns = []
        for idx, col in enumerate(self.df.columns):
            letter = self._get_column_letter(idx)
            columns.append(f"{letter}: {col}")
        return columns
    
    def _get_column_letter(self, idx: int) -> str:
        """Convert column index to Excel-style letter"""
        result = ""
        while idx >= 0:
            result = chr(65 + (idx % 26)) + result
            idx = idx // 26 - 1
        return result
    
    def add_operation_to_queue_smart(self, operation):
        """
        Add operation with SMART column selection dialogs
        Uses enhanced UI components for better UX
        """

        # Get column list with letters
        columns = self.get_column_list_with_letters()

        # Check for special operation types
        if operation.metadata.id == 'data_reorder_columns':
            # Use specialized reorder columns dialog
            self._show_reorder_columns_dialog(operation, columns)
            return

        # Determine if operation needs special column selection
        needs_single_column = any(p.type == 'column' for p in operation.metadata.parameters)
        needs_multi_column = any(p.type == 'column_list' for p in operation.metadata.parameters)

        if needs_single_column and not needs_multi_column:
            # Use smart single column selector
            self._show_single_column_dialog(operation, columns)
        elif needs_multi_column:
            # Use smart multi-column selector
            self._show_multi_column_dialog(operation, columns)
        else:
            # Use standard parameter dialog for operations without column selection
            self._show_standard_parameter_dialog(operation)
    
    def _show_single_column_dialog(self, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Show dialog with smart single column selector"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title and description
        ttk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=550,
            font=('Arial', 11)
        ).pack(pady=(0, 5))

        ttk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Arial', 10),
            foreground='gray'
        ).pack(pady=(0, 20))

        param_widgets = {}

        # Process each parameter
        for param in operation.metadata.parameters:
            param_frame = ttk.Frame(main_frame)
            param_frame.pack(fill='x', pady=10)

            label_text = param.description
            if param.required:
                label_text += " *"

            # Get current value if in edit mode
            current_value = current_params.get(param.name) if current_params else None

            if param.type == 'column':
                # Use ColumnSelector
                selector = ColumnSelector(param_frame, columns, label_text)
                selector.pack(fill='x')
                # Pre-fill if editing
                if current_value:
                    selector.set_value(current_value)
                param_widgets[param.name] = selector

            elif param.type == 'text':
                ttk.Label(param_frame, text=label_text, font=('Arial', 11, 'bold')).pack(anchor='w')
                widget = ttk.Entry(param_frame, font=('Arial', 12))
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'number':
                ttk.Label(param_frame, text=label_text, font=('Arial', 11, 'bold')).pack(anchor='w')
                widget = ttk.Entry(param_frame, font=('Arial', 12))
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'boolean':
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else (param.default if param.default else False)
                var = tk.BooleanVar(value=value_to_set)
                widget = ttk.Checkbutton(param_frame, text=label_text, variable=var)
                widget.pack(anchor='w', pady=2)
                param_widgets[param.name] = var

            elif param.type == 'choice':
                ttk.Label(param_frame, text=label_text, font=('Arial', 11, 'bold')).pack(anchor='w')
                widget = ttk.Combobox(param_frame, values=param.choices,
                                     font=('Arial', 12), state='readonly')
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.set(value_to_set)
                elif param.choices:
                    widget.set(param.choices[0])
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget
        
        def on_add():
            params = {}
            for param in operation.metadata.parameters:
                widget = param_widgets.get(param.name)
                if widget:
                    if isinstance(widget, tk.BooleanVar):
                        params[param.name] = widget.get()
                    elif isinstance(widget, ColumnSelector):
                        params[param.name] = widget.get_value()
                    elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                        value = widget.get()
                        if param.type == 'number':
                            try:
                                value = float(value)
                            except:
                                value = 0
                        params[param.name] = value

            if edit_mode:
                # Update existing operation in queue
                self.operation_queue[edit_index] = {
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': self.operation_queue[edit_index]['enabled']  # Preserve enabled state
                }
                self.status_var.set(f"Updated: {operation.metadata.name}")
            else:
                # Add new operation to queue
                self.operation_queue.append({
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': True
                })
                self.status_var.set(f"Added: {operation.metadata.name}")

            self.refresh_queue_display()
            dialog.destroy()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(20, 0))

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        button_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=button_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)
    
    def _show_multi_column_dialog(self, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Show dialog with smart multi-column selector"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x600")
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title and description
        ttk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=550,
            font=('Arial', 11)
        ).pack(pady=(0, 5))

        ttk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Arial', 10),
            foreground='gray'
        ).pack(pady=(0, 20))

        param_widgets = {}

        # Process each parameter
        for param in operation.metadata.parameters:
            param_frame = ttk.Frame(main_frame)
            param_frame.pack(fill='both', expand=(param.type == 'column_list'), pady=10)

            label_text = param.description
            if param.required:
                label_text += " *"

            # Get current value if in edit mode
            current_value = current_params.get(param.name) if current_params else None

            if param.type == 'column_list':
                # Use MultiColumnSelector
                selector = MultiColumnSelector(param_frame, columns, label_text)
                selector.pack(fill='both', expand=True)
                # Pre-fill if editing
                if current_value:
                    selector.set_selected_columns(current_value)
                param_widgets[param.name] = selector

            elif param.type == 'column':
                # Single column selector
                selector = ColumnSelector(param_frame, columns, label_text)
                selector.pack(fill='x')
                # Pre-fill if editing
                if current_value:
                    selector.set_value(current_value)
                param_widgets[param.name] = selector

            elif param.type == 'text':
                ttk.Label(param_frame, text=label_text, font=('Arial', 11, 'bold')).pack(anchor='w')
                widget = ttk.Entry(param_frame, font=('Arial', 12))
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'boolean':
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else (param.default if param.default else False)
                var = tk.BooleanVar(value=value_to_set)
                widget = ttk.Checkbutton(param_frame, text=label_text, variable=var)
                widget.pack(anchor='w', pady=2)
                param_widgets[param.name] = var

            elif param.type == 'choice':
                ttk.Label(param_frame, text=label_text, font=('Arial', 11, 'bold')).pack(anchor='w')
                widget = ttk.Combobox(param_frame, values=param.choices,
                                     font=('Arial', 12), state='readonly')
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.set(value_to_set)
                elif param.choices:
                    widget.set(param.choices[0])
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget

        def on_add():
            params = {}
            for param in operation.metadata.parameters:
                widget = param_widgets.get(param.name)
                if widget:
                    if isinstance(widget, MultiColumnSelector):
                        params[param.name] = widget.get_selected_columns()
                    elif isinstance(widget, ColumnSelector):
                        params[param.name] = widget.get_value()
                    elif isinstance(widget, tk.BooleanVar):
                        params[param.name] = widget.get()
                    elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                        value = widget.get()
                        if param.type == 'number':
                            try:
                                value = float(value)
                            except:
                                value = 0
                        params[param.name] = value

            if edit_mode:
                # Update existing operation in queue
                self.operation_queue[edit_index] = {
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': self.operation_queue[edit_index]['enabled']  # Preserve enabled state
                }
                self.status_var.set(f"Updated: {operation.metadata.name}")
            else:
                # Add new operation to queue
                self.operation_queue.append({
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': True
                })
                self.status_var.set(f"Added: {operation.metadata.name}")

            self.refresh_queue_display()
            dialog.destroy()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(20, 0))

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        button_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=button_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)

    def _show_standard_parameter_dialog(self, operation, edit_mode=False, edit_index=None, current_params=None):
        """Standard parameter dialog for operations without column selection"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title and description
        ttk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=550,
            font=('Arial', 11)
        ).pack(pady=(0, 5))

        ttk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Arial', 10),
            foreground='gray'
        ).pack(pady=(0, 20))

        param_widgets = {}

        for param in operation.metadata.parameters:
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=8)

            label_text = param.description
            if param.required:
                label_text += " *"

            ttk.Label(frame, text=label_text, font=('Arial', 11, 'bold')).pack(anchor='w')

            # Get current value if in edit mode
            current_value = current_params.get(param.name) if current_params else None

            if param.type == 'text':
                widget = ttk.Entry(frame, font=('Arial', 12))
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'number':
                widget = ttk.Entry(frame, font=('Arial', 12))
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.insert(0, str(value_to_set))
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'boolean':
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else (param.default if param.default else False)
                var = tk.BooleanVar(value=value_to_set)
                widget = ttk.Checkbutton(frame, text="Yes", variable=var)
                widget.pack(anchor='w', pady=2)
                param_widgets[param.name] = var

            elif param.type == 'choice':
                widget = ttk.Combobox(frame, values=param.choices,
                                     font=('Arial', 12), state='readonly')
                # Pre-fill from current_params or use default
                value_to_set = current_value if current_value is not None else param.default
                if value_to_set:
                    widget.set(value_to_set)
                elif param.choices:
                    widget.set(param.choices[0])
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget

            elif param.type == 'file':
                widget = ttk.Entry(frame, font=('Arial', 12))
                # Pre-fill from current_params
                if current_value:
                    widget.insert(0, str(current_value))
                widget.pack(fill='x', pady=2)
                param_widgets[param.name] = widget
        
        def on_add():
            params = {}
            for param in operation.metadata.parameters:
                widget = param_widgets.get(param.name)
                if widget:
                    if isinstance(widget, tk.BooleanVar):
                        params[param.name] = widget.get()
                    elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                        value = widget.get()
                        if param.type == 'number':
                            try:
                                value = float(value)
                            except:
                                value = 0
                        params[param.name] = value

            if edit_mode:
                # Update existing operation in queue
                self.operation_queue[edit_index] = {
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': self.operation_queue[edit_index]['enabled']  # Preserve enabled state
                }
                self.status_var.set(f"Updated: {operation.metadata.name}")
            else:
                # Add new operation to queue
                self.operation_queue.append({
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': True
                })
                self.status_var.set(f"Added: {operation.metadata.name}")

            self.refresh_queue_display()
            dialog.destroy()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(20, 0))

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        button_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=button_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)

    def _show_reorder_columns_dialog(self, operation, columns):
        """Show specialized dialog for reordering columns"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reorder Columns")
        dialog.geometry("700x650")
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title and description
        ttk.Label(
            main_frame,
            text="Reorder Columns",
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text="Arrange columns in desired order. Use arrow buttons to move selected column up/down.",
            wraplength=650,
            font=('Arial', 11)
        ).pack(pady=(0, 10))

        # Current columns section
        ttk.Label(
            main_frame,
            text="Current Columns (drag or use arrows to reorder):",
            font=('Arial', 11, 'bold')
        ).pack(anchor='w', pady=(10, 5))

        # Create frame for listbox and buttons
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=5)

        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        column_listbox = tk.Listbox(
            list_frame,
            font=('Consolas', 11),
            height=15,
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set
        )
        column_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=column_listbox.yview)

        # Populate with current columns
        for col_info in columns:
            column_listbox.insert(tk.END, col_info)

        # Arrow buttons frame
        arrow_frame = ttk.Frame(main_frame)
        arrow_frame.pack(fill='x', pady=10)

        def move_up():
            selection = column_listbox.curselection()
            if selection and selection[0] > 0:
                idx = selection[0]
                item = column_listbox.get(idx)
                column_listbox.delete(idx)
                column_listbox.insert(idx - 1, item)
                column_listbox.selection_set(idx - 1)

        def move_down():
            selection = column_listbox.curselection()
            if selection and selection[0] < column_listbox.size() - 1:
                idx = selection[0]
                item = column_listbox.get(idx)
                column_listbox.delete(idx)
                column_listbox.insert(idx + 1, item)
                column_listbox.selection_set(idx + 1)

        def move_to_top():
            selection = column_listbox.curselection()
            if selection and selection[0] > 0:
                idx = selection[0]
                item = column_listbox.get(idx)
                column_listbox.delete(idx)
                column_listbox.insert(0, item)
                column_listbox.selection_set(0)

        def move_to_bottom():
            selection = column_listbox.curselection()
            if selection and selection[0] < column_listbox.size() - 1:
                idx = selection[0]
                item = column_listbox.get(idx)
                column_listbox.delete(idx)
                column_listbox.insert(tk.END, item)
                column_listbox.selection_set(column_listbox.size() - 1)

        ttk.Button(arrow_frame, text="⬆ Move Up", command=move_up, width=15).pack(side='left', padx=5)
        ttk.Button(arrow_frame, text="⬇ Move Down", command=move_down, width=15).pack(side='left', padx=5)
        ttk.Button(arrow_frame, text="⤒ Move to Top", command=move_to_top, width=15).pack(side='left', padx=5)
        ttk.Button(arrow_frame, text="⤓ Move to Bottom", command=move_to_bottom, width=15).pack(side='left', padx=5)

        # Keep unlisted checkbox
        keep_unlisted_var = tk.BooleanVar(value=False)
        check_frame = ttk.Frame(main_frame)
        check_frame.pack(fill='x', pady=10)

        ttk.Checkbutton(
            check_frame,
            text="Keep columns not in the reordered list (append at end)",
            variable=keep_unlisted_var
        ).pack(anchor='w')

        ttk.Label(
            check_frame,
            text="If unchecked, only the columns in the list above will be kept.",
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor='w', padx=20)

        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Final Column Order Preview", padding=10)
        preview_frame.pack(fill='x', pady=10)

        preview_label = ttk.Label(
            preview_frame,
            text="",
            wraplength=640,
            font=('Consolas', 9),
            foreground='blue'
        )
        preview_label.pack()

        def update_preview():
            # Get current order from listbox
            ordered_cols = []
            for i in range(column_listbox.size()):
                col_text = column_listbox.get(i)
                # Extract column name (format: "A: Column Name")
                if ':' in col_text:
                    col_name = col_text.split(':', 1)[1].strip()
                    ordered_cols.append(col_name)

            if keep_unlisted_var.get():
                preview_text = f"Order: {', '.join(ordered_cols)}\n+ any other columns not listed"
            else:
                preview_text = f"Final columns: {', '.join(ordered_cols)}"

            preview_label.config(text=preview_text)

        # Update preview when selection changes or checkbox toggled
        column_listbox.bind('<<ListboxSelect>>', lambda e: update_preview())
        keep_unlisted_var.trace('w', lambda *args: update_preview())
        update_preview()  # Initial preview

        def on_add():
            # Extract column names in order
            column_order = []
            for i in range(column_listbox.size()):
                col_text = column_listbox.get(i)
                # Extract column name (format: "A: Column Name")
                if ':' in col_text:
                    col_name = col_text.split(':', 1)[1].strip()
                    column_order.append(col_name)

            if not column_order:
                messagebox.showwarning("Warning", "Please arrange at least one column")
                return

            params = {
                'column_order': column_order,
                'keep_unlisted': keep_unlisted_var.get()
            }

            # Add to queue
            self.operation_queue.append({
                'operation_id': operation.metadata.id,
                'name': operation.metadata.name,
                'parameters': params,
                'enabled': True
            })

            self.refresh_queue_display()
            self.status_var.set(f"Added: Reorder Columns ({len(column_order)} columns)")
            dialog.destroy()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✓ Add to Queue", command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)

    def refresh_queue_display(self):
        """Refresh queue listbox"""
        self.queue_listbox.delete(0, tk.END)
        for i, op in enumerate(self.operation_queue):
            enabled = "☑" if op['enabled'] else "☐"
            self.queue_listbox.insert(tk.END, f"{i+1}. {enabled} {op['name']}")
    
    def move_up(self):
        """Move selected operation up"""
        selection = self.queue_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            self.operation_queue[idx], self.operation_queue[idx-1] = \
                self.operation_queue[idx-1], self.operation_queue[idx]
            self.refresh_queue_display()
            self.queue_listbox.selection_set(idx-1)
    
    def move_down(self):
        """Move selected operation down"""
        selection = self.queue_listbox.curselection()
        if selection and selection[0] < len(self.operation_queue) - 1:
            idx = selection[0]
            self.operation_queue[idx], self.operation_queue[idx+1] = \
                self.operation_queue[idx+1], self.operation_queue[idx]
            self.refresh_queue_display()
            self.queue_listbox.selection_set(idx+1)
    
    def remove_operation(self):
        """Remove selected operation"""
        selection = self.queue_listbox.curselection()
        if selection:
            del self.operation_queue[selection[0]]
            self.refresh_queue_display()

    def edit_operation(self):
        """Edit selected operation"""
        selection = self.queue_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an operation to edit")
            return

        idx = selection[0]
        op_config = self.operation_queue[idx]

        # Get the operation from registry
        operation = registry.get_by_id(op_config['operation_id'])
        if not operation:
            messagebox.showerror("Error", f"Operation {op_config['operation_id']} not found")
            return

        # Get current columns from dataframe
        columns = list(self.df.columns) if self.df is not None else []

        # Determine which dialog to show based on parameter types
        needs_single_column = any(p.type == 'column' for p in operation.metadata.parameters)
        needs_multi_column = any(p.type == 'column_list' for p in operation.metadata.parameters)

        # Show appropriate dialog with edit mode enabled
        if needs_single_column and not needs_multi_column:
            self._show_single_column_dialog(operation, columns, edit_mode=True, edit_index=idx, current_params=op_config['parameters'])
        elif needs_multi_column:
            self._show_multi_column_dialog(operation, columns, edit_mode=True, edit_index=idx, current_params=op_config['parameters'])
        else:
            self._show_standard_parameter_dialog(operation, edit_mode=True, edit_index=idx, current_params=op_config['parameters'])

    def clear_queue(self):
        """Clear all operations"""
        if messagebox.askyesno("Confirm", "Clear all operations from queue?"):
            self.operation_queue = []
            self.refresh_queue_display()
    
    def change_sheet(self):
        """Allow user to change the active sheet for the current Excel file"""
        if not self.current_file or not self.available_sheets:
            messagebox.showwarning("Warning", "No Excel file with multiple sheets loaded")
            return

        if len(self.available_sheets) <= 1:
            messagebox.showinfo("Info", "This file only has one sheet")
            return

        # Show sheet selection dialog with current sheet highlighted
        from ui.sheet_selection_dialog import SheetSelectionDialog
        file_name = Path(self.current_file).name
        dialog = SheetSelectionDialog(self.root, self.available_sheets, file_name)

        # Pre-select current sheet if known
        if self.current_sheet_name:
            try:
                current_index = self.available_sheets.index(self.current_sheet_name)
                dialog.sheet_listbox.selection_clear(0, tk.END)
                dialog.sheet_listbox.selection_set(current_index)
                dialog.sheet_listbox.see(current_index)
            except (ValueError, AttributeError):
                pass

        selected_sheet = dialog.show()

        if selected_sheet and selected_sheet != self.current_sheet_name:
            # Load new sheet
            try:
                print(f"DEBUG: Changing sheet from {self.current_sheet_name} to {selected_sheet}")
                self.df = pd.read_excel(self.current_file, sheet_name=selected_sheet)
                self.current_sheet_name = selected_sheet

                # Clear result data when switching sheets
                self.result_df = None
                self.removed_df = None

                # Update file info
                self.file_info_var.set(
                    f"📁 {Path(self.current_file).name} | Sheet: {selected_sheet} • {len(self.df):,} rows × {len(self.df.columns)} columns"
                )

                # Refresh preview
                self.enhanced_preview.load_dataframe(self.df, is_result=False)

                self.status_var.set(f"Switched to sheet: {selected_sheet}")
                messagebox.showinfo("Sheet Changed", f"Now viewing sheet: {selected_sheet}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load sheet:\n{str(e)}")

    def load_file(self):
        """Load data file with enhanced preview and sheet selection"""
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not filename:
            return

        try:
            # Reset sheet tracking
            self.current_sheet_name = None
            self.available_sheets = []

            # Hide change sheet button by default
            self.change_sheet_btn.pack_forget()

            # Handle CSV files (no sheet selection needed)
            if filename.endswith('.csv'):
                self.df = pd.read_csv(filename)
                self.current_file = filename

                # Update file info (no sheet name for CSV)
                self.file_info_var.set(
                    f"📁 {Path(filename).name} • {len(self.df):,} rows × {len(self.df.columns)} columns"
                )

            # Handle Excel files (with sheet selection)
            else:
                # Detect available sheets
                print(f"DEBUG: Loading Excel file: {filename}")  # Debug logging
                excel_file = pd.ExcelFile(filename)
                sheet_names = excel_file.sheet_names
                self.available_sheets = sheet_names
                print(f"DEBUG: Detected {len(sheet_names)} sheets: {sheet_names}")  # Debug logging

                # If only one sheet, load it automatically
                if len(sheet_names) == 1:
                    selected_sheet = sheet_names[0]
                    print(f"DEBUG: Single sheet detected, auto-loading: {selected_sheet}")  # Debug
                    self.current_sheet_name = selected_sheet
                    self.df = pd.read_excel(filename, sheet_name=selected_sheet)
                    self.current_file = filename

                    # Update file info with sheet name
                    self.file_info_var.set(
                        f"📁 {Path(filename).name} | Sheet: {selected_sheet} • {len(self.df):,} rows × {len(self.df.columns)} columns"
                    )
                    # No need for change sheet button with single sheet

                # Multiple sheets - show selection dialog
                else:
                    print(f"DEBUG: Multiple sheets detected, showing dialog...")  # Debug logging
                    selected_sheet = select_sheet_from_file(self.root, filename, sheet_names)
                    print(f"DEBUG: Dialog returned: {selected_sheet}")  # Debug logging

                    # User cancelled sheet selection
                    if selected_sheet is None:
                        self.status_var.set("File load cancelled - no sheet selected")
                        print("DEBUG: User cancelled sheet selection")  # Debug
                        return

                    # Load selected sheet
                    print(f"DEBUG: Loading selected sheet: {selected_sheet}")  # Debug
                    self.current_sheet_name = selected_sheet
                    self.df = pd.read_excel(filename, sheet_name=selected_sheet)
                    self.current_file = filename

                    # Update file info with sheet name
                    self.file_info_var.set(
                        f"📁 {Path(filename).name} | Sheet: {selected_sheet} • {len(self.df):,} rows × {len(self.df.columns)} columns"
                    )

                    # Show "Change Sheet" button for multi-sheet files
                    self.change_sheet_btn.pack(side='right', padx=10)

            # Use enhanced preview
            self.enhanced_preview.load_dataframe(self.df, is_result=False)

            # Build success message
            success_msg = f"Loaded {len(self.df):,} records with {len(self.df.columns)} columns"
            if self.current_sheet_name:
                success_msg += f"\n\nSheet: {self.current_sheet_name}"
                if len(self.available_sheets) > 1:
                    success_msg += f" (of {len(self.available_sheets)} sheets)"

            self.status_var.set(f"Loaded {len(self.df):,} records successfully")

            messagebox.showinfo("Success", success_msg)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def run_operations(self):
        """Execute all queued operations"""
        if self.df is None:
            messagebox.showwarning("Warning", "Please load a file first")
            return
        
        if not self.operation_queue:
            messagebox.showwarning("Warning", "No operations in queue")
            return
        
        if not messagebox.askyesno("Confirm",
                                  f"Run {len(self.operation_queue)} operations on {len(self.df):,} rows?"):
            return
        
        try:
            # Validate
            is_valid, errors = Validator.validate_queue(self.df, self.operation_queue)
            if not is_valid:
                error_msg = "\n".join(errors)
                messagebox.showerror("Validation Error",
                                   f"Cannot execute:\n{error_msg}")
                return
            
            # Execute
            self.status_var.set("Executing operations...")
            self.root.update()

            # Use execute_queue_with_tracking to capture removed rows
            self.result_df, self.removed_df = self.executor.execute_queue_with_tracking(self.df, self.operation_queue)

            # Display in enhanced preview
            self.enhanced_preview.load_dataframe(self.result_df, is_result=True)

            # Build success message with removed rows info
            removed_count = len(self.removed_df) if self.removed_df is not None and not self.removed_df.empty else 0
            success_msg = f"Operations completed!\n\nInput: {len(self.df):,} rows\nOutput: {len(self.result_df):,} rows"
            if removed_count > 0:
                success_msg += f"\nRemoved: {removed_count:,} rows"

            self.status_var.set(f"✅ Complete! {len(self.result_df):,} rows in results")

            messagebox.showinfo("Success", success_msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Execution failed:\n{str(e)}")
    
    def on_progress(self, current, total, operation_name):
        """Progress callback"""
        self.status_var.set(f"Executing {current}/{total}: {operation_name}")
        self.root.update()
    
    def save_results(self):
        """Save results to file with multi-sheet export"""
        if self.result_df is None:
            messagebox.showwarning("Warning", "No results to save")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv")
            ]
        )

        if not filename:
            return

        try:
            if filename.endswith('.csv'):
                # CSV can only save one sheet - save results only
                ExportHelper.export_to_csv(self.result_df, filename)
                success_msg = f"Results saved to:\n{filename}\n\nNote: CSV format only saves Results sheet."
            else:
                # Excel - export multi-sheet workbook
                sheets = {}

                # Sheet 1: Original data
                if self.df is not None:
                    sheets['Original'] = self.df

                # Sheet 2: Results
                sheets['Results'] = self.result_df

                # Sheet 3: Removed (if any rows were removed)
                if self.removed_df is not None and not self.removed_df.empty:
                    sheets['Removed'] = self.removed_df

                ExportHelper.export_multiple_sheets(sheets, filename)

                # Build success message
                sheet_info = []
                if 'Original' in sheets:
                    sheet_info.append(f"• Original: {len(sheets['Original']):,} rows")
                sheet_info.append(f"• Results: {len(sheets['Results']):,} rows")
                if 'Removed' in sheets:
                    sheet_info.append(f"• Removed: {len(sheets['Removed']):,} rows")

                success_msg = f"Workbook saved to:\n{filename}\n\nSheets:\n" + "\n".join(sheet_info)

            messagebox.showinfo("Success", success_msg)
            self.status_var.set(f"Saved to {Path(filename).name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{str(e)}")
    
    def load_preset(self):
        """Load a preset"""
        presets = self.preset_manager.list_presets()
        
        if not presets:
            messagebox.showinfo("Info", "No presets available")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Preset")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select a Preset:",
                 style='Heading.TLabel').pack(pady=10)
        
        listbox = tk.Listbox(dialog, font=('Arial', 11))
        listbox.pack(fill='both', expand=True, padx=20, pady=10)
        
        preset_map = {}
        for preset in presets:
            icon = "🔒" if preset.is_system else "📝"
            text = f"{icon} {preset.name} - {preset.description}"
            listbox.insert(tk.END, text)
            preset_map[listbox.size()-1] = preset
        
        def on_load():
            selection = listbox.curselection()
            if selection:
                preset = preset_map[selection[0]]
                self.operation_queue = []
                
                for op_config in preset.operations:
                    operation = registry.get_by_id(op_config.operation_id)
                    if operation:
                        self.operation_queue.append({
                            'operation_id': op_config.operation_id,
                            'name': operation.metadata.name,
                            'parameters': op_config.parameters,
                            'enabled': op_config.enabled
                        })
                
                self.refresh_queue_display()
                self.status_var.set(f"Loaded preset: {preset.name}")
                dialog.destroy()
                messagebox.showinfo("Success",
                                  f"Loaded '{preset.name}' with {len(preset.operations)} operations")
        
        ttk.Button(dialog, text="Load",
                  command=on_load,
                  style='Primary.TButton').pack(pady=10)
    
    def save_preset(self):
        """Save current queue as preset"""
        if not self.operation_queue:
            messagebox.showwarning("Warning", "No operations to save")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Preset")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Preset Name:",
                 style='Heading.TLabel').pack(pady=10, padx=20)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var,
                 font=('Arial', 12), width=40).pack(padx=20, pady=5)
        
        ttk.Label(dialog, text="Description:",
                 style='Heading.TLabel').pack(pady=10, padx=20)
        desc_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=desc_var,
                 font=('Arial', 12), width=40).pack(padx=20, pady=5)
        
        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Please enter a name")
                return

            preset_id = name.lower().replace(' ', '_')

            # Check if preset already exists
            existing_preset = self.preset_manager.load_preset(preset_id)

            if existing_preset:
                # Preset exists - ask for confirmation to overwrite
                response = messagebox.askyesnocancel(
                    "Preset Exists",
                    f"A preset named '{existing_preset.name}' already exists.\n\n"
                    f"Do you want to overwrite it?\n\n"
                    f"• Yes = Overwrite existing preset\n"
                    f"• No = Enter a different name\n"
                    f"• Cancel = Cancel save",
                    icon='warning'
                )

                if response is None:  # Cancel
                    return
                elif response is False:  # No - allow user to change name
                    name_var.set("")
                    messagebox.showinfo("Info", "Please enter a different preset name")
                    return
                # else: response is True - continue with overwrite

            operations = [
                OperationConfig(
                    operation_id=op['operation_id'],
                    parameters=op['parameters'],
                    order=i,
                    enabled=op.get('enabled', True)
                )
                for i, op in enumerate(self.operation_queue)
            ]

            # Create preset with updated timestamp if overwriting
            preset = Preset(
                id=preset_id,
                name=name,
                description=desc_var.get(),
                category="Custom",
                operations=operations,
                created_at=existing_preset.created_at if existing_preset else datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            try:
                self.preset_manager.save_preset(preset)
                if existing_preset:
                    messagebox.showinfo("Success", f"Preset '{name}' updated successfully!")
                else:
                    messagebox.showinfo("Success", f"Preset '{name}' saved!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{str(e)}")
        
        ttk.Button(dialog, text="Save",
                  command=save,
                  style='Success.TButton').pack(pady=15)
    
    def init_ai(self):
        """Initialize AI assistant"""
        api_key = self.api_key.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter your Claude API key")
            return
        
        try:
            self.ai_assistant = ClaudeAssistant(api_key)
            self.add_to_conversation("System", "✅ AI Assistant connected! Ask me anything about your data.")
            messagebox.showinfo("Success", "AI Assistant is ready!")
            self.status_var.set("AI Assistant connected")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect:\n{str(e)}")
    
    def send_ai_message(self):
        """Send message to AI"""
        if not self.ai_assistant:
            messagebox.showwarning("Warning", "Please connect to AI first")
            return
        
        message = self.ai_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        self.add_to_conversation("You", message)
        self.ai_input.delete("1.0", tk.END)
        
        # Get data context
        df_info = None
        if self.df is not None:
            df_info = {
                'rows': len(self.df),
                'columns': list(self.df.columns)
            }
        
        try:
            response = self.ai_assistant.chat(message, df_info)
            self.add_to_conversation("AI", response)
        except Exception as e:
            self.add_to_conversation("Error", str(e))
    
    def add_to_conversation(self, speaker, message):
        """Add message to conversation display"""
        self.conversation_text.insert(tk.END, f"\n{'='*50}\n")
        self.conversation_text.insert(tk.END, f"{speaker}:\n", "bold")
        self.conversation_text.insert(tk.END, f"{message}\n")
        self.conversation_text.see(tk.END)
        self.conversation_text.tag_configure("bold", font=('Arial', 11, 'bold'))
    
    def clear_ai_chat(self):
        """Clear AI conversation"""
        if self.ai_assistant:
            self.ai_assistant.clear_conversation()
        self.conversation_text.delete("1.0", tk.END)
        self.add_to_conversation("System", "Conversation cleared. Starting fresh!")
    
    def analyze_data_quality(self):
        """Analyze data quality and suggest cleaning operations"""
        self.dq_integration.analyze_data()

    def open_settings(self):
        """Open settings dialog"""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.root, self.config_manager)
        dialog.show()


def main():
    root = tk.Tk()
    app = UniversalExcelToolV2Enhanced(root)
    root.mainloop()


if __name__ == "__main__":
    main()