"""
Enhanced Data Preview Component for Universal Excel Tool V2.1+
Provides auto-fit columns and expandable full-screen preview
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Optional


class EnhancedDataPreview(ttk.Frame):
    """
    Enhanced data preview with auto-fit columns and expandable view
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.df: Optional[pd.DataFrame] = None
        self.max_embedded_rows = 100  # Limit for embedded preview
        
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
        
        # Create treeviews for both tabs
        self.original_tree = self._create_treeview(self.original_frame)
        self.results_tree = self._create_treeview(self.results_frame)
        
        # Info label
        self.info_label = ttk.Label(
            self,
            text="No data loaded",
            font=('Segoe UI', 10),
            foreground='gray'
        )
        self.info_label.pack(pady=5)
    
    def _create_treeview(self, parent) -> ttk.Treeview:
        """Create a treeview with scrollbars and Excel-style appearance"""
        # Frame for tree and scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True)

        # Scrollbars (Excel-style)
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
        v_scroll.pack(side='right', fill='y')

        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')

        # Treeview with Excel styling
        tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
            show='tree headings',
            selectmode='extended'
        )
        tree.pack(side='left', fill='both', expand=True)

        # Configure scrollbars
        v_scroll.config(command=tree.yview)
        h_scroll.config(command=tree.xview)

        # Style with alternating rows (Excel-like)
        tree.tag_configure('oddrow', background='#FFFFFF')
        tree.tag_configure('evenrow', background='#F9F9F9')
        tree.tag_configure('selected', background='#CCE4F7', foreground='#000000')

        # Apply Excel-specific styling
        style = ttk.Style()
        style.configure('Excel.Treeview',
                       background='#FFFFFF',
                       foreground='#000000',
                       fieldbackground='#FFFFFF',
                       font=('Segoe UI', 10),
                       rowheight=25)

        style.configure('Excel.Treeview.Heading',
                       background='#F3F2F1',
                       foreground='#323130',
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat',
                       borderwidth=1)

        style.map('Excel.Treeview.Heading',
                 background=[('active', '#E1DFDD')])

        tree.configure(style='Excel.Treeview')

        return tree
    
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
        
        # Select which tree to populate
        tree = self.results_tree if is_result else self.original_tree
        
        # Clear existing data
        tree.delete(*tree.get_children())
        
        # Setup columns
        columns = ['Row'] + list(df.columns)
        tree['columns'] = columns
        
        # Configure column 0 (row numbers)
        tree.column('#0', width=0, stretch=False)
        tree.heading('#0', text='')
        
        # Configure all columns with auto-fit
        column_widths = self._calculate_column_widths(df)
        
        for i, col in enumerate(columns):
            tree.column(
                col,
                width=column_widths[i],
                minwidth=50,
                anchor='w',
                stretch=True
            )

            # Excel-style two-row headers: Letter (top) + Name (bottom)
            if i == 0:
                # Row number column
                tree.heading(col, text='#', anchor='center')
            else:
                # Data columns with letter + name
                col_letter = self._get_column_letter(i - 1)
                # Format: "  A  \nColumn Name" for visual two-row effect
                header_text = f"   {col_letter}   \n{col}"
                tree.heading(col, text=header_text, anchor='center')
        
        # Add data rows (limit to max_embedded_rows for performance)
        display_rows = min(len(df), self.max_embedded_rows)
        
        for idx in range(display_rows):
            row_data = [str(idx + 1)]  # Row number
            row_values = df.iloc[idx].tolist()
            
            for val in row_values:
                # Handle different data types
                if pd.isna(val):
                    row_data.append('')
                elif isinstance(val, float):
                    row_data.append(f"{val:.2f}" if val != int(val) else str(int(val)))
                else:
                    row_data.append(str(val))
            
            # Alternate row colors
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tree.insert('', 'end', values=row_data, tags=(tag,))
        
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
    
    def _calculate_column_widths(self, df: pd.DataFrame) -> list:
        """
        Calculate optimal column widths based on content
        Similar to Excel's auto-fit functionality
        """
        widths = [60]  # Row number column
        
        for col in df.columns:
            # Get column name length
            header_width = len(str(col)) * 8 + 40  # Account for column letter
            
            # Get max content length (sample first 100 rows for performance)
            sample_size = min(100, len(df))
            content_width = 0
            
            if sample_size > 0:
                max_len = df[col].head(sample_size).astype(str).str.len().max()
                content_width = max_len * 8 + 20  # 8 pixels per character + padding
            
            # Use larger of header or content width
            optimal_width = max(header_width, content_width, 80)  # Min 80px
            
            # Cap at reasonable maximum
            widths.append(min(optimal_width, 400))
        
        return widths
    
    def _get_column_letter(self, idx: int) -> str:
        """Convert column index to Excel-style letter (A, B, ... Z, AA, AB, ...)"""
        result = ""
        while idx >= 0:
            result = chr(65 + (idx % 26)) + result
            idx = idx // 26 - 1
        return result
    
    def _open_expanded_view(self):
        """Open full-screen expanded preview window"""
        if self.df is None or self.df.empty:
            return
        
        # Create expanded window
        expanded_window = tk.Toplevel(self)
        expanded_window.title("📊 Data Preview - Full Screen")
        expanded_window.geometry("1200x800")
        
        # Make it maximizable
        expanded_window.state('zoomed')  # Start maximized on Windows
        
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
        
        # Create full treeview
        full_tree = self._create_treeview(expanded_window)
        
        # Load ALL data (no row limit)
        columns = ['Row'] + list(self.df.columns)
        full_tree['columns'] = columns
        
        # Configure columns
        full_tree.column('#0', width=0, stretch=False)
        full_tree.heading('#0', text='')
        
        column_widths = self._calculate_column_widths(self.df)
        
        for i, col in enumerate(columns):
            full_tree.column(
                col,
                width=column_widths[i],
                minwidth=50,
                anchor='w',
                stretch=True
            )

            # Excel-style two-row headers
            if i == 0:
                full_tree.heading(col, text='#', anchor='center')
            else:
                col_letter = self._get_column_letter(i - 1)
                header_text = f"   {col_letter}   \n{col}"
                full_tree.heading(col, text=header_text, anchor='center')
        
        # Add ALL rows
        for idx in range(len(self.df)):
            row_data = [str(idx + 1)]
            row_values = self.df.iloc[idx].tolist()
            
            for val in row_values:
                if pd.isna(val):
                    row_data.append('')
                elif isinstance(val, float):
                    row_data.append(f"{val:.2f}" if val != int(val) else str(int(val)))
                else:
                    row_data.append(str(val))
            
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            full_tree.insert('', 'end', values=row_data, tags=(tag,))
        
        # Status bar
        status = ttk.Label(
            expanded_window,
            text=f"💡 Tip: Use scroll bars to navigate • All {len(self.df):,} rows are loaded",
            font=('Segoe UI', 10),
            foreground='#666666'
        )
        status.pack(pady=5)
    
    def clear(self):
        """Clear all data from preview"""
        self.df = None
        self.original_tree.delete(*self.original_tree.get_children())
        self.results_tree.delete(*self.results_tree.get_children())
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
    root.title("Enhanced Preview Test")
    root.geometry("900x600")
    
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
        'State': ['NY', 'CA', 'IL'] * 67
    }
    
    df = pd.DataFrame(sample_data)
    preview.load_dataframe(df)
    
    root.mainloop()
