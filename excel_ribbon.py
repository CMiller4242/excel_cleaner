"""
Excel 365-Style Ribbon Component
Implements proper ribbon interface with tabs and grouped sections
"""

import tkinter as tk
from tkinter import ttk


class RibbonGroup(ttk.Frame):
    """A group of buttons in the ribbon (e.g., 'Clipboard', 'File')"""

    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.configure(style='RibbonGroup.TFrame')

        # Group content frame
        self.content_frame = ttk.Frame(self, style='RibbonGroup.TFrame')
        self.content_frame.pack(fill='both', expand=True, padx=4, pady=2)

        # Group label at bottom
        label = ttk.Label(
            self,
            text=title,
            font=('Segoe UI', 9),
            foreground='#666666',
            background='#F3F2F1',
            anchor='center'
        )
        label.pack(side='bottom', fill='x')

        # Separator line on right
        separator = ttk.Frame(self, style='RibbonSeparator.TFrame', width=1)
        separator.pack(side='right', fill='y', padx=(4, 0))

    def add_button(self, text, command, icon="", style='RibbonButton.TButton', row=0, column=0):
        """Add a button to this group"""
        btn_frame = ttk.Frame(self.content_frame, style='RibbonGroup.TFrame')
        btn_frame.grid(row=row, column=column, padx=2, pady=2, sticky='nsew')

        if icon:
            full_text = f"{icon}\n{text}"
        else:
            full_text = text

        btn = ttk.Button(
            btn_frame,
            text=full_text,
            command=command,
            style=style,
            width=10
        )
        btn.pack(fill='both', expand=True)
        return btn


class ExcelRibbon(ttk.Frame):
    """
    Excel 365-style Ribbon with tabs and grouped sections
    Matches the compact, professional look of modern Excel
    """

    def __init__(self, parent, app_ref, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_ref  # Reference to main app for callbacks
        self.configure(style='Ribbon.TFrame')

        # Current active tab
        self.active_tab = tk.StringVar(value='home')

        # Create ribbon structure
        self._setup_ribbon()

    def _setup_ribbon(self):
        """Setup ribbon tabs and content area"""
        # Tab bar (top row)
        tab_bar = ttk.Frame(self, style='RibbonTabBar.TFrame', height=30)
        tab_bar.pack(fill='x', side='top')
        tab_bar.pack_propagate(False)

        # Tab buttons
        self.tab_buttons = {}
        tabs = [
            ('home', 'Home'),
            ('data', 'Data'),
            ('transform', 'Transform'),
            ('review', 'Review'),
            ('help', 'Help')
        ]

        for tab_id, label in tabs:
            btn = tk.Button(
                tab_bar,
                text=label,
                command=lambda t=tab_id: self.switch_tab(t),
                relief='flat',
                font=('Segoe UI', 11),
                bg='#F3F2F1',
                fg='#323130',
                activebackground='#FFFFFF',
                activeforeground='#0078D4',
                padx=15,
                pady=5,
                borderwidth=0,
                cursor='hand2'
            )
            btn.pack(side='left')
            self.tab_buttons[tab_id] = btn

        # Content area (ribbon groups)
        self.content_area = ttk.Frame(self, style='Ribbon.TFrame', height=90)
        self.content_area.pack(fill='both', expand=True, side='top')
        self.content_area.pack_propagate(False)

        # Initialize with Home tab
        self.switch_tab('home')

    def switch_tab(self, tab_id):
        """Switch to a different ribbon tab"""
        self.active_tab.set(tab_id)

        # Update tab button styles
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(bg='#FFFFFF', fg='#0078D4', relief='raised')
            else:
                btn.configure(bg='#F3F2F1', fg='#323130', relief='flat')

        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()

        # Load appropriate tab content
        if tab_id == 'home':
            self._create_home_tab()
        elif tab_id == 'data':
            self._create_data_tab()
        elif tab_id == 'transform':
            self._create_transform_tab()
        elif tab_id == 'review':
            self._create_review_tab()
        elif tab_id == 'help':
            self._create_help_tab()

    def _create_home_tab(self):
        """Create Home tab with File, Operations, and Run groups"""
        # Clipboard group
        clipboard_group = RibbonGroup(self.content_area, "Clipboard")
        clipboard_group.pack(side='left', fill='y', padx=2)

        # File group
        file_group = RibbonGroup(self.content_area, "File")
        file_group.pack(side='left', fill='y', padx=2)

        file_group.add_button("Open", self.app.load_file, "📁", row=0, column=0)
        file_group.add_button("Save", self.app.save_results, "💾", row=0, column=1)

        # Presets group
        presets_group = RibbonGroup(self.content_area, "Presets")
        presets_group.pack(side='left', fill='y', padx=2)

        presets_group.add_button("Load\nPreset", self.app.load_preset, "📋", row=0, column=0)
        presets_group.add_button("Save\nPreset", self.app.save_preset, "💾", row=0, column=1)

        # Operations group
        ops_group = RibbonGroup(self.content_area, "Operations")
        ops_group.pack(side='left', fill='y', padx=2)

        ops_group.add_button("Add Op", self.app.toggle_operations_sidebar, "➕", row=0, column=0)
        ops_group.add_button("Edit", lambda: None, "✏️", row=0, column=1)

        # Run group
        run_group = RibbonGroup(self.content_area, "Run")
        run_group.pack(side='left', fill='y', padx=2)

        run_group.add_button("Execute", self.app.run_operations, "▶️",
                           style='RibbonButtonSuccess.TButton', row=0, column=0)
        run_group.add_button("Preview", lambda: None, "🔍", row=0, column=1)

    def _create_data_tab(self):
        """Create Data tab"""
        import_group = RibbonGroup(self.content_area, "Import")
        import_group.pack(side='left', fill='y', padx=2)
        import_group.add_button("Open", self.app.load_file, "📁", row=0, column=0)

        export_group = RibbonGroup(self.content_area, "Export")
        export_group.pack(side='left', fill='y', padx=2)
        export_group.add_button("Save", self.app.save_results, "💾", row=0, column=0)

        clean_group = RibbonGroup(self.content_area, "Clean")
        clean_group.pack(side='left', fill='y', padx=2)
        clean_group.add_button("Remove\nBlanks", lambda: None, "🧹", row=0, column=0)
        clean_group.add_button("Trim", lambda: None, "✂️", row=0, column=1)

    def _create_transform_tab(self):
        """Create Transform tab"""
        text_group = RibbonGroup(self.content_area, "Text")
        text_group.pack(side='left', fill='y', padx=2)
        text_group.add_button("Upper", lambda: None, "ABC", row=0, column=0)
        text_group.add_button("Lower", lambda: None, "abc", row=0, column=1)

        columns_group = RibbonGroup(self.content_area, "Columns")
        columns_group.pack(side='left', fill='y', padx=2)
        columns_group.add_button("Reorder", lambda: None, "⇅", row=0, column=0)
        columns_group.add_button("Split", lambda: None, "⚡", row=0, column=1)

    def _create_review_tab(self):
        """Create Review tab"""
        quality_group = RibbonGroup(self.content_area, "Quality")
        quality_group.pack(side='left', fill='y', padx=2)
        quality_group.add_button("Analyze", self.app.analyze_data_quality, "📊",
                               style='RibbonButtonAccent.TButton', row=0, column=0)

        duplicates_group = RibbonGroup(self.content_area, "Duplicates")
        duplicates_group.pack(side='left', fill='y', padx=2)
        duplicates_group.add_button("Find", lambda: None, "🔍", row=0, column=0)
        duplicates_group.add_button("Remove", lambda: None, "🗑", row=0, column=1)

    def _create_help_tab(self):
        """Create Help tab"""
        assist_group = RibbonGroup(self.content_area, "Assistant")
        assist_group.pack(side='left', fill='y', padx=2)
        assist_group.add_button("AI Help", lambda: None, "🤖", row=0, column=0)

        docs_group = RibbonGroup(self.content_area, "Documentation")
        docs_group.pack(side='left', fill='y', padx=2)
        docs_group.add_button("Guide", lambda: None, "📖", row=0, column=0)
        docs_group.add_button("About", lambda: None, "ℹ️", row=0, column=1)


class FormulaBar(ttk.Frame):
    """Excel-style formula/filter bar above the data grid"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style='FormulaBar.TFrame', height=30)
        self.pack_propagate(False)

        # Name Box (shows current selection)
        name_label = ttk.Label(
            self,
            text="Name Box:",
            font=('Segoe UI', 10),
            background='#FAFAFA'
        )
        name_label.pack(side='left', padx=(10, 5))

        self.name_box = ttk.Combobox(
            self,
            width=15,
            font=('Segoe UI', 10),
            state='readonly'
        )
        self.name_box.pack(side='left', padx=5)
        self.name_box.set('A1')

        # fx label
        fx_label = ttk.Label(
            self,
            text="fx",
            font=('Segoe UI', 10, 'bold'),
            background='#FAFAFA',
            foreground='#0078D4'
        )
        fx_label.pack(side='left', padx=(10, 5))

        # Formula/filter display
        self.formula_var = tk.StringVar(value="No active filter")
        formula_entry = ttk.Entry(
            self,
            textvariable=self.formula_var,
            font=('Segoe UI', 10),
            state='readonly'
        )
        formula_entry.pack(side='left', fill='x', expand=True, padx=5)

    def update_current_filter(self, filter_text):
        """Update the current filter display"""
        if filter_text:
            self.formula_var.set(f"Current Filter: {filter_text}")
        else:
            self.formula_var.set("No active filter")


class ExcelStatusBar(ttk.Frame):
    """Excel-style status bar with detailed information"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style='StatusBar.TFrame', height=25)
        self.pack_propagate(False)

        # Status message (left)
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            font=('Segoe UI', 10),
            background='#F3F2F1',
            foreground='#323130'
        )
        status_label.pack(side='left', padx=10)

        # Separator
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=5)

        # Mode indicator
        self.mode_var = tk.StringVar(value="Mode: Simple")
        mode_label = ttk.Label(
            self,
            textvariable=self.mode_var,
            font=('Segoe UI', 10),
            background='#F3F2F1',
            foreground='#666666'
        )
        mode_label.pack(side='left', padx=10)

        # Separator
        ttk.Separator(self, orient='vertical').pack(side='left', fill='y', padx=5)

        # Row count (right side)
        self.row_count_var = tk.StringVar(value="No data")
        row_label = ttk.Label(
            self,
            textvariable=self.row_count_var,
            font=('Segoe UI', 10),
            background='#F3F2F1',
            foreground='#323130'
        )
        row_label.pack(side='right', padx=10)

    def update_status(self, message):
        """Update status message"""
        self.status_var.set(message)

    def update_mode(self, mode):
        """Update mode display"""
        self.mode_var.set(f"Mode: {mode.title()}")

    def update_row_count(self, count):
        """Update row count display"""
        if count == 0:
            self.row_count_var.set("No data")
        else:
            self.row_count_var.set(f"{count:,} rows")
