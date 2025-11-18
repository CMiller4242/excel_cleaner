"""
Smart Column Selector Component for Universal Excel Tool V2.1+
Provides intelligent column selection with dropdowns, search, and multi-select
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable


class ColumnSelector(ttk.Frame):
    """
    Smart column selector with search and dropdown
    For single-column operations
    """
    
    def __init__(self, parent, columns: List[str], label: str = "Select Column", **kwargs):
        super().__init__(parent, **kwargs)
        self.columns = columns
        self.label_text = label
        self.selected_value = tk.StringVar()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the selector interface"""
        # Label
        ttk.Label(
            self,
            text=self.label_text,
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        # Combobox with search
        self.combo = ttk.Combobox(
            self,
            textvariable=self.selected_value,
            values=self.columns,
            state='normal',  # Allow typing for search
            font=('Segoe UI', 11),
            width=40
        )
        self.combo.pack(fill='x', pady=(0, 10))
        
        # Bind for auto-complete/search
        self.combo.bind('<KeyRelease>', self._on_key_release)
        
        # Helper text
        ttk.Label(
            self,
            text="💡 Type to search or click dropdown to select",
            font=('Segoe UI', 9),
            foreground='#666666'
        ).pack(anchor='w')
    
    def _on_key_release(self, event):
        """Handle key release for search/filter functionality"""
        typed = self.selected_value.get().lower()
        
        if typed == '':
            self.combo['values'] = self.columns
        else:
            # Filter columns that contain typed text
            filtered = [col for col in self.columns if typed in col.lower()]
            self.combo['values'] = filtered
    
    def get_value(self) -> str:
        """Get selected column name"""
        value = self.selected_value.get()
        
        # Remove column letter prefix if present (e.g., "A: Company" -> "Company")
        if ':' in value:
            return value.split(':', 1)[1].strip()
        return value
    
    def set_value(self, value: str):
        """Set selected column"""
        self.selected_value.set(value)
    
    def update_columns(self, columns: List[str]):
        """Update available columns"""
        self.columns = columns
        self.combo['values'] = columns


class MultiColumnSelector(ttk.Frame):
    """
    Multi-column selector with checkbox list
    For operations that need multiple columns
    """
    
    def __init__(self, parent, columns: List[str], label: str = "Select Columns", 
                 max_height: int = 200, **kwargs):
        super().__init__(parent, **kwargs)
        self.columns = columns
        self.label_text = label
        self.max_height = max_height
        self.checkboxes = {}
        self.selected_vars = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the selector interface"""
        # Label
        ttk.Label(
            self,
            text=self.label_text,
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor='w', pady=(0, 5))
        
        # Frame with scrollbar for checkboxes
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill='both', expand=True)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(
            canvas_frame,
            height=min(self.max_height, len(self.columns) * 30),
            bg='white',
            highlightthickness=1,
            highlightbackground='#cccccc'
        )
        self.canvas.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Inner frame for checkboxes
        self.checkbox_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor='nw')
        
        # Add checkboxes for each column
        for col in self.columns:
            var = tk.BooleanVar(value=False)
            self.selected_vars[col] = var
            
            cb = ttk.Checkbutton(
                self.checkbox_frame,
                text=col,
                variable=var,
                onvalue=True,
                offvalue=False
            )
            cb.pack(anchor='w', padx=5, pady=2)
            self.checkboxes[col] = cb
        
        # Update scroll region
        self.checkbox_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        
        # Bind canvas resize
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Selection buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text="✓ Select All",
            command=self._select_all,
            width=15
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame,
            text="✗ Clear All",
            command=self._clear_all,
            width=15
        ).pack(side='left', padx=5)
        
        # Helper text
        ttk.Label(
            self,
            text="💡 Check columns to include in operation",
            font=('Segoe UI', 9),
            foreground='#666666'
        ).pack(anchor='w', pady=(5, 0))
    
    def _on_canvas_configure(self, event):
        """Handle canvas resize"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _select_all(self):
        """Select all checkboxes"""
        for var in self.selected_vars.values():
            var.set(True)
    
    def _clear_all(self):
        """Clear all checkboxes"""
        for var in self.selected_vars.values():
            var.set(False)
    
    def get_selected_columns(self) -> List[str]:
        """Get list of selected column names"""
        selected = []
        for col, var in self.selected_vars.items():
            if var.get():
                # Remove column letter prefix if present
                clean_col = col.split(':', 1)[1].strip() if ':' in col else col
                selected.append(clean_col)
        return selected
    
    def set_selected_columns(self, columns: List[str]):
        """Set which columns are selected"""
        for col, var in self.selected_vars.items():
            clean_col = col.split(':', 1)[1].strip() if ':' in col else col
            var.set(clean_col in columns)
    
    def update_columns(self, columns: List[str]):
        """Update available columns"""
        # Clear existing checkboxes
        for cb in self.checkboxes.values():
            cb.destroy()
        
        self.checkboxes.clear()
        self.selected_vars.clear()
        
        # Add new checkboxes
        self.columns = columns
        for col in self.columns:
            var = tk.BooleanVar(value=False)
            self.selected_vars[col] = var
            
            cb = ttk.Checkbutton(
                self.checkbox_frame,
                text=col,
                variable=var,
                onvalue=True,
                offvalue=False
            )
            cb.pack(anchor='w', padx=5, pady=2)
            self.checkboxes[col] = cb
        
        # Update scroll region
        self.checkbox_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))


class SmartColumnDialog:
    """
    Helper class to create operation dialogs with smart column selection
    """
    
    @staticmethod
    def create_single_column_dialog(parent, title: str, columns: List[str],
                                   column_label: str = "Select Column",
                                   additional_params: dict = None,
                                   on_submit: Callable = None) -> tk.Toplevel:
        """
        Create a dialog for single column selection with optional additional parameters
        
        Args:
            parent: Parent window
            title: Dialog title
            columns: List of available columns
            column_label: Label for column selector
            additional_params: Dict of {param_name: (label, widget_type, default_value)}
            on_submit: Callback function(selected_column, additional_values)
        """
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("500x400")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(
            main_frame,
            text=title,
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(0, 20))
        
        # Column selector
        col_selector = ColumnSelector(main_frame, columns, column_label)
        col_selector.pack(fill='x', pady=(0, 20))
        
        # Additional parameters
        param_widgets = {}
        if additional_params:
            for param_name, (label, widget_type, default) in additional_params.items():
                param_frame = ttk.Frame(main_frame)
                param_frame.pack(fill='x', pady=(0, 10))
                
                ttk.Label(
                    param_frame,
                    text=label,
                    font=('Segoe UI', 11, 'bold')
                ).pack(anchor='w', pady=(0, 5))
                
                if widget_type == 'entry':
                    widget = ttk.Entry(param_frame, font=('Segoe UI', 11))
                    widget.insert(0, str(default))
                    widget.pack(fill='x')
                elif widget_type == 'combobox':
                    widget = ttk.Combobox(param_frame, values=default, font=('Segoe UI', 11))
                    widget.set(default[0] if default else '')
                    widget.pack(fill='x')
                
                param_widgets[param_name] = widget
        
        # Result storage
        result = {'submitted': False, 'column': None, 'params': {}}
        
        def submit():
            column = col_selector.get_value()
            if not column:
                tk.messagebox.showwarning("Missing Selection", "Please select a column")
                return
            
            result['submitted'] = True
            result['column'] = column
            
            for param_name, widget in param_widgets.items():
                result['params'][param_name] = widget.get()
            
            if on_submit:
                on_submit(result['column'], result['params'])
            
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=cancel,
            width=15
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame,
            text="✓ Add to Queue",
            command=submit,
            style='Success.TButton',
            width=15
        ).pack(side='right', padx=5)
        
        dialog.result = result
        return dialog
    
    @staticmethod
    def create_multi_column_dialog(parent, title: str, columns: List[str],
                                  column_label: str = "Select Columns",
                                  additional_params: dict = None,
                                  on_submit: Callable = None) -> tk.Toplevel:
        """
        Create a dialog for multiple column selection
        """
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("500x500")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(
            main_frame,
            text=title,
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(0, 20))
        
        # Multi-column selector
        col_selector = MultiColumnSelector(main_frame, columns, column_label)
        col_selector.pack(fill='both', expand=True, pady=(0, 20))
        
        # Additional parameters
        param_widgets = {}
        if additional_params:
            for param_name, (label, widget_type, default) in additional_params.items():
                param_frame = ttk.Frame(main_frame)
                param_frame.pack(fill='x', pady=(0, 10))
                
                ttk.Label(
                    param_frame,
                    text=label,
                    font=('Segoe UI', 11, 'bold')
                ).pack(anchor='w', pady=(0, 5))
                
                if widget_type == 'entry':
                    widget = ttk.Entry(param_frame, font=('Segoe UI', 11))
                    widget.insert(0, str(default))
                    widget.pack(fill='x')
                elif widget_type == 'combobox':
                    widget = ttk.Combobox(param_frame, values=default, font=('Segoe UI', 11))
                    widget.set(default[0] if default else '')
                    widget.pack(fill='x')
                
                param_widgets[param_name] = widget
        
        # Result storage
        result = {'submitted': False, 'columns': [], 'params': {}}
        
        def submit():
            columns_selected = col_selector.get_selected_columns()
            if not columns_selected:
                tk.messagebox.showwarning("Missing Selection", "Please select at least one column")
                return
            
            result['submitted'] = True
            result['columns'] = columns_selected
            
            for param_name, widget in param_widgets.items():
                result['params'][param_name] = widget.get()
            
            if on_submit:
                on_submit(result['columns'], result['params'])
            
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=cancel,
            width=15
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame,
            text="✓ Add to Queue",
            command=submit,
            style='Success.TButton',
            width=15
        ).pack(side='right', padx=5)
        
        dialog.result = result
        return dialog


# Example usage and testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Smart Column Selector Test")
    root.geometry("600x500")
    
    # Sample columns with Excel-style letters
    sample_columns = [
        "A: Customer ID",
        "B: Company Name",
        "C: Contact Name",
        "D: Email",
        "E: Phone",
        "F: Address",
        "G: City",
        "H: State",
        "I: Zip Code"
    ]
    
    # Test single column selector
    def test_single():
        def on_submit(column, params):
            print(f"Selected column: {column}")
            print(f"Additional params: {params}")
        
        dialog = SmartColumnDialog.create_single_column_dialog(
            root,
            title="Remove Columns",
            columns=sample_columns,
            column_label="Column to Remove",
            on_submit=on_submit
        )
        root.wait_window(dialog)
    
    # Test multi-column selector
    def test_multi():
        def on_submit(columns, params):
            print(f"Selected columns: {columns}")
            print(f"Additional params: {params}")
        
        dialog = SmartColumnDialog.create_multi_column_dialog(
            root,
            title="Concatenate Columns",
            columns=sample_columns,
            column_label="Columns to Combine",
            additional_params={
                'separator': ('Separator', 'entry', ' '),
                'new_column': ('New Column Name', 'entry', 'Combined')
            },
            on_submit=on_submit
        )
        root.wait_window(dialog)
    
    # Buttons to test
    ttk.Button(root, text="Test Single Column Selector", command=test_single).pack(pady=20)
    ttk.Button(root, text="Test Multi-Column Selector", command=test_multi).pack(pady=20)
    
    root.mainloop()
