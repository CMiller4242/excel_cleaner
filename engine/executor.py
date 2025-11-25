"""Operation Executor - Run operations in sequence"""
import pandas as pd
from typing import List, Dict, Callable, Tuple, Optional
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from operations.registry import registry

class OperationExecutor:
    """Execute a queue of operations"""

    def __init__(self, progress_callback: Callable = None):
        self.progress_callback = progress_callback
        # Track removed rows for multi-sheet export
        self.removed_rows = pd.DataFrame()
        self.removed_rows_metadata = []

    def preview_execute_queue(self, df: pd.DataFrame, operations: List[Dict]) -> Optional[pd.DataFrame]:
        """
        Execute operations in preview mode (lightweight, no tracking)
        Used to show immediate preview of results without full execution

        Args:
            df: Input DataFrame
            operations: List of operation configs

        Returns:
            Preview DataFrame or None if errors occur
        """
        if df is None or df.empty:
            return None

        try:
            result_df = df.copy()

            for op_config in operations:
                if not op_config.get('enabled', True):
                    continue

                operation_id = op_config['operation_id']
                params = op_config['parameters']

                # Get operation
                operation = registry.get_by_id(operation_id)
                if not operation:
                    # Skip invalid operations in preview
                    continue

                # Validate parameters (skip if invalid in preview)
                is_valid, error = operation.validate_params(result_df, params)
                if not is_valid:
                    continue

                # Execute operation
                result_df = operation.execute(result_df, params)

            return result_df

        except Exception as e:
            # Silently fail in preview mode - just return original
            print(f"Preview execution error: {e}")
            return df

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

        # Reset removed rows tracking
        self.removed_rows = pd.DataFrame()
        self.removed_rows_metadata = []

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

            # Check if operation removes rows
            rows_before = len(result_df)

            # Execute
            result_df = operation.execute(result_df, params)

            # Track removed rows
            rows_after = len(result_df)
            if rows_after < rows_before:
                rows_removed = rows_before - rows_after
                # Try to identify which rows were removed
                self._track_removed_rows(
                    df_before=result_df,  # We can't access before state easily
                    df_after=result_df,
                    operation_name=operation.metadata.name,
                    operation_id=operation_id,
                    rows_removed=rows_removed
                )

            # Progress callback
            if self.progress_callback:
                self.progress_callback(i + 1, len(operations), operation.metadata.name)

        return result_df

    def execute_queue_with_tracking(self, df: pd.DataFrame, operations: List[Dict]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Execute operations and return both results and removed rows

        Args:
            df: Input DataFrame
            operations: List of operation configs

        Returns:
            Tuple of (result_df, removed_df)
        """
        result_df = df.copy()

        # Reset removed rows tracking
        self.removed_rows = pd.DataFrame()
        self.removed_rows_metadata = []

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

            # Store state before execution
            df_before = result_df.copy()
            df_before_index = set(df_before.index)

            # Execute
            result_df = operation.execute(result_df, params)

            # Track removed rows by comparing indices
            df_after_index = set(result_df.index)
            removed_indices = df_before_index - df_after_index

            if removed_indices:
                removed_data = df_before.loc[list(removed_indices)].copy()
                removed_data['_Removed_By'] = operation.metadata.name
                removed_data['_Operation_ID'] = operation_id
                removed_data['_Step'] = i + 1

                # Append to removed rows
                if self.removed_rows.empty:
                    self.removed_rows = removed_data
                else:
                    self.removed_rows = pd.concat([self.removed_rows, removed_data], ignore_index=True)

            # Progress callback
            if self.progress_callback:
                self.progress_callback(i + 1, len(operations), operation.metadata.name)

        return result_df, self.removed_rows

    def _track_removed_rows(self, df_before, df_after, operation_name, operation_id, rows_removed):
        """Track metadata about removed rows"""
        self.removed_rows_metadata.append({
            'operation': operation_name,
            'operation_id': operation_id,
            'rows_removed': rows_removed
        })

    def get_removed_rows(self) -> pd.DataFrame:
        """Get all removed rows with metadata"""
        return self.removed_rows

    def get_removed_rows_summary(self) -> List[Dict]:
        """Get summary of removed rows by operation"""
        return self.removed_rows_metadata
    
    def preview_queue(self, df: pd.DataFrame, operations: List[Dict], max_rows: int = 100) -> pd.DataFrame:
        """Preview what operations will do"""
        preview_df = df.head(max_rows).copy()
        return self.execute_queue(preview_df, operations)
