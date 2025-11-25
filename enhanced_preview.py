"""
Enhanced Data Preview Component for Universal Excel Tool V2.1+
Now using tksheet for true Excel-like appearance and functionality
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Optional
from tksheet import Sheet


class EnhancedDataPreview(ttk.Frame):
    """
    Enhanced data preview with tksheet for Excel-like appearance
    Maintains all existing functionality while improving visual fidelity
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.df: Optional[pd.DataFrame] = None
        self.max_embedded_rows = 1000  # Increased - tksheet handles more rows efficiently

        self._setup_ui()

    def _setup_ui(self):
        """Setup the preview interface"""
        # Header with expand button
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(
            header_frame,
            text="📊 Data Preview",
            font=('Segoe UI', 12, 'bold')
        ).pack(side='left')

        # Expand button
        self.expand_btn = ttk.Button(
            header_frame,
            text="⛶ Expand Preview",
            command=self._open_expanded_view,
            style='Primary.TButton'
        )
        self.expand_btn.pack(side='right', padx=5)

        # Tab control for Original/Results
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Original data tab
        self.original_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.original_frame, text="📄 Original")

        # Results data tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="✅ Results")

        # Create tksheet widgets for both tabs
        self.original_sheet = self._create_sheet(self.original_frame)
        self.results_sheet = self._create_sheet(self.results_frame)

        # Info label
        self.info_label = ttk.Label(
            self,
            text="No data loaded",
            font=('Segoe UI', 10),
            foreground='gray'
        )
        self.info_label.pack(pady=5)

    def _create_sheet(self, parent) -> Sheet:
        """Create a tksheet widget with Excel-style configuration"""
        # Create sheet
        sheet = Sheet(
            parent,
            theme="light blue",
            show_row_index=True,  # Excel-like row numbers
            show_top_left=True,   # Corner cell
            show_header=True,     # CRITICAL: Show column headers
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            empty_horizontal=0,
            empty_vertical=0,
            height=600,
            width=1200
        )

        # Enable Excel-like interactions
        sheet.enable_bindings(
            "single_select",              # Click to select cell
            "row_select",                 # Click row number
            "column_select",              # Click column header
            "column_width_resize",        # Drag column border
            "double_click_column_resize", # Double-click to auto-fit
            "row_height_resize",          # Drag row border
            "arrowkeys",                  # Navigate with arrows
            "right_click_popup_menu",     # Context menu
            "rc_select",                  # Right-click select
            "copy",                       # Ctrl+C
            "cut",                        # Ctrl+X
            "paste",                      # Ctrl+V
            "delete",                     # Delete key
            "undo"                        # Ctrl+Z
        )

        # Configure Excel 365-style appearance
        sheet.set_options(
            font=("Segoe UI", 10, "normal"),
            header_font=("Segoe UI", 10, "bold"),
            index_font=("Segoe UI", 10, "normal"),
            header_bg="#F3F2F1",
            header_fg="#323130",
            index_bg="#F3F2F1",
            index_fg="#323130",
            top_left_bg="#F3F2F1",
            top_left_fg="#323130",
            frame_bg="#FFFFFF",
            table_bg="#FFFFFF",
            table_grid_fg="#E0E0E0",
            table_selected_cells_border_fg="#0078D4",
            table_selected_cells_bg="#CCE4F7",
            table_selected_rows_border_fg="#0078D4",
            table_selected_rows_bg="#CCE4F7",
            table_selected_columns_bg="#CCE4F7",
            header_selected_cells_bg="#DEEBF7",
            header_selected_cells_fg="#323130",
            row_index=1,  # Start row numbers at 1 (Excel-style)
            header_height=30  # Header height for single-line display
        )

        # Alternating row colors (Excel-style)
        sheet.set_options(table_bg="#FFFFFF")

        # Pack the sheet
        sheet.pack(fill="both", expand=True, padx=0, pady=0)

        return sheet

    def load_dataframe(self, df: pd.DataFrame, is_result: bool = False):
        """
        Load dataframe into preview with auto-fit columns

        Args:
            df: DataFrame to display
            is_result: If True, load into Results tab; otherwise Original tab
        """
        if df is None or df.empty:
            return

        self.df = df

        # Select which sheet to populate
        sheet = self.results_sheet if is_result else self.original_sheet

        # Prepare headers with Excel-style column letters
        # Use single line with letter and name together for compatibility
        headers = []
        for idx, col_name in enumerate(df.columns):
            col_letter = self._get_column_letter(idx)
            # Single-line header: Letter - Name
            header_text = f"{col_letter} - {col_name}"
            headers.append(header_text)

        # Limit rows for performance (can be adjusted)
        display_rows = min(len(df), self.max_embedded_rows)

        # Prepare data
        data = []
        for idx in range(display_rows):
            row_values = df.iloc[idx].tolist()
            formatted_row = []

            for val in row_values:
                # Handle different data types
                if pd.isna(val):
                    formatted_row.append('')
                elif isinstance(val, float):
                    formatted_row.append(f"{val:.2f}" if val != int(val) else str(int(val)))
                else:
                    formatted_row.append(str(val))

            data.append(formatted_row)

        # Set data first
        sheet.set_sheet_data(data)

        # Then set headers (must be done after data for proper column count)
        sheet.headers(headers)

        # Auto-fit columns for readability
        sheet.set_all_cell_sizes_to_text()

        # Refresh the display to ensure headers are visible
        sheet.refresh()

        # Alternating row colors
        for row_idx in range(display_rows):
            if row_idx % 2 == 1:  # Odd rows (0-indexed)
                sheet.highlight_rows(
                    row_idx,
                    bg="#F9F9F9",
                    fg="#000000",
                    highlight_index=False
                )

        # Update info label
        total_rows = len(df)
        total_cols = len(df.columns)

        if total_rows > self.max_embedded_rows:
            info_text = f"📊 Showing {display_rows:,} of {total_rows:,} rows • {total_cols} columns (Click 'Expand Preview' to see all rows)"
        else:
            info_text = f"📊 {total_rows:,} rows • {total_cols} columns"

        self.info_label.config(text=info_text)

        # Switch to appropriate tab
        if is_result:
            self.notebook.select(self.results_frame)
        else:
            self.notebook.select(self.original_frame)

    def _get_column_letter(self, idx: int) -> str:
        """Convert column index to Excel-style letter (A, B, ... Z, AA, AB, ...)"""
        result = ""
        while idx >= 0:
            result = chr(65 + (idx % 26)) + result
            idx = idx // 26 - 1
        return result

    def _open_expanded_view(self):
        """Open full-screen expanded preview window with tksheet"""
        if self.df is None or self.df.empty:
            return

        # Create expanded window
        expanded_window = tk.Toplevel(self)
        expanded_window.title("📊 Data Preview - Full Screen")
        expanded_window.geometry("1400x900")

        # Make it maximizable
        try:
            expanded_window.state('zoomed')  # Start maximized on Windows
        except:
            pass  # Not all platforms support this

        # Header
        header = ttk.Frame(expanded_window)
        header.pack(fill='x', padx=10, pady=10)

        ttk.Label(
            header,
            text=f"📊 Full Data Preview - {len(self.df):,} rows × {len(self.df.columns)} columns",
            font=('Segoe UI', 14, 'bold')
        ).pack(side='left')

        ttk.Button(
            header,
            text="✖ Close",
            command=expanded_window.destroy,
            style='Warning.TButton'
        ).pack(side='right')

        # Create full tksheet
        full_sheet = Sheet(
            expanded_window,
            theme="light blue",
            show_row_index=True,
            show_top_left=True,
            show_header=True,     # CRITICAL: Show column headers
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            empty_horizontal=0,
            empty_vertical=0
        )

        # Enable bindings
        full_sheet.enable_bindings(
            "single_select",
            "row_select",
            "column_select",
            "column_width_resize",
            "double_click_column_resize",
            "row_height_resize",
            "arrowkeys",
            "right_click_popup_menu",
            "rc_select",
            "copy",
            "cut",
            "paste",
            "delete",
            "undo"
        )

        # Configure appearance
        full_sheet.set_options(
            font=("Segoe UI", 10, "normal"),
            header_font=("Segoe UI", 10, "bold"),
            index_font=("Segoe UI", 10, "normal"),
            header_bg="#F3F2F1",
            header_fg="#323130",
            index_bg="#F3F2F1",
            index_fg="#323130",
            top_left_bg="#F3F2F1",
            top_left_fg="#323130",
            frame_bg="#FFFFFF",
            table_bg="#FFFFFF",
            table_grid_fg="#E0E0E0",
            table_selected_cells_border_fg="#0078D4",
            table_selected_cells_bg="#CCE4F7",
            row_index=1,
            header_height=30
        )

        # Prepare headers
        headers = []
        for idx, col_name in enumerate(self.df.columns):
            col_letter = self._get_column_letter(idx)
            header_text = f"{col_letter} - {col_name}"
            headers.append(header_text)

        # Load ALL data
        data = []
        for idx in range(len(self.df)):
            row_values = self.df.iloc[idx].tolist()
            formatted_row = []

            for val in row_values:
                if pd.isna(val):
                    formatted_row.append('')
                elif isinstance(val, float):
                    formatted_row.append(f"{val:.2f}" if val != int(val) else str(int(val)))
                else:
                    formatted_row.append(str(val))

            data.append(formatted_row)

        # Set data first
        full_sheet.set_sheet_data(data)

        # Then set headers
        full_sheet.headers(headers)

        # Auto-fit columns
        full_sheet.set_all_cell_sizes_to_text()

        # Refresh to ensure headers are visible
        full_sheet.refresh()

        # Alternating row colors
        for row_idx in range(len(self.df)):
            if row_idx % 2 == 1:
                full_sheet.highlight_rows(
                    row_idx,
                    bg="#F9F9F9",
                    fg="#000000",
                    highlight_index=False
                )

        full_sheet.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Status bar
        status = ttk.Label(
            expanded_window,
            text=f"💡 Tip: Use scroll bars to navigate • Resize columns by dragging borders • All {len(self.df):,} rows loaded",
            font=('Segoe UI', 10),
            foreground='#666666'
        )
        status.pack(pady=5)

    def clear(self):
        """Clear all data from preview"""
        self.df = None
        self.original_sheet.set_sheet_data([[]])
        self.results_sheet.set_sheet_data([[]])
        self.info_label.config(text="No data loaded")

    def get_column_names(self) -> list:
        """Get list of column names from loaded dataframe"""
        if self.df is None:
            return []
        return list(self.df.columns)

    def get_column_with_letter(self, col_name: str) -> str:
        """Get column name with Excel-style letter prefix"""
        if self.df is None or col_name not in self.df.columns:
            return col_name

        idx = list(self.df.columns).index(col_name)
        letter = self._get_column_letter(idx)
        return f"{letter}: {col_name}"


# Example usage and testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Enhanced Preview Test - tksheet")
    root.geometry("1200x700")

    # Create preview
    preview = EnhancedDataPreview(root)
    preview.pack(fill='both', expand=True, padx=10, pady=10)

    # Load sample data
    sample_data = {
        'Customer ID': range(1, 201),
        'Company Name': ['Acme Corp', 'Smith Industries', 'Tech Solutions'] * 67,
        'Contact Name': ['John Doe', 'Jane Smith', 'Bob Johnson'] * 67,
        'Email': ['john@acme.com', 'jane@smith.com', 'bob@tech.com'] * 67,
        'Phone': ['555-0001', '555-0002', '555-0003'] * 67,
        'City': ['New York', 'Los Angeles', 'Chicago'] * 67,
        'State': ['NY', 'CA', 'IL'] * 67,
        'Amount': [1234.56, 9876.54, 4567.89] * 67
    }

    df = pd.DataFrame(sample_data)
    preview.load_dataframe(df)

    root.mainloop()
