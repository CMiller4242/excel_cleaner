"""Validator - Validate operations before execution"""
import logging
import pandas as pd
from typing import List, Dict, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from operations.registry import registry

# Import Issue class for non-fatal validation
try:
    from workbook_session import Issue
except ImportError:
    Issue = None  # Fallback if not available


class Validator:
    """Validate operations and parameters"""

    @staticmethod
    def validate_queue(df: pd.DataFrame, operations: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate a queue of operations using pipeline-aware schema accumulation.

        Each operation is validated against the dataframe produced by all prior
        *valid* operations, so columns created earlier in the workflow are visible
        to later operations.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        result_df = df.copy()

        logging.debug("[VALIDATION] validate_queue: starting with columns=%s", list(result_df.columns))

        for i, op_config in enumerate(operations):
            if not op_config.get('enabled', True):
                continue

            operation_id = op_config.get('operation_id')
            params = op_config.get('parameters', {})

            # Check operation exists
            operation = registry.get_by_id(operation_id)
            if not operation:
                errors.append(f"Operation not found: {operation_id}")
                continue

            logging.debug(
                "[PIPELINE] Before op %d '%s': columns=%s",
                i, operation.metadata.name, list(result_df.columns)
            )

            # Validate against the ACCUMULATED schema (after all prior valid ops)
            is_valid, error = operation.validate_params(result_df, params)
            if not is_valid:
                errors.append(f"{operation.metadata.name}: {error}")
                # Skip advancing result_df — invalid op produces no schema change
                continue

            # Advance accumulated schema so downstream ops can see new columns
            try:
                result_df = operation.execute(result_df, params)
                logging.debug(
                    "[PIPELINE] After op %d '%s': columns=%s",
                    i, operation.metadata.name, list(result_df.columns)
                )
            except Exception as exc:
                # Execution failed during validation dry-run; don't advance schema
                logging.warning(
                    "[PIPELINE] op %d '%s' failed during schema dry-run: %s",
                    i, operation.metadata.name, exc
                )

        return len(errors) == 0, errors

    @staticmethod
    def validate_queue_non_fatal(df: pd.DataFrame, operations: List[Dict], sheet_name: str = "Sheet") -> List:
        """
        Validate a queue of operations in non-fatal mode using pipeline-aware
        schema accumulation.

        Each operation is validated against the dataframe produced by all prior
        *valid* operations, so columns created earlier in the workflow are visible
        to later operations.  Records issues but allows execution to continue.

        Args:
            df: DataFrame to validate against
            operations: List of operation configs
            sheet_name: Name of the sheet being validated

        Returns:
            List of Issue objects (empty if no issues)
        """
        issues = []

        if Issue is None:
            # Fallback to fatal validation if Issue class not available
            Validator.validate_queue(df, operations)
            return issues

        result_df = df.copy()

        logging.debug(
            "[VALIDATION] validate_queue_non_fatal: starting with columns=%s", list(result_df.columns)
        )

        for i, op_config in enumerate(operations):
            if not op_config.get('enabled', True):
                continue

            operation_id = op_config.get('operation_id')
            params = op_config.get('parameters', {})
            op_name = op_config.get('name', 'Unknown Operation')

            # Check operation exists
            operation = registry.get_by_id(operation_id)
            if not operation:
                issue = Issue(
                    sheet_name=sheet_name,
                    op_index=i,
                    op_label=op_name,
                    code='OPERATION_NOT_FOUND',
                    message=f"Operation not found: {operation_id}",
                    details={'operation_id': operation_id}
                )
                issues.append(issue)
                continue

            logging.debug(
                "[PIPELINE] Before op %d '%s': columns=%s",
                i, operation.metadata.name, list(result_df.columns)
            )

            # Validate against ACCUMULATED schema
            is_valid, error = operation.validate_params(result_df, params)
            if not is_valid:
                issue = Issue(
                    sheet_name=sheet_name,
                    op_index=i,
                    op_label=operation.metadata.name,
                    code='INVALID_PARAMETERS',
                    message=error,
                    details={'parameters': params}
                )
                issues.append(issue)
                # Don't advance schema for invalid ops
                continue

            # Advance accumulated schema so downstream ops can see new columns
            try:
                result_df = operation.execute(result_df, params)
                logging.debug(
                    "[PIPELINE] After op %d '%s': columns=%s",
                    i, operation.metadata.name, list(result_df.columns)
                )
            except Exception as exc:
                logging.warning(
                    "[PIPELINE] op %d '%s' failed during schema dry-run: %s",
                    i, operation.metadata.name, exc
                )

        return issues
