"""
Data Quality Analysis Integration Module
Connects analyzer, AI enhancement, and GUI components

This module can be imported into main_gui_v2.py to add the
"Analyze Data Quality" feature

FIXED: Operation queue format now matches main GUI expectations
"""

import threading
from typing import Optional, Callable
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox


class DataQualityIntegration:
    """
    Integration class for data quality analysis feature
    
    Usage in main_gui_v2.py:
    1. Import this module
    2. Initialize: self.dq_integration = DataQualityIntegration(self)
    3. Add button that calls: self.dq_integration.analyze_data()
    """
    
    def __init__(self, main_gui):
        """
        Initialize integration
        
        Args:
            main_gui: Reference to main GUI object (main_gui_v2.UniversalExcelTool instance)
        """
        self.main_gui = main_gui
        self.analyzer = None  # Lazy load
        self.ai_enhancer = None  # Lazy load
        self.current_report = None
        self.current_ai_enhancement = None
    
    def analyze_data(self):
        """
        Main entry point - analyze currently loaded data
        """
        # Check if data is loaded
        if not hasattr(self.main_gui, 'df') or self.main_gui.df is None:
            messagebox.showerror("No Data Loaded", "Please load a file first before analyzing.")
            return
        
        # Import here to avoid circular imports
        from analysis.data_quality_analyzer import DataQualityAnalyzer
        from analysis.analysis_dialog import ProgressDialog, AnalysisDialog
        
        # Show progress dialog
        progress = ProgressDialog(self.main_gui.root, "Analyzing Data Quality...")
        progress.update_status("Scanning data for issues...")
        
        # Run analysis in thread to keep GUI responsive
        def run_analysis():
            try:
                # Step 1: Run deterministic analysis
                if self.analyzer is None:
                    self.analyzer = DataQualityAnalyzer()
                
                self.current_report = self.analyzer.analyze(self.main_gui.df)
                
                # Step 2: Try AI enhancement if API key available
                self.current_ai_enhancement = None
                if self.should_use_ai():
                    progress.update_status("Getting AI insights...")
                    self.current_ai_enhancement = self.enhance_with_ai()
                
                # Close progress and show results
                progress.close()
                self.show_analysis_results()
                
            except Exception as e:
                progress.close()
                messagebox.showerror("Analysis Error", f"Error during analysis: {str(e)}")
        
        # Start analysis thread
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
    
    def should_use_ai(self) -> bool:
        """Check if AI enhancement should be used"""
        # Check if AI assistant is available and connected
        if not hasattr(self.main_gui, 'ai_assistant'):
            return False
        
        if self.main_gui.ai_assistant is None:
            return False
        
        # Check if API key is set
        if not hasattr(self.main_gui.ai_assistant, 'api_key'):
            return False
        
        if not self.main_gui.ai_assistant.api_key:
            return False
        
        return True
    
    def enhance_with_ai(self) -> Optional[dict]:
        """Enhance analysis with AI if available"""
        try:
            from analysis.ai_enhancement import AIAnalysisEnhancer
            
            # Get API key from existing AI assistant
            api_key = self.main_gui.ai_assistant.api_key
            
            # Create enhancer
            if self.ai_enhancer is None:
                self.ai_enhancer = AIAnalysisEnhancer(api_key)
            
            # Build data summary
            df_summary = {
                "rows": len(self.main_gui.df),
                "columns": len(self.main_gui.df.columns),
                "column_names": list(self.main_gui.df.columns),
                "sample_data": self.main_gui.df.head(3).to_dict()
            }
            
            # Get enhancement
            enhancement = self.ai_enhancer.enhance_analysis(
                self.current_report,
                df_summary
            )
            
            return enhancement
            
        except Exception as e:
            print(f"AI enhancement failed: {e}")
            return None
    
    def show_analysis_results(self):
        """Show analysis results dialog"""
        from analysis.analysis_dialog import AnalysisDialog
        
        # Create and show dialog
        dialog = AnalysisDialog(
            self.main_gui.root,
            self.current_report,
            self.current_ai_enhancement
        )
        
        result = dialog.show()
        
        # If user clicked "Add to Queue", add selected operations
        if result == "apply":
            selected_ops = dialog.get_selected_operations()
            self.add_operations_to_queue(selected_ops)
    
    def _validate_operation_params(self, operation, params: dict) -> Optional[str]:
        """
        Validate that all required parameters for an operation are present

        Args:
            operation: BaseOperation instance
            params: Parameter dictionary

        Returns:
            Error message if validation fails, None if valid
        """
        # Get required parameters from operation metadata
        required_params = []
        for param in operation.metadata.parameters:
            if param.required is not False:  # Default is True if not specified
                required_params.append(param.name)

        # Check each required parameter
        missing_params = []
        for param_name in required_params:
            if param_name not in params:
                missing_params.append(param_name)
            elif params[param_name] is None:
                missing_params.append(param_name)
            elif isinstance(params[param_name], str) and not params[param_name].strip():
                missing_params.append(param_name)
            elif isinstance(params[param_name], list) and len(params[param_name]) == 0:
                # Empty list is OK for some operations (like remove_duplicates with columns=[])
                # Only flag if it's truly missing, not if it's an intentional empty list
                pass

        if missing_params:
            return f"Missing required parameter(s): {', '.join(missing_params)}"

        return None

    def add_operations_to_queue(self, operation_configs: list):
        """
        Add selected operations to the main GUI's operation queue

        FIXED: Now properly formats operations to match main GUI's queue structure

        Args:
            operation_configs: List of operation config dicts from analyzer
        """
        if not operation_configs:
            return
        
        from operations.registry import registry
        
        added_count = 0
        failed_ops = []
        
        for op_config in operation_configs:
            op_id = op_config.get('operation_id')
            params = op_config.get('params', {})

            # Get operation from registry
            operation = registry.get_by_id(op_id)

            if operation is None:
                failed_ops.append(op_id)
                print(f"Warning: Operation '{op_id}' not found in registry")
                continue

            # VALIDATION: Check that all required parameters are present
            validation_error = self._validate_operation_params(operation, params)
            if validation_error:
                failed_ops.append(f"{op_id} ({validation_error})")
                print(f"Validation failed for '{op_id}': {validation_error}")
                continue

            # FIXED: Format to match main GUI's queue structure
            # The main GUI expects this exact format
            try:
                queue_entry = {
                    'operation_id': op_id,
                    'name': operation.metadata.name,
                    'parameters': params,
                    'enabled': True
                }
                
                # Add to GUI's operation queue
                self.main_gui.operation_queue.append(queue_entry)
                
                # Update GUI display
                display_text = f"{operation.metadata.name}"
                if params:
                    # Format parameters for display
                    param_parts = []
                    for k, v in params.items():
                        if k and v:
                            if isinstance(v, list):
                                param_parts.append(f"{k}={', '.join(map(str, v))}")
                            else:
                                param_parts.append(f"{k}={v}")
                    if param_parts:
                        display_text += f" ({'; '.join(param_parts)})"
                
                # Add checkmark prefix to match GUI format
                display_text = f"{len(self.main_gui.operation_queue)}. ☑ {display_text}"
                
                self.main_gui.queue_listbox.insert(tk.END, display_text)
                added_count += 1
                
            except Exception as e:
                print(f"Failed to add operation {op_id}: {e}")
                import traceback
                traceback.print_exc()
                failed_ops.append(op_id)
        
        # Show confirmation
        if added_count > 0:
            message = f"✅ Added {added_count} operation(s) to queue"
            if failed_ops:
                message += f"\n\n⚠ Failed to add:\n"
                for op in failed_ops:
                    message += f"  • {op}\n"

            messagebox.showinfo("Operations Added", message)
        elif failed_ops:
            error_message = "Could not add the following operations:\n\n"
            for op in failed_ops:
                error_message += f"  • {op}\n"
            error_message += "\nPlease check that:\n"
            error_message += "  - The operations are registered in the system\n"
            error_message += "  - All required parameters have valid values\n"
            error_message += "  - Column names match your data\n"

            messagebox.showerror("Failed to Add Operations", error_message)
    
    def get_quick_stats(self) -> dict:
        """Get quick statistics about the current data"""
        if not hasattr(self.main_gui, 'df') or self.main_gui.df is None:
            return {}
        
        df = self.main_gui.df
        
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": df.isnull().sum().sum(),
            "duplicate_rows": df.duplicated().sum(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024
        }


def add_analyze_button_to_gui(main_gui):
    """
    Helper function to add the "Analyze Data Quality" button to existing GUI
    
    Call this from main_gui_v2.py's create_widgets() method
    
    Args:
        main_gui: Instance of UniversalExcelTool
    """
    # Initialize integration
    if not hasattr(main_gui, 'dq_integration'):
        main_gui.dq_integration = DataQualityIntegration(main_gui)
    
    # Add button to toolbar
    analyze_button = ttk.Button(
        main_gui.toolbar,
        text="🔍 Analyze Data Quality",
        command=main_gui.dq_integration.analyze_data,
        width=20
    )
    analyze_button.pack(side=tk.LEFT, padx=5)
    
    return analyze_button