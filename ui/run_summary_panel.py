"""
Run Summary Panel for CleanSheet
Shows per-sheet execution status, metrics, and issues
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from workbook_session import WorkbookSession, SheetState


class RunSummaryPanel(ttk.Frame):
    """
    Non-modal, persistent panel showing run/validation results for all sheets

    Features:
    - Per-sheet status icons (✓ Clean, ⚠ Needs Attention, ○ Not run yet)
    - Row counts (before → after)
    - Operation counts (total / skipped)
    - Removed rows count
    - Issues count
    - Interactive: click sheet to switch, click issue to jump to operation
    """

    def __init__(self, parent, workbook_session: Optional[WorkbookSession] = None,
                 on_sheet_click: Optional[Callable[[str], None]] = None,
                 on_issue_click: Optional[Callable[[str, int], None]] = None,
                 **kwargs):
        super().__init__(parent, **kwargs)

        self.workbook_session = workbook_session
        self.on_sheet_click = on_sheet_click  # Callback: on_sheet_click(sheet_name)
        self.on_issue_click = on_issue_click  # Callback: on_issue_click(sheet_name, op_index)

        self._create_widgets()

    def _create_widgets(self):
        """Create the summary panel UI"""
        # Header
        header_frame = ttk.Frame(self, style='Header.TFrame')
        header_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(
            header_frame,
            text="Run Summary",
            font=('Segoe UI', 10, 'bold')
        ).pack(side='left')

        # Collapse/expand button (optional future enhancement)
        # For now, keep it simple

        # Main content area with scrollbar
        content_frame = ttk.Frame(self)
        content_frame.pack(fill='both', expand=True, padx=5, pady=(0, 5))

        # Create treeview for sheet summary
        columns = ('status', 'sheet', 'ops', 'rows', 'removed', 'issues')
        self.tree = ttk.Treeview(
            content_frame,
            columns=columns,
            show='tree headings',
            height=8,
            selectmode='browse'
        )

        # Configure columns
        self.tree.heading('#0', text='')
        self.tree.column('#0', width=0, stretch=False)  # Hide tree column

        self.tree.heading('status', text='')
        self.tree.column('status', width=30, anchor='center', stretch=False)

        self.tree.heading('sheet', text='Sheet')
        self.tree.column('sheet', width=120, anchor='w')

        self.tree.heading('ops', text='Ops')
        self.tree.column('ops', width=60, anchor='center')

        self.tree.heading('rows', text='Rows')
        self.tree.column('rows', width=100, anchor='center')

        self.tree.heading('removed', text='Removed')
        self.tree.column('removed', width=70, anchor='center')

        self.tree.heading('issues', text='Issues')
        self.tree.column('issues', width=60, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(content_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind click event
        self.tree.bind('<ButtonRelease-1>', self._on_tree_click)
        self.tree.bind('<Double-Button-1>', self._on_tree_double_click)

        # Issue details pane (shown when sheet selected)
        self.details_frame = ttk.Frame(self)
        self.details_frame.pack(fill='both', expand=False, padx=5, pady=(0, 5))

        # Initially hidden
        self.details_frame.pack_forget()

        # Details label
        self.details_label = ttk.Label(
            self.details_frame,
            text="",
            font=('Segoe UI', 9),
            foreground='#666666'
        )
        self.details_label.pack(anchor='w', pady=2)

        # Issues listbox
        self.issues_listbox = tk.Listbox(
            self.details_frame,
            height=4,
            font=('Consolas', 9),
            borderwidth=1,
            relief='solid'
        )
        self.issues_listbox.pack(fill='both', expand=True)
        self.issues_listbox.bind('<Double-Button-1>', self._on_issue_double_click)

    def set_workbook_session(self, workbook_session: WorkbookSession):
        """Update the workbook session reference"""
        self.workbook_session = workbook_session
        self.refresh()

    def refresh(self):
        """Refresh the summary display from workbook session"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.workbook_session:
            return

        # Populate tree with sheet data
        for sheet_name in self.workbook_session.get_visible_sheets():
            sheet_state = self.workbook_session.get_sheet(sheet_name)
            if not sheet_state:
                continue

            # Build row data
            status_icon = sheet_state.get_status_icon()
            display_name = sheet_state.sheet_name_display

            # Ops column
            ops_total = sheet_state.last_run_ops_total or len(sheet_state.operations)
            ops_skipped = sheet_state.last_run_ops_skipped or 0
            if ops_skipped > 0:
                ops_text = f"{ops_total} ({ops_skipped} skip)"
            else:
                ops_text = str(ops_total) if ops_total else "-"

            # Rows column
            if sheet_state.last_run_before_rows is not None and sheet_state.last_run_after_rows is not None:
                rows_text = f"{sheet_state.last_run_before_rows:,} → {sheet_state.last_run_after_rows:,}"
            else:
                rows_text = "-"

            # Removed column
            removed_text = str(sheet_state.last_removed_count) if sheet_state.last_removed_count else "-"

            # Issues column
            issue_count = len(sheet_state.issues)
            issues_text = str(issue_count) if issue_count > 0 else "-"

            # Insert row
            self.tree.insert(
                '',
                'end',
                iid=sheet_name,  # Use sheet_name as item ID
                values=(status_icon, display_name, ops_text, rows_text, removed_text, issues_text),
                tags=(status_icon,)
            )

        # Configure row colors based on status
        self.tree.tag_configure('✓', foreground='#107C10')  # Green
        self.tree.tag_configure('⚠', foreground='#D83B01')  # Red/Orange
        self.tree.tag_configure('○', foreground='#666666')  # Gray

    def _on_tree_click(self, event):
        """Handle tree item selection"""
        selection = self.tree.selection()
        if not selection:
            self.details_frame.pack_forget()
            return

        sheet_name = selection[0]  # Item ID is sheet_name
        sheet_state = self.workbook_session.get_sheet(sheet_name) if self.workbook_session else None

        if not sheet_state:
            self.details_frame.pack_forget()
            return

        # Show issue details if issues exist
        if sheet_state.has_issues():
            self.details_label.config(
                text=f"Issues in {sheet_state.sheet_name_display} ({len(sheet_state.issues)})"
            )

            # Populate issues list
            self.issues_listbox.delete(0, tk.END)
            for issue in sheet_state.issues:
                issue_text = f"Op {issue.op_index + 1}: [{issue.code}] {issue.message}"
                self.issues_listbox.insert(tk.END, issue_text)
                # Store issue data as a tag
                self.issues_listbox.itemconfig(tk.END, {'tags': (sheet_name, issue.op_index)})

            self.details_frame.pack(fill='both', expand=False, padx=5, pady=(0, 5))
        else:
            self.details_frame.pack_forget()

    def _on_tree_double_click(self, event):
        """Handle double-click on sheet row - switch to that sheet"""
        selection = self.tree.selection()
        if not selection:
            return

        sheet_name = selection[0]
        if self.on_sheet_click:
            self.on_sheet_click(sheet_name)

    def _on_issue_double_click(self, event):
        """Handle double-click on issue - jump to operation"""
        selection = self.issues_listbox.curselection()
        if not selection:
            return

        idx = selection[0]

        # Get sheet and op_index from the currently selected tree item
        tree_selection = self.tree.selection()
        if not tree_selection:
            return

        sheet_name = tree_selection[0]
        sheet_state = self.workbook_session.get_sheet(sheet_name) if self.workbook_session else None

        if not sheet_state or idx >= len(sheet_state.issues):
            return

        issue = sheet_state.issues[idx]

        if self.on_issue_click:
            self.on_issue_click(sheet_name, issue.op_index)

    def show(self):
        """Show the panel"""
        self.pack(fill='both', expand=True)

    def hide(self):
        """Hide the panel"""
        self.pack_forget()
