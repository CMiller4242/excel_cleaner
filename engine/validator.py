"""Validator - Validate operations before execution"""
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

    @staticmethod
    def validate_queue_non_fatal(df: pd.DataFrame, operations: List[Dict], sheet_name: str = "Sheet") -> List:
        """
        Validate a queue of operations in non-fatal mode
        Records issues but allows execution to continue

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
            is_valid, errors = Validator.validate_queue(df, operations)
            return issues

        for i, op_config in enumerate(operations):
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

            # Validate parameters
            is_valid, error = operation.validate_params(df, params)
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

        return issues

    @staticmethod
    def validate_sheets_dry_run(workbook_session, sheet_names: List[str]) -> Dict[str, List]:
        """
        Perform validation dry-run on multiple sheets without mutating results

        Args:
            workbook_session: WorkbookSession instance
            sheet_names: List of sheet names to validate

        Returns:
            Dict mapping sheet_name -> List[Issue]
        """
        from datetime import datetime

        validation_results = {}

        for sheet_name in sheet_names:
            sheet_state = workbook_session.get_sheet(sheet_name)
            if not sheet_state:
                continue

            # Get dataframe (lazy load if needed)
            df = sheet_state.df_original
            if df is None or df.empty:
                # Try to load if not loaded
                if not sheet_state.is_loaded and workbook_session.is_excel:
                    # Sheet not loaded yet - skip validation
                    continue
                else:
                    # No data available
                    continue

            # Clear previous issues
            sheet_state.clear_issues()

            # Run validation
            issues = Validator.validate_queue_non_fatal(
                df,
                sheet_state.operations,
                sheet_state.sheet_name_display
            )

            # Store issues in sheet state
            sheet_state.issues = issues

            # Update run metadata
            sheet_state.last_action = "validate"
            sheet_state.last_run_at = datetime.now().isoformat()
            sheet_state.last_run_before_rows = len(df)
            sheet_state.last_run_ops_total = len(sheet_state.operations)
            sheet_state.last_run_ops_skipped = len(issues)  # Each issue represents a potential skip
            # Don't update after_rows or removed_count for validate-only

            validation_results[sheet_name] = issues

        return validation_results
