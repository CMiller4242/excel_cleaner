#!/usr/bin/env python3
"""
Universal Excel Tool V2.1+ - Office 365 Redesign
Major UI overhaul to make data preview the primary focus

Changes from original:
- Data preview now occupies 60-70% of screen (was ~30%)
- Workflow queue moved to bottom panel (was center)
- Operations sidebar is collapsible (was always visible left panel)
- Office 365 color scheme and spacing
- Card-style operation queue
- Ribbon-style navigation tabs
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
from pathlib import Path
import sys
import os

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Import existing components
from operations.registry import registry
from engine.executor import OperationExecutor
from engine.validator import Validator
from presets.preset_manager import PresetManager, Preset, OperationConfig
from ui.themes.accessible_theme import AccessibleTheme
from ai_assistant.claude_assistant import ClaudeAssistant
from utils.export_helper import ExportHelper
from enhanced_preview import EnhancedDataPreview
from smart_column_selector import ColumnSelector, MultiColumnSelector
from analysis.data_quality_integration import DataQualityIntegration
from excel_ribbon import ExcelRibbon, FormulaBar, ExcelStatusBar
from datetime import datetime


class UniversalExcelToolV2Office365:
    """Office 365-style application with data-first layout"""

    def __init__(self, root):
        self.root = root
        self.root.title("🔷 Universal Excel Tool - Professional Edition")
        self.root.geometry("1600x900")
        self.root.minsize(1200, 800)

        # Data
        self.df = None
        self.result_df = None
        self.removed_df = None
        self.current_file = None
        self.operation_queue = []

        # Mode: simple or advanced
        self.mode = tk.StringVar(value="simple")

        # AI Assistant
        self.ai_assistant = None
        self.api_key = tk.StringVar(value=os.environ.get('ANTHROPIC_API_KEY', ''))

        # Managers
        self.preset_manager = PresetManager()
        self.executor = OperationExecutor(progress_callback=self.on_progress)

        # Data Quality Integration
        self.dq_integration = DataQualityIntegration(self)

        # UI state
        self.operations_visible = False
        self.operations_sidebar = None
        self.queue_collapsed = False

        # Apply theme and create UI
        AccessibleTheme.apply_theme(self.root)
        self.setup_office365_theme()
        self.create_widgets()

    def setup_office365_theme(self):
        """Apply Office 365 color scheme"""
        style = ttk.Style()

        # Office 365 Colors
        colors = {
            'primary_blue': '#0078D4',
            'success_green': '#107C10',
            'bg_light': '#F3F2F1',
            'white': '#FFFFFF',
            'text_dark': '#323130',
            'text_gray': '#666666',
            'border': '#E1DFDD',
        }

        # Header style
        style.configure('Header.TFrame', background=colors['bg_light'])
        style.configure('HeaderTitle.TLabel',
                       font=('Segoe UI', 14, 'bold'),
                       foreground=colors['text_dark'],
                       background=colors['bg_light'])
        style.configure('HeaderText.TLabel',
                       font=('Segoe UI', 11),
                       foreground=colors['text_gray'],
                       background=colors['bg_light'])

        # Ribbon styles
        style.configure('Ribbon.TFrame', background=colors['white'])
        style.configure('RibbonTab.TButton',
                       font=('Segoe UI', 11),
                       padding=(10, 5))

        # Status bar
        style.configure('Status.TLabel',
                       font=('Segoe UI', 11),
                       foreground=colors['text_dark'],
                       background=colors['bg_light'],
                       padding=5)

        # Card style
        style.configure('Card.TFrame', background=colors['white'])

        # Queue card style
        style.configure('QueueCard.TFrame',
                       background=colors['white'],
                       relief=tk.RAISED,
                       borderwidth=1)

    def create_widgets(self):
        """Create Excel 365-style interface with compact ribbon and data-first layout"""

        # ==================== COMPACT HEADER (30px) ====================
        header = ttk.Frame(self.root, style='Header.TFrame', height=30)
        header.pack(fill='x')
        header.pack_propagate(False)

        # App name (smaller)
        ttk.Label(header, text="🔷 Universal Excel Tool",
                 font=('Segoe UI', 11, 'bold'),
                 foreground='#0078D4',
                 background='#F3F2F1').pack(side='left', padx=15)

        # Mode selector (compact)
        mode_frame = ttk.Frame(header, style='Header.TFrame')
        mode_frame.pack(side='right', padx=15)

        ttk.Label(mode_frame, text="Mode:",
                 font=('Segoe UI', 9),
                 foreground='#666666',
                 background='#F3F2F1').pack(side='left', padx=5)

        mode_menu = ttk.Combobox(mode_frame, textvariable=self.mode,
                                 values=["simple", "advanced"],
                                 state='readonly', width=10,
                                 font=('Segoe UI', 9))
        mode_menu.pack(side='left', padx=5)
        mode_menu.bind('<<ComboboxSelected>>', lambda e: self.on_mode_change())

        # ==================== EXCEL RIBBON (120px) ====================
        self.excel_ribbon = ExcelRibbon(self.root, app_ref=self)
        self.excel_ribbon.pack(fill='x')

        # ==================== FORMULA BAR (30px) ====================
        self.formula_bar = FormulaBar(self.root)
        self.formula_bar.pack(fill='x', pady=(2, 0))

        # ==================== EXCEL STATUS BAR (bottom, 25px) ====================
        self.excel_status_bar = ExcelStatusBar(self.root)
        self.excel_status_bar.pack(side='bottom', fill='x')

        # Update status bar with initial mode
        self.excel_status_bar.update_mode(self.mode.get())

        # Keep reference to status var for backward compatibility
        self.status_var = self.excel_status_bar.status_var

        # ==================== MAIN LAYOUT ====================
        # Vertical PanedWindow: Data Preview (70%) + Workflow Queue (30%)
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_paned.pack(fill='both', expand=True, padx=10, pady=5)

        # -------- DATA PREVIEW (Primary focus, 70%) --------
        data_frame = ttk.Frame(self.main_paned, style='Card.TFrame')
        self.main_paned.add(data_frame, weight=7)

        # File info header
        header_frame = ttk.Frame(data_frame, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(10, 5), padx=20)

        self.file_info_var = tk.StringVar(value="📄 No file loaded")
        ttk.Label(header_frame, textvariable=self.file_info_var,
                 font=('Segoe UI', 12, 'bold'),
                 foreground='#323130').pack(side='left')

        # Enhanced data preview - LARGE and spacious
        self.enhanced_preview = EnhancedDataPreview(data_frame)
        self.enhanced_preview.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        # -------- WORKFLOW QUEUE (Bottom panel, compact 20%) --------
        queue_frame = ttk.Frame(self.main_paned, style='WorkflowCompact.TFrame')
        self.main_paned.add(queue_frame, weight=2)  # Reduced from 3 to 2 for more compact

        # Queue header with collapse button (more compact)
        queue_header = ttk.Frame(queue_frame, style='WorkflowCompact.TFrame', height=35)
        queue_header.pack(fill='x', pady=3, padx=10)
        queue_header.pack_propagate(False)

        self.collapse_btn = ttk.Button(queue_header, text="▼",
                                       command=self.toggle_queue_collapse,
                                       width=2,
                                       style='RibbonButton.TButton')
        self.collapse_btn.pack(side='left', padx=3)

        ttk.Label(queue_header, text="⚙️ Workflow",
                 font=('Segoe UI', 11, 'bold'),
                 foreground='#323130',
                 background='#FAFAFA').pack(side='left', padx=8)

        self.queue_count_label = ttk.Label(queue_header, text="(0)",
                                           font=('Segoe UI', 9),
                                           foreground='#666666',
                                           background='#FAFAFA')
        self.queue_count_label.pack(side='left')

        # Queue action buttons (compact)
        queue_actions = ttk.Frame(queue_header, style='WorkflowCompact.TFrame')
        queue_actions.pack(side='right', padx=5)

        ttk.Button(queue_actions, text="+ Add",
                  command=self.toggle_operations_sidebar,
                  style='RibbonButtonSuccess.TButton',
                  width=8).pack(side='left', padx=2)
        ttk.Button(queue_actions, text="▶️ Run",
                  command=self.run_operations,
                  style='RibbonButtonSuccess.TButton',
                  width=8).pack(side='left', padx=2)

        # Queue content (cards view)
        self.queue_content = ttk.Frame(queue_frame, style='Card.TFrame')
        self.queue_content.pack(fill='both', expand=True, padx=10, pady=5)

        # Canvas for scrollable queue cards
        canvas = tk.Canvas(self.queue_content, bg='#F3F2F1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.queue_content, orient='vertical', command=canvas.yview)
        self.queue_cards_frame = ttk.Frame(canvas, style='Card.TFrame')

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        canvas_window = canvas.create_window((0, 0), window=self.queue_cards_frame, anchor='nw')

        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            if canvas.winfo_width() > 1:
                canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        self.queue_cards_frame.bind('<Configure>', configure_scroll_region)
        canvas.bind('<Configure>', configure_scroll_region)

        self.queue_canvas = canvas

        # Initialize search var for operations
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)

        # Load initial display
        self.refresh_queue_display()

    # ==================== RIBBON TAB METHODS (Legacy - now handled by ExcelRibbon) ====================
    # These methods are kept for backward compatibility but ribbon is now handled by ExcelRibbon class

    # ==================== OPERATIONS SIDEBAR METHODS ====================

    def toggle_operations_sidebar(self):
        """Toggle operations sidebar visibility"""
        if self.operations_visible:
            self.hide_operations_sidebar()
        else:
            self.show_operations_sidebar()

    def show_operations_sidebar(self):
        """Show operations sidebar (overlay style)"""
        if self.operations_sidebar is not None:
            return  # Already shown

        # Create overlay sidebar
        self.operations_sidebar = tk.Toplevel(self.root)
        self.operations_sidebar.transient(self.root)
        self.operations_sidebar.overrideredirect(True)

        # Position at left side
        x = self.root.winfo_x() + 10
        y = self.root.winfo_y() + 130  # Below ribbon
        height = self.root.winfo_height() - 180
        self.operations_sidebar.geometry(f"320x{height}+{x}+{y}")

        # Sidebar content
        sidebar_frame = ttk.Frame(self.operations_sidebar, style='Card.TFrame', relief=tk.RAISED, borderwidth=2)
        sidebar_frame.pack(fill='both', expand=True)

        # Header
        header = ttk.Frame(sidebar_frame, style='Card.TFrame')
        header.pack(fill='x', pady=10, padx=10)

        ttk.Label(header, text="🔧 Operations",
                 font=('Segoe UI', 14, 'bold')).pack(side='left')
        ttk.Button(header, text="✕",
                  command=self.hide_operations_sidebar,
                  width=3).pack(side='right')

        # Search box
        search_frame = ttk.Frame(sidebar_frame, style='Card.TFrame')
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text="Search:", font=('Segoe UI', 10)).pack(side='left', padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Segoe UI', 10))
        search_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Operations tree
        tree_frame = ttk.Frame(sidebar_frame, style='Card.TFrame')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.ops_tree = ttk.Treeview(tree_frame, show='tree')
        ops_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.ops_tree.yview)
        self.ops_tree.configure(yscrollcommand=ops_scroll.set)

        self.ops_tree.pack(side='left', fill='both', expand=True)
        ops_scroll.pack(side='right', fill='y')

        self.ops_tree.bind('<Double-1>', self.on_operation_select)

        self.load_operations()

        self.operations_visible = True

    def hide_operations_sidebar(self):
        """Hide operations sidebar"""
        if self.operations_sidebar is not None:
            self.operations_sidebar.destroy()
            self.operations_sidebar = None
        self.operations_visible = False

    # ==================== QUEUE DISPLAY METHODS ====================

    def toggle_queue_collapse(self):
        """Toggle workflow queue collapse/expand"""
        if self.queue_collapsed:
            # Expand
            self.queue_content.pack(fill='both', expand=True, padx=10, pady=5)
            self.collapse_btn.config(text="▼")
            self.queue_collapsed = False
        else:
            # Collapse
            self.queue_content.pack_forget()
            self.collapse_btn.config(text="▲")
            self.queue_collapsed = True

    def refresh_queue_display(self):
        """Refresh workflow queue with compact card-style display"""
        # Clear existing cards
        for widget in self.queue_cards_frame.winfo_children():
            widget.destroy()

        # Update count (compact format)
        count = len(self.operation_queue)
        self.queue_count_label.config(text=f"({count})")

        # Update status bar
        if hasattr(self, 'excel_status_bar'):
            if self.df is not None:
                self.excel_status_bar.update_row_count(len(self.df))

        if count == 0:
            # Show empty state (compact)
            empty_label = ttk.Label(self.queue_cards_frame,
                                   text="No operations. Click '+ Add' to start.",
                                   font=('Segoe UI', 10),
                                   foreground='#666666',
                                   background='#FAFAFA')
            empty_label.pack(pady=15)
            return

        # Create card for each operation
        for i, op in enumerate(self.operation_queue):
            self._create_operation_card(i, op)

    def _create_operation_card(self, index, op):
        """Create a compact card widget for an operation (Excel-style)"""
        # Card frame (more compact)
        card = ttk.Frame(self.queue_cards_frame, style='QueueCard.TFrame')
        card.pack(fill='x', pady=2, padx=5)

        # Card content (reduced padding)
        content = ttk.Frame(card, style='Card.TFrame')
        content.pack(fill='both', expand=True, padx=8, pady=5)

        # Left side: checkbox and operation info
        left = ttk.Frame(content, style='Card.TFrame')
        left.pack(side='left', fill='both', expand=True)

        # Checkbox and number
        check_frame = ttk.Frame(left, style='Card.TFrame')
        check_frame.pack(side='left', padx=(0, 10))

        enabled = op.get('enabled', True)
        check_var = tk.BooleanVar(value=enabled)

        def toggle_enabled():
            self.operation_queue[index]['enabled'] = check_var.get()

        cb = ttk.Checkbutton(check_frame, variable=check_var, command=toggle_enabled)
        cb.pack(side='left')

        ttk.Label(check_frame, text=f"{index+1}.",
                 font=('Segoe UI', 11, 'bold'),
                 foreground='#666666').pack(side='left', padx=5)

        # Operation info
        info_frame = ttk.Frame(left, style='Card.TFrame')
        info_frame.pack(side='left', fill='both', expand=True)

        ttk.Label(info_frame, text=op['name'],
                 font=('Segoe UI', 10, 'bold'),
                 foreground='#323130').pack(anchor='w')

        # Parameters summary (compact)
        params_text = self._format_params_summary(op['parameters'])
        ttk.Label(info_frame, text=params_text,
                 font=('Segoe UI', 9),
                 foreground='#666666').pack(anchor='w')

        # Right side: action buttons
        actions = ttk.Frame(content, style='Card.TFrame')
        actions.pack(side='right')

        ttk.Button(actions, text="✏️", width=3,
                  command=lambda: self.edit_operation_by_index(index)).pack(side='left', padx=2)
        ttk.Button(actions, text="🗑", width=3,
                  command=lambda: self.remove_operation_by_index(index)).pack(side='left', padx=2)

        if index > 0:
            ttk.Button(actions, text="↑", width=3,
                      command=lambda: self.move_operation(index, -1)).pack(side='left', padx=2)
        if index < len(self.operation_queue) - 1:
            ttk.Button(actions, text="↓", width=3,
                      command=lambda: self.move_operation(index, 1)).pack(side='left', padx=2)

    def _format_params_summary(self, params):
        """Format operation parameters as summary text"""
        if not params:
            return "No parameters"

        # Format first few key parameters
        summary_parts = []
        for key, value in list(params.items())[:3]:
            if isinstance(value, list):
                summary_parts.append(f"{key}: {len(value)} items")
            elif isinstance(value, bool):
                summary_parts.append(f"{key}: {'Yes' if value else 'No'}")
            elif isinstance(value, str) and len(value) > 30:
                summary_parts.append(f"{key}: {value[:27]}...")
            else:
                summary_parts.append(f"{key}: {value}")

        return " • ".join(summary_parts)

    def edit_operation_by_index(self, index):
        """Edit operation at specific index"""
        op_config = self.operation_queue[index]

        # Get the operation from registry
        operation = registry.get_by_id(op_config['operation_id'])
        if not operation:
            messagebox.showerror("Error", f"Operation {op_config['operation_id']} not found")
            return

        # Get current columns from dataframe
        columns = list(self.df.columns) if self.df is not None else []

        # Determine which dialog to show
        needs_single_column = any(p.type == 'column' for p in operation.metadata.parameters)
        needs_multi_column = any(p.type == 'column_list' for p in operation.metadata.parameters)

        # Show appropriate dialog with edit mode enabled
        if needs_single_column and not needs_multi_column:
            self._show_single_column_dialog(operation, columns, edit_mode=True, edit_index=index, current_params=op_config['parameters'])
        elif needs_multi_column:
            self._show_multi_column_dialog(operation, columns, edit_mode=True, edit_index=index, current_params=op_config['parameters'])
        else:
            self._show_standard_parameter_dialog(operation, edit_mode=True, edit_index=index, current_params=op_config['parameters'])

    def remove_operation_by_index(self, index):
        """Remove operation at specific index"""
        del self.operation_queue[index]
        self.refresh_queue_display()

    def move_operation(self, index, direction):
        """Move operation up (-1) or down (+1)"""
        new_index = index + direction
        if 0 <= new_index < len(self.operation_queue):
            self.operation_queue[index], self.operation_queue[new_index] = \
                self.operation_queue[new_index], self.operation_queue[index]
            self.refresh_queue_display()

    # ==================== EXISTING METHODS FROM ORIGINAL FILE ====================
    # NOTE: All other methods from the original main_gui_v2.py should be copied here
    # Including: load_operations, on_mode_change, on_search, on_operation_select,
    # load_file, run_operations, save_results, save_preset, load_preset,
    # analyze_data_quality, _show_*_dialog methods, etc.
    # For brevity, I'm showing the structure. The actual implementation should include all methods.

    def load_operations(self):
        """Load operations into tree"""
        if not hasattr(self, 'ops_tree') or self.ops_tree is None:
            return

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
        self.status_var.set(f"Switched to {mode.title()} mode")
        if hasattr(self, 'excel_status_bar'):
            self.excel_status_bar.update_mode(mode)
        self.load_operations()

    def on_search(self, *args):
        """Filter operations by search"""
        if not hasattr(self, 'ops_tree') or self.ops_tree is None:
            return

        query = self.search_var.get().lower()
        if not query:
            self.load_operations()
            return

        self.ops_tree.delete(*self.ops_tree.get_children())

        results = registry.search(query)
        if results:
            search_node = self.ops_tree.insert('', 'end', text=f"🔍 Search: '{query}'", open=True)
            for op in results:
                self.ops_tree.insert(search_node, 'end',
                                   text=f"  ▶ {op.metadata.name}",
                                   tags=(op.metadata.id,))

    def on_progress(self, current, total, message):
        """Progress callback for operations"""
        self.status_var.set(f"Processing: {message} ({current}/{total})")
        self.root.update_idletasks()


# ==================== MAIN ====================


    # ==================== METHODS FROM ORIGINAL (AUTO-COPIED) ====================

    def _get_column_letter(self, idx: int) -> str:
        """Convert column index to Excel-style letter"""
        result = ""
        while idx >= 0:
            result = chr(65 + (idx % 26)) + result
            idx = idx // 26 - 1
        return result
    

    def get_column_list_with_letters(self):
        """Get column list with Excel-style letters for dropdowns"""
        if self.df is None:
            return []
        
        columns = []
        for idx, col in enumerate(self.df.columns):
            letter = self._get_column_letter(idx)
            columns.append(f"{letter}: {col}")
        return columns
    

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


    def clear_queue(self):
        """Clear all operations"""
        if messagebox.askyesno("Confirm", "Clear all operations from queue?"):
            self.operation_queue = []
            self.refresh_queue_display()
    

    def load_file(self):
        """Load data file with enhanced preview"""
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
            if filename.endswith('.csv'):
                self.df = pd.read_csv(filename)
            else:
                self.df = pd.read_excel(filename)
            
            self.current_file = filename
            self.file_info_var.set(
                f"📁 {Path(filename).name} • {len(self.df):,} rows × {len(self.df.columns)} columns"
            )
            
            # Use enhanced preview
            self.enhanced_preview.load_dataframe(self.df, is_result=False)

            self.status_var.set(f"Loaded {len(self.df):,} records successfully")

            # Update Excel status bar
            if hasattr(self, 'excel_status_bar'):
                self.excel_status_bar.update_row_count(len(self.df))

            messagebox.showinfo("Success",
                              f"Loaded {len(self.df):,} records with {len(self.df.columns)} columns")
            
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

            # Update Excel status bar
            if hasattr(self, 'excel_status_bar'):
                self.excel_status_bar.update_row_count(len(self.result_df))

            messagebox.showinfo("Success", success_msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Execution failed:\n{str(e)}")
    

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


def main():
    root = tk.Tk()
    app = UniversalExcelToolV2Office365(root)
    root.mainloop()


if __name__ == "__main__":
    main()
