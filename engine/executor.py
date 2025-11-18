"""Operation Executor - Run operations in sequence"""
import pandas as pd
from typing import List, Dict, Callable
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from operations.registry import registry

class OperationExecutor:
    """Execute a queue of operations"""
    
    def __init__(self, progress_callback: Callable = None):
        self.progress_callback = progress_callback
    
    def execute_queue(self, df: pd.DataFrame, operations: List[Dict]) -> pd.DataFrame:
        """
        Execute multiple operations in sequence
        
        Args:
            df: Input DataFrame
            operations: List of {operation_id, parameters, enabled} dicts
            
        Returns:
            Transformed DataFrame
        """
        result_df = df.copy()
        
        for i, op_config in enumerate(operations):
            if not op_config.get('enabled', True):
                continue
            
            operation_id = op_config['operation_id']
            params = op_config['parameters']
            
            # Get operation
            operation = registry.get_by_id(operation_id)
            if not operation:
                raise ValueError(f"Operation {operation_id} not found")
            
            # Validate parameters
            is_valid, error = operation.validate_params(result_df, params)
            if not is_valid:
                raise ValueError(f"Invalid parameters for {operation_id}: {error}")
            
            # Execute
            result_df = operation.execute(result_df, params)
            
            # Progress callback
            if self.progress_callback:
                self.progress_callback(i + 1, len(operations), operation.metadata.name)
        
        return result_df
    
    def preview_queue(self, df: pd.DataFrame, operations: List[Dict], max_rows: int = 100) -> pd.DataFrame:
        """Preview what operations will do"""
        preview_df = df.head(max_rows).copy()
        return self.execute_queue(preview_df, operations)
