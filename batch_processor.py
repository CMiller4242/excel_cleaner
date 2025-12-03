"""
Clean Sheet - Batch File Processor
Handles processing multiple files with the same operation queue
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Callable, Optional

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Process multiple files with the same set of operations

    Features:
    - Process each file independently
    - Progress tracking
    - Error handling per file
    - Results collection
    """

    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Initialize batch processor

        Args:
            progress_callback: Function to call with progress updates
                              Signature: callback(current, total, filename, status)
        """
        self.progress_callback = progress_callback
        self.results = []
        self.errors = []

    def process_batch(self, files: List[Dict], operation_queue: List,
                     executor) -> Dict:
        """
        Process multiple files with the same operations

        Args:
            files: List of file dictionaries with 'name', 'path', 'df'
            operation_queue: List of operations to apply
            executor: OperationExecutor instance

        Returns:
            Dictionary with results:
            {
                'successful': List[Dict],  # Successfully processed files
                'failed': List[Dict],      # Files that failed
                'summary': Dict            # Processing summary
            }
        """
        self.results = []
        self.errors = []
        total_files = len(files)

        logger.info(f"Starting batch processing of {total_files} files")

        for idx, file_obj in enumerate(files, 1):
            filename = file_obj['name']

            try:
                # Update progress
                if self.progress_callback:
                    self.progress_callback(idx, total_files, filename, 'processing')

                logger.info(f"Processing file {idx}/{total_files}: {filename}")

                # Get original dataframe (make a copy)
                df = file_obj['df'].copy()
                original_rows = len(df)

                # Apply all operations
                removed_rows = []
                for operation in operation_queue:
                    if not operation.get('enabled', True):
                        continue  # Skip disabled operations

                    # Execute operation
                    result = executor.execute_operation(
                        df=df,
                        operation_id=operation['operation_id'],
                        params=operation['params']
                    )

                    # Update dataframe and track removed rows
                    df = result['dataframe']
                    if 'removed_rows' in result and result['removed_rows'] is not None:
                        removed_rows.append(result['removed_rows'])

                # Combine removed rows
                removed_df = None
                if removed_rows:
                    removed_df = pd.concat(removed_rows, ignore_index=True)

                # Store successful result
                result_obj = {
                    'name': filename,
                    'path': file_obj.get('path', ''),
                    'original_df': file_obj['df'],
                    'result_df': df,
                    'removed_df': removed_df,
                    'original_rows': original_rows,
                    'final_rows': len(df),
                    'operations_applied': len([op for op in operation_queue if op.get('enabled', True)]),
                    'status': 'success'
                }

                self.results.append(result_obj)

                # Update progress to complete
                if self.progress_callback:
                    self.progress_callback(idx, total_files, filename, 'complete')

                logger.info(f"✓ Completed {filename}: {original_rows} → {len(df)} rows")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"✗ Error processing {filename}: {error_msg}")

                # Store error
                error_obj = {
                    'name': filename,
                    'path': file_obj.get('path', ''),
                    'error': error_msg,
                    'status': 'error'
                }

                self.errors.append(error_obj)

                # Update progress to error
                if self.progress_callback:
                    self.progress_callback(idx, total_files, filename, 'error')

        # Generate summary
        summary = {
            'total_files': total_files,
            'successful': len(self.results),
            'failed': len(self.errors),
            'total_original_rows': sum(r['original_rows'] for r in self.results),
            'total_final_rows': sum(r['final_rows'] for r in self.results),
            'operations_per_file': self.results[0]['operations_applied'] if self.results else 0
        }

        logger.info(f"Batch processing complete: {summary['successful']} succeeded, {summary['failed']} failed")

        return {
            'successful': self.results,
            'failed': self.errors,
            'summary': summary
        }

    def get_results(self) -> List[Dict]:
        """Get successfully processed files"""
        return self.results

    def get_errors(self) -> List[Dict]:
        """Get files that failed processing"""
        return self.errors

    def has_errors(self) -> bool:
        """Check if any files failed"""
        return len(self.errors) > 0
