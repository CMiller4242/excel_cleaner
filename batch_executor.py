"""
Simple Batch Executor
Runs single-file execution logic multiple times
"""

from typing import List, Dict
from tkinter import messagebox


class SimpleBatchExecutor:
    """Execute operations on multiple files using proven single-file logic"""

    def __init__(self, main_app):
        """
        Args:
            main_app: Reference to main CleanSheetApp instance
        """
        self.main_app = main_app

    def execute_batch(self, file_objects: List[Dict]) -> List[Dict]:
        """
        Execute operations on multiple files

        Strategy: For each file, run the normal single-file execution logic
        that's already proven to work

        Args:
            file_objects: List of file objects with 'df' and 'operations'

        Returns:
            list: Results with success/error status per file
        """
        results = []
        total = len(file_objects)

        for idx, file_obj in enumerate(file_objects):
            file_name = file_obj['name']

            # Update progress
            self.main_app.status_var.set(
                f"Processing {file_name} ({idx + 1}/{total})..."
            )
            self.main_app.root.update()

            try:
                # Execute operations for this file
                result_df, removed_df = self._execute_single_file(file_obj)

                # Store results
                file_obj['result_df'] = result_df
                file_obj['removed_df'] = removed_df
                file_obj['status'] = 'success'

                results.append({
                    'file': file_name,
                    'status': 'success',
                    'rows_before': len(file_obj['df']),
                    'rows_after': len(result_df),
                    'rows_removed': len(removed_df) if removed_df is not None else 0
                })

            except Exception as e:
                file_obj['status'] = 'error'
                file_obj['error'] = str(e)

                results.append({
                    'file': file_name,
                    'status': 'error',
                    'error': str(e)
                })

        # Update status
        success_count = sum(1 for r in results if r['status'] == 'success')
        self.main_app.status_var.set(
            f"✅ Batch complete! {success_count}/{total} files processed"
        )

        return results

    def _execute_single_file(self, file_obj: Dict):
        """
        Execute operations on a single file using the WORKING single-file logic

        This is the KEY method - it reuses proven execution code

        Args:
            file_obj: File object with 'df' and 'operations'

        Returns:
            tuple: (result_df, removed_df)
        """
        df = file_obj['df'].copy()
        operations = file_obj.get('operations', [])

        if not operations:
            # No operations, return original
            return df, None

        # Import the working executor (SAME AS SINGLE FILE MODE)
        from engine.executor import OperationExecutor
        from engine.validator import Validator

        executor = OperationExecutor()

        # Convert operation configs to queue format
        operation_queue = []
        for op_config in operations:
            # Skip disabled operations
            if not op_config.get('enabled', True):
                continue

            # Convert to queue format (operation_id, name, parameters)
            queue_item = {
                'operation_id': op_config.get('name'),  # Use name as ID for now
                'name': op_config.get('name'),
                'parameters': op_config.get('parameters', {}),
                'enabled': True
            }
            operation_queue.append(queue_item)

        if not operation_queue:
            # All operations disabled
            return df, None

        # Validate (SAME AS SINGLE FILE MODE)
        is_valid, errors = Validator.validate_queue(df, operation_queue)
        if not is_valid:
            error_msg = "\n".join(errors)
            raise ValueError(f"Validation failed: {error_msg}")

        # Execute (USING THE WORKING METHOD)
        result_df, removed_df = executor.execute_queue_with_tracking(df, operation_queue)

        return result_df, removed_df
