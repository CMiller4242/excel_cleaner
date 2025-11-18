"""Validator - Validate operations before execution"""
import pandas as pd
from typing import List, Dict, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from operations.registry import registry

class Validator:
    """Validate operations and parameters"""
    
    @staticmethod
    def validate_queue(df: pd.DataFrame, operations: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate a queue of operations
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        for op_config in operations:
            operation_id = op_config.get('operation_id')
            params = op_config.get('parameters', {})
            
            # Check operation exists
            operation = registry.get_by_id(operation_id)
            if not operation:
                errors.append(f"Operation not found: {operation_id}")
                continue
            
            # Validate parameters
            is_valid, error = operation.validate_params(df, params)
            if not is_valid:
                errors.append(f"{operation.metadata.name}: {error}")
        
        return len(errors) == 0, errors
