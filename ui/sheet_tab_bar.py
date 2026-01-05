"""
Sheet Tab Bar - Excel-like horizontal tab bar for multi-sheet navigation

Displays all available sheets as clickable tabs with:
- Active sheet highlighted in Office 365 blue (#0078D4)
- Inactive sheets in light gray (#F3F2F1)
- Horizontal scrolling for many sheets
- Click to switch sheets instantly
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
import logging


class SheetTabBar(ttk.Frame):
    """Excel-like sheet tab bar for multi-sheet workbook navigation"""

    # Office 365 color scheme
    ACTIVE_BG = "#0078D4"      # Office 365 blue
    ACTIVE_FG = "#FFFFFF"      # White text
    INACTIVE_BG = "#F3F2F1"    # Light gray
    INACTIVE_FG = "#323130"    # Dark gray text
    HOVER_BG = "#E1DFDD"       # Slightly darker gray on hover
    BORDER_COLOR = "#EDEBE9"   # Border between tabs

    def __init__(self, parent, on_sheet_change: Callable[[str], None], **kwargs):
        """
        Initialize sheet tab bar

        Args:
            parent: Parent widget
            on_sheet_change: Callback function(sheet_name: str) called when sheet is clicked
            **kwargs: Additional ttk.Frame options
        """
        super().__init__(parent, **kwargs)

        self.on_sheet_change = on_sheet_change
        self.sheet_names: List[str] = []
        self.active_sheet: Optional[str] = None
        self.tab_buttons: dict[str, tk.Label] = {}
        self.sheets_with_issues: set = set()  # Track which sheets have validation issues

        # Configure the frame
        self.configure(style='SheetTabBar.TFrame')

        # Create scrollable canvas for tabs
        self._create_widgets()

        logging.info("[SHEET TAB BAR] Initialized")

    def _create_widgets(self):
        """Create the scrollable tab container"""
        # Create canvas with horizontal scrollbar
        self.canvas = tk.Canvas(
            self,
            height=35,
            bg=self.INACTIVE_BG,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(side='left', fill='both', expand=True)

        # Horizontal scrollbar
        self.scrollbar = ttk.Scrollbar(
            self,
            orient='horizontal',
            command=self.canvas.xview
        )
        self.scrollbar.pack(side='bottom', fill='x')

        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        # Frame inside canvas to hold tabs
        self.tabs_frame = tk.Frame(
            self.canvas,
            bg=self.INACTIVE_BG
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.tabs_frame,
            anchor='nw'
        )

        # Bind canvas resize to update scroll region
        self.tabs_frame.bind('<Configure>', self._on_frame_configure)

    def _on_frame_configure(self, event=None):
        """Update canvas scroll region when tabs frame size changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def set_sheets(self, sheet_names: List[str], active_sheet: Optional[str] = None):
        """
        Set the list of sheet names to display

        Args:
            sheet_names: List of sheet names
            active_sheet: Name of the currently active sheet (optional)
        """
        self.sheet_names = sheet_names
        self.active_sheet = active_sheet

        # Clear existing tabs
        for widget in self.tabs_frame.winfo_children():
            widget.destroy()
        self.tab_buttons.clear()

        # Create tab for each sheet
        for i, sheet_name in enumerate(sheet_names):
            self._create_tab(sheet_name, i)

        # Update scroll region
        self.tabs_frame.update_idletasks()
        self._on_frame_configure()

        logging.info(f"[SHEET TAB BAR] Displaying {len(sheet_names)} sheets")

    def _create_tab(self, sheet_name: str, index: int):
        """
        Create a single tab button

        Args:
            sheet_name: Name of the sheet
            index: Index position of the tab
        """
        is_active = (sheet_name == self.active_sheet)
        has_issues = (sheet_name in self.sheets_with_issues)

        # Add warning icon if sheet has issues
        display_text = f"{sheet_name} ⚠" if has_issues else sheet_name

        # Create tab as a Label (acts like a button)
        tab = tk.Label(
            self.tabs_frame,
            text=display_text,
            bg=self.ACTIVE_BG if is_active else self.INACTIVE_BG,
            fg=self.ACTIVE_FG if is_active else self.INACTIVE_FG,
            font=('Segoe UI', 10, 'bold' if is_active else 'normal'),
            padx=15,
            pady=8,
            cursor='hand2',
            relief='flat',
            borderwidth=1,
            highlightthickness=0
        )

        # Position tab
        tab.grid(row=0, column=index, padx=1, pady=2, sticky='nsew')

        # Store reference
        self.tab_buttons[sheet_name] = tab

        # Bind click event
        tab.bind('<Button-1>', lambda e, name=sheet_name: self._on_tab_click(name))

        # Bind hover events for inactive tabs
        if not is_active:
            tab.bind('<Enter>', lambda e, t=tab: t.configure(bg=self.HOVER_BG))
            tab.bind('<Leave>', lambda e, t=tab: t.configure(bg=self.INACTIVE_BG))

    def _on_tab_click(self, sheet_name: str):
        """
        Handle tab click event

        Args:
            sheet_name: Name of the clicked sheet
        """
        if sheet_name != self.active_sheet:
            logging.info(f"[SHEET TAB BAR] Tab clicked: {sheet_name}")
            self.set_active_sheet(sheet_name)

            # Call the callback to switch sheets
            if self.on_sheet_change:
                self.on_sheet_change(sheet_name)

    def set_active_sheet(self, sheet_name: str):
        """
        Update the active sheet highlighting

        Args:
            sheet_name: Name of the sheet to mark as active
        """
        if sheet_name not in self.sheet_names:
            logging.warning(f"[SHEET TAB BAR] Sheet '{sheet_name}' not found in tab bar")
            return

        old_active = self.active_sheet
        self.active_sheet = sheet_name

        # Update old active tab to inactive
        if old_active and old_active in self.tab_buttons:
            old_tab = self.tab_buttons[old_active]
            old_tab.configure(
                bg=self.INACTIVE_BG,
                fg=self.INACTIVE_FG,
                font=('Segoe UI', 10, 'normal')
            )
            # Re-bind hover events
            old_tab.bind('<Enter>', lambda e, t=old_tab: t.configure(bg=self.HOVER_BG))
            old_tab.bind('<Leave>', lambda e, t=old_tab: t.configure(bg=self.INACTIVE_BG))

        # Update new active tab
        if sheet_name in self.tab_buttons:
            new_tab = self.tab_buttons[sheet_name]
            new_tab.configure(
                bg=self.ACTIVE_BG,
                fg=self.ACTIVE_FG,
                font=('Segoe UI', 10, 'bold')
            )
            # Remove hover events from active tab
            new_tab.unbind('<Enter>')
            new_tab.unbind('<Leave>')

        logging.info(f"[SHEET TAB BAR] Active sheet: {sheet_name}")

    def get_active_sheet(self) -> Optional[str]:
        """Get the currently active sheet name"""
        return self.active_sheet

    def show(self):
        """Show the tab bar"""
        self.pack(side='bottom', fill='x', pady=(0, 0))
        logging.info("[SHEET TAB BAR] Visible")

    def hide(self):
        """Hide the tab bar"""
        self.pack_forget()
        logging.info("[SHEET TAB BAR] Hidden")

    def clear(self):
        """Clear all tabs"""
        for widget in self.tabs_frame.winfo_children():
            widget.destroy()
        self.tab_buttons.clear()
        self.sheet_names = []
        self.active_sheet = None
        self.sheets_with_issues.clear()
        logging.info("[SHEET TAB BAR] Cleared")

    def mark_sheet_issues(self, sheet_name: str, has_issues: bool = True):
        """
        Mark or unmark a sheet as having validation issues

        Args:
            sheet_name: Name of the sheet
            has_issues: True to mark with warning icon, False to remove
        """
        if has_issues:
            self.sheets_with_issues.add(sheet_name)
        else:
            self.sheets_with_issues.discard(sheet_name)

        # Update tab display if it exists
        if sheet_name in self.tab_buttons:
            tab = self.tab_buttons[sheet_name]
            is_active = (sheet_name == self.active_sheet)
            display_text = f"{sheet_name} ⚠" if has_issues else sheet_name
            tab.configure(text=display_text)
            logging.info(f"[SHEET TAB BAR] Sheet '{sheet_name}' {'marked' if has_issues else 'unmarked'} with issues")

    def update_all_issue_indicators(self, sheets_with_issues: set):
        """
        Update issue indicators for all sheets at once

        Args:
            sheets_with_issues: Set of sheet names that have issues
        """
        self.sheets_with_issues = sheets_with_issues.copy()

        # Update all tabs
        for sheet_name in self.sheet_names:
            if sheet_name in self.tab_buttons:
                tab = self.tab_buttons[sheet_name]
                has_issues = (sheet_name in self.sheets_with_issues)
                display_text = f"{sheet_name} ⚠" if has_issues else sheet_name
                tab.configure(text=display_text)

        if sheets_with_issues:
            logging.info(f"[SHEET TAB BAR] Updated issue indicators for {len(sheets_with_issues)} sheets")


# Example usage and testing
if __name__ == "__main__":
    def on_sheet_change(sheet_name: str):
        print(f"Sheet changed to: {sheet_name}")
        # Update active sheet in the tab bar
        tab_bar.set_active_sheet(sheet_name)

    # Create test window
    root = tk.Tk()
    root.title("SheetTabBar Test")
    root.geometry("800x100")

    # Create tab bar
    tab_bar = SheetTabBar(root, on_sheet_change=on_sheet_change)
    tab_bar.pack(side='bottom', fill='x')

    # Test with multiple sheets
    test_sheets = ['Products', 'Orders', 'Employees', 'Customers', 'Inventory',
                   'Sales', 'Reports', 'Analytics', 'Dashboard']
    tab_bar.set_sheets(test_sheets, active_sheet='Products')

    # Add buttons to test functionality
    control_frame = tk.Frame(root)
    control_frame.pack(side='top', pady=10)

    tk.Button(
        control_frame,
        text="Show Tab Bar",
        command=tab_bar.show
    ).pack(side='left', padx=5)

    tk.Button(
        control_frame,
        text="Hide Tab Bar",
        command=tab_bar.hide
    ).pack(side='left', padx=5)

    tk.Button(
        control_frame,
        text="Clear Tabs",
        command=tab_bar.clear
    ).pack(side='left', padx=5)

    root.mainloop()
