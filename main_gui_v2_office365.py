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
import subprocess
import traceback
from typing import Optional

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Version and configuration imports
from version import __version__, __app_name__, __app_tagline__, GITHUB_REPO, __release_date__, COPYRIGHT
from config_manager import ConfigManager, FirstRunConfigDialog
from utils.auto_updater import AutoUpdater, UpdateNotificationDialog, UpdateProgressDialog
from utils.logging_setup import setup_logging, get_log_directory, get_debug_info, get_recent_logs
from utils.session_recovery import SessionRecovery

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
        self.logger = logging.getLogger(__name__)

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

        # Email validation cache (session only)
        self.email_validation_cache = {}  # {normalized_email: validation_result_dict}

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

        # Session recovery
        self.session_recovery = SessionRecovery()
        self.last_export_path = None

        # Global exception handler for Tkinter callbacks
        self.root.report_callback_exception = self.handle_exception

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

        # Prompt for session recovery after UI is ready
        self.root.after(100, self.check_session_recovery)

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
        ttk.Button(queue_actions, text="✨ Smart Format",
                  command=self.launch_smart_format,
                  style='RibbonButton.TButton',
                  width=16).pack(side='left', padx=2)

        # History controls — disabled until a file is loaded / undo is available
        ttk.Frame(queue_actions, width=8).pack(side='left')  # visual spacer
        self.undo_btn = ttk.Button(queue_actions, text="↩ Undo",
                                   command=self.perform_undo,
                                   style='RibbonButton.TButton',
                                   width=8, state='disabled')
        self.undo_btn.pack(side='left', padx=2)
        self.redo_btn = ttk.Button(queue_actions, text="↪ Redo",
                                   command=self.perform_redo,
                                   style='RibbonButton.TButton',
                                   width=8, state='disabled')
        self.redo_btn.pack(side='left', padx=2)
        self.reset_btn = ttk.Button(queue_actions, text="⟲ Reset",
                                    command=self.perform_reset,
                                    style='RibbonButton.TButton',
                                    width=8, state='disabled')
        self.reset_btn.pack(side='left', padx=2)

        # Keyboard shortcuts for undo/redo
        self.root.bind('<Control-z>', lambda e: self.perform_undo())
        self.root.bind('<Control-y>', lambda e: self.perform_redo())
        self.root.bind('<Control-Z>', lambda e: self.perform_redo())

        # Smart Format recommendations panel (hidden until Smart Format is applied)
        self.smart_format_panel = tk.Frame(queue_frame, bg='#FFF4CE', relief='flat')
        self._build_smart_format_panel()

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
            self._push_undo_snapshot()
            self.operation_queue[index]['enabled'] = check_var.get()
            self._save_current_workflow()
            self._update_history_buttons()

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

        # Build the effective column list at *this* position in the pipeline.
        # Apply all operations that come before `index` so that columns created
        # by earlier operations (e.g. 'Lead Score') are available in the dropdown.
        if self.df is not None:
            prior_ops = self.operation_queue[:index]
            if prior_ops:
                state_df = self.executor.preview_execute_queue(self.df, prior_ops)
                columns = list(state_df.columns) if state_df is not None else list(self.df.columns)
            else:
                columns = list(self.df.columns)
        else:
            columns = []

        logging.debug(
            "[EDIT_OP] Editing op %d '%s' with effective columns=%s",
            index, operation.metadata.name, columns
        )

        # Check for special operations first
        if operation.metadata.id == 'add_column_smart':
            self._show_add_column_smart_dialog(operation, columns, edit_mode=True, edit_index=index, current_params=op_config['parameters'])
            return

        if operation.metadata.id == 'filter_lower_48':
            self._show_lower_48_dialog(operation, columns, edit_mode=True, edit_index=index, current_params=op_config['parameters'])
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
        self._push_undo_snapshot()
        del self.operation_queue[index]
        self.refresh_queue_display()
        # Save workflow changes to active sheet
        self._save_current_workflow()
        self._update_history_buttons()

    def move_operation(self, index, direction):
        """Move operation up (-1) or down (+1)"""
        new_index = index + direction
        if 0 <= new_index < len(self.operation_queue):
            self._push_undo_snapshot()
            self.operation_queue[index], self.operation_queue[new_index] = \
                self.operation_queue[new_index], self.operation_queue[index]
            self.refresh_queue_display()
            # Save workflow changes to active sheet
            self._save_current_workflow()
            self._update_history_buttons()

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

    def set_status(self, message: str):
        """
        Set status message in UI.

        Compatibility wrapper that tries various status update mechanisms
        and never throws exceptions.

        Args:
            message: Status message to display
        """
        try:
            # Try status_var first (primary mechanism)
            if hasattr(self, 'status_var') and self.status_var:
                self.status_var.set(message)
                return
        except Exception:
            pass

        try:
            # Try status_text_var
            if hasattr(self, 'status_text_var') and self.status_text_var:
                self.status_text_var.set(message)
                return
        except Exception:
            pass

        try:
            # Try status_label
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.config(text=message)
                return
        except Exception:
            pass

        try:
            # Try update_status method
            if hasattr(self, 'update_status'):
                self.update_status(message)
                return
        except Exception:
            pass

        # Fallback: print to console
        print(f"[STATUS] {message}")

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
        """Create the Combine Mode UI panel with file status tracking and conversion actions."""
        self.combine_panel = tk.Frame(self.root, bg='white')

        # Outer scrollable container
        outer_canvas = tk.Canvas(self.combine_panel, bg='white', highlightthickness=0)
        outer_scroll = ttk.Scrollbar(self.combine_panel, orient='vertical',
                                     command=outer_canvas.yview)
        outer_canvas.configure(yscrollcommand=outer_scroll.set)
        outer_scroll.pack(side='right', fill='y')
        outer_canvas.pack(side='left', fill='both', expand=True)

        main_container = ttk.Frame(outer_canvas, style='Card.TFrame')
        canvas_window = outer_canvas.create_window((0, 0), window=main_container, anchor='nw')

        def _on_frame_configure(event):
            outer_canvas.configure(scrollregion=outer_canvas.bbox('all'))

        def _on_canvas_configure(event):
            outer_canvas.itemconfig(canvas_window, width=event.width)

        main_container.bind('<Configure>', _on_frame_configure)
        outer_canvas.bind('<Configure>', _on_canvas_configure)

        # ── Title ──────────────────────────────────────────────────────────────
        ttk.Label(
            main_container,
            text="Combine Files",
            font=('Segoe UI', 18, 'bold'),
            foreground='#0078D4'
        ).pack(pady=(15, 4), padx=20)

        ttk.Label(
            main_container,
            text=(
                "Upload multiple files, convert as needed, then combine.\n"
                "Mixed formats are handled — convert all files to the same "
                "format before combining."
            ),
            font=('Segoe UI', 10),
            foreground='#666666',
            justify='center'
        ).pack(pady=(0, 15), padx=20)

        # ── File List Section ──────────────────────────────────────────────────
        upload_frame = ttk.LabelFrame(main_container, text="📁 Files", padding=12)
        upload_frame.pack(fill='both', expand=True, padx=20, pady=(0, 8))

        # Top button row
        top_btn_row = ttk.Frame(upload_frame)
        top_btn_row.pack(fill='x', pady=(0, 8))

        ttk.Button(
            top_btn_row,
            text="Browse Files...",
            command=self.combine_browse_files,
            style='Accent.TButton',
            width=18
        ).pack(side='left', padx=(0, 6))

        ttk.Button(
            top_btn_row,
            text="Remove Selected",
            command=self.combine_remove_file,
            width=16
        ).pack(side='left', padx=(0, 6))

        ttk.Button(
            top_btn_row,
            text="Clear All",
            command=self.combine_clear_files,
            width=10
        ).pack(side='left')

        # Error Details button (right-aligned)
        self.combine_error_btn = ttk.Button(
            top_btn_row,
            text="Error Details",
            command=self._combine_show_file_error,
            width=14
        )
        self.combine_error_btn.pack(side='right')

        # Treeview for file list
        tree_frame = ttk.Frame(upload_frame)
        tree_frame.pack(fill='both', expand=True)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient='vertical')
        tree_scroll_y.pack(side='right', fill='y')

        tree_scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        tree_scroll_x.pack(side='bottom', fill='x')

        self.combine_file_tree = ttk.Treeview(
            tree_frame,
            columns=('status', 'format', 'rows'),
            show='tree headings',
            selectmode='extended',
            height=8,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
        )
        self.combine_file_tree.pack(side='left', fill='both', expand=True)
        tree_scroll_y.config(command=self.combine_file_tree.yview)
        tree_scroll_x.config(command=self.combine_file_tree.xview)

        self.combine_file_tree.heading('#0', text='Filename', anchor='w')
        self.combine_file_tree.heading('status', text='Status', anchor='w')
        self.combine_file_tree.heading('format', text='Format', anchor='center')
        self.combine_file_tree.heading('rows', text='Rows', anchor='e')

        self.combine_file_tree.column('#0', width=300, minwidth=160, stretch=True)
        self.combine_file_tree.column('status', width=150, minwidth=100, stretch=False)
        self.combine_file_tree.column('format', width=70, minwidth=50, stretch=False, anchor='center')
        self.combine_file_tree.column('rows', width=70, minwidth=50, stretch=False, anchor='e')

        # Tag-based colour coding
        self.combine_file_tree.tag_configure('loaded',      foreground='#107C10')
        self.combine_file_tree.tag_configure('failed',      foreground='#D83B01')
        self.combine_file_tree.tag_configure('converted',   foreground='#0078D4')
        self.combine_file_tree.tag_configure('needs_sheet', foreground='#CA5010')

        # Double-click to show error / sheet picker
        self.combine_file_tree.bind('<Double-Button-1>', self._combine_on_tree_double_click)

        # ── Conversion Action Bar ──────────────────────────────────────────────
        conv_frame = ttk.LabelFrame(main_container, text="🔄 Convert", padding=10)
        conv_frame.pack(fill='x', padx=20, pady=(0, 8))

        conv_row1 = ttk.Frame(conv_frame)
        conv_row1.pack(fill='x', pady=(0, 5))

        ttk.Button(
            conv_row1,
            text="Convert Selected → CSV",
            command=self._combine_convert_selected_to_csv,
            width=22
        ).pack(side='left', padx=(0, 6))

        ttk.Button(
            conv_row1,
            text="Convert Selected → XLSX",
            command=self._combine_convert_selected_to_xlsx,
            width=22
        ).pack(side='left', padx=(0, 6))

        self.combine_retry_btn = ttk.Button(
            conv_row1,
            text="Retry Failed",
            command=self._combine_retry_failed,
            width=14
        )
        self.combine_retry_btn.pack(side='right')

        conv_row2 = ttk.Frame(conv_frame)
        conv_row2.pack(fill='x')

        ttk.Button(
            conv_row2,
            text="Convert All → CSV",
            command=self._combine_convert_all_to_csv,
            width=22
        ).pack(side='left', padx=(0, 6))

        ttk.Button(
            conv_row2,
            text="Convert All → XLSX",
            command=self._combine_convert_all_to_xlsx,
            width=22
        ).pack(side='left')

        # ── Summary Bar ───────────────────────────────────────────────────────
        summary_frame = ttk.LabelFrame(main_container, text="📊 Summary", padding=10)
        summary_frame.pack(fill='x', padx=20, pady=(0, 8))

        self.combine_summary_text = tk.Text(
            summary_frame,
            height=4,
            font=('Consolas', 10),
            wrap='word',
            state='disabled',
            bg='#FAFAFA',
            relief='flat'
        )
        self.combine_summary_text.pack(fill='x')

        # ── Combine Button ─────────────────────────────────────────────────────
        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill='x', padx=20, pady=(5, 20))

        self.combine_btn = ttk.Button(
            action_frame,
            text="🔗 Combine Files",
            command=self.combine_files_execute,
            style='Success.TButton',
            width=25,
            state='disabled'
        )
        self.combine_btn.pack()

        # Initialise
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
            dialog.geometry("300x175")

            ttk.Label(dialog, text="Export Format:").pack(pady=10)
            ttk.Radiobutton(dialog, text="Excel (.xlsx)", variable=format_var, value="xlsx").pack()
            ttk.Radiobutton(dialog, text="CSV (.csv)", variable=format_var, value="csv").pack()
            ttk.Radiobutton(dialog, text="Text (.txt)", variable=format_var, value="txt").pack()

            def do_export():
                count = ExportHelper.export_grouped_files(groups, output_dir, format_var.get())
                messagebox.showinfo("Success", f"Exported {count} grouped files")
                dialog.destroy()

            ttk.Button(dialog, text="Export", command=do_export).pack(pady=10)
            dialog.mainloop()

    # ==================== COMBINE MODE METHODS ====================

    def combine_browse_files(self):
        """Browse and add files to the combine queue with safe loading and sheet selection."""
        filenames = filedialog.askopenfilenames(
            title="Select Files to Combine",
            filetypes=[
                ("All Supported", "*.xlsx *.xls *.xlsm *.csv *.txt *.tsv"),
                ("Excel files", "*.xlsx *.xls *.xlsm"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt *.tsv"),
                ("All files", "*.*")
            ]
        )

        if not filenames:
            return

        # Deduplicate: skip already-loaded paths
        existing_originals = {
            f['original_path'] for f in self.combine_mode_handler.loaded_files
        }
        new_filenames = [fn for fn in filenames if fn not in existing_originals]
        skipped = len(filenames) - len(new_filenames)

        # Validate file limit (2–50 files total)
        total_after = len(self.combine_mode_handler.loaded_files) + len(new_filenames)
        if total_after > 50:
            messagebox.showerror(
                "Too Many Files",
                f"Cannot add {len(new_filenames)} files.\n"
                f"Maximum 50 files allowed.\n"
                f"Currently loaded: {len(self.combine_mode_handler.loaded_files)}"
            )
            return

        if not new_filenames:
            if skipped:
                messagebox.showinfo("Already Loaded",
                                    "All selected files are already in the combine list.")
            return

        self.status_var.set(f"Loading {len(new_filenames)} files...")

        loaded_ok = 0
        loaded_failed = 0

        for filename in new_filenames:
            # For Excel files with multiple sheets, ask which sheet to use
            sheet_name = None
            file_type = self.combine_mode_handler.detect_file_type(filename)
            if file_type == 'excel':
                sheets = self.combine_mode_handler.get_excel_sheets(filename)
                if len(sheets) > 1:
                    sheet_name = select_sheet_from_file(self.root, filename, sheets)
                    if sheet_name is None:
                        # User cancelled — add as needs_sheet so it shows in the list
                        from utils.file_conversion import get_extension_format
                        file_info = {
                            'name': Path(filename).name,
                            'path': filename,
                            'df': None,
                            'type': 'excel',
                            'delimiter': None,
                            'sheet': None,
                            'rows': 0,
                            'columns': 0,
                            'original_path': filename,
                            'original_format': get_extension_format(filename),
                            'current_format': get_extension_format(filename),
                            'load_status': 'needs_sheet',
                            'last_error': 'No sheet selected — double-click to select a sheet.',
                        }
                        self.combine_mode_handler.loaded_files.append(file_info)
                        loaded_failed += 1
                        continue
                elif len(sheets) == 1:
                    sheet_name = sheets[0]

            # Safe load: errors become 'failed' entries, not exceptions
            file_info = self.combine_mode_handler.add_file_safe(filename, sheet_name=sheet_name)
            if file_info['load_status'] == 'loaded':
                loaded_ok += 1
            else:
                loaded_failed += 1

        # Refresh the Treeview to reflect what was just loaded
        self._refresh_combine_file_list()
        self.update_combine_summary()
        self._combine_update_btn_state()

        # Status message
        parts = []
        if loaded_ok:
            parts.append(f"{loaded_ok} loaded")
        if loaded_failed:
            parts.append(f"{loaded_failed} need attention")
        if skipped:
            parts.append(f"{skipped} skipped (duplicate)")
        self.status_var.set("Files: " + ", ".join(parts) if parts else "No new files added")

    def combine_remove_file(self):
        """Remove all selected files from the combine queue."""
        selected_iids = self.combine_file_tree.selection()
        if not selected_iids:
            messagebox.showwarning("No Selection", "Please select one or more files to remove.")
            return

        # IIDs are original_paths; remove each
        for iid in selected_iids:
            # Find the matching file_info by original_path
            entry = next(
                (f for f in self.combine_mode_handler.loaded_files
                 if f['original_path'] == iid),
                None
            )
            if entry:
                # Use current path for handler's internal list
                self.combine_mode_handler.loaded_files.remove(entry)

        # If handler detected_file_type / delimiter now stale, reset them
        if not self.combine_mode_handler.loaded_files:
            self.combine_mode_handler.detected_file_type = None
            self.combine_mode_handler.detected_delimiter = None

        self._refresh_combine_file_list()
        self.update_combine_summary()
        self._combine_update_btn_state()

    def combine_clear_files(self):
        """Clear all files from the combine queue."""
        if not self.combine_mode_handler.loaded_files:
            return

        if not messagebox.askyesno(
            "Clear All Files",
            "Are you sure you want to clear all files from the combine queue?"
        ):
            return

        self.combine_mode_handler.clear_files()
        self._refresh_combine_file_list()
        self.update_combine_summary()
        self._combine_update_btn_state()
        self.status_var.set("Cleared all files")

    def update_combine_summary(self):
        """Update the summary panel with extended status info."""
        if not hasattr(self, 'combine_summary_text'):
            return

        ext = self.combine_mode_handler.get_summary_extended()

        lines = []
        if ext['total'] == 0:
            lines.append("No files loaded yet.")
            lines.append("Browse files to begin. Mixed formats are supported — convert before combining.")
        else:
            status_parts = [f"Total: {ext['total']}"]
            if ext['loaded']:
                status_parts.append(f"Loaded: {ext['loaded']}")
            if ext['converted']:
                status_parts.append(f"Converted: {ext['converted']}")
            if ext['failed']:
                status_parts.append(f"Failed: {ext['failed']}")
            if ext['needs_sheet']:
                status_parts.append(f"Needs Sheet: {ext['needs_sheet']}")
            lines.append("  ".join(status_parts))

            if ext['formats']:
                lines.append(f"Formats present: {', '.join(ext['formats'])}")
                if len(ext['formats']) > 1:
                    lines.append(
                        "  ⚠ Mixed formats detected — use 'Convert All → CSV' or "
                        "'Convert All → XLSX' before combining."
                    )

            if ext['total_rows']:
                lines.append(f"Total rows (loaded): {ext['total_rows']:,}")

        self.combine_summary_text.config(state='normal')
        self.combine_summary_text.delete(1.0, tk.END)
        self.combine_summary_text.insert(1.0, "\n".join(lines))
        self.combine_summary_text.config(state='disabled')

    # ══════════════════════════════════════════════════════════════════════════
    # Combine Mode – internal helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_combine_file_list(self):
        """Rebuild the Treeview from combine_mode_handler.loaded_files."""
        if not hasattr(self, 'combine_file_tree'):
            return

        self.combine_file_tree.delete(*self.combine_file_tree.get_children())

        for fi in self.combine_mode_handler.loaded_files:
            status = fi.get('load_status', 'unknown')
            original_fmt = fi.get('original_format', '')
            current_fmt = fi.get('current_format', '')

            if status == 'converted':
                status_display = f"Converted → {current_fmt}"
            elif status == 'failed':
                status_display = 'Failed'
            elif status == 'needs_sheet':
                status_display = 'Needs Sheet Selection'
            else:
                status_display = 'Loaded'

            rows_val = fi.get('rows', 0)
            rows_display = f"{rows_val:,}" if rows_val else '—'

            # IID = original_path so it is stable across conversions
            self.combine_file_tree.insert(
                '',
                'end',
                iid=fi['original_path'],
                text=fi['name'],
                values=(status_display, current_fmt or original_fmt, rows_display),
                tags=(status,),
            )

    def _combine_update_btn_state(self):
        """Enable/disable the Combine button based on how many files are ready."""
        if not hasattr(self, 'combine_btn'):
            return
        combinable = self.combine_mode_handler.get_combinable_files()
        state = 'normal' if len(combinable) >= 2 else 'disabled'
        self.combine_btn.config(state=state)

    def _combine_on_tree_double_click(self, event):
        """Handle double-click on a Treeview row."""
        iid = self.combine_file_tree.focus()
        if not iid:
            return
        fi = next(
            (f for f in self.combine_mode_handler.loaded_files
             if f['original_path'] == iid),
            None
        )
        if fi is None:
            return

        if fi.get('load_status') == 'needs_sheet':
            self._combine_pick_sheet_for_file(fi)
        elif fi.get('load_status') == 'failed':
            self._combine_show_file_error()

    def _combine_pick_sheet_for_file(self, fi: dict):
        """Show sheet-selection dialog for a 'needs_sheet' file and reload it."""
        sheets = self.combine_mode_handler.get_excel_sheets(fi['original_path'])
        if not sheets:
            messagebox.showerror(
                "Cannot Read Sheets",
                f"Could not read sheet names from:\n{fi['name']}"
            )
            return

        sheet_name = select_sheet_from_file(self.root, fi['original_path'], sheets)
        if sheet_name is None:
            return  # User cancelled

        # Attempt to load now
        try:
            fi['sheet'] = sheet_name
            df = self.combine_mode_handler.load_file_to_dataframe(
                fi['original_path'], sheet_name=sheet_name
            )
            fi['df'] = df
            fi['rows'] = len(df)
            fi['columns'] = len(df.columns)
            fi['load_status'] = 'loaded'
            fi['last_error'] = None
            # Update detected type
            if self.combine_mode_handler.detected_file_type is None:
                self.combine_mode_handler.detected_file_type = 'excel'
        except Exception as e:
            fi['load_status'] = 'failed'
            fi['last_error'] = str(e)
            messagebox.showerror(
                "Load Error",
                f"Could not load sheet '{sheet_name}' from {fi['name']}:\n\n{e}"
            )

        self._refresh_combine_file_list()
        self.update_combine_summary()
        self._combine_update_btn_state()

    def _combine_show_file_error(self):
        """Show last_error details for selected files."""
        selected_iids = self.combine_file_tree.selection()
        if not selected_iids:
            messagebox.showinfo("Error Details", "Select one or more files to see their error details.")
            return

        messages = []
        for iid in selected_iids:
            fi = next(
                (f for f in self.combine_mode_handler.loaded_files
                 if f['original_path'] == iid),
                None
            )
            if fi and fi.get('last_error'):
                messages.append(f"File: {fi['name']}\nError: {fi['last_error']}")
            elif fi:
                messages.append(f"File: {fi['name']}\nStatus: {fi.get('load_status', 'unknown')} — no error details.")

        if messages:
            messagebox.showinfo("Error Details", "\n\n─────────────────\n\n".join(messages))

    def _combine_get_selected_file_infos(self) -> list:
        """Return file_info dicts for all Treeview-selected rows."""
        selected_iids = self.combine_file_tree.selection()
        result = []
        for iid in selected_iids:
            fi = next(
                (f for f in self.combine_mode_handler.loaded_files
                 if f['original_path'] == iid),
                None
            )
            if fi:
                result.append(fi)
        return result

    def _combine_convert_files(self, file_infos: list, target_format: str):
        """
        Convert a list of file_info entries to the target format.

        Args:
            file_infos: list of file_info dicts to convert
            target_format: 'csv' or 'xlsx'
        """
        from utils.file_conversion import (
            convert_file_to_csv, convert_file_to_xlsx, get_extension_format
        )

        if not file_infos:
            messagebox.showinfo("Nothing to Convert", "No files selected for conversion.")
            return

        converted = 0
        skipped = 0
        errors = []

        for fi in file_infos:
            # Skip already-correct format (unless it's failed/needs_sheet)
            current_ext = Path(fi['path']).suffix.lower()
            target_ext = f'.{target_format}'
            already_right_format = current_ext == target_ext
            already_correct_and_loaded = (
                already_right_format and fi.get('load_status') in ('loaded', 'converted')
            )
            if already_correct_and_loaded:
                skipped += 1
                continue

            # For Excel → CSV: need sheet selection if not already set
            sheet_name = fi.get('sheet')
            if (fi.get('type') == 'excel' or
                    Path(fi['path']).suffix.lower() in ('.xlsx', '.xls', '.xlsm')):
                if sheet_name is None:
                    sheets = self.combine_mode_handler.get_excel_sheets(fi['path'])
                    if len(sheets) > 1:
                        sheet_name = select_sheet_from_file(self.root, fi['path'], sheets)
                        if sheet_name is None:
                            # User cancelled this one
                            fi['load_status'] = 'needs_sheet'
                            fi['last_error'] = 'No sheet selected — double-click to select a sheet.'
                            skipped += 1
                            continue
                    elif len(sheets) == 1:
                        sheet_name = sheets[0]

            try:
                if target_format == 'csv':
                    new_path = convert_file_to_csv(fi['path'], sheet_name)
                else:
                    new_path = convert_file_to_xlsx(fi['path'], sheet_name)

                # Reload DataFrame from converted file
                new_type = self.combine_mode_handler.detect_file_type(new_path)
                delimiter = None
                if new_type == 'text':
                    delimiter = self.combine_mode_handler.detect_delimiter(new_path)
                df = self.combine_mode_handler.load_file_to_dataframe(
                    new_path, delimiter=delimiter, sheet_name=None
                )

                # Update file_info in-place
                fi['path'] = new_path
                fi['name'] = Path(new_path).name
                fi['df'] = df
                fi['type'] = new_type
                fi['delimiter'] = delimiter
                fi['sheet'] = None
                fi['rows'] = len(df)
                fi['columns'] = len(df.columns)
                fi['current_format'] = get_extension_format(new_path)
                fi['load_status'] = 'converted'
                fi['last_error'] = None

                # Update handler-level type/delimiter if first file sets them
                if self.combine_mode_handler.detected_file_type is None:
                    self.combine_mode_handler.detected_file_type = new_type
                if new_type == 'text' and self.combine_mode_handler.detected_delimiter is None:
                    self.combine_mode_handler.detected_delimiter = delimiter

                converted += 1

            except Exception as e:
                logging.error(f"Conversion failed for '{fi['name']}': {e}", exc_info=True)
                fi['load_status'] = 'failed'
                fi['last_error'] = f"Conversion to {target_format.upper()} failed: {e}"
                errors.append(f"{fi['name']}: {e}")

        # Refresh UI
        self._refresh_combine_file_list()
        self.update_combine_summary()
        self._combine_update_btn_state()

        # Status report
        parts = []
        if converted:
            parts.append(f"{converted} converted to {target_format.upper()}")
        if skipped:
            parts.append(f"{skipped} skipped")
        if errors:
            parts.append(f"{len(errors)} failed")
        self.status_var.set(", ".join(parts) if parts else "No changes made")

        if errors:
            msg = "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... and {len(errors) - 5} more"
            messagebox.showwarning(
                "Conversion Errors",
                f"Some files could not be converted:\n\n{msg}"
            )
        elif converted:
            messagebox.showinfo(
                "Conversion Complete",
                f"Converted {converted} file(s) to {target_format.upper()}.\n"
                f"Files are now ready to combine."
            )

    def _combine_convert_selected_to_csv(self):
        """Convert Treeview-selected files to CSV."""
        targets = self._combine_get_selected_file_infos()
        if not targets:
            messagebox.showwarning("No Selection",
                                   "Select one or more files in the list first.")
            return
        self._combine_convert_files(targets, 'csv')

    def _combine_convert_selected_to_xlsx(self):
        """Convert Treeview-selected files to XLSX."""
        targets = self._combine_get_selected_file_infos()
        if not targets:
            messagebox.showwarning("No Selection",
                                   "Select one or more files in the list first.")
            return
        self._combine_convert_files(targets, 'xlsx')

    def _combine_convert_all_to_csv(self):
        """Convert all loaded files to CSV."""
        targets = list(self.combine_mode_handler.loaded_files)
        if not targets:
            messagebox.showinfo("Nothing to Convert", "No files loaded.")
            return
        self._combine_convert_files(targets, 'csv')

    def _combine_convert_all_to_xlsx(self):
        """Convert all loaded files to XLSX."""
        targets = list(self.combine_mode_handler.loaded_files)
        if not targets:
            messagebox.showinfo("Nothing to Convert", "No files loaded.")
            return
        self._combine_convert_files(targets, 'xlsx')

    def _combine_retry_failed(self):
        """Attempt to reload all files with load_status 'failed'."""
        failed = [
            f for f in self.combine_mode_handler.loaded_files
            if f.get('load_status') == 'failed'
        ]
        if not failed:
            messagebox.showinfo("No Failed Files",
                                "There are no failed files to retry.")
            return

        retried = 0
        still_failed = 0

        for fi in failed:
            try:
                file_type = self.combine_mode_handler.detect_file_type(fi['original_path'])
                delimiter = None
                sheet_name = fi.get('sheet')

                if file_type == 'excel' and sheet_name is None:
                    sheets = self.combine_mode_handler.get_excel_sheets(fi['original_path'])
                    if len(sheets) > 1:
                        sheet_name = select_sheet_from_file(
                            self.root, fi['original_path'], sheets
                        )
                        if sheet_name is None:
                            fi['load_status'] = 'needs_sheet'
                            fi['last_error'] = 'No sheet selected — double-click to select.'
                            still_failed += 1
                            continue
                    elif len(sheets) == 1:
                        sheet_name = sheets[0]

                if file_type == 'text':
                    delimiter = self.combine_mode_handler.detect_delimiter(fi['original_path'])

                df = self.combine_mode_handler.load_file_to_dataframe(
                    fi['original_path'], delimiter=delimiter, sheet_name=sheet_name
                )

                fi['df'] = df
                fi['type'] = file_type
                fi['delimiter'] = delimiter
                fi['sheet'] = sheet_name
                fi['rows'] = len(df)
                fi['columns'] = len(df.columns)
                fi['load_status'] = 'loaded'
                fi['last_error'] = None
                retried += 1

            except Exception as e:
                fi['load_status'] = 'failed'
                fi['last_error'] = str(e)
                still_failed += 1

        self._refresh_combine_file_list()
        self.update_combine_summary()
        self._combine_update_btn_state()

        msg_parts = []
        if retried:
            msg_parts.append(f"{retried} file(s) loaded successfully")
        if still_failed:
            msg_parts.append(f"{still_failed} still failed — try converting them instead")
        self.status_var.set("; ".join(msg_parts) if msg_parts else "Retry complete")

    def _combine_pre_combine_check(self) -> bool:
        """
        Check the combine set for mixed formats or failed files before combining.

        Returns True if it is safe to proceed, False if the user chose to cancel.
        Shows a dialog summarising the situation when issues are found.
        """
        all_files = self.combine_mode_handler.loaded_files
        good_files = self.combine_mode_handler.get_combinable_files()
        failed_files = [f for f in all_files if f.get('load_status') == 'failed']
        needs_sheet = [f for f in all_files if f.get('load_status') == 'needs_sheet']

        file_types = {f.get('type') for f in good_files if f.get('type')}
        has_mixed_types = len(file_types) > 1

        issues = []
        if failed_files:
            names = ', '.join(f['name'] for f in failed_files[:3])
            extra = f" (+{len(failed_files)-3} more)" if len(failed_files) > 3 else ''
            issues.append(f"• {len(failed_files)} failed file(s): {names}{extra}")
        if needs_sheet:
            names = ', '.join(f['name'] for f in needs_sheet[:3])
            issues.append(f"• {len(needs_sheet)} file(s) need sheet selection: {names}")
        if has_mixed_types:
            type_names = ', '.join(sorted(file_types))
            issues.append(f"• Mixed file types in combine set: {type_names}")

        if not issues:
            return True  # Nothing to warn about

        summary_lines = [
            f"Ready to combine: {len(good_files)} file(s)",
            "",
        ] + issues + [
            "",
            "Do you want to continue with the available loaded files,",
            "or cancel to convert/fix the remaining files first?",
        ]

        result = messagebox.askyesno(
            "Pre-Combine Check",
            "\n".join(summary_lines),
            icon='warning'
        )
        return result  # True = continue, False = cancel

    # ══════════════════════════════════════════════════════════════════════════
    # End Combine Mode helpers
    # ══════════════════════════════════════════════════════════════════════════

    def combine_files_execute(self):
        """
        Execute file combination and export.

        COMBINE_CSV_FIX: Use CSV-aware methods for text files to preserve exact formatting.
        Only operates on files with load_status in ('loaded', 'converted').
        """
        # Pre-combine check for mixed formats / failed files
        if not self._combine_pre_combine_check():
            return  # User chose to cancel and fix files first

        # Work only with combinable files
        good_files = self.combine_mode_handler.get_combinable_files()

        # Final validation on the good-files subset
        is_valid, error_msg = self.combine_mode_handler.validate_files(good_files)
        if not is_valid:
            messagebox.showerror("Validation Error", error_msg)
            return

        try:
            # Determine type from good files (they should all be the same by now)
            file_types = {f.get('type') for f in good_files if f.get('type')}
            file_type = 'text' if 'text' in file_types else 'excel'

            if file_type == 'text':
                # Use raw text line-based combining
                file_paths = [f['path'] for f in good_files]

                # Determine delimiter from first text file
                delimiter = None
                for f in good_files:
                    if f.get('type') == 'text' and f.get('delimiter'):
                        delimiter = f['delimiter']
                        break
                if delimiter is None:
                    delimiter = self.combine_mode_handler.detected_delimiter or ','

                # Combine files using raw text processing
                header_line, data_lines, files_processed = (
                    self.combine_mode_handler.combine_text_files_raw(file_paths, delimiter)
                )

                messagebox.showinfo(
                    "Files Combined",
                    f"Successfully combined {len(good_files)} files!\n\n"
                    f"Total data rows: {len(data_lines):,}\n"
                    f"Repeated headers removed automatically.\n\n"
                    "Original formatting preserved exactly.\n"
                    "Click OK to select the export location."
                )

                ext_summary = self.combine_mode_handler.get_summary_extended()
                self.combine_export_dialog_raw(header_line, data_lines, ext_summary)

            else:
                # Excel files – use pandas method
                dataframes = [f['df'] for f in good_files]
                combined_df = self.combine_mode_handler.combine_dataframes(dataframes)

                messagebox.showinfo(
                    "Files Combined",
                    f"Successfully combined {len(good_files)} files!\n\n"
                    f"Total rows: {len(combined_df):,}\n"
                    f"Total columns: {len(combined_df.columns)}\n\n"
                    "Click OK to select the export location."
                )

                ext_summary = self.combine_mode_handler.get_summary_extended()
                self.combine_export_dialog(combined_df, ext_summary)

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
            filetypes = [("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("Text files", "*.txt")]
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
            elif output_path.endswith('.txt') and file_type == 'excel':
                # Excel-sourced TXT: quoted comma format (QUOTE_ALL)
                ExportHelper.export_to_txt(combined_df, output_path)
            else:
                # CSV/TSV or text-sourced .txt: preserve detected delimiter
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
                f"Delimiter: {self.combine_mode_handler.detected_delimiter or 'auto-detected'}"
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

        if operation.metadata.id == 'filter_lower_48':
            # Use specialized Lower 48 dialog with country/checkbox controls
            self._show_lower_48_dialog(operation, columns)
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
            self._push_undo_snapshot()
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
            self._update_history_buttons()
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

            self._push_undo_snapshot()
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
            self._update_history_buttons()
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

            self._push_undo_snapshot()
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
            self._update_history_buttons()
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

            elif param.type == 'add_columns_list':
                # Special widget for adding multiple columns with dynamic add/remove rows
                from ui.widgets.add_columns_widget import AddColumnsWidget

                # Create the add columns widget
                widget = AddColumnsWidget(frame)
                widget.pack(fill='both', expand=True, pady=2)

                # Pre-fill column definitions if in edit mode
                if current_value and isinstance(current_value, list):
                    widget.set_columns(current_value)

                param_widgets[param.name] = widget

        def on_add():
            from ui.widgets.column_rename_widget import ColumnRenameWidget
            from ui.widgets.add_columns_widget import AddColumnsWidget

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
                    elif isinstance(widget, AddColumnsWidget):
                        # Get column definitions from the add columns widget
                        # First validate
                        is_valid, error_msg = widget.validate()
                        if not is_valid:
                            from tkinter import messagebox
                            messagebox.showwarning("Invalid Column Definitions", error_msg)
                            return
                        columns = widget.get_columns()
                        if not columns and param.required:
                            from tkinter import messagebox
                            messagebox.showwarning("Missing Columns", f"{param.description} is required")
                            return
                        params[param.name] = columns
                    elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                        value = widget.get()
                        if param.type == 'number':
                            try:
                                value = float(value)
                            except:
                                value = 0
                        params[param.name] = value

            self._push_undo_snapshot()
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
            self._update_history_buttons()
            dialog.destroy()

        # Fixed button frame at the bottom (NOT in scrollable area)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10, padx=10)

        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        button_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=button_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)


    def _show_lower_48_dialog(self, operation, columns, edit_mode=False, edit_index=None, current_params=None):
        """Custom dialog for Filter to Lower 48 States operation."""
        from ui.widgets.scrollable_frame import ScrollableOperationFrame

        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Edit' if edit_mode else 'Add'}: {operation.metadata.name}")
        dialog.geometry("620x620")
        dialog.transient(self.root)
        dialog.grab_set()

        # Scrollable content area
        scrollable = ScrollableOperationFrame(dialog)
        scrollable.pack(fill='both', expand=True, padx=10, pady=(10, 0))
        main_frame = scrollable.scroll_frame

        # --- Title ---
        ttk.Label(
            main_frame,
            text=operation.metadata.name,
            font=('Segoe UI', 14, 'bold'),
        ).pack(pady=(10, 4), padx=10)

        ttk.Label(
            main_frame,
            text=operation.metadata.description,
            wraplength=570,
            font=('Arial', 11),
        ).pack(pady=(0, 14), padx=10)

        # Helper: current param value
        def cp(name, default=None):
            if current_params and name in current_params:
                return current_params[name]
            return default

        # --- State column (required) ---
        state_frame = ttk.LabelFrame(main_frame, text="State Column  (required)", padding=8)
        state_frame.pack(fill='x', pady=(0, 6), padx=10)

        state_selector = ColumnSelector(state_frame, columns, "Select state column *")
        state_selector.pack(fill='x')
        saved_state = cp('state_column', '')
        if saved_state:
            state_selector.set_value(saved_state)

        # --- Country column (optional) ---
        country_frame = ttk.LabelFrame(main_frame, text="Country Column  (optional)", padding=8)
        country_frame.pack(fill='x', pady=(0, 6), padx=10)

        ttk.Label(
            country_frame,
            text="Leave blank to skip country-based filtering.",
            font=('Arial', 9),
            foreground='gray',
        ).pack(anchor='w', pady=(0, 4))

        country_selector = ColumnSelector(country_frame, [''] + columns, "Select country column (optional)")
        country_selector.pack(fill='x')
        saved_country = cp('country_column', '')
        if saved_country:
            country_selector.set_value(saved_country)

        # --- Country sub-options (shown/hidden based on country selection) ---
        country_opts_frame = ttk.Frame(country_frame)
        country_opts_frame.pack(fill='x', pady=(6, 0))

        require_usa_var = tk.BooleanVar(value=cp('require_usa_country', True))
        require_usa_cb = ttk.Checkbutton(
            country_opts_frame,
            text='Require USA in Country column  (US / USA / United States)',
            variable=require_usa_var,
        )
        require_usa_cb.pack(anchor='w')

        allow_blank_country_var = tk.BooleanVar(value=cp('allow_blank_country', True))
        allow_blank_cb = ttk.Checkbutton(
            country_opts_frame,
            text='Allow rows where Country is blank',
            variable=allow_blank_country_var,
        )
        allow_blank_cb.pack(anchor='w')

        def _update_country_opts(*_):
            raw = country_selector.get_value().strip()
            state = 'normal' if raw else 'disabled'
            require_usa_cb.config(state=state)
            allow_blank_cb.config(state=state)

        # Bind to combobox changes
        country_selector.combo.bind('<<ComboboxSelected>>', _update_country_opts)
        country_selector.combo.bind('<KeyRelease>', _update_country_opts)
        _update_country_opts()  # Set initial state

        # --- Options ---
        opts_frame = ttk.LabelFrame(main_frame, text="Options", padding=8)
        opts_frame.pack(fill='x', pady=(0, 6), padx=10)

        normalize_var = tk.BooleanVar(value=cp('normalize_states', True))
        ttk.Checkbutton(
            opts_frame,
            text='Normalize full state names to abbreviations  (e.g. "New York" → "NY", "N.Y." → "NY")',
            variable=normalize_var,
        ).pack(anchor='w')

        remove_blank_var = tk.BooleanVar(value=cp('remove_blank_states', True))
        ttk.Checkbutton(
            opts_frame,
            text='Remove rows with blank or unrecognised state',
            variable=remove_blank_var,
        ).pack(anchor='w', pady=(4, 0))

        include_dc_var = tk.BooleanVar(value=cp('include_dc', False))
        ttk.Checkbutton(
            opts_frame,
            text='Include DC (Washington D.C.) in the Lower 48 allow-list',
            variable=include_dc_var,
        ).pack(anchor='w', pady=(4, 0))

        # --- Submit ---
        def on_add():
            state_col = state_selector.get_value().strip()
            if not state_col:
                from tkinter import messagebox as mb
                mb.showwarning("State Column Required", "Please select a State column.", parent=dialog)
                return

            country_col = country_selector.get_value().strip()

            params = {
                'state_column': state_col,
                'country_column': country_col,
                'normalize_states': normalize_var.get(),
                'remove_blank_states': remove_blank_var.get(),
                'require_usa_country': require_usa_var.get(),
                'allow_blank_country': allow_blank_country_var.get(),
                'include_dc': include_dc_var.get(),
            }

            self._push_undo_snapshot()
            if edit_mode:
                self.operation_queue[edit_index] = {
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': self.operation_queue[edit_index]['enabled'],
                }
                self.status_var.set(f"Updated: {operation.metadata.name}")
            else:
                self.operation_queue.append({
                    'operation_id': operation.metadata.id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': True,
                })
                self.status_var.set(f"Added: {operation.metadata.name}")

            self.refresh_queue_display()
            self._save_current_workflow()
            self._update_history_buttons()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', pady=10, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=15).pack(side='left', padx=5)
        btn_text = "✓ Update" if edit_mode else "✓ Add to Queue"
        ttk.Button(btn_frame, text=btn_text, command=on_add, style='Success.TButton', width=15).pack(side='right', padx=5)


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

            # Persist session to disk (debounced)
            self.save_session_debounced()

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
            self._push_undo_snapshot()
            self.operation_queue = []
            self.refresh_queue_display()

            # Save cleared queue to active sheet
            self._save_current_workflow()
            self._update_history_buttons()

    # ==================== UNDO / REDO / RESET ====================

    def _push_undo_snapshot(self):
        """Snapshot the current queue state onto the active sheet's undo stack before a mutation."""
        if not self.workbook_session:
            return
        active = self.workbook_session.get_active_sheet()
        if active:
            # Sync GUI queue → sheet state so the snapshot is accurate
            active.operations = copy.deepcopy(self.operation_queue)
            active.push_undo()

    def _update_history_buttons(self):
        """Enable or disable the Undo/Redo/Reset toolbar buttons to reflect current state."""
        if not hasattr(self, 'undo_btn') or self.undo_btn is None:
            return
        has_undo = False
        has_redo = False
        if self.workbook_session:
            active = self.workbook_session.get_active_sheet()
            if active:
                has_undo = bool(active.undo_stack)
                has_redo = bool(active.redo_stack)
        self.undo_btn.config(state='normal' if has_undo else 'disabled')
        self.redo_btn.config(state='normal' if has_redo else 'disabled')
        self.reset_btn.config(state='normal' if self.df is not None else 'disabled')

    def perform_undo(self):
        """Undo the last workflow change on the active sheet."""
        if not self.workbook_session:
            return
        active = self.workbook_session.get_active_sheet()
        if not active or not active.undo_stack:
            return
        if active.undo():
            self.operation_queue = copy.deepcopy(active.operations)
            self.refresh_queue_display()
            self._save_current_workflow()
            self.update_preview_state()
            self._update_history_buttons()

    def perform_redo(self):
        """Redo the last undone workflow change on the active sheet."""
        if not self.workbook_session:
            return
        active = self.workbook_session.get_active_sheet()
        if not active or not active.redo_stack:
            return
        if active.redo():
            self.operation_queue = copy.deepcopy(active.operations)
            self.refresh_queue_display()
            self._save_current_workflow()
            self.update_preview_state()
            self._update_history_buttons()

    def perform_reset(self):
        """Clear all workflow operations and restore the original loaded data state."""
        if self.df is None:
            return
        if not messagebox.askyesno(
            "Reset Workflow",
            "Remove all operations and return to the original loaded data?\n\n"
            "This will also clear the undo history for the current sheet."
        ):
            return
        if self.workbook_session:
            active = self.workbook_session.get_active_sheet()
            if active:
                active.undo_stack.clear()
                active.redo_stack.clear()
        self.operation_queue = []
        self.refresh_queue_display()
        self._save_current_workflow()
        self.update_preview_state()
        self._update_history_buttons()
        self.status_var.set("Reset: workflow cleared — showing original loaded data.")

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
                raw_df = pd.read_excel(self.current_file, sheet_name=sheet_name)
                self.workbook_session.load_sheet_data(sheet_name, raw_df)
                # If smart format has already been applied (e.g. session recovery),
                # use its result as the working df so workflow ops see target columns.
                if sheet_state.smart_format and sheet_state.has_results():
                    self.df = sheet_state.df_result
                    logging.info(
                        "[SHEET TAB] Sheet loaded; using smart-format result df "
                        "(%d rows, target schema)", len(self.df)
                    )
                else:
                    self.df = raw_df
                    logging.info(f"[SHEET TAB] Sheet loaded: {len(self.df):,} rows")
            else:
                # Sheet already loaded – use formatted df if smart format was applied,
                # so that any subsequent workflow ops validate against target columns.
                if sheet_state.smart_format and sheet_state.has_results():
                    self.df = sheet_state.df_result
                    logging.info(
                        "[SHEET TAB] Restored smart-format result df for '%s' "
                        "(%d rows, columns: %s)",
                        sheet_name, len(self.df),
                        sheet_state.df_result.columns.tolist(),
                    )
                else:
                    self.df = sheet_state.df_original
                    logging.info(
                        f"[SHEET TAB] Sheet retrieved from cache: {len(self.df):,} rows"
                    )

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

            # STEP 6: Refresh Smart Format recommendations panel for new sheet
            self.refresh_smart_format_panel()

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
            self._update_history_buttons()

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

            # Save session after successful file load
            self.logger.info("Saving session after file load")
            self.save_session_debounced()
            self._update_history_buttons()

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

            # Save session after successful operations run
            self.logger.info("Saving session after operations execution")
            self.save_session_debounced()

            if validation_issues:
                messagebox.showwarning("Success with Issues", success_msg)
            else:
                messagebox.showinfo("Success", success_msg)

        except Exception as e:
            messagebox.showerror("Error", f"Execution failed:\n{str(e)}")

    # ------------------------------------------------------------------
    # Smart Format – Mail File Standard
    # ------------------------------------------------------------------

    def _build_smart_format_panel(self):
        """Build the Smart Format status panel contents (initially hidden)."""
        panel = tk.Frame(self.smart_format_panel, bg='#FFF4CE')
        panel.pack(fill='x')

        # ---- Header row: indicator + dismiss ----
        header_row = tk.Frame(panel, bg='#FFF4CE')
        header_row.pack(fill='x', padx=8, pady=(4, 2))

        self._sf_indicator_lbl = tk.Label(
            header_row,
            text="✨ Smart Format: Mail File Standard (Configured)",
            font=('Segoe UI', 8, 'bold'),
            bg='#FFF4CE', fg='#5D4037',
            anchor='w',
        )
        self._sf_indicator_lbl.pack(side='left')

        tk.Button(
            header_row,
            text="✕",
            font=('Segoe UI', 7),
            bg='#FFF4CE', fg='#795548',
            bd=0, padx=3, pady=0,
            cursor='hand2',
            command=self._dismiss_smart_format_panel,
            relief='flat',
            activebackground='#FFE082',
        ).pack(side='right')

        # ---- Button row ----
        btn_row = tk.Frame(panel, bg='#FFF4CE')
        btn_row.pack(fill='x', padx=8, pady=(0, 5))

        # Edit Smart Format
        tk.Button(
            btn_row,
            text="✏ Edit Smart Format…",
            font=('Segoe UI', 8),
            bg='#0078D4', fg='white',
            bd=0, padx=8, pady=3,
            cursor='hand2',
            command=self._edit_smart_format,
            relief='flat',
            activebackground='#005A9E',
        ).pack(side='left', padx=(0, 4))

        self._dedupe_rec_btn = tk.Button(
            btn_row,
            text="⊕ Add Dedupe Step",
            font=('Segoe UI', 8),
            bg='#F9A825', fg='white',
            bd=0, padx=8, pady=3,
            cursor='hand2',
            command=self._add_recommended_dedupe,
            relief='flat',
            activebackground='#F57F17',
        )
        self._dedupe_rec_btn.pack(side='left', padx=(0, 4))

        self._issues_rec_btn = tk.Button(
            btn_row,
            text="⚠ Review Issues",
            font=('Segoe UI', 8),
            bg='#E65100', fg='white',
            bd=0, padx=8, pady=3,
            cursor='hand2',
            command=self._review_smart_format_issues,
            relief='flat',
            activebackground='#BF360C',
        )
        self._issues_rec_btn.pack(side='left', padx=(0, 4))

        # Clear Smart Format
        tk.Button(
            btn_row,
            text="🗑 Clear Smart Format",
            font=('Segoe UI', 8),
            bg='#797775', fg='white',
            bd=0, padx=8, pady=3,
            cursor='hand2',
            command=self._clear_smart_format,
            relief='flat',
            activebackground='#484644',
        ).pack(side='right', padx=(4, 0))

    def refresh_smart_format_panel(self):
        """Show/hide the Smart Format status panel and update buttons for the active sheet."""
        if not hasattr(self, 'smart_format_panel'):
            return

        # Determine if smart format is configured for the active sheet.
        # Check smart_format field first (new), fall back to legacy meta flag.
        sf_config = None
        meta = {}
        if self.workbook_session:
            active = self.workbook_session.get_active_sheet()
            if active:
                sf_config = getattr(active, 'smart_format', None)
                meta = getattr(active, 'meta', {})

        applied = (sf_config is not None) or meta.get('smart_format_mail_standard_applied', False)

        if not applied:
            self.smart_format_panel.pack_forget()
            return

        # Show the panel (before queue_content)
        if not self.smart_format_panel.winfo_ismapped():
            self.smart_format_panel.pack(
                fill='x', padx=10, pady=(0, 4),
                before=self.queue_content,
            )

        # --- Update indicator label ---
        if hasattr(self, '_sf_indicator_lbl'):
            template = (sf_config or {}).get('template_id', 'Mail Standard')
            preset   = (sf_config or {}).get('preset_name')
            lbl_txt  = f"✨ Smart Format: {template} (Configured)"
            if preset:
                lbl_txt += f"  •  Preset: {preset}"
            self._sf_indicator_lbl.config(text=lbl_txt)

        # --- Update dedupe button ---
        dedupe_in_queue = any(
            op.get('operation_id') == 'data_remove_duplicates'
            for op in self.operation_queue
        )
        if dedupe_in_queue:
            self._dedupe_rec_btn.config(
                text="✓ Dedupe Already in Queue",
                state='disabled',
                bg='#9E9E9E',
            )
        else:
            # Try to get recommended keys from smart_format config or legacy meta
            rec_keys = []
            if sf_config:
                rec_keys = sf_config.get('recommended_dedupe_keys', [])
            if not rec_keys:
                rec_keys = meta.get('recommended_dedupe_keys', [])

            if rec_keys:
                key_label = " + ".join(rec_keys[:3])
                btn_text = f"⊕ Add Dedupe  ({key_label})"
            else:
                btn_text = "⊕ Add Dedupe Step"
            self._dedupe_rec_btn.config(
                text=btn_text,
                state='normal',
                bg='#F9A825',
            )

        # --- Update issues button ---
        sf_issues = []
        if self.workbook_session:
            active = self.workbook_session.get_active_sheet()
            if active:
                sf_issues = [
                    i for i in getattr(active, 'issues', [])
                    if getattr(i, 'op_label', '') == 'Smart Format (Mail Standard)'
                ]
        if sf_issues:
            self._issues_rec_btn.config(
                text=f"⚠ Review {len(sf_issues)} Issue(s)",
                state='normal',
                bg='#E65100',
            )
        else:
            self._issues_rec_btn.config(
                text="✓ No Issues",
                state='disabled',
                bg='#9E9E9E',
            )

    def _dismiss_smart_format_panel(self):
        """Hide the recommendations panel without clearing sheet meta."""
        self.smart_format_panel.pack_forget()

    def _add_recommended_dedupe(self):
        """Append a Remove Duplicate Rows operation using the recommended keys."""
        if not self.workbook_session:
            return
        active = self.workbook_session.get_active_sheet()
        if not active:
            return

        rec_keys = active.meta.get('recommended_dedupe_keys', [])

        # Push undo snapshot before modifying queue
        active.push_undo()

        self.operation_queue.append({
            'operation_id': 'data_remove_duplicates',
            'name': 'Remove Duplicate Rows',
            'parameters': {
                'multi_level_deduplication': False,
                'columns': rec_keys,
                'keep': 'first',
                'smart_matching': True,
            },
            'enabled': True,
        })
        self.refresh_queue_display()
        self._save_current_workflow()
        self.status_var.set("Added: Remove Duplicate Rows (recommended keys)")

        # Disable the button to prevent duplicate additions
        self._dedupe_rec_btn.config(
            text="✓ Dedupe Already in Queue",
            state='disabled',
            bg='#9E9E9E',
        )

    def _review_smart_format_issues(self):
        """Show a summary dialog for Smart Format issues on the active sheet."""
        if not self.workbook_session:
            return
        active = self.workbook_session.get_active_sheet()
        if not active:
            return

        sf_issues = [
            i for i in getattr(active, 'issues', [])
            if getattr(i, 'op_label', '') == 'Smart Format (Mail Standard)'
        ]

        if not sf_issues:
            messagebox.showinfo("Smart Format Issues", "No issues recorded for this sheet.")
            return

        lines = [f"Smart Format Issues ({len(sf_issues)} total)\n"]
        for iss in sf_issues:
            code = getattr(iss, 'code', '?')
            msg  = getattr(iss, 'message', '')
            lines.append(f"  [{code}]  {msg}")

        messagebox.showinfo("Smart Format Issues", "\n".join(lines))

    def launch_smart_format(self, existing_config=None):
        """
        Launch the Smart Format wizard and, upon Apply, transform the active
        sheet's data into the 24-column mail-file standard.

        Parameters
        ----------
        existing_config : dict or None
            If provided the wizard opens in edit mode pre-populated with
            the prior selections from SheetState.smart_format.
        """
        if self.df is None:
            messagebox.showwarning("No Data", "Please load a file first.")
            return

        from ui.smart_format_wizard import SmartFormatWizard
        from utils.smart_mapping import apply_mail_standard, REQUIRED_SCHEMA, BCC_REQUIRED_SCHEMA
        from utils.smart_preset_manager import TEMPLATE_ID_MAIL_STANDARD, TEMPLATE_ID_BCC_MAIL
        from workbook_session import Issue

        raw_cols = self.df.columns.tolist()

        # Determine schema type: reuse existing config in edit mode, else ask user
        if existing_config:
            _template_id = existing_config.get("template_id", TEMPLATE_ID_MAIL_STANDARD)
        else:
            _template_id = self._ask_smart_format_schema()
            if _template_id is None:
                return  # user cancelled selector

        if _template_id == TEMPLATE_ID_BCC_MAIL:
            _schema = BCC_REQUIRED_SCHEMA
            _schema_label = "BCC Mail File Config"
        else:
            _schema = REQUIRED_SCHEMA
            _schema_label = "Mail File Standard"

        # Show wizard (blocks until closed)
        wizard = SmartFormatWizard(
            self.root, raw_cols,
            existing_config=existing_config,
            schema=_schema,
            template_id=_template_id,
        )
        mapping_config = wizard.show()

        if mapping_config is None:
            return   # user cancelled

        # ---- Apply the mail standard ----
        try:
            df_out, raw_issues, apply_meta = apply_mail_standard(
                self.df, mapping_config, _schema
            )
        except Exception as exc:
            messagebox.showerror("Smart Format Error",
                                 f"Failed to apply mail standard:\n{exc}")
            return

        # ---- Convert raw issues to Issue objects ----
        _op_label = f"Smart Format ({_schema_label})"
        sheet_name = self.current_sheet_name or "Sheet"
        issue_objects = []
        for raw in raw_issues:
            issue_objects.append(Issue(
                sheet_name=sheet_name,
                op_index=-1,
                op_label=_op_label,
                code=raw["code"],
                message=raw["message"],
                details=raw.get("details", {}),
            ))

        # ---- Apply operations from Ops Builder (Step 4) ----
        ops_plan = mapping_config.get("operations_plan", {})
        df_final, ops_added, removed_from_ops = self._apply_smart_format_ops_plan(
            df_out, ops_plan
        )

        # ---- Compute recommended dedupe keys from output columns ----
        _DEDUPE_PRIORITY = (
            ["FULLNAME", "COMPANY", "DELADDR", "ZIP+4"]
            if _template_id == TEMPLATE_ID_BCC_MAIL
            else ["Email Address", "Company", "Address1", "Zip", "Contact"]
        )
        rec_keys = [k for k in _DEDUPE_PRIORITY if k in df_final.columns]

        # ---- Build persistent smart_format config for SheetState ----
        from datetime import datetime as _dt
        sf_config = {
            "template_id":     mapping_config.get("template_id", "MAIL_STANDARD_V1"),
            "mapping_config": {
                "column_map":       mapping_config.get("column_map", {}),
                "derivation_plan":  mapping_config.get("derivation_plan", "blank"),
                "first_col":        mapping_config.get("first_col"),
                "last_col":         mapping_config.get("last_col"),
            },
            "operations_plan":         ops_plan,
            "created_blank":           apply_meta.get("created_blank", []),
            "dropped_columns":         apply_meta.get("dropped_columns", []),
            "recommended_dedupe_keys": rec_keys,
            "last_applied_timestamp":  _dt.now().isoformat(),
            "preset_name":             mapping_config.get("preset_name"),
            "version":                 "1",
        }

        # ---- Update active sheet state ----
        # Phase 1 (mapping) + Phase 2 (post-ops) are already complete.
        # Update self.df to the formatted result so any future workflow
        # operations the user adds will validate / execute against the
        # target-schema columns (Address1, Company, etc.), not the raw columns.
        self.df = df_final
        self.result_df = df_final
        if self.workbook_session:
            active_sheet = self.workbook_session.get_active_sheet()
            if active_sheet:
                active_sheet.df_result = df_final
                active_sheet.is_dirty = True

                # Persist Smart Format config – this is NEVER cleared by
                # normal workflow ops; only by "Clear Smart Format".
                active_sheet.smart_format = sf_config

                # Legacy meta flag for backward compatibility
                active_sheet.meta["smart_format_mail_standard_applied"] = True
                active_sheet.meta["recommended_dedupe_keys"] = rec_keys

                # Append smart-format issues (preserve previous issues)
                existing_sf_issues = [
                    i for i in getattr(active_sheet, "issues", [])
                    if getattr(i, "op_label", "") != _op_label
                ]
                active_sheet.issues = existing_sf_issues + issue_objects

                # NOTE: Post-mapping ops (dedupe, remove-rows, etc.) are
                # intentionally NOT added to the regular operation_queue.
                # They have already been applied to df_final above, and their
                # parameters reference target-schema column names.  Adding
                # them to the queue would cause "column not found" validation
                # errors if the user ever clicks Run on the original pipeline.
                # The ops are stored in smart_format["operations_plan"] so
                # they can be reviewed / re-applied via "Edit Smart Format".
                logging.info(
                    "[SmartFormat] Applied. Working df updated to target schema: %s",
                    df_final.columns.tolist(),
                )

                if issue_objects and self.sheet_tab_bar and self.current_sheet_name:
                    self.sheet_tab_bar.mark_sheet_issues(
                        self.current_sheet_name, has_issues=True
                    )
        else:
            # Single-file mode without workbook session
            pass

        # ---- Refresh preview ----
        if hasattr(self, "enhanced_preview"):
            self.enhanced_preview.load_dataframe(df_final, is_result=True)

        # ---- Status / success message ----
        n_blank   = len(apply_meta.get("created_blank", []))
        n_dropped = len(apply_meta.get("dropped_columns", []))
        n_issues  = len(issue_objects)
        n_ops     = len(ops_added)

        status_parts = [f"Smart Format applied — {len(df_final.columns)} columns, {len(df_final):,} rows"]
        if n_blank:
            status_parts.append(f"{n_blank} blank column(s) created")
        if n_dropped:
            status_parts.append(f"{n_dropped} extra column(s) dropped")
        if n_ops:
            status_parts.append(f"{n_ops} post-mapping op(s) run")
        if n_issues:
            status_parts.append(f"{n_issues} issue(s) flagged")

        self.status_var.set("  |  ".join(status_parts))

        # Summary dialog
        detail_lines = []
        if apply_meta.get("derived_contact"):
            detail_lines.append("• Contact derived from First + Last Name")
        if n_blank:
            detail_lines.append(
                f"• {n_blank} column(s) created blank: "
                + ", ".join(apply_meta.get("created_blank", [])[:8])
                + ("…" if n_blank > 8 else "")
            )
        if n_dropped:
            dropped = apply_meta.get("dropped_columns", [])
            detail_lines.append(
                f"• {n_dropped} source column(s) dropped: "
                + ", ".join(dropped[:6])
                + ("…" if n_dropped > 6 else "")
            )
        if n_ops:
            detail_lines.append(
                f"• {n_ops} post-mapping operation(s) applied (dedupe / remove rows / remove blanks)"
            )
        if n_issues:
            detail_lines.append(f"• {n_issues} issue(s) recorded (see sheet ⚠ indicator)")

        msg = f"{_schema_label} applied successfully.\n\n" + "\n".join(detail_lines)

        # Show status panel
        self.refresh_smart_format_panel()

        messagebox.showinfo("Smart Format Complete", msg)

    def _ask_smart_format_schema(self):
        """
        Show a small dialog for the user to choose a Smart Format schema.

        Returns the selected template_id string, or None if cancelled.
        """
        result = [None]

        dlg = tk.Toplevel(self.root)
        dlg.title("Smart Format — Choose Configuration")
        dlg.geometry("400x190")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(
            dlg,
            text="Select a Smart Format configuration:",
            font=("Segoe UI", 10, "bold"),
        ).pack(padx=20, pady=(20, 10), anchor=tk.W)

        choice = tk.StringVar(value="MAIL_STANDARD_V1")
        ttk.Radiobutton(
            dlg,
            text="Mail File Standard  (24 columns)",
            variable=choice, value="MAIL_STANDARD_V1",
        ).pack(anchor=tk.W, padx=36, pady=2)
        ttk.Radiobutton(
            dlg,
            text="BCC Mail File Config  (21 columns)",
            variable=choice, value="BCC_MAIL_V1",
        ).pack(anchor=tk.W, padx=36, pady=2)

        def _confirm():
            result[0] = choice.get()
            dlg.destroy()

        def _cancel():
            dlg.destroy()

        btn_bar = tk.Frame(dlg)
        btn_bar.pack(pady=(14, 0), fill=tk.X, padx=20)
        ttk.Button(btn_bar, text="Cancel", command=_cancel).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_bar, text="Continue  ▶", command=_confirm).pack(side=tk.RIGHT, padx=4)

        dlg.bind("<Return>", lambda e: _confirm())
        dlg.bind("<Escape>", lambda e: _cancel())
        self.root.wait_window(dlg)
        return result[0]

    def _apply_smart_format_ops_plan(self, df_out, ops_plan):
        """
        Apply Operations Builder ops to the smart-format output df.

        Returns
        -------
        (df_final, ops_added, removed_rows)
            df_final   – DataFrame after all ops applied
            ops_added  – list of operation dicts added to queue
            removed_rows – DataFrame of removed rows (may be None)
        """
        import pandas as pd

        df_final = df_out
        ops_added = []
        all_removed = []

        if not ops_plan:
            return df_final, ops_added, None

        available_cols = set(df_out.columns.tolist())

        # ---- 1. Dedupe ----
        dedupe_cfg = ops_plan.get("dedupe", {})
        if dedupe_cfg.get("enabled"):
            keys = [k for k in dedupe_cfg.get("keys", []) if k in available_cols]
            if not keys:
                logging.warning("[SmartFormat] Dedupe skipped: no valid keys in output columns")
            else:
                op_dict = {
                    "operation_id": "data_remove_duplicates",
                    "name": "Remove Duplicate Rows",
                    "parameters": {
                        "columns": keys,
                        "keep": "first",
                        "smart_matching": False,
                        "multi_level_deduplication": False,
                    },
                    "enabled": True,
                }
                try:
                    result, removed = self.executor.execute_queue_with_tracking(
                        df_final, [op_dict]
                    )
                    df_final = result
                    if removed is not None and not removed.empty:
                        all_removed.append(removed)
                    ops_added.append(op_dict)
                except Exception as exc:
                    logging.warning("[SmartFormat] Dedupe failed: %s", exc)

        # ---- 2. Remove rows containing ----
        rrc = ops_plan.get("remove_rows_containing", {})
        if rrc.get("enabled"):
            cols = [c for c in rrc.get("columns", []) if c in available_cols]
            patterns = rrc.get("patterns", "").strip()
            if not cols:
                logging.warning("[SmartFormat] RemoveRowsContaining skipped: no valid columns")
            elif not patterns:
                logging.warning("[SmartFormat] RemoveRowsContaining skipped: no patterns given")
            else:
                match_type = rrc.get("match_type", "contains")
                op_dict = {
                    "operation_id": "remove_rows_containing",
                    "name": "Remove Rows Containing",
                    "parameters": {
                        "columns": cols,
                        "patterns": patterns,
                        "preset": "Custom (use patterns above)",
                        "case_sensitive": False,
                        "match_whole_cell": match_type == "equals",
                        "remove_blanks": False,
                    },
                    "enabled": True,
                }
                try:
                    result, removed = self.executor.execute_queue_with_tracking(
                        df_final, [op_dict]
                    )
                    df_final = result
                    if removed is not None and not removed.empty:
                        all_removed.append(removed)
                    ops_added.append(op_dict)
                except Exception as exc:
                    logging.warning("[SmartFormat] RemoveRowsContaining failed: %s", exc)

        # ---- 3. Remove blank rows ----
        rbr = ops_plan.get("remove_blank_rows", {})
        if rbr.get("enabled"):
            cols = [c for c in rbr.get("columns", []) if c in available_cols]
            if not cols:
                logging.warning("[SmartFormat] RemoveBlankRows skipped: no valid columns")
            else:
                op_dict = {
                    "operation_id": "remove_rows_containing",
                    "name": "Remove Blank Rows",
                    "parameters": {
                        "columns": cols,
                        "patterns": "",
                        "preset": "Custom (use patterns above)",
                        "case_sensitive": False,
                        "match_whole_cell": False,
                        "remove_blanks": True,
                    },
                    "enabled": True,
                }
                try:
                    result, removed = self.executor.execute_queue_with_tracking(
                        df_final, [op_dict]
                    )
                    df_final = result
                    if removed is not None and not removed.empty:
                        all_removed.append(removed)
                    ops_added.append(op_dict)
                except Exception as exc:
                    logging.warning("[SmartFormat] RemoveBlankRows failed: %s", exc)

        # Combine removed rows
        combined_removed = None
        if all_removed:
            import pandas as pd
            combined_removed = pd.concat(all_removed, ignore_index=True)

        return df_final, ops_added, combined_removed

    def _edit_smart_format(self):
        """Reopen the Smart Format wizard pre-populated with the current sheet's config."""
        if self.df is None:
            messagebox.showwarning("No Data", "Please load a file first.")
            return

        existing_config = None
        if self.workbook_session:
            active = self.workbook_session.get_active_sheet()
            if active:
                existing_config = getattr(active, 'smart_format', None)

        self.launch_smart_format(existing_config=existing_config)

    def _clear_smart_format(self):
        """Remove Smart Format config from the active sheet after user confirmation."""
        if not self.workbook_session:
            return
        active = self.workbook_session.get_active_sheet()
        if not active:
            return

        confirmed = messagebox.askyesno(
            "Clear Smart Format",
            "This will remove the Smart Format configuration for this sheet.\n\n"
            "The current data view will be preserved but the Smart Format indicator "
            "will be cleared.\n\nContinue?",
            icon="warning",
        )
        if not confirmed:
            return

        # Clear smart_format field
        active.smart_format = None
        # Clear legacy meta flag
        active.meta.pop("smart_format_mail_standard_applied", None)
        active.meta.pop("recommended_dedupe_keys", None)
        active.is_dirty = True

        # Hide the panel
        self.refresh_smart_format_panel()
        self.status_var.set("Smart Format configuration cleared for this sheet.")

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

            # Also check for extra sheets like EMAIL_VALIDATION from tool actions
            if not has_results and self.workbook_session.extra_sheets:
                has_results = any(
                    df is not None and not df.empty
                    for df in self.workbook_session.extra_sheets.values()
                )
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

            # Save last export path for session recovery
            self.last_export_path = filename
            self.logger.info(f"Saved export to: {filename}")

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

                    # Save session after preset application
                    self.logger.info("Saving session after preset application")
                    self.save_session_debounced()

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

    # ==================== EMAIL VALIDATION METHODS ====================

    def validate_emails_tool(self):
        """Launch email validation wizard and process validation."""
        # Check if workbook session exists and is Excel
        if not self.workbook_session:
            messagebox.showwarning(
                "No File Loaded",
                "Please load an Excel file before using email validation.",
                parent=self.root
            )
            return

        if not self.workbook_session.is_excel:
            messagebox.showinfo(
                "Excel Only",
                "Email validation is only available for Excel files with multiple sheets.",
                parent=self.root
            )
            return

        # Check for API key
        if not self.config_manager:
            messagebox.showerror(
                "Configuration Error",
                "Configuration manager not available.",
                parent=self.root
            )
            return

        api_key = self.config_manager.get_emailable_api_key()
        if not api_key:
            result = messagebox.askyesno(
                "API Key Required",
                "Emailable API key is not configured.\n\n"
                "Would you like to open Settings to configure it now?",
                parent=self.root
            )
            if result:
                self.open_settings()
            return

        # Launch wizard
        from ui.email_validation_wizard import EmailValidationWizard

        wizard = EmailValidationWizard(
            self.root,
            self.workbook_session,
            on_start_validation=self._start_email_validation
        )
        wizard.show()

    def _start_email_validation(self, config):
        """Start email validation with the given configuration."""
        from integrations.emailable_client import EmailableClient
        from integrations.email_validation_runner import EmailValidationRunner
        from ui.progress_dialog import ProgressDialog
        import queue

        # Create progress dialog
        progress_dialog = ProgressDialog(
            self.root,
            title="Email Validation",
            cancelable=True
        )

        # Create message queue for thread-safe UI updates
        progress_queue = queue.Queue()

        # Progress callback (called from worker thread)
        def progress_callback(message, current, total):
            progress_queue.put(('progress', message, current, total))

        # Completion callback (called from worker thread)
        def completion_callback(success, result_or_error):
            progress_queue.put(('complete', success, result_or_error))

        # Create Emailable client
        api_key = self.config_manager.get_emailable_api_key()
        client = EmailableClient(api_key)

        # Create and start runner
        runner = EmailValidationRunner(
            emailable_client=client,
            workbook_session=self.workbook_session,
            config=config,
            validation_cache=self.email_validation_cache,
            progress_callback=progress_callback,
            completion_callback=completion_callback
        )

        # Wire up cancel button
        progress_dialog.on_cancel = runner.cancel

        # Start validation
        runner.start()

        # Poll queue for updates
        def check_queue():
            try:
                while True:
                    msg_type, *args = progress_queue.get_nowait()

                    if msg_type == 'progress':
                        message, current, total = args
                        progress_dialog.update_progress(message, current, total)

                    elif msg_type == 'complete':
                        success, result_or_error = args
                        progress_dialog.close()

                        if success:
                            result = result_or_error
                            summary = result['summary']

                            # Show summary
                            summary_text = (
                                f"Email validation completed successfully!\n\n"
                                f"Total Occurrences: {summary['total_occurrences']}\n"
                                f"Unique Emails: {summary['unique_emails']}\n\n"
                                f"Deliverable: {summary['deliverable']}\n"
                                f"Risky: {summary['risky']}\n"
                                f"Undeliverable: {summary['undeliverable']}\n"
                                f"Unknown/Error: {summary['unknown']}\n\n"
                                f"Bad (Risky + Undeliverable): {summary['bad']}\n\n"
                                f"Results have been saved to the EMAIL_VALIDATION sheet.\n"
                                f"Use 'Save Results' to export the workbook with validation data."
                            )

                            messagebox.showinfo(
                                "Validation Complete",
                                summary_text,
                                parent=self.root
                            )

                            # Refresh UI if needed
                            try:
                                self.set_status("Email validation completed. Use 'Save Results' to export.")
                            except Exception as e:
                                print(f"[WARNING] Failed to update status: {e}")

                        else:
                            error = result_or_error
                            messagebox.showerror(
                                "Validation Failed",
                                f"Email validation failed:\n\n{error}",
                                parent=self.root
                            )

                        return  # Stop polling

            except queue.Empty:
                pass

            # Continue polling
            self.root.after(100, check_queue)

        # Start polling
        self.root.after(100, check_queue)

    def open_settings(self):
        """Open settings dialog."""
        from ui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.root, self.config_manager)
        result = dialog.show()

        if result:
            # Settings were saved, refresh API key if needed
            if self.config_manager:
                api_key = self.config_manager.get_api_key()
                if api_key:
                    self.api_key.set(api_key)

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

    # ==================== EXCEPTION HANDLING ====================

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Global exception handler for Tkinter callbacks
        Logs exceptions and shows user-friendly error dialog
        """
        # Format the exception
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Log the full traceback
        self.logger.error(f"Unhandled exception in UI callback:\n{error_msg}")

        # Show user-friendly dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Unexpected Error")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Icon and message
        header_frame = tk.Frame(dialog, bg='#F3F2F1', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="⚠️ Unexpected Error",
            font=('Segoe UI', 12, 'bold'),
            bg='#F3F2F1',
            fg='#D83B01'
        ).pack(pady=15)

        # Message
        msg_frame = tk.Frame(dialog, bg='white')
        msg_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(
            msg_frame,
            text=f"An unexpected error occurred:\n\n{exc_type.__name__}: {str(exc_value)}\n\n"
                 "The error has been logged. You can continue working, but some\n"
                 "functionality may not work correctly. Consider restarting the app.",
            font=('Segoe UI', 10),
            bg='white',
            justify='left',
            wraplength=450
        ).pack(pady=10)

        # Buttons
        button_frame = tk.Frame(dialog, bg='white')
        button_frame.pack(fill='x', padx=20, pady=(0, 20))

        def copy_details():
            """Copy error details to clipboard"""
            self.root.clipboard_clear()
            self.root.clipboard_append(error_msg)
            messagebox.showinfo("Copied", "Error details copied to clipboard", parent=dialog)

        tk.Button(
            button_frame,
            text="Copy Details",
            command=copy_details,
            font=('Segoe UI', 10),
            padx=15,
            pady=5
        ).pack(side='left', padx=(0, 10))

        tk.Button(
            button_frame,
            text="OK",
            command=dialog.destroy,
            font=('Segoe UI', 10, 'bold'),
            bg='#0078D4',
            fg='white',
            padx=20,
            pady=5
        ).pack(side='left')

    # ==================== SESSION RECOVERY ====================

    def check_session_recovery(self):
        """
        Check if there's a saved session and prompt user to restore it
        Called after UI initialization
        """
        session_data = self.session_recovery.load_session()

        if not session_data:
            return

        # Show restore prompt
        response = messagebox.askyesno(
            "Restore Previous Session?",
            f"A previous session was found:\n\n"
            f"File: {Path(session_data['file_path']).name}\n"
            f"Sheets: {len(session_data['sheet_names'])}\n"
            f"Last saved: {session_data.get('timestamp', 'Unknown')}\n\n"
            "Would you like to restore this session?",
            icon='question'
        )

        if response:
            # User chose to restore
            try:
                self._restore_session(session_data)
                self.logger.info("Session restored successfully")
                messagebox.showinfo(
                    "Session Restored",
                    "Your previous session has been restored.\n\n"
                    "Note: Data will be reloaded from the original file."
                )
            except Exception as e:
                self.logger.error(f"Failed to restore session: {e}", exc_info=True)
                messagebox.showerror(
                    "Restore Failed",
                    f"Failed to restore session:\n{str(e)}\n\n"
                    "The session has been discarded."
                )
                self.session_recovery.clear_session()
        else:
            # User chose to discard
            self.session_recovery.clear_session()
            self.logger.info("User discarded saved session")

    def _restore_session(self, session_data):
        """
        Restore session data into the app
        """
        file_path = session_data['file_path']
        is_excel = session_data['is_excel']

        if is_excel:
            # Restore Excel workbook session
            self.current_file = file_path

            # Create workbook session
            self.workbook_session = WorkbookSession(file_path, is_excel=True)

            # Restore session state
            self.session_recovery.restore_session_to_workbook(session_data, self.workbook_session)

            # Initialize sheet names (lazy load - don't load dataframes yet)
            sheet_names = session_data['sheet_names']
            self.available_sheets = sheet_names

            # Update UI - show sheet tabs
            if self.sheet_tab_bar:
                self.sheet_tab_bar.destroy()

            self.sheet_tab_bar = SheetTabBar(
                self.center_area,
                sheet_names=self.workbook_session.get_visible_sheets(),
                deleted_sheets=list(self.workbook_session.deleted_sheets),
                on_sheet_select=self.on_sheet_selected,
                on_sheet_rename=self.on_sheet_renamed,
                on_sheet_delete=self.on_sheet_deleted,
                on_sheet_restore=self.on_sheet_restored,
                workbook_session=self.workbook_session
            )
            self.sheet_tab_bar.pack(side='bottom', fill='x')

            # Set active sheet
            if self.workbook_session.active_sheet:
                self.on_sheet_selected(self.workbook_session.active_sheet)

            # Update status
            self.excel_status_bar.update_status(f"Session restored: {Path(file_path).name}")

        else:
            # CSV file - simpler restore
            self.current_file = file_path
            # Load the CSV
            self.df = pd.read_csv(file_path)

            # Create single-sheet workbook session
            self.workbook_session = WorkbookSession(file_path, is_excel=False)
            self.workbook_session.initialize_from_csv(self.df)

            # Restore operations
            self.session_recovery.restore_session_to_workbook(session_data, self.workbook_session)

            sheet_state = self.workbook_session.get_active_sheet()
            if sheet_state and sheet_state.operations:
                self.operation_queue = sheet_state.operations
                self.update_queue_display()

            # Update preview
            if hasattr(self, 'data_preview'):
                self.data_preview.update_data(self.df)

    def save_session_debounced(self):
        """
        Save current session with debouncing to avoid disk thrashing
        """
        if self.workbook_session is None:
            return

        # Cancel any pending save
        if hasattr(self, '_save_timer_id') and self._save_timer_id:
            self.root.after_cancel(self._save_timer_id)

        # Schedule new save after 500ms
        self._save_timer_id = self.root.after(
            500,
            lambda: self.session_recovery.save_session(
                self.workbook_session,
                self.last_export_path
            )
        )

    # ==================== END SESSION RECOVERY ====================

    # ==================== LOGGING UI METHODS ====================

    def open_logs_folder(self):
        """Open the logs folder in file explorer"""
        try:
            log_dir = get_log_directory()

            # Open folder based on platform
            import platform
            system = platform.system()

            if system == "Windows":
                os.startfile(str(log_dir))
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", str(log_dir)])
            else:  # Linux
                subprocess.Popen(["xdg-open", str(log_dir)])

            self.logger.info(f"Opened logs folder: {log_dir}")

        except Exception as e:
            self.logger.error(f"Failed to open logs folder: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to open logs folder:\n{str(e)}\n\n"
                f"Logs are located at:\n{get_log_directory()}"
            )

    def copy_debug_info(self):
        """Copy debug information to clipboard"""
        try:
            debug_info = get_debug_info(version=__version__)

            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(debug_info)

            messagebox.showinfo(
                "Debug Info Copied",
                "Debug information has been copied to clipboard.\n\n"
                "You can paste this into support emails or issue reports."
            )

            self.logger.info("Debug info copied to clipboard")

        except Exception as e:
            self.logger.error(f"Failed to copy debug info: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to copy debug info:\n{str(e)}"
            )

    # ==================== END LOGGING UI METHODS ====================

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

    # Setup centralized logging with rotation
    log_dir = setup_logging(app_name=__app_name__, version=__version__)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting {__app_name__} v{__version__}")

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
