#!/usr/bin/env python3
"""
Clean Sheet - Professional Data Cleaning Made Simple
Version 2.1+ - Office 365 Redesign

Major UI overhaul to make data preview the primary focus

Changes from original:
- Data preview now occupies 60-70% of screen (was ~30%)
- Workflow queue moved to bottom panel (was center)
- Operations sidebar is collapsible (was always visible left panel)
- Office 365 color scheme and spacing
- Card-style operation queue
- Ribbon-style navigation tabs
- Auto-update system with GitHub releases
- Professional branding and configuration management
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
from pathlib import Path
import sys
import os
import logging
import threading
import copy
from typing import Optional

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Version and configuration imports
from version import __version__, __app_name__, __app_tagline__, GITHUB_REPO, __release_date__, COPYRIGHT
from config_manager import ConfigManager, FirstRunConfigDialog
from utils.auto_updater import AutoUpdater, UpdateNotificationDialog, UpdateProgressDialog

# Import existing components
from operations.registry import registry
from engine.executor import OperationExecutor
from engine.validator import Validator
from presets.preset_manager import PresetManager, Preset, OperationConfig
from ui.themes.accessible_theme import AccessibleTheme
from ui.dedupe_panel import DedupePanel
from ui.sheet_selection_dialog import select_sheet_from_file, SheetSelectionDialog
from ui.sheet_tab_bar import SheetTabBar
from ui.multi_sheet_preset_dialog import MultiSheetPresetDialog
from workbook_session import WorkbookSession, SheetState, Issue

# Authentication imports
from auth.login_window import LoginWindow
from auth.auth_manager import AuthManager
from config import Config
from ai_assistant.claude_assistant import ClaudeAssistant
from utils.export_helper import ExportHelper
from batch_processor import BatchProcessor
from file_combiner import FileCombiner
from combine_mode_handler import CombineModeHandler
# DISABLED: combine_pivot mode temporarily disabled for redevelopment
# from combine_pivot_engine import CombinePivotEngine
from enhanced_preview import EnhancedDataPreview
from smart_column_selector import ColumnSelector, MultiColumnSelector
from analysis.data_quality_integration import DataQualityIntegration
from excel_ribbon import ExcelRibbon, FormulaBar, ExcelStatusBar
from datetime import datetime


class CleanSheetApp:
    """Clean Sheet - Professional Data Cleaning Made Simple

    Office 365-style application with data-first layout and auto-update capabilities
    """

    def __init__(self, root, session_token=None, user_email=None, config_manager=None):
        self.root = root

        # Configuration manager
        self.config_manager = config_manager

        # Set title with user info if authenticated
        if user_email:
            self.root.title(f"{__app_name__} v{__version__} - {user_email}")
        else:
            self.root.title(f"{__app_name__} v{__version__} - {__app_tagline__}")

        self.root.geometry("1600x900")
        self.root.minsize(1200, 800)

        # Authentication
        self.session_token = session_token
        self.user_email = user_email
        self.auth_manager = None
        if session_token:
            self.auth_manager = AuthManager()

        # Data - Single File Mode
        self.df = None
        self.result_df = None
        self.removed_df = None
        self.current_file = None
        self.operation_queue = []

        # Sheet selection tracking (for multi-sheet Excel files)
        self.current_sheet_name = None  # Currently selected sheet name
        self.available_sheets = []  # List of all sheets in current file

        # Workbook session for multi-sheet Excel support
        self.workbook_session: Optional[WorkbookSession] = None
        self.sheet_tab_bar: Optional[SheetTabBar] = None  # Excel-like sheet tabs

        # Data - Multi-File Mode
        self.loaded_files = []  # List of {'name': str, 'path': str, 'df': DataFrame}
        self.processing_mode = tk.StringVar(value="single")  # "single" or "batch"
        self.selected_files = []  # Track which files are selected for processing

        # Mode: simple or advanced
        self.mode = tk.StringVar(value="simple")

        # AI Assistant
        self.ai_assistant = None
        # Get API key from config manager if available, otherwise from environment
        api_key = ''
        if self.config_manager:
            api_key = self.config_manager.get_api_key()
        if not api_key:
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        self.api_key = tk.StringVar(value=api_key)

        # Managers
        self.preset_manager = PresetManager()
        self.executor = OperationExecutor(progress_callback=self.on_progress)
        self.batch_processor = BatchProcessor(progress_callback=self.on_batch_progress)
        self.file_combiner = FileCombiner()
        self.combine_mode_handler = CombineModeHandler()
        # DISABLED: combine_pivot mode temporarily disabled for redevelopment
        # self.combine_pivot_engine = CombinePivotEngine()

        # Data Quality Integration
        self.dq_integration = DataQualityIntegration(self)

        # Auto-updater
        self.updater = AutoUpdater(__version__, GITHUB_REPO)

        # UI state
        self.operations_visible = False
        self.operations_sidebar = None
        self.queue_collapsed = False
        self.file_panel_visible = False
        self.file_management_panel = None
        self.dedupe_panel_visible = False
        self.dedupe_panel = None
        self.combine_panel_visible = False
        self.combine_panel = None

        # Apply theme and create UI
        AccessibleTheme.apply_theme(self.root)
        self.setup_office365_theme()
        self.create_widgets()

        # Check for updates on startup (if 24 hours passed)
        if self.config_manager and self.config_manager.should_check_updates():
            if self.updater.should_check_for_updates():
                self.check_for_updates_background()

    def setup_office365_theme(self):
        """Apply Office 365 light color scheme"""
        style = ttk.Style()

        # Office 365 Light Colors (ORIGINAL)
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

        # Workflow frame style
        style.configure('WorkflowCompact.TFrame', background='#FAFAFA')

        # Button styles
        style.configure('HeaderButton.TButton',
                       font=('Segoe UI', 9),
                       padding=(8, 4))

        style.configure('RibbonButton.TButton',
                       font=('Segoe UI', 10),
                       padding=(10, 5))

        style.configure('RibbonButtonSuccess.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background=colors['success_green'],
                       foreground='white',
                       padding=(10, 5))

    def create_widgets(self):
        """Create Excel 365-style interface with compact ribbon and data-first layout"""

        # ==================== HEADER BAR (45px) ====================
        header = ttk.Frame(self.root, style='Header.TFrame', height=45)
        header.pack(fill='x')
        header.pack_propagate(False)

        # Left side - App title
        title_frame = ttk.Frame(header, style='Header.TFrame')
        title_frame.pack(side='left', padx=15, pady=8)

        ttk.Label(
            title_frame,
            text=f"🔷 {__app_name__}",
            font=('Segoe UI', 11, 'bold'),
            foreground='#0078D4',
            background='#F3F2F1'
        ).pack(side='left')

        ttk.Label(
            title_frame,
            text=f"  v{__version__}",
            font=('Segoe UI', 8),
            foreground='#666666',
            background='#F3F2F1'
        ).pack(side='left', pady=(2, 0))

        # Right side - Processing mode, mode selector, user info, logout
        right_container = ttk.Frame(header, style='Header.TFrame')
        right_container.pack(side='right', padx=15, pady=8)

        # Processing mode selector (Single/Batch)
        proc_mode_frame = ttk.Frame(right_container, style='Header.TFrame')
        proc_mode_frame.pack(side='left', padx=(0, 15))

        ttk.Label(proc_mode_frame, text="Files:",
                 font=('Segoe UI', 9),
                 foreground='#666666',
                 background='#F3F2F1').pack(side='left', padx=(0, 5))

        # DISABLED: "combine_pivot" mode temporarily disabled for redevelopment
        proc_mode_menu = ttk.Combobox(proc_mode_frame, textvariable=self.processing_mode,
                                      values=["single", "batch", "compare", "combine"],
                                      state='readonly', width=14,
                                      font=('Segoe UI', 9))
        proc_mode_menu.pack(side='left')
        proc_mode_menu.bind('<<ComboboxSelected>>', lambda e: self.on_processing_mode_change())

        # Mode selector (Simple/Advanced)
        mode_frame = ttk.Frame(right_container, style='Header.TFrame')
        mode_frame.pack(side='left', padx=(0, 15))

        ttk.Label(mode_frame, text="Mode:",
                 font=('Segoe UI', 9),
                 foreground='#666666',
                 background='#F3F2F1').pack(side='left', padx=(0, 5))

        mode_menu = ttk.Combobox(mode_frame, textvariable=self.mode,
                                 values=["simple", "advanced"],
                                 state='readonly', width=10,
                                 font=('Segoe UI', 9))
        mode_menu.pack(side='left')
        mode_menu.bind('<<ComboboxSelected>>', lambda e: self.on_mode_change())

        # User info and logout button (if authenticated)
        if self.session_token and self.user_email:
            # User email label
            ttk.Label(
                right_container,
                text=f"Logged in: {self.user_email}",
                font=('Segoe UI', 9),
                foreground='#666666',
                background='#F3F2F1'
            ).pack(side='left', padx=(0, 10))

            # Logout button
            ttk.Button(
                right_container,
                text="Logout",
                command=self.handle_logout,
                style='HeaderButton.TButton',
                width=8
            ).pack(side='left', padx=5)

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

        # File info header with Reorder Columns button
        header_frame = ttk.Frame(data_frame, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(10, 5), padx=20)

        self.file_info_var = tk.StringVar(value="📄 No file loaded")
        ttk.Label(header_frame, textvariable=self.file_info_var,
                 font=('Segoe UI', 12, 'bold'),
                 foreground='#323130').pack(side='left')

        # Change Sheet button (right side, initially hidden)
        self.change_sheet_btn = ttk.Button(
            header_frame,
            text="📑 Change Sheet",
            command=self.change_sheet,
            style='RibbonButton.TButton',
            width=15
        )
        # Button will be shown/hidden dynamically based on file type

        # Reorder Columns button (right side)
        ttk.Button(
            header_frame,
            text="⚙️ Reorder Columns",
            command=self.open_reorder_columns_dialog,
            style='RibbonButton.TButton',
            width=18
        ).pack(side='right', padx=5)

        # Enhanced data preview - LARGE and spacious
        self.enhanced_preview = EnhancedDataPreview(data_frame)
        self.enhanced_preview.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        # Sheet tab bar (Excel-like, initially hidden)
        self.sheet_tab_bar = SheetTabBar(data_frame, on_sheet_change=self.on_tab_click)
        # Tab bar will be shown/hidden dynamically based on file type

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

        self.workflow_title_label = ttk.Label(
            queue_header,
            text="⚙️ Workflow",
            font=('Segoe UI', 11, 'bold')
        )
        self.workflow_title_label.pack(side='left', padx=8)

        self.queue_count_label = ttk.Label(
            queue_header,
            text="(0)",
            font=('Segoe UI', 9)
        )
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
            # If sidebar exists, just bring it to front
            try:
                self.operations_sidebar.lift()
                self.operations_sidebar.focus_set()
                return
            except tk.TclError:
                # Window was destroyed, create new one
                self.operations_sidebar = None

        # Create overlay sidebar
        self.operations_sidebar = tk.Toplevel(self.root)
        self.operations_sidebar.transient(self.root)
        self.operations_sidebar.overrideredirect(True)

        # CRITICAL FIX: Update window to get accurate geometry
        self.root.update_idletasks()

        # Position at left side using rootx/rooty for accurate screen coordinates
        x = self.root.winfo_rootx() + 10
        # NEW LAYOUT: Header (30px) + Ribbon (120px) + Formula Bar (30px) = 180px
        y = self.root.winfo_rooty() + 190  # Below formula bar
        height = self.root.winfo_height() - 230  # Account for taller header area

        # Ensure minimum height
        if height < 300:
            height = 300

        self.operations_sidebar.geometry(f"320x{height}+{x}+{y}")

        # CRITICAL: Bring window to front and give it focus
        self.operations_sidebar.lift()
        self.operations_sidebar.attributes('-topmost', True)
        self.operations_sidebar.after_idle(self.operations_sidebar.attributes, '-topmost', False)

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

        # Search box with autocomplete
        search_frame = ttk.Frame(sidebar_frame, style='Card.TFrame')
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text="Search:", font=('Segoe UI', 10)).pack(side='left', padx=5)

        # Get all operation names for autocomplete
        all_op_names = []
        for category in registry.get_all_categories():
            operations = registry.get_by_category(category)
            all_op_names.extend([op.metadata.name for op in operations])

        # Create filter combobox (simple and reliable)
        from ui.widgets.filter_combobox import FilterCombobox

        self.search_entry = FilterCombobox(
            search_frame,
            values=sorted(all_op_names),
            font=('Segoe UI', 10),
            width=35
        )
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Sync search_var with entry for tree filtering
        def on_search_change(*args):
            current = self.search_entry.get().strip()
            self.search_var.set(current)

        def on_search_selected(event):
            """When operation is selected from dropdown"""
            selected = self.search_entry.get().strip()
            if selected:
                self.search_var.set(selected)

        self.search_entry.bind('<KeyRelease>', on_search_change)
        self.search_entry.bind('<<ComboboxSelected>>', on_search_selected)
        self.search_entry.bind('<Return>', on_search_selected)

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

        # Ensure window is visible and has focus after content is loaded
        self.operations_sidebar.update()
        self.operations_sidebar.deiconify()
        self.operations_sidebar.focus_set()

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
                                   font=('Segoe UI', 10))
            empty_label.pack(pady=15)
            return

        # Create card for each operation
        for i, op in enumerate(self.operation_queue):
            self._create_operation_card(i, op)

        # Update preview to show results after current operations
        self.update_preview_state()

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

        cb = ttk.Checkbutton(check_frame, variable=check_var, command=toggle_enabled, style='TCheckbutton')
        cb.pack(side='left')

        ttk.Label(check_frame, text=f"{index+1}.",
                 font=('Segoe UI', 11, 'bold')).pack(side='left', padx=5)

        # Operation info
        info_frame = ttk.Frame(left, style='Card.TFrame')
        info_frame.pack(side='left', fill='both', expand=True)

        ttk.Label(info_frame, text=op['name'],
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')

        # Parameters summary (compact)
        params_text = self._format_params_summary(op['parameters'])
        ttk.Label(info_frame, text=params_text,
                 font=('Segoe UI', 9)).pack(anchor='w')

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

        # Check for special operations first
        if operation.metadata.id == 'add_column_smart':
            self._show_add_column_smart_dialog(operation, columns, edit_mode=True, edit_index=index, current_params=op_config['parameters'])
            return

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
        # Save workflow changes to active sheet
        self._save_current_workflow()

    def move_operation(self, index, direction):
        """Move operation up (-1) or down (+1)"""
        new_index = index + direction
        if 0 <= new_index < len(self.operation_queue):
            self.operation_queue[index], self.operation_queue[new_index] = \
                self.operation_queue[new_index], self.operation_queue[index]
            self.refresh_queue_display()
            # Save workflow changes to active sheet
            self._save_current_workflow()

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

    def on_processing_mode_change(self):
        """Handle processing mode toggle (single/batch/compare/combine)"""
        mode = self.processing_mode.get()
        self.status_var.set(f"Switched to {mode.title().replace('_', ' ')} mode")

        if mode == "batch":
            # Show file management panel, hide others
            self.show_file_management_panel()
            self.hide_dedupe_panel()
            self.hide_combine_panel()
            # self.hide_combine_pivot_panel()  # DISABLED: combine_pivot temporarily disabled
        elif mode == "compare":
            # Show compare panel, hide others
            self.hide_file_management_panel()
            self.show_dedupe_panel()
            self.hide_combine_panel()
            # self.hide_combine_pivot_panel()  # DISABLED: combine_pivot temporarily disabled
        elif mode == "combine":
            # Show combine panel, hide others
            self.hide_file_management_panel()
            self.hide_dedupe_panel()
            self.show_combine_panel()
            # self.hide_combine_pivot_panel()  # DISABLED: combine_pivot temporarily disabled
        # DISABLED: combine_pivot mode temporarily disabled for redevelopment
        # elif mode == "combine_pivot":
        #     # Show combine pivot panel, hide others
        #     self.hide_file_management_panel()
        #     self.hide_dedupe_panel()
        #     self.hide_combine_panel()
        #     self.show_combine_pivot_panel()
        else:
            # Single file mode - hide all panels
            self.hide_file_management_panel()
            self.hide_dedupe_panel()
            self.hide_combine_panel()
            # self.hide_combine_pivot_panel()  # DISABLED: combine_pivot temporarily disabled

        # Refresh ribbon to show/hide mode-specific operations
        if hasattr(self, 'excel_ribbon'):
            current_tab = self.excel_ribbon.active_tab.get()
            self.excel_ribbon.switch_tab(current_tab)

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

    def on_batch_progress(self, current, total, filename, status):
        """Progress callback for batch processing"""
        if status == 'processing':
            self.status_var.set(f"Processing file {current}/{total}: {filename}")
        elif status == 'complete':
            self.status_var.set(f"Completed {current}/{total}: {filename}")
        elif status == 'error':
            self.status_var.set(f"Error processing {current}/{total}: {filename}")
        self.root.update_idletasks()

    # ==================== MULTI-FILE MANAGEMENT ====================

    def show_file_management_panel(self):
        """Show file management panel for batch mode"""
        if self.file_panel_visible:
            return

        # Hide single-file UI
        if hasattr(self, 'main_paned'):
            self.main_paned.pack_forget()

        # Create split pane if it doesn't exist
        if not hasattr(self, 'split_pane_container'):
            self._create_split_pane()

        # Show split pane
        self.split_pane_container.pack(fill='both', expand=True, padx=10, pady=5)
        self.file_panel_visible = True
        self.status_var.set("Batch mode enabled - Load multiple files")

    def hide_file_management_panel(self):
        """Hide file management panel for single file mode"""
        if not self.file_panel_visible:
            return

        # Hide split pane
        if hasattr(self, 'split_pane_container'):
            self.split_pane_container.pack_forget()

        # Show single-file UI
        if hasattr(self, 'main_paned'):
            self.main_paned.pack(fill='both', expand=True, padx=10, pady=5)

        self.file_panel_visible = False
        self.status_var.set("Single file mode enabled")

    def show_dedupe_panel(self):
        """Show comparison panel for compare mode"""
        if self.dedupe_panel_visible:
            return

        # Hide single-file UI
        if hasattr(self, 'main_paned'):
            self.main_paned.pack_forget()

        # Create compare panel if it doesn't exist
        if self.dedupe_panel is None:
            self.dedupe_panel = DedupePanel(self.root)

        # Show compare panel
        self.dedupe_panel.pack(fill='both', expand=True, padx=10, pady=5)
        self.dedupe_panel_visible = True
        self.status_var.set("Comparison mode enabled - Compare two files")

    def hide_dedupe_panel(self):
        """Hide comparison panel"""
        if not self.dedupe_panel_visible:
            return

        # Hide compare panel
        if self.dedupe_panel is not None:
            self.dedupe_panel.pack_forget()

        # Show single-file UI
        if hasattr(self, 'main_paned'):
            self.main_paned.pack(fill='both', expand=True, padx=10, pady=5)

        self.dedupe_panel_visible = False
        self.status_var.set("Single file mode enabled")

    def show_combine_panel(self):
        """Show combine panel for combine mode"""
        if self.combine_panel_visible:
            return

        # Hide single-file UI
        if hasattr(self, 'main_paned'):
            self.main_paned.pack_forget()

        # Create combine panel if it doesn't exist
        if self.combine_panel is None:
            self._create_combine_panel()

        # Show combine panel
        self.combine_panel.pack(fill='both', expand=True, padx=10, pady=5)
        self.combine_panel_visible = True
        self.status_var.set("Combine mode enabled - Upload multiple files to combine")

    def hide_combine_panel(self):
        """Hide combine panel"""
        if not self.combine_panel_visible:
            return

        # Hide combine panel
        if self.combine_panel is not None:
            self.combine_panel.pack_forget()

        # Show single-file UI
        if hasattr(self, 'main_paned'):
            self.main_paned.pack(fill='both', expand=True, padx=10, pady=5)

        self.combine_panel_visible = False
        self.status_var.set("Single file mode enabled")

    def _create_combine_panel(self):
        """Create the Combine Mode UI panel"""
        self.combine_panel = tk.Frame(self.root, bg='white')

        # Main container with scrolling
        main_container = ttk.Frame(self.combine_panel, style='Card.TFrame')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_label = ttk.Label(
            main_container,
            text="Combine Files",
            font=('Segoe UI', 18, 'bold'),
            foreground='#0078D4'
        )
        title_label.pack(pady=(10, 5), padx=20)

        subtitle_label = ttk.Label(
            main_container,
            text="Combine multiple CSV/TXT files into one file with exact formatting preservation.\n"
                 "Header from first file is kept. Repeated headers are automatically removed.\n"
                 "No formatting changes - quotes, spacing, and delimiters preserved exactly.",
            font=('Segoe UI', 10),
            foreground='#666666',
            justify='center'
        )
        subtitle_label.pack(pady=(0, 20), padx=20)

        # File Upload Section
        upload_frame = ttk.LabelFrame(main_container, text="📁 File Upload", padding=15)
        upload_frame.pack(fill='both', padx=20, pady=10)

        btn_upload = ttk.Button(
            upload_frame,
            text="Browse Files...",
            command=self.combine_browse_files,
            style='Accent.TButton',
            width=20
        )
        btn_upload.pack(pady=10)

        # File list with scrollbar
        list_frame = ttk.Frame(upload_frame)
        list_frame.pack(fill='both', expand=True, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.combine_file_listbox = tk.Listbox(
            list_frame,
            height=8,
            font=('Consolas', 10),
            yscrollcommand=scrollbar.set
        )
        self.combine_file_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.combine_file_listbox.yview)

        # Buttons for file management
        file_btn_frame = ttk.Frame(upload_frame)
        file_btn_frame.pack(fill='x', pady=5)

        ttk.Button(
            file_btn_frame,
            text="Remove Selected",
            command=self.combine_remove_file,
            width=15
        ).pack(side='left', padx=5)

        ttk.Button(
            file_btn_frame,
            text="Clear All",
            command=self.combine_clear_files,
            width=15
        ).pack(side='left', padx=5)

        # Summary Panel
        summary_frame = ttk.LabelFrame(main_container, text="📊 Summary", padding=15)
        summary_frame.pack(fill='x', padx=20, pady=10)

        self.combine_summary_text = tk.Text(
            summary_frame,
            height=6,
            font=('Consolas', 10),
            wrap='word',
            state='disabled'
        )
        self.combine_summary_text.pack(fill='x')

        # Combine Button
        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill='x', padx=20, pady=20)

        self.combine_btn = ttk.Button(
            action_frame,
            text="🔗 Combine Files",
            command=self.combine_files_execute,
            style='Success.TButton',
            width=25,
            state='disabled'
        )
        self.combine_btn.pack()

        # Initialize summary
        self.update_combine_summary()

    def _create_split_pane(self):
        """Create the split pane layout for batch mode"""
        from ui.file_list_panel import FileListPanel
        from ui.file_detail_panel import FileDetailPanel

        self.split_pane_container = tk.Frame(self.root, bg="white")

        # Left pane (file list)
        self.file_list_panel = FileListPanel(
            self.split_pane_container,
            app_ref=self
        )
        self.file_list_panel.pack(side=tk.LEFT, fill=tk.Y)

        # Resizable divider
        divider = tk.Frame(
            self.split_pane_container,
            bg="#CCC",
            width=2,
            cursor="sb_h_double_arrow"
        )
        divider.pack(side=tk.LEFT, fill=tk.Y)

        # Right pane (file detail)
        self.file_detail_panel = FileDetailPanel(
            self.split_pane_container,
            app_ref=self
        )
        self.file_detail_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate presets in file list panel
        if hasattr(self.file_list_panel, 'populate_preset_dropdown'):
            self.file_list_panel.populate_preset_dropdown()

    def _on_file_selected(self, file_obj):
        """Handle file selection in left pane"""
        if hasattr(self, 'file_detail_panel'):
            self.file_detail_panel.show_file(file_obj)

    def load_multiple_files(self):
        """Load multiple files for batch processing"""
        filenames = filedialog.askopenfilenames(
            title="Select Multiple Data Files",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not filenames:
            return

        self.status_var.set(f"Loading {len(filenames)} files...")

        loaded_count = 0
        for filename in filenames:
            try:
                # Detect if file has header
                if filename.endswith('.csv'):
                    df_test = self._load_csv_with_encoding_detection(filename, nrows=5)
                else:
                    df_test = pd.read_excel(filename, nrows=5)

                # Smart header detection
                has_header = self._detect_header(df_test)

                # Load full file
                if filename.endswith('.csv'):
                    df = self._load_csv_with_encoding_detection(filename, header=0 if has_header else None)
                else:
                    df = pd.read_excel(filename, header=0 if has_header else None)

                # Add to loaded files
                file_obj = {
                    'name': Path(filename).name,
                    'path': filename,
                    'df': df,
                    'operations': [],  # Empty operations list
                    'result_df': None,
                    'removed_df': None
                }
                self.loaded_files.append(file_obj)

                # Add to file list panel if in batch mode
                if hasattr(self, 'file_list_panel') and self.file_list_panel:
                    self.file_list_panel.add_file(file_obj)

                loaded_count += 1

            except Exception as e:
                logging.error(f"Failed to load {filename}: {e}")
                messagebox.showerror("Load Error", f"Failed to load {Path(filename).name}:\n{str(e)}")

        if loaded_count > 0:
            self.status_var.set(f"Loaded {loaded_count} files successfully")
        else:
            self.status_var.set("No files loaded")

    def _detect_header(self, df_sample):
        """Smart header detection"""
        if len(df_sample) < 2:
            return True

        first_row = df_sample.iloc[0]
        numeric_count = sum(pd.api.types.is_numeric_dtype(type(val)) for val in first_row)
        return numeric_count < len(first_row) * 0.7

    def _load_csv_with_encoding_detection(self, file_path, **kwargs):
        """
        Load CSV with automatic encoding detection

        Tries multiple encodings in order of likelihood:
        1. UTF-8 (standard)
        2. UTF-8-SIG (with BOM)
        3. Windows-1252 (Excel default on Windows)
        4. Latin-1 (ISO-8859-1)
        5. CP1252 (another Windows encoding)

        Args:
            file_path: Path to the CSV file
            **kwargs: Additional arguments to pass to pd.read_csv (e.g., nrows, header)

        Returns:
            pandas.DataFrame: Loaded data

        Raises:
            Exception: If all encoding attempts fail
        """
        encodings = [
            'utf-8',
            'utf-8-sig',
            'windows-1252',
            'latin-1',
            'cp1252',
            'iso-8859-1'
        ]

        last_error = None

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, **kwargs)

                # Success! Log which encoding worked (for debugging)
                logging.info(f"Successfully loaded {Path(file_path).name} with encoding: {encoding}")

                return df

            except (UnicodeDecodeError, UnicodeError) as e:
                last_error = e
                continue

            except Exception as e:
                # Other errors (not encoding-related) - don't continue trying
                raise e

        # If all encodings failed, try using chardet library for detection
        try:
            import chardet

            # Read file in binary mode to detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                detected_encoding = result['encoding']
                confidence = result['confidence']

            logging.info(f"Detected encoding: {detected_encoding} (confidence: {confidence:.2%})")

            if detected_encoding and confidence > 0.7:
                df = pd.read_csv(file_path, encoding=detected_encoding, **kwargs)
                return df

        except ImportError:
            # chardet not installed, skip this method
            logging.debug("chardet not installed, skipping advanced encoding detection")

        except Exception as e:
            logging.error(f"Encoding detection failed: {str(e)}")

        # If everything failed, raise the original error
        raise Exception(
            f"Could not determine file encoding. Tried: {', '.join(encodings)}\n"
            f"Original error: {str(last_error)}"
        )

    def update_file_list_display(self):
        """Update the file list display in UI"""
        # This would update a listbox or tree view with loaded files
        # For now, just update status
        pass

    def remove_selected_files(self):
        """Remove selected files from loaded files list"""
        # Implementation depends on UI widget used
        pass

    def process_batch_files(self):
        """Process all selected files using SimpleBatchExecutor"""
        if not self.loaded_files:
            messagebox.showwarning("No Files", "Please load files first")
            return

        # Get selected files
        if hasattr(self, 'file_list_panel'):
            selected_files = self.file_list_panel.get_selected_files()
        else:
            selected_files = self.loaded_files

        if not selected_files:
            messagebox.showwarning(
                "No Files Selected",
                "Please select at least one file to process"
            )
            return

        # Check if files have operations
        files_with_ops = [f for f in selected_files if f.get('operations')]
        files_without_ops = [f['name'] for f in selected_files if not f.get('operations')]

        if not files_with_ops:
            messagebox.showwarning(
                "No Operations",
                "None of the selected files have operations in their workflows.\n\n"
                "Please add operations to at least one file before processing."
            )
            return

        if files_without_ops:
            msg = (f"{len(files_without_ops)} file(s) have no operations and will be skipped:\n\n" +
                   "\n".join(files_without_ops[:5]) +
                   ("\n..." if len(files_without_ops) > 5 else "") +
                   f"\n\nProcess {len(files_with_ops)} file(s) with operations?")
            if not messagebox.askyesno("Files Without Operations", msg):
                return
        else:
            # All files have operations
            if not messagebox.askyesno(
                "Confirm Processing",
                f"Process {len(selected_files)} file(s)?\n\n"
                "Each file will be processed with its own workflow."
            ):
                return

        # Use SimpleBatchExecutor
        from batch_executor import SimpleBatchExecutor

        executor = SimpleBatchExecutor(self)

        try:
            # Only process files with operations
            results = executor.execute_batch(files_with_ops)

            # Show summary
            success_count = sum(1 for r in results if r['status'] == 'success')
            error_count = len(results) - success_count

            if error_count == 0:
                total_rows_before = sum(r['rows_before'] for r in results)
                total_rows_after = sum(r['rows_after'] for r in results)
                total_removed = sum(r.get('rows_removed', 0) for r in results)

                success_msg = (
                    f"✅ Successfully processed {success_count} file(s)!\n\n"
                    f"Total rows:\n"
                    f"  • Input: {total_rows_before:,}\n"
                    f"  • Output: {total_rows_after:,}\n"
                    f"  • Removed: {total_removed:,}"
                )
                messagebox.showinfo("Success", success_msg)
            else:
                error_files = [r['file'] for r in results if r['status'] == 'error']
                error_details = "\n".join(
                    f"  • {r['file']}: {r['error'][:50]}..." if len(r['error']) > 50 else f"  • {r['file']}: {r['error']}"
                    for r in results if r['status'] == 'error'
                )

                messagebox.showwarning(
                    "Partial Success",
                    f"Processed: {success_count} file(s)\n"
                    f"Errors: {error_count} file(s)\n\n"
                    f"Failed files:\n{error_details[:300]}" +
                    ("..." if len(error_details) > 300 else "")
                )

            # Refresh UI to show results
            if hasattr(self, 'file_detail_panel') and self.file_detail_panel.current_file:
                # Refresh the current file's display to show results
                self.file_detail_panel.show_file(self.file_detail_panel.current_file)

        except Exception as e:
            import logging
            logging.error(f"Batch processing failed: {e}")
            messagebox.showerror(
                "Batch Processing Failed",
                f"Error during batch processing:\n{str(e)}"
            )

    def combine_files_dialog(self):
        """Show dialog for combining files"""
        if not self.loaded_files:
            messagebox.showwarning("No Files", "Please load files first")
            return

        # Check column compatibility
        is_compatible, mismatch_info = self.file_combiner.check_column_compatibility(self.loaded_files)

        if not is_compatible:
            # Show column mismatch dialog
            report = self.file_combiner.generate_column_mismatch_report()
            result = messagebox.askyesnocancel(
                "Column Mismatch",
                report + "\n\nProceed with combining?",
                icon='warning'
            )
            if not result:
                return

        # Show combine options dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Combine Files Options")
        dialog.geometry("500x400")
        dialog.transient(self.root)

        # Options
        ttk.Label(dialog, text="Combine Files", font=('Segoe UI', 14, 'bold')).pack(pady=10)

        # Column strategy
        ttk.Label(dialog, text="Column Strategy:").pack(pady=5)
        strategy_var = tk.StringVar(value="all")
        ttk.Radiobutton(dialog, text="All columns (fill missing with blanks)",
                       variable=strategy_var, value="all").pack()
        ttk.Radiobutton(dialog, text="Common columns only",
                       variable=strategy_var, value="common").pack()
        ttk.Radiobutton(dialog, text="Use first file's columns",
                       variable=strategy_var, value="first").pack()

        # Group by column option
        ttk.Label(dialog, text="\nGroup by column (optional):").pack(pady=5)
        group_var = tk.StringVar(value="")
        groupable_cols = self.file_combiner.get_groupable_columns(self.loaded_files)
        group_combo = ttk.Combobox(dialog, textvariable=group_var,
                                   values=["(No grouping)"] + groupable_cols,
                                   state='readonly')
        group_combo.pack()
        group_combo.set("(No grouping)")

        def do_combine():
            strategy = strategy_var.get()
            group_col = group_var.get() if group_var.get() != "(No grouping)" else None

            try:
                if group_col:
                    # Group and combine
                    groups = self.file_combiner.combine_and_group_by_column(
                        self.loaded_files, group_col, strategy
                    )
                    messagebox.showinfo("Success", f"Created {len(groups)} grouped files")
                    self.show_grouped_export_dialog(groups)
                else:
                    # Simple combine
                    combined_df = self.file_combiner.combine_files_simple(
                        self.loaded_files, strategy
                    )
                    messagebox.showinfo("Success", f"Combined into {len(combined_df)} rows × {len(combined_df.columns)} columns")
                    self.show_combined_export_dialog(combined_df)

                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Combine Error", f"Failed to combine files:\n{str(e)}")

        ttk.Button(dialog, text="Combine Files", command=do_combine).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

    def show_batch_export_dialog(self, results):
        """Show export dialog for batch processing results"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Batch Results")
        dialog.geometry("500x350")
        dialog.transient(self.root)

        ttk.Label(dialog, text="Export Batch Results", font=('Segoe UI', 14, 'bold')).pack(pady=10)
        ttk.Label(dialog, text=f"{len(results)} files processed successfully").pack()

        # Export format
        ttk.Label(dialog, text="\nExport Format:").pack(pady=5)
        format_var = tk.StringVar(value="xlsx")
        ttk.Radiobutton(dialog, text="Excel (.xlsx)", variable=format_var, value="xlsx").pack()
        ttk.Radiobutton(dialog, text="CSV (.csv)", variable=format_var, value="csv").pack()
        ttk.Radiobutton(dialog, text="Text (.txt)", variable=format_var, value="txt").pack()

        # Include removed rows
        include_removed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Include removed rows files",
                       variable=include_removed_var).pack(pady=5)

        # Export options
        ttk.Label(dialog, text="\nExport Option:").pack(pady=5)
        export_option_var = tk.StringVar(value="zip")
        ttk.Radiobutton(dialog, text="ZIP Archive", variable=export_option_var, value="zip").pack()
        ttk.Radiobutton(dialog, text="Individual files to folder",
                       variable=export_option_var, value="folder").pack()

        def do_export():
            file_format = format_var.get()
            include_removed = include_removed_var.get()
            export_option = export_option_var.get()

            try:
                if export_option == "zip":
                    # Export as ZIP
                    output_path = filedialog.asksaveasfilename(
                        title="Save ZIP Archive",
                        defaultextension=".zip",
                        filetypes=[("ZIP files", "*.zip")]
                    )
                    if output_path:
                        success = ExportHelper.export_batch_as_zip(
                            results, output_path, file_format, include_removed
                        )
                        if success:
                            messagebox.showinfo("Success", f"Exported to {output_path}")
                            dialog.destroy()
                else:
                    # Export to folder
                    output_dir = filedialog.askdirectory(title="Select Output Folder")
                    if output_dir:
                        count = ExportHelper.export_batch_individual(
                            results, output_dir, file_format, include_removed
                        )
                        messagebox.showinfo("Success", f"Exported {count} files to {output_dir}")
                        dialog.destroy()

            except Exception as e:
                messagebox.showerror("Export Error", f"Export failed:\n{str(e)}")

        ttk.Button(dialog, text="Export", command=do_export).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

    def show_combined_export_dialog(self, combined_df):
        """Show export dialog for combined DataFrame"""
        output_path = filedialog.asksaveasfilename(
            title="Save Combined File",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt")
            ]
        )

        if output_path:
            ext = Path(output_path).suffix.lower()
            format_map = {'.xlsx': 'xlsx', '.csv': 'csv', '.txt': 'txt'}
            file_format = format_map.get(ext, 'xlsx')

            success = ExportHelper.export_combined_file(combined_df, output_path, file_format)
            if success:
                messagebox.showinfo("Success", f"Combined file saved to {output_path}")

    def show_grouped_export_dialog(self, groups):
        """Show export dialog for grouped files"""
        output_dir = filedialog.askdirectory(title="Select Output Folder for Grouped Files")

        if output_dir:
            # Ask for format
            format_var = tk.StringVar(value="xlsx")
            dialog = tk.Toplevel(self.root)
            dialog.title("Export Format")
            dialog.geometry("300x150")

            ttk.Label(dialog, text="Export Format:").pack(pady=10)
            ttk.Radiobutton(dialog, text="Excel (.xlsx)", variable=format_var, value="xlsx").pack()
            ttk.Radiobutton(dialog, text="CSV (.csv)", variable=format_var, value="csv").pack()

            def do_export():
                count = ExportHelper.export_grouped_files(groups, output_dir, format_var.get())
                messagebox.showinfo("Success", f"Exported {count} grouped files")
                dialog.destroy()

            ttk.Button(dialog, text="Export", command=do_export).pack(pady=10)
            dialog.mainloop()

    # ==================== COMBINE MODE METHODS ====================

    def combine_browse_files(self):
        """Browse and add files to combine queue"""
        filenames = filedialog.askopenfilenames(
            title="Select Files to Combine",
            filetypes=[
                ("All Supported", "*.xlsx *.xls *.csv *.txt *.tsv"),
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt *.tsv"),
                ("All files", "*.*")
            ]
        )

        if not filenames:
            return

        # Validate file limit (2-50 files total)
        total_files = len(self.combine_mode_handler.loaded_files) + len(filenames)
        if total_files > 50:
            messagebox.showerror(
                "Too Many Files",
                f"Cannot add {len(filenames)} files. Maximum 50 files allowed.\nCurrently loaded: {len(self.combine_mode_handler.loaded_files)}"
            )
            return

        self.status_var.set(f"Loading {len(filenames)} files...")

        loaded_count = 0
        errors = []

        for filename in filenames:
            try:
                # Add file to combine handler
                file_info = self.combine_mode_handler.add_file(filename)

                # Add to listbox display
                display_text = f"{file_info['name']} ({file_info['rows']} rows, {file_info['columns']} cols, {file_info['type']})"
                if file_info['type'] == 'text':
                    delimiter_map = {',': 'comma', '|': 'pipe', '\t': 'tab'}
                    delim_name = delimiter_map.get(file_info['delimiter'], file_info['delimiter'])
                    display_text += f" [{delim_name}]"

                self.combine_file_listbox.insert(tk.END, display_text)
                loaded_count += 1

            except Exception as e:
                errors.append(f"{Path(filename).name}: {str(e)}")
                logging.error(f"Failed to load {filename} for combine: {e}")

        # Show errors if any
        if errors:
            error_msg = "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more errors"
            messagebox.showerror("Load Errors", f"Failed to load some files:\n\n{error_msg}")

        # Update status and summary
        if loaded_count > 0:
            self.status_var.set(f"Loaded {loaded_count} files successfully")
            self.update_combine_summary()

            # Validate files
            is_valid, error_msg = self.combine_mode_handler.validate_files(
                self.combine_mode_handler.loaded_files
            )
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                self.combine_btn.config(state='disabled')
            else:
                # Enable combine button if 2+ files
                if len(self.combine_mode_handler.loaded_files) >= 2:
                    self.combine_btn.config(state='normal')
        else:
            self.status_var.set("No files loaded")

    def combine_remove_file(self):
        """Remove selected file from combine queue"""
        selection = self.combine_file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to remove")
            return

        index = selection[0]
        file_info = self.combine_mode_handler.loaded_files[index]

        # Remove from handler
        self.combine_mode_handler.remove_file(file_info['path'])

        # Remove from listbox
        self.combine_file_listbox.delete(index)

        # Update summary
        self.update_combine_summary()

        # Disable combine button if less than 2 files
        if len(self.combine_mode_handler.loaded_files) < 2:
            self.combine_btn.config(state='disabled')

    def combine_clear_files(self):
        """Clear all files from combine queue"""
        if not self.combine_mode_handler.loaded_files:
            return

        result = messagebox.askyesno(
            "Clear All Files",
            "Are you sure you want to clear all files from the combine queue?"
        )

        if result:
            self.combine_mode_handler.clear_files()
            self.combine_file_listbox.delete(0, tk.END)
            self.update_combine_summary()
            self.combine_btn.config(state='disabled')
            self.status_var.set("Cleared all files")

    def update_combine_summary(self):
        """Update the summary panel with current file info"""
        summary = self.combine_mode_handler.get_summary()

        # Build summary text
        summary_text = []
        summary_text.append(f"Files detected: {summary['file_count']}")

        if summary['file_count'] > 0:
            summary_text.append(f"Detected file type: {summary['file_type'] or 'Unknown'}")
            if summary['delimiter']:
                summary_text.append(f"Detected delimiter: {summary['delimiter']}")
            summary_text.append(f"Total rows: {summary['total_rows']:,}")
            summary_text.append(f"Total unique columns: {summary['total_columns']}")
        else:
            summary_text.append("")
            summary_text.append("No files loaded yet")
            summary_text.append("Upload 2 or more files to begin")

        # Update text widget
        self.combine_summary_text.config(state='normal')
        self.combine_summary_text.delete(1.0, tk.END)
        self.combine_summary_text.insert(1.0, "\n".join(summary_text))
        self.combine_summary_text.config(state='disabled')

    def combine_files_execute(self):
        """
        Execute file combination and export

        COMBINE_CSV_FIX: Use CSV-aware methods for text files to preserve exact formatting
        """
        # Final validation
        is_valid, error_msg = self.combine_mode_handler.validate_files(
            self.combine_mode_handler.loaded_files
        )

        if not is_valid:
            messagebox.showerror("Validation Error", error_msg)
            return

        try:
            file_type = self.combine_mode_handler.detected_file_type

            # RAW TEXT COMBINING: Use line-based processing for exact format preservation
            if file_type == 'text':
                # Use raw text line-based combining
                file_paths = [f['path'] for f in self.combine_mode_handler.loaded_files]
                delimiter = self.combine_mode_handler.detected_delimiter

                # Combine files using raw text processing
                header_line, data_lines, files_processed = self.combine_mode_handler.combine_text_files_raw(
                    file_paths, delimiter
                )

                # Show success message
                summary = self.combine_mode_handler.get_summary()
                messagebox.showinfo(
                    "Files Combined",
                    f"Successfully combined {summary['file_count']} files!\n\n"
                    f"Total data rows: {len(data_lines):,}\n"
                    f"Repeated headers removed automatically.\n\n"
                    "Original formatting preserved exactly.\n"
                    "Click OK to select export location."
                )

                # Show export dialog with raw text data
                self.combine_export_dialog_raw(header_line, data_lines, summary)

            else:
                # Excel files - use pandas method
                dataframes = [f['df'] for f in self.combine_mode_handler.loaded_files]
                combined_df = self.combine_mode_handler.combine_dataframes(dataframes)

                # Show success message
                summary = self.combine_mode_handler.get_summary()
                messagebox.showinfo(
                    "Files Combined",
                    f"Successfully combined {summary['file_count']} files!\n\n"
                    f"Total rows: {len(combined_df):,}\n"
                    f"Total columns: {len(combined_df.columns)}\n\n"
                    "Click OK to select export location."
                )

                # Show export dialog with DataFrame
                self.combine_export_dialog(combined_df, summary)

        except Exception as e:
            logging.error(f"Combine execution error: {e}", exc_info=True)
            messagebox.showerror("Combine Error", f"Failed to combine files:\n\n{str(e)}")

    def combine_export_dialog(self, combined_df, summary):
        """Show export dialog for combined data"""
        # Determine output file type based on input files
        file_type = self.combine_mode_handler.detected_file_type
        delimiter = self.combine_mode_handler.detected_delimiter

        # Set default extension and filetypes
        if file_type == 'excel':
            default_ext = '.xlsx'
            filetypes = [("Excel files", "*.xlsx")]
        else:
            # Text file - preserve delimiter
            if delimiter == '\t':
                default_ext = '.tsv'
                filetypes = [("TSV files", "*.tsv"), ("CSV files", "*.csv"), ("Text files", "*.txt")]
            elif delimiter == '|':
                default_ext = '.txt'
                filetypes = [("Text files", "*.txt"), ("CSV files", "*.csv")]
            else:  # comma
                default_ext = '.csv'
                filetypes = [("CSV files", "*.csv"), ("Text files", "*.txt")]

        # Ask for save location
        output_path = filedialog.asksaveasfilename(
            title="Save Combined File",
            defaultextension=default_ext,
            filetypes=filetypes
        )

        if not output_path:
            return

        try:
            # Export based on file type
            if output_path.endswith('.xlsx'):
                combined_df.to_excel(output_path, index=False)
            else:
                # Text file - use detected delimiter or comma
                sep = delimiter if delimiter else ','
                combined_df.to_csv(output_path, index=False, sep=sep)

            messagebox.showinfo(
                "Export Successful",
                f"Combined file saved successfully!\n\n"
                f"Location: {output_path}\n"
                f"Rows: {len(combined_df):,}\n"
                f"Columns: {len(combined_df.columns)}"
            )

            self.status_var.set(f"Exported combined file: {Path(output_path).name}")

        except Exception as e:
            logging.error(f"Export error: {e}", exc_info=True)
            messagebox.showerror("Export Error", f"Failed to export file:\n\n{str(e)}")

    def combine_export_dialog_raw(self, header_line: str, data_lines: list, summary: dict):
        """
        Show export dialog for raw text combined data

        RAW TEXT EXPORT: Use raw text writing to preserve exact formatting

        Args:
            header_line: Header line from first file (as raw text)
            data_lines: Data lines (list of strings)
            summary: Summary dict with file info
        """
        # Determine output file type based on input files
        delimiter = self.combine_mode_handler.detected_delimiter

        # Set default extension and filetypes
        if delimiter == '\t':
            default_ext = '.tsv'
            filetypes = [("TSV files", "*.tsv"), ("CSV files", "*.csv"), ("Text files", "*.txt")]
        elif delimiter == '|':
            default_ext = '.txt'
            filetypes = [("Text files", "*.txt"), ("CSV files", "*.csv")]
        else:  # comma
            default_ext = '.csv'
            filetypes = [("CSV files", "*.csv"), ("Text files", "*.txt")]

        # Ask for save location
        output_path = filedialog.asksaveasfilename(
            title="Save Combined File",
            defaultextension=default_ext,
            filetypes=filetypes
        )

        if not output_path:
            return

        try:
            # RAW TEXT EXPORT: Write using raw text method
            self.combine_mode_handler.export_text_file_raw(
                output_path, header_line, data_lines
            )

            messagebox.showinfo(
                "Export Successful",
                f"Combined file saved successfully!\n\n"
                f"Location: {output_path}\n"
                f"Data rows: {len(data_lines):,}\n\n"
                f"Original formatting preserved exactly.\n"
                f"Delimiter: {summary.get('delimiter', 'unknown')}"
            )

            self.status_var.set(f"Exported combined file: {Path(output_path).name}")

        except Exception as e:
            logging.error(f"Raw text export error: {e}", exc_info=True)
            messagebox.showerror("Export Error", f"Failed to export file:\n\n{str(e)}")

    # ==================== COMBINE PIVOT MODE (CSV/XLSX) ====================
    # DISABLED: All combine_pivot methods below are temporarily disabled for redevelopment.
    # The mode has been removed from the UI dropdown and cannot be selected.
    # Implementation files (combine_pivot_engine.py) are preserved for future reference.
    # ===========================================================================

    def show_combine_pivot_panel(self):
        """Show combine pivot panel - DISABLED"""
        # DISABLED: This method is not called as combine_pivot is disabled
        return
        # Hide single-file UI
        if hasattr(self, 'main_paned'):
            self.main_paned.pack_forget()

        # Create combine pivot panel if it doesn't exist
        if not hasattr(self, 'combine_pivot_panel') or self.combine_pivot_panel is None:
            self._create_combine_pivot_panel()

        # Show combine pivot panel
        self.combine_pivot_panel.pack(fill='both', expand=True, padx=10, pady=5)
        self.combine_pivot_panel_visible = True
        self.status_var.set("Combine Pivot mode enabled - Upload CSV/XLSX files to combine into pivot-ready dataset")

    def hide_combine_pivot_panel(self):
        """Hide combine pivot panel - DISABLED"""
        # DISABLED: This method is safe to call but does nothing as combine_pivot is disabled
        return
        # if not hasattr(self, 'combine_pivot_panel_visible') or not self.combine_pivot_panel_visible:
        #     return
        #
        # # Hide combine pivot panel
        # if hasattr(self, 'combine_pivot_panel') and self.combine_pivot_panel is not None:
        #     self.combine_pivot_panel.pack_forget()
        #
        # # Show single-file UI
        # if hasattr(self, 'main_paned'):
        #     self.main_paned.pack(fill='both', expand=True, padx=10, pady=5)
        #
        # self.combine_pivot_panel_visible = False
        # self.status_var.set("Single file mode enabled")

    def _create_combine_pivot_panel(self):
        """Create the Combine Pivot Mode UI panel"""
        self.combine_pivot_panel = tk.Frame(self.root, bg='white')

        # Initialize storage for file-specific data
        self.combine_pivot_file_widgets = []  # List of dicts with file info and widgets
        self.combine_pivot_file_sheets = {}  # {file_path: selected_sheet}

        # Create scrollable container
        # Canvas for scrolling
        canvas = tk.Canvas(self.combine_pivot_panel, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.combine_pivot_panel, orient='vertical', command=canvas.yview)

        # Scrollable frame inside canvas
        scrollable_frame = ttk.Frame(canvas, style='Card.TFrame')

        # Configure canvas scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Create window in canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw', tags='scrollable_frame')
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        scrollbar.pack(side='right', fill='y', pady=20)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)

        # Also make canvas width adapt to window
        def _on_canvas_configure(event):
            canvas.itemconfig('scrollable_frame', width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)

        # Store canvas reference for later updates
        self.combine_pivot_canvas = canvas

        # Main container is now the scrollable_frame
        main_container = scrollable_frame

        # Title
        title_label = ttk.Label(
            main_container,
            text="Combine CSV/XLSX Files (Pivot Mode)",
            font=('Segoe UI', 18, 'bold'),
            foreground='#0078D4'
        )
        title_label.pack(pady=(10, 5), padx=20)

        subtitle_label = ttk.Label(
            main_container,
            text="Combine multiple CSV and Excel files into a unified pivot-ready dataset.\n"
                 "All files must have identical headers and column counts.",
            font=('Segoe UI', 10),
            foreground='#666666',
            justify='center'
        )
        subtitle_label.pack(pady=(0, 20), padx=20)

        # ==================== SECTION 1: FILE UPLOAD ====================
        upload_section = ttk.LabelFrame(main_container, text="📁 File Upload", padding=15)
        upload_section.pack(fill='x', padx=10, pady=8)

        btn_upload = ttk.Button(
            upload_section,
            text="+ Add Files (CSV/XLSX)",
            command=self.combine_pivot_browse_files,
            style='Accent.TButton',
            width=25
        )
        btn_upload.pack(pady=(0, 10))

        # File list container
        self.combine_pivot_files_container = ttk.Frame(upload_section)
        self.combine_pivot_files_container.pack(fill='both', expand=True)

        # Buttons for file management
        file_btn_frame = ttk.Frame(upload_section)
        file_btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(
            file_btn_frame,
            text="Clear All Files",
            command=self.combine_pivot_clear_files,
            width=18
        ).pack(side='left', padx=5)

        # ==================== SECTION 2: HEADER NORMALIZATION OPTIONS ====================
        norm_section = ttk.LabelFrame(main_container, text="⚙️ Header Normalization Options", padding=15)
        norm_section.pack(fill='x', padx=10, pady=8)

        ttk.Label(
            norm_section,
            text="Allow minor header differences:",
            font=('Segoe UI', 10, 'bold')
        ).pack(anchor='w', pady=(0, 8))

        self.normalize_lowercase_var = tk.BooleanVar(value=False)
        self.normalize_whitespace_var = tk.BooleanVar(value=True)
        self.normalize_special_chars_var = tk.BooleanVar(value=False)
        self.normalize_underscores_var = tk.BooleanVar(value=False)

        # Normalization option checkboxes
        options = [
            (self.normalize_lowercase_var, "Lowercase headers (allows 'Name' vs 'name')"),
            (self.normalize_whitespace_var, "Trim whitespace (allows ' Name ' vs 'Name')"),
            (self.normalize_special_chars_var, "Remove special characters (allows 'Name!' vs 'Name')"),
            (self.normalize_underscores_var, "Normalize underscores/spaces (allows 'first_name' vs 'first name')")
        ]

        for var, text in options:
            chk = ttk.Checkbutton(
                norm_section,
                text=text,
                variable=var,
                command=self.combine_pivot_update_options
            )
            chk.pack(anchor='w', pady=3, padx=20)

        # ==================== SECTION 3: SUMMARY & VALIDATION ====================
        summary_section = ttk.LabelFrame(main_container, text="📊 Summary & Validation", padding=15)
        summary_section.pack(fill='x', padx=10, pady=8)

        self.combine_pivot_summary_text = tk.Text(
            summary_section,
            height=7,
            font=('Consolas', 9),
            wrap='word',
            state='disabled',
            bg='#FAFAFA'
        )
        self.combine_pivot_summary_text.pack(fill='x')

        # ==================== SECTION 4: COMBINE ACTION ====================
        action_section = ttk.LabelFrame(main_container, text="🚀 Combine Action", padding=15)
        action_section.pack(fill='x', padx=10, pady=(8, 20))

        action_frame = ttk.Frame(action_section)
        action_frame.pack(fill='x')

        self.combine_pivot_btn = ttk.Button(
            action_frame,
            text="▶ Combine Files",
            command=self.combine_pivot_execute,
            style='Success.TButton',
            width=30,
            state='disabled'
        )
        self.combine_pivot_btn.pack(side='left', padx=(0, 10))

        self.combine_pivot_preview_btn = ttk.Button(
            action_frame,
            text="👁️ Preview Combined Data",
            command=self.combine_pivot_preview,
            width=30,
            state='disabled'
        )
        self.combine_pivot_preview_btn.pack(side='left')

        # Initialize summary
        self.combine_pivot_update_summary()

        self.combine_pivot_panel_visible = False

    def combine_pivot_add_file_widget(self, file_info):
        """Add a file entry with sheet selector to the files container

        IMPORTANT: This creates an independent widget for EACH file.
        Excel files get their own sheet selector dropdown.
        """
        file_path = file_info['path']
        file_name = file_info['name']
        file_type = file_info['type']

        # Create frame for this file
        file_frame = ttk.Frame(self.combine_pivot_files_container, relief='solid', borderwidth=1)
        file_frame.pack(fill='x', pady=5, padx=5)

        # File info row
        info_frame = ttk.Frame(file_frame)
        info_frame.pack(fill='x', padx=10, pady=8)

        # File icon and name
        icon = "📊" if file_type == 'excel' else "📄"
        file_label = ttk.Label(
            info_frame,
            text=f"{icon} {file_name}",
            font=('Segoe UI', 10, 'bold')
        )
        file_label.pack(side='left')

        # Remove button
        remove_btn = ttk.Button(
            info_frame,
            text="✕",
            command=lambda: self.combine_pivot_remove_file_by_path(file_path),
            width=3
        )
        remove_btn.pack(side='right')

        # Details row
        details_frame = ttk.Frame(file_frame)
        details_frame.pack(fill='x', padx=10, pady=(0, 8))

        details_text = f"{file_info['rows']} rows × {file_info['columns']} columns"
        ttk.Label(details_frame, text=details_text, font=('Segoe UI', 9), foreground='#666').pack(side='left')

        # Sheet selector for Excel files - EVERY Excel file gets its own dropdown + Apply button
        sheet_combo = None
        apply_btn = None
        if file_type == 'excel':
            sheet_frame = ttk.Frame(file_frame)
            sheet_frame.pack(fill='x', padx=10, pady=(0, 8))

            ttk.Label(sheet_frame, text="Sheet:", font=('Segoe UI', 9)).pack(side='left', padx=(0, 5))

            # Get all sheets for this specific file
            sheets = self.combine_pivot_engine.get_excel_sheets(file_path)

            # Check if there's a previously selected sheet for this file, otherwise use current
            current_sheet = self.combine_pivot_file_sheets.get(file_path, file_info.get('sheet', sheets[0] if sheets else ''))
            sheet_var = tk.StringVar(value=current_sheet)

            sheet_combo = ttk.Combobox(
                sheet_frame,
                textvariable=sheet_var,
                values=sheets,
                state='readonly',
                width=20,  # Per spec: 18-22 chars
                font=('Segoe UI', 9)
            )
            sheet_combo.pack(side='left', padx=(0, 5))

            # Apply button - user must click to apply sheet selection
            def on_apply_sheet():
                """Apply the selected sheet for this specific file"""
                new_sheet = sheet_var.get()

                # Store the selection
                self.combine_pivot_file_sheets[file_path] = new_sheet

                # Reload file with new sheet
                try:
                    new_df = self.combine_pivot_engine.load_excel(file_path, new_sheet)

                    # Update file info in engine
                    for f in self.combine_pivot_engine.loaded_files:
                        if f['path'] == file_path:
                            f['df'] = new_df
                            f['sheet'] = new_sheet
                            f['rows'] = len(new_df)
                            f['columns'] = len(new_df.columns)
                            f['headers'] = new_df.columns.tolist()

                            # Update UI details display
                            details_text = f"{f['rows']} rows × {f['columns']} columns"
                            for widget in details_frame.winfo_children():
                                widget.destroy()
                            ttk.Label(details_frame, text=details_text, font=('Segoe UI', 9), foreground='#666').pack(side='left')
                            break

                    # Re-run validation with new data
                    self.combine_pivot_update_summary()

                    self.status_var.set(f"✓ Applied sheet '{new_sheet}' for {file_name}")

                except Exception as e:
                    logging.error(f"Error applying sheet: {e}")
                    messagebox.showerror("Error", f"Failed to apply sheet '{new_sheet}':\n\n{str(e)}")

            apply_btn = ttk.Button(
                sheet_frame,
                text="Apply Sheet",
                command=on_apply_sheet,
                width=12
            )
            apply_btn.pack(side='left', padx=(0, 5))

        # Store widget reference
        widget_info = {
            'file_path': file_path,
            'frame': file_frame,
            'sheet_combo': sheet_combo,
            'apply_btn': apply_btn,
            'file_type': file_type
        }
        self.combine_pivot_file_widgets.append(widget_info)

    def combine_pivot_browse_files(self):
        """Browse and add CSV/XLSX files to combine queue"""
        file_paths = filedialog.askopenfilenames(
            title="Select CSV or Excel files to combine",
            filetypes=[
                ("Supported files", "*.csv *.txt *.xlsx *.xls *.xlsm"),
                ("CSV files", "*.csv *.txt"),
                ("Excel files", "*.xlsx *.xls *.xlsm"),
                ("All files", "*.*")
            ]
        )

        if not file_paths:
            return

        for file_path in file_paths:
            try:
                ext = Path(file_path).suffix.lower()

                # For Excel files, use first sheet by default (user can change it in the dropdown)
                sheet_name = None
                if ext in ['.xlsx', '.xls', '.xlsm']:
                    sheets = self.combine_pivot_engine.get_excel_sheets(file_path)
                    sheet_name = sheets[0] if sheets else None

                # Add file to engine
                file_info = self.combine_pivot_engine.add_file(file_path, sheet_name)

                # Add file widget to UI
                self.combine_pivot_add_file_widget(file_info)

                self.status_var.set(f"Added {file_info['name']}")

            except Exception as e:
                logging.error(f"Error adding file {file_path}: {e}")
                messagebox.showerror("Error", f"Failed to add file:\n\n{str(e)}")

        # Update summary
        self.combine_pivot_update_summary()

    def combine_pivot_update_options(self):
        """Update normalization options in engine"""
        # Update engine normalization settings
        self.combine_pivot_engine.normalize_lowercase = self.normalize_lowercase_var.get()
        self.combine_pivot_engine.normalize_whitespace = self.normalize_whitespace_var.get()

        # Note: special_chars and underscores normalization will be added to engine later if needed
        # For now, just track them in the UI

        # Re-validate if files are loaded
        if len(self.combine_pivot_engine.loaded_files) >= 2:
            self.combine_pivot_update_summary()

    def combine_pivot_update_summary(self):
        """Update summary panel with file info and validation status"""
        self.combine_pivot_summary_text.config(state='normal')
        self.combine_pivot_summary_text.delete('1.0', tk.END)

        if not self.combine_pivot_engine.loaded_files:
            self.combine_pivot_summary_text.insert('1.0', "No files loaded")
            self.combine_pivot_summary_text.config(state='disabled')
            self.combine_pivot_btn.config(state='disabled')
            self.combine_pivot_preview_btn.config(state='disabled')
            return

        summary = self.combine_pivot_engine.get_summary()

        # Display file count and summary
        summary_text = f"📁 Files loaded: {summary['file_count']}\n"
        summary_text += f"📊 Total rows (combined): {summary['total_rows']:,}\n"
        summary_text += f"📋 Column count: {summary['column_count']}\n"
        summary_text += f"📝 Headers: {', '.join([str(h) for h in summary['headers'][:5]])}{'...' if summary['column_count'] > 5 else ''}\n\n"

        # Validate headers if 2+ files
        if len(self.combine_pivot_engine.loaded_files) >= 2:
            dataframes = [f['df'] for f in self.combine_pivot_engine.loaded_files]
            is_valid, error_msg = self.combine_pivot_engine.validate_headers(dataframes)

            if is_valid:
                summary_text += "✅ VALIDATION PASSED\n"
                summary_text += "All files have identical headers and column counts.\n"
                summary_text += "Ready to combine!"

                # Enable buttons
                self.combine_pivot_btn.config(state='normal')
                self.combine_pivot_preview_btn.config(state='normal')
            else:
                summary_text += "❌ VALIDATION FAILED\n"
                summary_text += error_msg

                # Disable buttons
                self.combine_pivot_btn.config(state='disabled')
                self.combine_pivot_preview_btn.config(state='disabled')
        else:
            summary_text += "⚠️ Add at least 2 files to combine"
            self.combine_pivot_btn.config(state='disabled')
            self.combine_pivot_preview_btn.config(state='disabled')

        self.combine_pivot_summary_text.insert('1.0', summary_text)
        self.combine_pivot_summary_text.config(state='disabled')

    def combine_pivot_remove_file_by_path(self, file_path):
        """Remove a specific file from combine queue by path"""
        # Remove from engine
        self.combine_pivot_engine.remove_file(file_path)

        # Remove from file sheets dict
        self.combine_pivot_file_sheets.pop(file_path, None)

        # Find and remove widget
        widget_to_remove = None
        for widget_info in self.combine_pivot_file_widgets:
            if widget_info['file_path'] == file_path:
                widget_to_remove = widget_info
                break

        if widget_to_remove:
            widget_to_remove['frame'].destroy()
            self.combine_pivot_file_widgets.remove(widget_to_remove)

        # Update summary
        self.combine_pivot_update_summary()

    def combine_pivot_clear_files(self):
        """Clear all files from combine queue"""
        # Clear engine
        self.combine_pivot_engine.clear_files()

        # Clear file sheets dict
        self.combine_pivot_file_sheets.clear()

        # Destroy all file widgets
        for widget_info in self.combine_pivot_file_widgets:
            widget_info['frame'].destroy()
        self.combine_pivot_file_widgets.clear()

        # Update summary
        self.combine_pivot_update_summary()
        self.status_var.set("Cleared all files")

    def combine_pivot_execute(self):
        """Execute file combination"""
        if len(self.combine_pivot_engine.loaded_files) < 2:
            messagebox.showwarning("Not Enough Files", "Please add at least 2 files to combine")
            return

        try:
            # Get all dataframes
            dataframes = [f['df'] for f in self.combine_pivot_engine.loaded_files]

            # Validate headers
            is_valid, error_msg = self.combine_pivot_engine.validate_headers(dataframes)
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return

            # Combine dataframes
            combined_df = self.combine_pivot_engine.combine_dataframes(dataframes)

            # Show success message
            summary = self.combine_pivot_engine.get_summary()
            messagebox.showinfo(
                "Files Combined",
                f"Successfully combined {summary['file_count']} files!\n\n"
                f"Total rows: {len(combined_df):,}\n"
                f"Columns: {len(combined_df.columns)}\n\n"
                "Click OK to select export location."
            )

            # Show export dialog
            self.combine_pivot_export_dialog(combined_df, summary)

        except Exception as e:
            logging.error(f"Combine pivot execution error: {e}", exc_info=True)
            messagebox.showerror("Combine Error", f"Failed to combine files:\n\n{str(e)}")

    def combine_pivot_export_dialog(self, combined_df, summary):
        """Show export dialog for combined pivot data"""
        # Ask for output format
        format_dialog = tk.Toplevel(self.root)
        format_dialog.title("Select Output Format")
        format_dialog.geometry("400x200")
        format_dialog.transient(self.root)
        format_dialog.grab_set()

        ttk.Label(
            format_dialog,
            text="Select output format:",
            font=('Segoe UI', 11, 'bold')
        ).pack(pady=20)

        format_var = tk.StringVar(value='csv')

        ttk.Radiobutton(format_dialog, text="CSV (UTF-8)", variable=format_var, value='csv').pack(pady=5)
        ttk.Radiobutton(format_dialog, text="Excel (.xlsx)", variable=format_var, value='xlsx').pack(pady=5)

        selected_format = [None]

        def on_ok():
            selected_format[0] = format_var.get()
            format_dialog.destroy()

        ttk.Button(format_dialog, text="OK", command=on_ok, width=15).pack(pady=15)

        format_dialog.wait_window()

        if not selected_format[0]:
            return

        # Ask for save location
        if selected_format[0] == 'csv':
            output_path = filedialog.asksaveasfilename(
                title="Save Combined CSV",
                defaultextension='.csv',
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
        else:
            output_path = filedialog.asksaveasfilename(
                title="Save Combined Excel",
                defaultextension='.xlsx',
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )

        if not output_path:
            return

        try:
            # Export
            if selected_format[0] == 'csv':
                self.combine_pivot_engine.export_csv(combined_df, output_path)
            else:
                self.combine_pivot_engine.export_excel(combined_df, output_path)

            messagebox.showinfo(
                "Export Successful",
                f"Combined file saved successfully!\n\n"
                f"Location: {output_path}\n"
                f"Rows: {len(combined_df):,}\n"
                f"Columns: {len(combined_df.columns)}\n\n"
                f"Format: {selected_format[0].upper()}"
            )

            self.status_var.set(f"Exported combined file: {Path(output_path).name}")

        except Exception as e:
            logging.error(f"Export error: {e}", exc_info=True)
            messagebox.showerror("Export Error", f"Failed to export file:\n\n{str(e)}")

    def combine_pivot_preview(self):
        """Preview combined dataset"""
        if len(self.combine_pivot_engine.loaded_files) < 2:
            messagebox.showwarning("Not Enough Files", "Please add at least 2 files to combine")
            return

        try:
            # Get all dataframes
            dataframes = [f['df'] for f in self.combine_pivot_engine.loaded_files]

            # Validate headers
            is_valid, error_msg = self.combine_pivot_engine.validate_headers(dataframes)
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return

            # Combine dataframes
            combined_df = self.combine_pivot_engine.combine_dataframes(dataframes)

            # Show preview dialog
            preview_dialog = tk.Toplevel(self.root)
            preview_dialog.title("Preview Combined Dataset")
            preview_dialog.geometry("1000x600")
            preview_dialog.transient(self.root)

            ttk.Label(
                preview_dialog,
                text=f"Preview: First 200 rows of {len(combined_df):,} total rows",
                font=('Segoe UI', 11, 'bold')
            ).pack(pady=10)

            # Create preview area
            preview_frame = ttk.Frame(preview_dialog)
            preview_frame.pack(fill='both', expand=True, padx=10, pady=10)

            # Scrollbars
            x_scrollbar = ttk.Scrollbar(preview_frame, orient='horizontal')
            y_scrollbar = ttk.Scrollbar(preview_frame, orient='vertical')

            # Text widget for preview
            preview_text = tk.Text(
                preview_frame,
                font=('Consolas', 9),
                wrap='none',
                xscrollcommand=x_scrollbar.set,
                yscrollcommand=y_scrollbar.set
            )

            x_scrollbar.config(command=preview_text.xview)
            y_scrollbar.config(command=preview_text.yview)

            x_scrollbar.pack(side='bottom', fill='x')
            y_scrollbar.pack(side='right', fill='y')
            preview_text.pack(side='left', fill='both', expand=True)

            # Show first 200 rows
            preview_df = combined_df.head(200)
            preview_text.insert('1.0', preview_df.to_string(index=False))
            preview_text.config(state='disabled')

            ttk.Button(preview_dialog, text="Close", command=preview_dialog.destroy).pack(pady=10)

        except Exception as e:
            logging.error(f"Preview error: {e}", exc_info=True)
            messagebox.showerror("Preview Error", f"Failed to preview data:\n\n{str(e)}")

    # ==================== SPLIT PANE HELPER METHODS ====================

    def copy_workflow_to_selected(self, source_file_name):
        """Copy workflow from source file to selected files"""
        if not hasattr(self, 'file_list_panel'):
            return

        # Find source file
        source_file = None
        for f in self.loaded_files:
            if f['name'] == source_file_name:
                source_file = f
                break

        if not source_file:
            messagebox.showwarning("No Source", "Source file not found")
            return

        # Check if source has operations
        source_ops = source_file.get('operations', [])
        if not source_ops:
            messagebox.showwarning("No Workflow", "Source file has no workflow operations to copy")
            return

        # Get selected files
        selected_files = self.file_list_panel.get_selected_files()
        if not selected_files:
            messagebox.showwarning("No Selection", "Please select files to copy workflow to")
            return

        print(f"[DEBUG] Copying workflow from '{source_file_name}' to {len(selected_files)} file(s)")
        print(f"[DEBUG] Source has {len(source_ops)} operations")

        copied_count = 0

        for file_obj in selected_files:
            if file_obj != source_file:
                # CRITICAL: Deep copy operations to prevent shared references between files
                file_obj['operations'] = copy.deepcopy(source_ops)

                # Remove preset association since workflow is now manually copied
                file_obj.pop('preset_name', None)

                copied_count += 1
                print(f"[DEBUG] Copied workflow to '{file_obj['name']}' - now has {len(file_obj['operations'])} operations")

        # Refresh UI for all affected files
        # If currently viewing one of the target files, refresh its display
        if hasattr(self, 'file_detail_panel') and self.file_detail_panel.current_file:
            if self.file_detail_panel.current_file in selected_files:
                print(f"[DEBUG] Refreshing UI for currently selected file")
                self.file_detail_panel.show_file(self.file_detail_panel.current_file)

        messagebox.showinfo(
            "Success",
            f"Copied workflow with {len(source_ops)} operation(s) to {copied_count} file(s)"
        )

        print(f"[DEBUG] Workflow copy completed successfully")

    def apply_preset_to_selected_files(self, preset_name):
        """Apply a preset to selected files"""
        if not preset_name:
            return

        if not hasattr(self, 'file_list_panel'):
            return

        # Get selected files
        selected_files = self.file_list_panel.get_selected_files()
        if not selected_files:
            messagebox.showwarning("No Selection", "Please select files to apply preset to")
            return

        # Load preset
        preset = self.preset_manager.load_preset(preset_name)
        if not preset:
            messagebox.showerror("Error", f"Preset '{preset_name}' not found")
            return

        # Apply to each selected file
        applied_count = 0
        for file_obj in selected_files:
            file_obj['operations'] = preset.operations.copy()
            applied_count += 1

        messagebox.showinfo("Success", f"Applied preset '{preset_name}' to {applied_count} files")

        # Refresh display
        if hasattr(self, 'file_detail_panel') and self.file_detail_panel.current_file in selected_files:
            self.file_detail_panel.show_file(self.file_detail_panel.current_file)

    def run_workflow_for_file(self, file_obj):
        """Run workflow for a single file"""
        if not file_obj or not file_obj.get('operations'):
            messagebox.showwarning("No Workflow", "No operations to run")
            return

        try:
            self.status_var.set(f"Processing {file_obj['name']}...")

            # Execute operations
            result = self.executor.execute(file_obj['df'], file_obj['operations'])

            # Store results
            file_obj['result_df'] = result['result']
            file_obj['removed_df'] = result.get('removed', None)

            self.status_var.set(f"Processed {file_obj['name']} successfully")
            messagebox.showinfo("Success", f"Processed {file_obj['name']}\n\n"
                              f"Original rows: {len(file_obj['df'])}\n"
                              f"Result rows: {len(result['result'])}")

            # Refresh display
            if hasattr(self, 'file_detail_panel'):
                self.file_detail_panel.show_file(file_obj)

        except Exception as e:
            logging.error(f"Failed to process {file_obj['name']}: {e}")
            messagebox.showerror("Processing Error", f"Failed to process {file_obj['name']}:\n{str(e)}")

    def export_batch_results(self, export_type):
        """Export batch processing results"""
        if not self.loaded_files:
            messagebox.showwarning("No Files", "No files loaded")
            return

        # Get files with results
        results = [f for f in self.loaded_files if f.get('result_df') is not None]

        if not results:
            messagebox.showwarning("No Results", "No processed results to export.\n\nPlease process files first.")
            return

        if export_type == "zip":
            # Export as ZIP
            output_path = filedialog.asksaveasfilename(
                title="Save ZIP Archive",
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip")]
            )
            if output_path:
                success = ExportHelper.export_batch_as_zip(results, output_path, 'xlsx', False)
                if success:
                    messagebox.showinfo("Success", f"Exported {len(results)} files to ZIP archive")

        elif export_type == "individual":
            # Export to folder
            output_dir = filedialog.askdirectory(title="Select Output Folder")
            if output_dir:
                count = ExportHelper.export_batch_individual(results, output_dir, 'xlsx', False)
                messagebox.showinfo("Success", f"Exported {count} files to {output_dir}")

        elif export_type == "combined":
            # Combine and export
            try:
                combined_df = self.file_combiner.combine_files_simple(results, 'all')
                self.show_combined_export_dialog(combined_df)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to combine files:\n{str(e)}")


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
        # Use preview state to show columns as they will be after current operations
        current_df = self.get_current_dataframe_state()
        if current_df is None:
            return []

        columns = []
        for idx, col in enumerate(current_df.columns):
            letter = self._get_column_letter(idx)
            columns.append(f"{letter}: {col}")
        return columns

    def get_current_dataframe_state(self):
        """Get current dataframe state after preview execution of queued operations"""
        if self.df is None:
            return None

        # If no operations in queue, return original
        if not self.operation_queue:
            return self.df

        # Execute operations in preview mode
        preview_df = self.executor.preview_execute_queue(self.df, self.operation_queue)
        return preview_df if preview_df is not None else self.df

    def update_preview_state(self):
        """Update preview display to show results after current operations"""
        try:
            preview_df = self.get_current_dataframe_state()
            if preview_df is not None:
                # Show preview in results tab
                self.enhanced_preview.load_dataframe(preview_df, is_result=True)

                # Update status
                op_count = len([op for op in self.operation_queue if op.get('enabled', True)])
                if op_count > 0:
                    self.status_var.set(f"Preview: {op_count} operation(s) queued | {len(preview_df):,} rows")
                else:
                    self.status_var.set(f"Loaded: {len(self.df):,} rows")
        except Exception as e:
            logging.error(f"Error updating preview state: {e}")

    def open_reorder_columns_dialog(self):
        """Open the column reordering dialog"""
        current_df = self.get_current_dataframe_state()

        if current_df is None:
            messagebox.showwarning("No Data", "Please load a file first")
            return

        if len(current_df.columns) == 0:
            messagebox.showwarning("No Columns", "No columns available to reorder")
            return

        # Get column list with letters (uses preview state)
        columns = self.get_column_list_with_letters()

        # Get the reorder columns operation from registry
        from operations.registry import registry
        operation = registry.get_by_id('data_reorder_columns')

        if operation:
            # Show the reorder dialog
            self._show_reorder_columns_dialog(operation, columns)
        else:
            messagebox.showerror("Error", "Reorder columns operation not found")


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
    

    def add_operation_by_id(self, operation_id):
        """
        Add operation to queue by ID (for ribbon buttons)

        Args:
            operation_id: Operation ID to add
        """
        if self.df is None:
            messagebox.showwarning("No Data", "Please load a file first")
            return

        operation = registry.get_by_id(operation_id)
        if not operation:
            messagebox.showerror("Error", f"Operation {operation_id} not found")
            return

        # Show parameter dialog
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

        if operation.metadata.id == 'add_column_smart':
            # Use specialized Add Column Smart dialog with conditional visibility
            self._show_add_column_smart_dialog(operation, columns)
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

    def _show_add_column_smart_dialog(self, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Custom dialog for Add Column Smart operation with conditional field visibility"""
        from ui.widgets.scrollable_frame import ScrollableOperationFrame

        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("700x700")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create scrollable content area
        scrollable = ScrollableOperationFrame(dialog)
        scrollable.pack(fill='both', expand=True, padx=10, pady=(10, 0))
        main_frame = scrollable.scroll_frame

        # Title and description
        ttk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(10, 10), padx=10)

        ttk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=650,
            font=('Arial', 11)
        ).pack(pady=(0, 5), padx=10)

        ttk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Arial', 10),
            foreground='gray'
        ).pack(pady=(0, 20), padx=10)

        param_widgets = {}
        param_frames = {}  # Store frames for show/hide logic

        # New column name (always visible)
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill='x', pady=10, padx=10)
        ttk.Label(name_frame, text="Name for the new column *", font=('Arial', 11, 'bold')).pack(anchor='w')
        name_entry = ttk.Entry(name_frame, font=('Arial', 12))
        if current_params and 'new_column_name' in current_params:
            name_entry.insert(0, current_params['new_column_name'])
        name_entry.pack(fill='x', pady=2)
        param_widgets['new_column_name'] = name_entry

        # Mode selector (always visible)
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(fill='x', pady=10, padx=10)
        ttk.Label(mode_frame, text="How to populate the column *", font=('Arial', 11, 'bold')).pack(anchor='w')
        mode_var = tk.StringVar(value=current_params.get('mode', 'constant') if current_params else 'constant')
        mode_combo = ttk.Combobox(mode_frame, textvariable=mode_var,
                                  values=['constant', 'timestamp', 'smart'],
                                  font=('Arial', 12), state='readonly')
        mode_combo.pack(fill='x', pady=2)
        param_widgets['mode'] = mode_var

        # Constant mode fields
        constant_frame = ttk.Frame(main_frame)
        param_frames['constant'] = constant_frame
        ttk.Label(constant_frame, text="Value to fill (for Constant mode) *", font=('Arial', 11, 'bold')).pack(anchor='w')
        constant_entry = ttk.Entry(constant_frame, font=('Arial', 12))
        if current_params and 'constant_value' in current_params:
            constant_entry.insert(0, current_params['constant_value'])
        constant_entry.pack(fill='x', pady=2)
        param_widgets['constant_value'] = constant_entry

        # Timestamp mode fields
        timestamp_frame = ttk.Frame(main_frame)
        param_frames['timestamp'] = timestamp_frame
        ttk.Label(timestamp_frame, text="Date/time format (for Timestamp mode)", font=('Arial', 11, 'bold')).pack(anchor='w')
        timestamp_var = tk.StringVar(value=current_params.get('timestamp_format', 'YYYY-MM-DD') if current_params else 'YYYY-MM-DD')
        timestamp_combo = ttk.Combobox(timestamp_frame, textvariable=timestamp_var,
                                      values=['YYYY-MM-DD', 'MM/DD/YYYY', 'ISO'],
                                      font=('Arial', 12), state='readonly')
        timestamp_combo.pack(fill='x', pady=2)
        param_widgets['timestamp_format'] = timestamp_var

        # Smart mode - rule selector
        smart_rule_frame = ttk.Frame(main_frame)
        param_frames['smart_rule'] = smart_rule_frame
        ttk.Label(smart_rule_frame, text="Smart rule to apply (for Smart mode) *", font=('Arial', 11, 'bold')).pack(anchor='w')
        smart_rule_var = tk.StringVar(value=current_params.get('smart_rule', 'country_from_location') if current_params else 'country_from_location')
        smart_rule_combo = ttk.Combobox(smart_rule_frame, textvariable=smart_rule_var,
                                       values=['country_from_location', 'email_domain', 'parse_name'],
                                       font=('Arial', 12), state='readonly')
        smart_rule_combo.pack(fill='x', pady=2)
        param_widgets['smart_rule'] = smart_rule_var

        # Country detection fields
        city_frame = ttk.Frame(main_frame)
        param_frames['city_column'] = city_frame
        city_selector = ColumnSelector(city_frame, columns, "City column (for country detection) *")
        city_selector.pack(fill='x')
        if current_params and 'city_column' in current_params:
            city_selector.set_value(current_params['city_column'])
        param_widgets['city_column'] = city_selector

        state_frame = ttk.Frame(main_frame)
        param_frames['state_column'] = state_frame
        state_selector = ColumnSelector(state_frame, columns, "State column (for country detection) *")
        state_selector.pack(fill='x')
        if current_params and 'state_column' in current_params:
            state_selector.set_value(current_params['state_column'])
        param_widgets['state_column'] = state_selector

        zip_frame = ttk.Frame(main_frame)
        param_frames['zip_column'] = zip_frame
        zip_selector = ColumnSelector(zip_frame, columns, "ZIP code column (for country detection) *")
        zip_selector.pack(fill='x')
        if current_params and 'zip_column' in current_params:
            zip_selector.set_value(current_params['zip_column'])
        param_widgets['zip_column'] = zip_selector

        # Email domain fields
        email_frame = ttk.Frame(main_frame)
        param_frames['email_column'] = email_frame
        email_selector = ColumnSelector(email_frame, columns, "Email column (for domain extraction) *")
        email_selector.pack(fill='x')
        if current_params and 'email_column' in current_params:
            email_selector.set_value(current_params['email_column'])
        param_widgets['email_column'] = email_selector

        # Name parsing fields
        full_name_frame = ttk.Frame(main_frame)
        param_frames['full_name_column'] = full_name_frame
        full_name_selector = ColumnSelector(full_name_frame, columns, "Full name column (for name parsing) *")
        full_name_selector.pack(fill='x')
        if current_params and 'full_name_column' in current_params:
            full_name_selector.set_value(current_params['full_name_column'])
        param_widgets['full_name_column'] = full_name_selector

        name_part_frame = ttk.Frame(main_frame)
        param_frames['name_part'] = name_part_frame
        ttk.Label(name_part_frame, text="Choose which name part to extract *", font=('Arial', 11, 'bold')).pack(anchor='w')
        name_part_var = tk.StringVar(value=current_params.get('name_part', 'first') if current_params else 'first')
        name_part_combo = ttk.Combobox(name_part_frame, textvariable=name_part_var,
                                      values=['first', 'last'],
                                      font=('Arial', 12), state='readonly')
        name_part_combo.pack(fill='x', pady=2)
        param_widgets['name_part'] = name_part_var

        def update_visibility(*args):
            """Update field visibility based on mode and smart_rule selection"""
            mode = mode_var.get()
            smart_rule = smart_rule_var.get()

            # Hide all conditional frames first
            for frame in param_frames.values():
                frame.pack_forget()

            # Show relevant frames based on mode
            if mode == 'constant':
                constant_frame.pack(fill='x', pady=10, padx=10)

            elif mode == 'timestamp':
                timestamp_frame.pack(fill='x', pady=10, padx=10)

            elif mode == 'smart':
                smart_rule_frame.pack(fill='x', pady=10, padx=10)

                # Show fields based on smart rule
                if smart_rule == 'country_from_location':
                    city_frame.pack(fill='x', pady=10, padx=10)
                    state_frame.pack(fill='x', pady=10, padx=10)
                    zip_frame.pack(fill='x', pady=10, padx=10)

                elif smart_rule == 'email_domain':
                    email_frame.pack(fill='x', pady=10, padx=10)

                elif smart_rule == 'parse_name':
                    full_name_frame.pack(fill='x', pady=10, padx=10)
                    name_part_frame.pack(fill='x', pady=10, padx=10)

        # Bind visibility updates
        mode_var.trace('w', update_visibility)
        smart_rule_var.trace('w', update_visibility)

        # Initialize visibility
        update_visibility()

        def on_add():
            """Validate and add/update operation"""
            params = {
                'new_column_name': name_entry.get().strip(),
                'mode': mode_var.get(),
            }

            # Validate new column name
            if not params['new_column_name']:
                messagebox.showerror("Validation Error", "Please enter a name for the new column.")
                return

            mode = params['mode']

            # Collect mode-specific parameters and validate
            if mode == 'constant':
                params['constant_value'] = constant_entry.get()
                if not params['constant_value']:
                    messagebox.showerror("Validation Error", "Constant value is required for Constant mode.")
                    return

            elif mode == 'timestamp':
                params['timestamp_format'] = timestamp_var.get()

            elif mode == 'smart':
                params['smart_rule'] = smart_rule_var.get()
                smart_rule = params['smart_rule']

                if smart_rule == 'country_from_location':
                    params['city_column'] = city_selector.get_value()
                    params['state_column'] = state_selector.get_value()
                    params['zip_column'] = zip_selector.get_value()

                    missing = []
                    if not params['city_column'] or not params['city_column'].strip():
                        missing.append('City')
                    if not params['state_column'] or not params['state_column'].strip():
                        missing.append('State')
                    if not params['zip_column'] or not params['zip_column'].strip():
                        missing.append('ZIP')

                    if missing:
                        messagebox.showerror(
                            "Validation Error",
                            f"Country detection requires City, State, and ZIP columns. Please select all three.\n\nMissing: {', '.join(missing)}"
                        )
                        return

                elif smart_rule == 'email_domain':
                    params['email_column'] = email_selector.get_value()
                    if not params['email_column'] or not params['email_column'].strip():
                        messagebox.showerror(
                            "Validation Error",
                            "Email domain extraction requires selecting an Email column."
                        )
                        return

                elif smart_rule == 'parse_name':
                    params['full_name_column'] = full_name_selector.get_value()
                    params['name_part'] = name_part_var.get()

                    if not params['full_name_column'] or not params['full_name_column'].strip():
                        messagebox.showerror(
                            "Validation Error",
                            "Name parsing requires a Full Name column and selecting whether to extract 'first' or 'last'."
                        )
                        return

            # All validation passed - add to queue
            if edit_mode:
                # Update existing operation in queue
                self.operation_queue[edit_index] = {
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': self.operation_queue[edit_index]['enabled']
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
            # Save workflow changes to active sheet
            self._save_current_workflow()
            dialog.destroy()

        # Buttons (fixed at bottom)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10, padx=10)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        button_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=button_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)

    def _show_single_column_dialog(self, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Show dialog with smart single column selector"""
        from ui.widgets.scrollable_frame import ScrollableOperationFrame

        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create scrollable content area
        scrollable = ScrollableOperationFrame(dialog)
        scrollable.pack(fill='both', expand=True, padx=10, pady=(10, 0))

        # Use scroll_frame as the container for all content
        main_frame = scrollable.scroll_frame

        # Title and description
        ttk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(10, 10), padx=10)

        ttk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=550,
            font=('Arial', 11)
        ).pack(pady=(0, 5), padx=10)

        ttk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Arial', 10),
            foreground='gray'
        ).pack(pady=(0, 20), padx=10)

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
            # Save workflow changes to active sheet
            self._save_current_workflow()
            dialog.destroy()

        # Fixed button frame at the bottom (NOT in scrollable area)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10, padx=10)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        button_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=button_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)


    def _show_multi_column_dialog(self, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Show dialog with smart multi-column selector"""
        from ui.widgets.scrollable_frame import ScrollableOperationFrame

        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create scrollable container for all content
        scrollable = ScrollableOperationFrame(dialog)
        scrollable.pack(fill='both', expand=True, padx=10, pady=(10, 0))
        main_frame = scrollable.scroll_frame

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
            # Save workflow changes to active sheet
            self._save_current_workflow()
            dialog.destroy()

        # Buttons (fixed at bottom, not in scrollable area)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10, padx=10)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        button_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=button_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)


    def _show_standard_parameter_dialog(self, operation, edit_mode=False, edit_index=None, current_params=None):
        """Standard parameter dialog for operations without column selection"""
        from ui.widgets.scrollable_frame import ScrollableOperationFrame

        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create scrollable content area
        scrollable = ScrollableOperationFrame(dialog)
        scrollable.pack(fill='both', expand=True, padx=10, pady=(10, 0))

        # Use scroll_frame as the container for all content
        main_frame = scrollable.scroll_frame

        # Title and description
        ttk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(10, 10), padx=10)

        ttk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=550,
            font=('Arial', 11)
        ).pack(pady=(0, 5), padx=10)

        ttk.Label(
            main_frame,
            text=f"Excel equivalent: {operation.metadata.excel_equivalent}",
            font=('Arial', 10),
            foreground='gray'
        ).pack(pady=(0, 20), padx=10)

        param_widgets = {}

        for param in operation.metadata.parameters:
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=8, padx=10)

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

            elif param.type == 'column_rename_list':
                # Special widget for column renaming with dynamic add/remove rows
                from ui.widgets.column_rename_widget import ColumnRenameWidget

                # Get current columns for dropdown
                columns = self.get_column_list_with_letters() if hasattr(self, 'get_column_list_with_letters') else []

                # Create the rename widget
                widget = ColumnRenameWidget(frame, columns)
                widget.pack(fill='both', expand=True, pady=2)

                # Pre-fill mappings if in edit mode
                if current_value and isinstance(current_value, list):
                    widget.set_mappings(current_value)

                param_widgets[param.name] = widget

        def on_add():
            from ui.widgets.column_rename_widget import ColumnRenameWidget

            params = {}
            for param in operation.metadata.parameters:
                widget = param_widgets.get(param.name)
                if widget:
                    if isinstance(widget, tk.BooleanVar):
                        params[param.name] = widget.get()
                    elif isinstance(widget, ColumnRenameWidget):
                        # Get mappings from the column rename widget
                        mappings = widget.get_mappings()
                        if not mappings and param.required:
                            from tkinter import messagebox
                            messagebox.showwarning("Missing Mappings", f"{param.description} is required")
                            return
                        params[param.name] = mappings
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
            # Save workflow changes to active sheet
            self._save_current_workflow()
            dialog.destroy()

        # Fixed button frame at the bottom (NOT in scrollable area)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10, padx=10)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        button_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=button_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)


    def _show_reorder_columns_dialog(self, operation, columns):
        """Show specialized dialog for reordering columns"""
        from ui.widgets.scrollable_frame import ScrollableOperationFrame

        dialog = tk.Toplevel(self.root)
        dialog.title("Reorder Columns")
        dialog.geometry("700x650")
        dialog.transient(self.root)
        dialog.grab_set()

        # Create scrollable content area
        scrollable = ScrollableOperationFrame(dialog)
        scrollable.pack(fill='both', expand=True, padx=10, pady=(10, 0))

        # Use scroll_frame as the container for all content
        main_frame = scrollable.scroll_frame

        # Title and description
        ttk.Label(
            main_frame,
            text="Reorder Columns",
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(10, 10), padx=10)

        ttk.Label(
            main_frame,
            text="Arrange columns in desired order. Use arrow buttons to move selected column up/down.",
            wraplength=650,
            font=('Arial', 11)
        ).pack(pady=(0, 10), padx=10)

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

        # Fixed button frame at the bottom (NOT in scrollable area)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10, padx=10)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✓ Add to Queue", command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)


    def _save_current_workflow(self):
        """
        Save current operation queue to active sheet's state

        This preserves the workflow when switching sheets, enabling per-sheet workflows
        """
        if not self.workbook_session:
            return

        active_sheet = self.workbook_session.get_active_sheet()
        if active_sheet:
            # Save current operation queue to sheet state
            active_sheet.operations = copy.deepcopy(self.operation_queue)
            logging.info(f"[WORKFLOW] Saved {len(self.operation_queue)} operations to sheet '{active_sheet.sheet_name_display}'")

    def _load_sheet_workflow(self, sheet_name: str):
        """
        Load workflow from sheet state into operation queue

        Args:
            sheet_name: Name of the sheet to load workflow from

        This restores the per-sheet workflow when switching sheets
        """
        if not self.workbook_session:
            self.operation_queue = []
            return

        sheet_state = self.workbook_session.get_sheet(sheet_name)
        if sheet_state and sheet_state.operations:
            # Load sheet's operations into operation queue
            self.operation_queue = copy.deepcopy(sheet_state.operations)
            logging.info(f"[WORKFLOW] Loaded {len(self.operation_queue)} operations from sheet '{sheet_name}'")
        else:
            # No operations for this sheet - start with empty queue
            self.operation_queue = []
            logging.info(f"[WORKFLOW] Sheet '{sheet_name}' has no operations - starting with empty queue")

        # Refresh UI to show loaded operations
        self.refresh_queue_display()

    def clear_queue(self):
        """Clear all operations"""
        if messagebox.askyesno("Confirm", "Clear all operations from queue?"):
            self.operation_queue = []
            self.refresh_queue_display()

            # Save cleared queue to active sheet
            self._save_current_workflow()

    def on_tab_click(self, sheet_name: str):
        """
        Handle sheet tab click from SheetTabBar

        Args:
            sheet_name: Name of the clicked sheet tab
        """
        if not self.workbook_session or sheet_name == self.current_sheet_name:
            return  # Already on this sheet or no workbook loaded

        try:
            logging.info(f"[SHEET TAB] Tab clicked: {sheet_name}")

            # STEP 1: Save current sheet's workflow before switching
            self._save_current_workflow()

            # STEP 2: Switch active sheet in workbook session
            self.workbook_session.switch_to_sheet(sheet_name)
            sheet_state = self.workbook_session.get_active_sheet()

            if not sheet_state:
                raise ValueError(f"Sheet '{sheet_name}' not found in workbook")

            # STEP 3: LAZY LOAD - Load sheet data if not already loaded
            if not sheet_state.is_loaded:
                logging.info(f"[SHEET TAB] Lazy loading sheet '{sheet_name}'...")
                self.df = pd.read_excel(self.current_file, sheet_name=sheet_name)
                self.workbook_session.load_sheet_data(sheet_name, self.df)
                logging.info(f"[SHEET TAB] Sheet loaded: {len(self.df):,} rows")
            else:
                # Sheet already loaded - retrieve from session
                self.df = sheet_state.df_original
                logging.info(f"[SHEET TAB] Sheet retrieved from cache: {len(self.df):,} rows")

            self.current_sheet_name = sheet_name

            # STEP 4: Load results if available
            if sheet_state.has_results():
                self.result_df = sheet_state.df_result
                self.removed_df = sheet_state.removed_rows
                logging.info(f"[SHEET TAB] Restored results for sheet '{sheet_name}'")
            else:
                self.result_df = None
                self.removed_df = None

            # STEP 5: Load new sheet's workflow into operation queue
            self._load_sheet_workflow(sheet_name)

            # Update file info
            self.file_info_var.set(
                f"📁 {Path(self.current_file).name} | Sheet: {sheet_name} • {len(self.df):,} rows × {len(self.df.columns)} columns"
            )

            # Refresh preview
            self.enhanced_preview.load_dataframe(self.df, is_result=False)

            # Update status
            self.status_var.set(f"Switched to sheet: {sheet_name}")

            # Update Excel status bar if present
            if hasattr(self, 'excel_status_bar'):
                self.excel_status_bar.update_row_count(len(self.df))

            # Note: Sheet tab bar already updated via its own internal logic in set_active_sheet()

        except Exception as e:
            logging.error(f"[SHEET TAB ERROR] Failed to switch sheet: {str(e)}")
            messagebox.showerror("Error", f"Failed to load sheet:\n{str(e)}")

    def change_sheet(self):
        """Allow user to change the active sheet for the current Excel file (with lazy loading)"""
        if not self.workbook_session or not self.available_sheets:
            messagebox.showwarning("Warning", "No Excel file with multiple sheets loaded")
            return

        if len(self.available_sheets) <= 1:
            messagebox.showinfo("Info", "This file only has one sheet")
            return

        # Show sheet selection dialog with current sheet highlighted
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
            # Switch to new sheet (with lazy loading)
            try:
                logging.info(f"[WORKBOOK] Switching from '{self.current_sheet_name}' to '{selected_sheet}'")

                # STEP 1: Save current sheet's workflow before switching
                self._save_current_workflow()

                # STEP 2: Switch active sheet in workbook session
                self.workbook_session.switch_to_sheet(selected_sheet)
                sheet_state = self.workbook_session.get_active_sheet()

                if not sheet_state:
                    raise ValueError(f"Sheet '{selected_sheet}' not found in workbook")

                # STEP 3: LAZY LOAD - Load sheet data if not already loaded
                if not sheet_state.is_loaded:
                    logging.info(f"[WORKBOOK] Lazy loading sheet '{selected_sheet}'...")
                    self.df = pd.read_excel(self.current_file, sheet_name=selected_sheet)
                    self.workbook_session.load_sheet_data(selected_sheet, self.df)
                    logging.info(f"[WORKBOOK] Sheet loaded: {len(self.df):,} rows")
                else:
                    # Sheet already loaded - retrieve from session
                    self.df = sheet_state.df_original
                    logging.info(f"[WORKBOOK] Sheet retrieved from cache: {len(self.df):,} rows")

                self.current_sheet_name = selected_sheet

                # STEP 4: Load results if available
                if sheet_state.has_results():
                    self.result_df = sheet_state.df_result
                    self.removed_df = sheet_state.removed_rows
                    logging.info(f"[WORKBOOK] Restored results for sheet '{selected_sheet}'")
                else:
                    self.result_df = None
                    self.removed_df = None

                # STEP 5: Load new sheet's workflow into operation queue
                self._load_sheet_workflow(selected_sheet)

                # Update file info
                self.file_info_var.set(
                    f"📁 {Path(self.current_file).name} | Sheet: {selected_sheet} • {len(self.df):,} rows × {len(self.df.columns)} columns"
                )

                # Refresh preview
                self.enhanced_preview.load_dataframe(self.df, is_result=False)

                # Update status
                self.status_var.set(f"Switched to sheet: {selected_sheet}")

                # Update Excel status bar if present
                if hasattr(self, 'excel_status_bar'):
                    self.excel_status_bar.update_row_count(len(self.df))

                # Update sheet tab bar to show new active sheet
                if self.sheet_tab_bar and len(self.available_sheets) > 1:
                    self.sheet_tab_bar.set_active_sheet(selected_sheet)
                    logging.info(f"[SHEET TAB BAR] Updated active sheet to: {selected_sheet}")

                messagebox.showinfo("Sheet Changed", f"Now viewing sheet: {selected_sheet}\n\n{len(self.df):,} rows × {len(self.df.columns)} columns")

            except Exception as e:
                logging.error(f"[WORKBOOK ERROR] Sheet change failed: {str(e)}")
                messagebox.showerror("Error", f"Failed to load sheet:\n{str(e)}")


    def load_file(self):
        """Load data file with smart header detection, sheet selection, and lazy loading"""
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
            # Reset state
            self.current_sheet_name = None
            self.available_sheets = []
            self.change_sheet_btn.pack_forget()  # Hide by default
            self.workbook_session = None

            # === STEP 1: INITIALIZE WORKBOOK SESSION ===
            is_excel = not filename.endswith('.csv')

            if is_excel:
                logging.info(f"[WORKBOOK] Creating WorkbookSession for: {filename}")
                self.workbook_session = WorkbookSession(filename, is_excel=True)

                # Detect available sheets (lazy loading - don't load data yet)
                excel_file = pd.ExcelFile(filename)
                sheet_names = excel_file.sheet_names
                self.workbook_session.initialize_from_excel(sheet_names)
                self.available_sheets = sheet_names

                logging.info(f"[WORKBOOK] Detected {len(sheet_names)} sheets: {sheet_names}")

                # Select initial sheet
                if len(sheet_names) == 1:
                    selected_sheet = sheet_names[0]
                    logging.info(f"[WORKBOOK] Single sheet - auto-selecting: {selected_sheet}")
                else:
                    logging.info(f"[WORKBOOK] Multiple sheets - showing selection dialog...")
                    selected_sheet = select_sheet_from_file(self.root, filename, sheet_names)

                    if selected_sheet is None:
                        self.status_var.set("File load cancelled - no sheet selected")
                        logging.info("[WORKBOOK] User cancelled sheet selection")
                        return

                self.workbook_session.switch_to_sheet(selected_sheet)
                self.current_sheet_name = selected_sheet
                logging.info(f"[WORKBOOK] Active sheet: {selected_sheet}")

            # === STEP 2: HEADER DETECTION (test load with selected sheet) ===
            selected_sheet = self.current_sheet_name if is_excel else None

            if not is_excel:
                df_test = self._load_csv_with_encoding_detection(filename, nrows=5)
            else:
                # LAZY LOAD: Test load first 5 rows to detect headers
                df_test = pd.read_excel(filename, sheet_name=selected_sheet, nrows=5)
                logging.info(f"[WORKBOOK] Test load completed for sheet '{selected_sheet}'")

            # Check if first row has mostly "Unnamed" columns
            unnamed_count = sum(1 for col in df_test.columns if str(col).startswith('Unnamed'))
            unnamed_ratio = unnamed_count / len(df_test.columns) if len(df_test.columns) > 0 else 0

            # If >50% columns are "Unnamed", headers are probably in row 1
            if unnamed_ratio > 0.5:
                logging.info(f"[FILE LOAD] Detected {unnamed_ratio:.0%} unnamed columns - headers likely in row 1")

                # Ask user for confirmation
                response = messagebox.askyesno(
                    "Header Row Detection",
                    f"Detected {unnamed_count} unnamed columns.\n\n"
                    f"This usually means the first row contains metadata/titles "
                    f"and the actual headers are in the second row.\n\n"
                    f"Use row 2 as headers?\n\n"
                    f"(You can change this later using Transform → Set Header Row)",
                    icon='question'
                )

                if response:
                    header_row = 1
                else:
                    header_row = 0
            else:
                header_row = 0

            # === STEP 3: FULL LOAD with selected sheet and header row ===
            if not is_excel:
                # CSV: Load data and create simple workbook session
                self.df = self._load_csv_with_encoding_detection(filename, header=header_row)
                self.workbook_session = WorkbookSession(filename, is_excel=False)
                self.workbook_session.initialize_from_csv(self.df)
                logging.info(f"[WORKBOOK] CSV loaded: {len(self.df):,} rows")
            else:
                # Excel: LAZY LOAD - Load only the active sheet
                self.df = pd.read_excel(filename, sheet_name=selected_sheet, header=header_row)

                # Store in WorkbookSession
                active_sheet = self.workbook_session.get_active_sheet()
                if active_sheet:
                    self.workbook_session.load_sheet_data(selected_sheet, self.df)
                    logging.info(f"[WORKBOOK] Loaded sheet '{selected_sheet}': {len(self.df):,} rows")
                    logging.info(f"[WORKBOOK] Other sheets remain lazy (not loaded yet)")

            self.current_file = filename

            # === STEP 4: UPDATE UI ===
            # Update file info header (include sheet name for Excel)
            if self.current_sheet_name:
                self.file_info_var.set(
                    f"📁 {Path(filename).name} | Sheet: {self.current_sheet_name} • {len(self.df):,} rows × {len(self.df.columns)} columns"
                )
            else:
                # CSV file - no sheet name
                self.file_info_var.set(
                    f"📁 {Path(filename).name} • {len(self.df):,} rows × {len(self.df.columns)} columns"
                )

            # Show "Change Sheet" button ONLY for multi-sheet Excel files
            if len(self.available_sheets) > 1:
                self.change_sheet_btn.pack(side='right', padx=5)
                logging.info("[FILE LOAD] Showing 'Change Sheet' button (multi-sheet file)")

                # Show and populate sheet tab bar for multi-sheet Excel files
                if self.sheet_tab_bar:
                    self.sheet_tab_bar.set_sheets(self.available_sheets, self.current_sheet_name)
                    self.sheet_tab_bar.show()
                    logging.info(f"[SHEET TAB BAR] Displaying {len(self.available_sheets)} sheet tabs")
            else:
                # Hide sheet tab bar for single-sheet/CSV files
                if self.sheet_tab_bar:
                    self.sheet_tab_bar.hide()

            # Use enhanced preview
            self.enhanced_preview.load_dataframe(self.df, is_result=False)

            self.status_var.set(f"Loaded {len(self.df):,} records successfully")

            # Update Excel status bar
            if hasattr(self, 'excel_status_bar'):
                self.excel_status_bar.update_row_count(len(self.df))

            # Build success message
            success_msg = f"Loaded {len(self.df):,} records with {len(self.df.columns)} columns\n\nHeader row: {header_row + 1}"
            if self.current_sheet_name:
                success_msg += f"\n\nSheet: {self.current_sheet_name}"
                if len(self.available_sheets) > 1:
                    success_msg += f" (of {len(self.available_sheets)} sheets)"

            messagebox.showinfo("Success", success_msg)

        except Exception as e:
            logging.error(f"[FILE LOAD ERROR] {str(e)}")
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
            # Determine validation mode
            use_non_fatal = (self.workbook_session and
                           self.workbook_session.is_excel and
                           len(self.workbook_session.sheet_names) > 1)

            validation_issues = []

            if use_non_fatal:
                # MULTI-SHEET MODE: Use non-fatal validation
                logging.info("[VALIDATION] Using non-fatal validation for multi-sheet mode")
                validation_issues = Validator.validate_queue_non_fatal(
                    self.df,
                    self.operation_queue,
                    self.current_sheet_name or "Sheet"
                )

                if validation_issues:
                    # Show issues but allow user to continue
                    issue_summary = f"Found {len(validation_issues)} validation issue(s):\n\n"
                    for issue in validation_issues[:5]:  # Show first 5
                        issue_summary += f"• {issue.op_label}: {issue.message}\n"
                    if len(validation_issues) > 5:
                        issue_summary += f"\n... and {len(validation_issues) - 5} more"

                    response = messagebox.askyesnocancel(
                        "Validation Issues Found",
                        f"{issue_summary}\n\n"
                        f"Continue anyway?\n\n"
                        f"Yes = Continue execution (issues will be recorded)\n"
                        f"No = Cancel execution\n",
                        icon='warning'
                    )

                    if response is None or response is False:
                        # User cancelled
                        logging.info("[VALIDATION] User cancelled due to validation issues")
                        return

                    logging.info(f"[VALIDATION] User chose to continue despite {len(validation_issues)} issue(s)")

            else:
                # SINGLE-SHEET MODE: Use fatal validation (backward compatible)
                logging.info("[VALIDATION] Using fatal validation for single-sheet mode")
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

            # Save results to active sheet state
            if self.workbook_session:
                active_sheet = self.workbook_session.get_active_sheet()
                if active_sheet:
                    active_sheet.df_result = self.result_df
                    active_sheet.removed_rows = self.removed_df
                    active_sheet.is_dirty = True

                    # Store validation issues
                    active_sheet.issues = validation_issues

                    if validation_issues:
                        logging.warning(f"[VALIDATION] Recorded {len(validation_issues)} issue(s) for sheet '{active_sheet.sheet_name_display}'")

                        # Mark sheet tab with warning indicator
                        if self.sheet_tab_bar and self.current_sheet_name:
                            self.sheet_tab_bar.mark_sheet_issues(self.current_sheet_name, has_issues=True)

                    logging.info(f"[WORKFLOW] Saved results to sheet '{active_sheet.sheet_name_display}': {len(self.result_df):,} rows")

            # Display in enhanced preview
            self.enhanced_preview.load_dataframe(self.result_df, is_result=True)

            # Build success message with removed rows info
            removed_count = len(self.removed_df) if self.removed_df is not None and not self.removed_df.empty else 0
            success_msg = f"Operations completed!\n\nInput: {len(self.df):,} rows\nOutput: {len(self.result_df):,} rows"
            if removed_count > 0:
                success_msg += f"\nRemoved: {removed_count:,} rows"

            # Add validation issues warning if any
            if validation_issues:
                success_msg += f"\n\n⚠️ {len(validation_issues)} validation issue(s) recorded"
                if len(validation_issues) <= 3:
                    success_msg += ":\n"
                    for issue in validation_issues:
                        success_msg += f"  • {issue.op_label}: {issue.message}\n"

            self.status_var.set(f"✅ Complete! {len(self.result_df):,} rows in results")

            # Update Excel status bar
            if hasattr(self, 'excel_status_bar'):
                self.excel_status_bar.update_row_count(len(self.result_df))

            if validation_issues:
                messagebox.showwarning("Success with Issues", success_msg)
            else:
                messagebox.showinfo("Success", success_msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Execution failed:\n{str(e)}")
    

    def save_results(self):
        """Save results to file with multi-sheet export"""
        # Check if we have any results to save
        has_results = False
        if self.workbook_session:
            # Multi-sheet mode: Check if any sheet has results
            for sheet_state in self.workbook_session.sheets.values():
                if sheet_state.has_results():
                    has_results = True
                    break
        else:
            # Single-sheet mode: Check active result
            has_results = (self.result_df is not None)

        if not has_results:
            messagebox.showwarning("Warning", "No results to save. Run operations first.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt")
            ]
        )

        if not filename:
            return

        try:
            if filename.endswith('.csv'):
                # CSV can only save one sheet - save active sheet results only
                if self.result_df is not None:
                    ExportHelper.export_to_csv(self.result_df, filename)
                    if self.workbook_session:
                        success_msg = f"Results saved to:\n{filename}\n\nNote: CSV format only saves active sheet '{self.current_sheet_name}' results."
                    else:
                        success_msg = f"Results saved to:\n{filename}"
                else:
                    messagebox.showwarning("Warning", "Active sheet has no results")
                    return

            elif filename.endswith('.txt'):
                # TXT format - comma-delimited with quotes
                if self.result_df is not None:
                    ExportHelper.export_to_txt(self.result_df, filename, include_header=True)
                    if self.workbook_session:
                        success_msg = f"Results saved to:\n{filename}\n\nFormat: Comma-delimited with quoted fields\nNote: TXT format only saves active sheet '{self.current_sheet_name}' results."
                    else:
                        success_msg = f"Results saved to:\n{filename}\n\nFormat: Comma-delimited with quoted fields"
                else:
                    messagebox.showwarning("Warning", "Active sheet has no results")
                    return

            else:
                # Excel - export multi-sheet workbook
                if self.workbook_session and self.workbook_session.is_excel:
                    # MULTI-SHEET MODE: Use WorkbookSession to export all sheets
                    logging.info("[EXPORT] Multi-sheet mode - exporting all sheets via WorkbookSession")

                    # Get all export data from WorkbookSession
                    export_sheets = self.workbook_session.get_export_data()

                    if not export_sheets:
                        messagebox.showwarning("Warning", "No sheets to export")
                        return

                    ExportHelper.export_multiple_sheets(export_sheets, filename)

                    # Build success message
                    sheet_info = []
                    removed_count = 0
                    for sheet_name, df in export_sheets.items():
                        if sheet_name == 'REMOVED_ROWS':
                            removed_count = len(df)
                            sheet_info.append(f"• REMOVED_ROWS: {removed_count:,} rows (combined from all sheets)")
                        else:
                            sheet_info.append(f"• {sheet_name}: {len(df):,} rows")

                    success_msg = f"Multi-sheet workbook saved to:\n{filename}\n\n"
                    success_msg += f"Exported {len(export_sheets)} sheets:\n" + "\n".join(sheet_info)
                    success_msg += f"\n\n💡 All sheets preserved (processed + unprocessed)"

                    logging.info(f"[EXPORT] Exported {len(export_sheets)} sheets to {filename}")

                else:
                    # SINGLE-SHEET MODE: Export as before (Original, Results, Removed)
                    logging.info("[EXPORT] Single-sheet mode - exporting Original/Results/Removed")

                    sheets = {}

                    # Sheet 1: Original data
                    if self.df is not None:
                        sheets['Original'] = self.df

                    # Sheet 2: Results
                    if self.result_df is not None:
                        sheets['Results'] = self.result_df

                    # Sheet 3: Removed (if any rows were removed)
                    if self.removed_df is not None and not self.removed_df.empty:
                        sheets['Removed'] = self.removed_df

                    ExportHelper.export_multiple_sheets(sheets, filename)

                    # Build success message
                    sheet_info = []
                    if 'Original' in sheets:
                        sheet_info.append(f"• Original: {len(sheets['Original']):,} rows")
                    if 'Results' in sheets:
                        sheet_info.append(f"• Results: {len(sheets['Results']):,} rows")
                    if 'Removed' in sheets:
                        sheet_info.append(f"• Removed: {len(sheets['Removed']):,} rows")

                    success_msg = f"Workbook saved to:\n{filename}\n\nSheets:\n" + "\n".join(sheet_info)

            messagebox.showinfo("Success", success_msg)
            self.status_var.set(f"Saved to {Path(filename).name}")

        except Exception as e:
            logging.error(f"[EXPORT ERROR] {str(e)}")
            messagebox.showerror("Error", f"Failed to save:\n{str(e)}")
    

    def load_preset(self):
        """Load a preset with context menu for delete/rename"""
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

        ttk.Label(dialog, text="💡 Right-click on user presets to delete or rename",
                 font=('Segoe UI', 9), foreground='gray').pack(pady=5)

        listbox = tk.Listbox(dialog, font=('Arial', 11))
        listbox.pack(fill='both', expand=True, padx=20, pady=10)

        def refresh_preset_list():
            """Refresh the preset listbox"""
            listbox.delete(0, tk.END)
            preset_map.clear()

            current_presets = self.preset_manager.list_presets()
            for preset in current_presets:
                icon = "🔒" if preset.is_system else "📝"
                text = f"{icon} {preset.name} - {preset.description}"
                listbox.insert(tk.END, text)
                preset_map[listbox.size()-1] = preset

        preset_map = {}
        refresh_preset_list()

        def on_load():
            selection = listbox.curselection()
            if selection:
                preset = preset_map[selection[0]]

                # Check if multi-sheet mode
                if self.workbook_session and self.workbook_session.is_excel and len(self.workbook_session.sheet_names) > 1:
                    # MULTI-SHEET MODE: Show sheet selector dialog
                    logging.info(f"[PRESET] Multi-sheet mode - showing sheet selector for preset '{preset.name}'")

                    sheet_selector = MultiSheetPresetDialog(
                        self.root,
                        self.workbook_session.sheet_names,
                        preset.name,
                        len(preset.operations)
                    )
                    selected_sheets = sheet_selector.show()

                    if not selected_sheets:
                        # User cancelled
                        logging.info("[PRESET] User cancelled multi-sheet preset application")
                        return

                    # Build preset operations list
                    preset_operations = []
                    for op_config in preset.operations:
                        operation = registry.get_by_id(op_config.operation_id)
                        if operation:
                            preset_operations.append({
                                'operation_id': op_config.operation_id,
                                'name': operation.metadata.name,
                                'parameters': op_config.parameters,
                                'enabled': op_config.enabled
                            })

                    # Apply to selected sheets via WorkbookSession
                    self.workbook_session.apply_preset_to_sheets(preset_operations, selected_sheets)

                    # If current sheet was selected, refresh UI
                    if self.current_sheet_name in selected_sheets:
                        self._load_sheet_workflow(self.current_sheet_name)
                        logging.info(f"[PRESET] Refreshed current sheet '{self.current_sheet_name}' workflow")

                    dialog.destroy()
                    messagebox.showinfo(
                        "Success",
                        f"Applied preset '{preset.name}' to {len(selected_sheets)} sheet(s):\n\n" +
                        "\n".join([f"  • {s}" for s in selected_sheets]) +
                        f"\n\n{len(preset.operations)} operation(s) per sheet"
                    )
                    self.status_var.set(f"Preset '{preset.name}' applied to {len(selected_sheets)} sheets")
                    logging.info(f"[PRESET] Applied to {len(selected_sheets)} sheets: {selected_sheets}")

                else:
                    # SINGLE-SHEET MODE: Apply to active sheet only
                    logging.info(f"[PRESET] Single-sheet mode - applying preset '{preset.name}' to current sheet")

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
                    # Save loaded preset workflow to active sheet
                    self._save_current_workflow()
                    self.status_var.set(f"Loaded preset: {preset.name}")
                    dialog.destroy()
                    messagebox.showinfo("Success",
                                      f"Loaded '{preset.name}' with {len(preset.operations)} operations")

        def on_delete_preset():
            """Delete selected preset"""
            selection = listbox.curselection()
            if not selection:
                return

            preset = preset_map[selection[0]]

            # Check if can be modified
            if not self.preset_manager.can_modify_preset(preset.id):
                messagebox.showwarning("Cannot Delete",
                                      "System presets cannot be deleted.\n\nOnly user-created presets can be removed.")
                return

            # Confirm deletion
            response = messagebox.askyesno("Confirm Delete",
                                          f"Are you sure you want to delete preset:\n\n'{preset.name}'?\n\nThis cannot be undone.")

            if response:
                success = self.preset_manager.delete_preset(preset.id)
                if success:
                    messagebox.showinfo("Success", f"Preset '{preset.name}' deleted successfully")
                    refresh_preset_list()
                else:
                    messagebox.showerror("Error", f"Failed to delete preset '{preset.name}'")

        def on_rename_preset():
            """Rename selected preset"""
            selection = listbox.curselection()
            if not selection:
                return

            preset = preset_map[selection[0]]

            # Check if can be modified
            if not self.preset_manager.can_modify_preset(preset.id):
                messagebox.showwarning("Cannot Rename",
                                      "System presets cannot be renamed.\n\nOnly user-created presets can be modified.")
                return

            # Create rename dialog
            rename_dialog = tk.Toplevel(dialog)
            rename_dialog.title("Rename Preset")
            rename_dialog.geometry("450x200")
            rename_dialog.transient(dialog)
            rename_dialog.grab_set()

            ttk.Label(rename_dialog, text=f"Rename: {preset.name}",
                     font=('Segoe UI', 12, 'bold')).pack(pady=10)

            ttk.Label(rename_dialog, text="New Name:").pack(pady=5)
            name_var = tk.StringVar(value=preset.name)
            name_entry = ttk.Entry(rename_dialog, textvariable=name_var, width=40)
            name_entry.pack(pady=5)
            name_entry.select_range(0, tk.END)
            name_entry.focus()

            ttk.Label(rename_dialog, text="New Description:").pack(pady=5)
            desc_var = tk.StringVar(value=preset.description)
            ttk.Entry(rename_dialog, textvariable=desc_var, width=40).pack(pady=5)

            def do_rename():
                new_name = name_var.get().strip()
                new_desc = desc_var.get().strip()

                if not new_name:
                    messagebox.showwarning("Invalid Name", "Please enter a valid name")
                    return

                success = self.preset_manager.rename_preset(preset.id, new_name, new_desc)

                if success:
                    messagebox.showinfo("Success", f"Preset renamed to '{new_name}'")
                    refresh_preset_list()
                    rename_dialog.destroy()
                else:
                    messagebox.showerror("Error",
                                       "Failed to rename preset.\n\nA preset with this name may already exist.")

            btn_frame = ttk.Frame(rename_dialog)
            btn_frame.pack(pady=15)
            ttk.Button(btn_frame, text="Rename", command=do_rename,
                      style='Accent.TButton').pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Cancel", command=rename_dialog.destroy).pack(side='left', padx=5)

        def show_context_menu(event):
            """Show context menu on right-click"""
            # Get item under cursor
            index = listbox.nearest(event.y)
            if index < 0:
                return

            # Select the item
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(index)
            listbox.activate(index)

            preset = preset_map[index]

            # Create context menu
            context_menu = tk.Menu(dialog, tearoff=0)

            # Load option (always available)
            context_menu.add_command(label="📂 Load", command=on_load)

            # Separator
            if not preset.is_system:
                context_menu.add_separator()

                # Delete and Rename (only for user presets)
                context_menu.add_command(label="✏️ Rename", command=on_rename_preset)
                context_menu.add_command(label="🗑 Delete", command=on_delete_preset)

            # Show menu
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

        # Bind right-click
        listbox.bind("<Button-3>", show_context_menu)  # Windows/Linux
        listbox.bind("<Button-2>", show_context_menu)  # macOS

        # Bind double-click to load
        listbox.bind("<Double-Button-1>", lambda e: on_load())

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

    # ==================== AUTO-UPDATE METHODS ====================

    def check_for_updates_background(self):
        """Check for updates in background thread"""
        def callback(update_info):
            if update_info.get('update_available'):
                # Check if this version was skipped
                if self.config_manager:
                    skipped_version = self.config_manager.get_skipped_version()
                    if skipped_version == update_info['new_version']:
                        return  # Don't show notification for skipped version

                # Show update notification on UI thread
                self.root.after(0, lambda: self.show_update_notification(update_info))

        self.updater.check_for_updates_async(callback)

    def show_update_notification(self, update_info):
        """Show update available dialog"""
        dialog = UpdateNotificationDialog(self.root, update_info)
        result = dialog.show()

        if result == "update":
            self.download_and_install_update(update_info)
        elif result == "skip":
            # Record skipped version
            if self.config_manager:
                self.config_manager.set_skipped_version(update_info['new_version'])

    def download_and_install_update(self, update_info):
        """Download and install update with progress dialog"""
        # Create progress dialog
        progress_dialog = UpdateProgressDialog(self.root)

        def download_thread():
            try:
                new_exe = self.updater.download_update(
                    update_info['download_url'],
                    progress_dialog.update_progress
                )

                if new_exe:
                    # Close progress dialog
                    self.root.after(0, progress_dialog.close)

                    # Ask to restart
                    def ask_restart():
                        if messagebox.askyesno(
                            "Update Ready",
                            "Update downloaded successfully!\n\n"
                            "Clean Sheet will now restart to complete the installation.",
                            parent=self.root
                        ):
                            self.updater.install_update(new_exe)
                            sys.exit(0)

                    self.root.after(0, ask_restart)
                else:
                    self.root.after(0, progress_dialog.close)
                    self.root.after(0, lambda: messagebox.showerror(
                        "Update Failed",
                        "Failed to download update. Please try again later.",
                        parent=self.root
                    ))

            except Exception as e:
                self.root.after(0, progress_dialog.close)
                self.root.after(0, lambda: messagebox.showerror(
                    "Update Failed",
                    f"Error downloading update:\n{str(e)}",
                    parent=self.root
                ))

        threading.Thread(target=download_thread, daemon=True).start()

    def check_for_updates_manual(self):
        """Manually check for updates (from Help menu)"""
        try:
            update_info = self.updater.check_for_updates()

            if update_info.get('update_available'):
                self.show_update_notification(update_info)
            else:
                messagebox.showinfo(
                    "No Updates Available",
                    f"You're running the latest version of Clean Sheet (v{__version__}).",
                    parent=self.root
                )
        except Exception as e:
            messagebox.showerror(
                "Update Check Failed",
                f"Failed to check for updates:\n{str(e)}",
                parent=self.root
            )

    def show_about_dialog(self):
        """Show About dialog with version info"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Clean Sheet")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        about_window.transient(self.root)

        # Center window
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (about_window.winfo_screenheight() // 2) - (400 // 2)
        about_window.geometry(f"+{x}+{y}")

        # Force dialog to appear
        about_window.deiconify()
        about_window.lift()
        about_window.focus_force()
        about_window.grab_set()

        # Header
        header_frame = tk.Frame(about_window, bg="#0078D4", height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text=f"🔷 {__app_name__}",
            font=("Segoe UI", 18, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=15)

        tk.Label(
            header_frame,
            text=__app_tagline__,
            font=("Segoe UI", 11),
            bg="#0078D4",
            fg="white"
        ).pack()

        # Content
        content_frame = tk.Frame(about_window, padx=30, pady=30)
        content_frame.pack(fill=tk.BOTH, expand=True)

        info_text = f"""
Version: {__version__}
Release Date: {__release_date__}

{COPYRIGHT}

Clean Sheet is a professional data cleaning tool for Excel and CSV files.
Transform, clean, and standardize your data with 51+ built-in operations.

Features:
• 51+ Data cleaning operations
• Smart Data Quality Analyzer
• AI-Powered Assistant
• Preset workflow management
• Automatic updates
• Professional Office 365 UI

Repository: github.com/{GITHUB_REPO}
        """

        tk.Label(
            content_frame,
            text=info_text.strip(),
            font=("Segoe UI", 10),
            justify=tk.LEFT,
            wraplength=440
        ).pack(pady=(0, 20))

        # Buttons
        button_frame = tk.Frame(content_frame)
        button_frame.pack()

        tk.Button(
            button_frame,
            text="Check for Updates",
            command=lambda: [about_window.destroy(), self.check_for_updates_manual()],
            bg="#0078D4",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            button_frame,
            text="Close",
            command=about_window.destroy,
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT)

    # ==================== END AUTO-UPDATE METHODS ====================

    def handle_logout(self):
        """Handle user logout"""
        # Confirm logout
        if not messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?\n\nYour current work will be preserved."
        ):
            return

        try:
            logging.info(f"User logging out: {self.user_email}")

            # Delete session from MongoDB
            if self.auth_manager and self.session_token:
                self.auth_manager.logout(self.session_token)
                logging.info("Session deleted from MongoDB")

            # Close current window
            self.root.destroy()

            # Restart application with login window
            import subprocess
            import sys
            subprocess.Popen([sys.executable, __file__])

        except Exception as e:
            logging.error(f"Logout error: {e}")
            messagebox.showerror(
                "Logout Error",
                f"Failed to logout properly: {str(e)}\n\n"
                "The application will close, but your session may still be active."
            )
            # Close anyway
            try:
                self.root.destroy()
            except:
                pass


def main():
    """Main entry point with authentication and configuration"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logging.info(f"Starting {__app_name__} v{__version__}")

    # Initialize configuration manager
    config_manager = ConfigManager()

    # TEMPORARY BYPASS: Dialog visibility issue in frozen .exe
    # TODO v2.1.1: Fix FirstRunConfigDialog and re-enable
    # For now: Use .env file fallback for configuration
    if not config_manager.is_configured():
        logging.info("Configuration not found - attempting .env fallback")

        try:
            from dotenv import load_dotenv
            load_dotenv()

            mongodb_uri = os.getenv('MONGODB_URI', '')
            api_key = os.getenv('ANTHROPIC_API_KEY', '')

            if mongodb_uri:
                config_manager.set_mongodb_uri(mongodb_uri)
                logging.info("✓ MongoDB URI loaded from .env file")

            if api_key:
                config_manager.set_api_key(api_key)
                logging.info("✓ API key loaded from .env file")

            # Mark configuration as complete
            if not config_manager.config.has_section('App'):
                config_manager.config.add_section('App')
            config_manager.config.set('App', 'first_run_complete', 'true')
            config_manager.save_config()

            # Warn if no MongoDB URI found
            if not mongodb_uri:
                logging.warning("No MongoDB URI found in .env or config.ini")
                root = tk.Tk()
                root.withdraw()
                messagebox.showwarning(
                    "Configuration Required",
                    f"{__app_name__} requires MongoDB configuration.\n\n"
                    "Please create a .env file with:\n"
                    "MONGODB_URI=your_mongodb_connection_string\n\n"
                    "Or create config.ini in:\n"
                    f"{config_manager.get_config_path()}\n\n"
                    "The application will now exit.\n"
                    "See documentation for setup instructions."
                )
                root.destroy()
                return

        except Exception as e:
            logging.error(f"Configuration error: {e}")
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Configuration Error",
                f"Failed to load configuration:\n{str(e)}\n\n"
                "Please check your .env file or config.ini\n"
                "See documentation for help."
            )
            root.destroy()
            return

    # Storage for authentication data
    auth_data = {'token': None, 'email': None}

    def on_login_success(token, email):
        """
        Callback invoked when user successfully logs in

        CRITICAL: This function MUST accept TWO arguments (token, email)
        as this is how LoginWindow calls it.

        Args:
            token: Session token string
            email: User's email address
        """
        auth_data['token'] = token
        auth_data['email'] = email
        logging.info(f"✅ User authenticated: {email}")

    # Show login window
    try:
        login_window = LoginWindow(on_success_callback=on_login_success)
        token, email = login_window.run()

        # If authentication failed or was cancelled, exit
        if not token or not email:
            logging.info("Authentication cancelled or failed. Exiting.")
            return

        # Authentication successful - start main application
        logging.info(f"Starting main application for user: {email}")
        root = tk.Tk()
        app = CleanSheetApp(
            root,
            session_token=token,
            user_email=email,
            config_manager=config_manager
        )
        root.mainloop()

    except Exception as e:
        logging.error(f"Application error: {e}", exc_info=True)
        messagebox.showerror(
            "Application Error",
            f"Failed to start {__app_name__}:\n\n{str(e)}\n\n"
            "Please check your MongoDB configuration and try again."
        )


if __name__ == "__main__":
    main()
