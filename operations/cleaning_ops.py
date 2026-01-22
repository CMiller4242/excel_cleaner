"""
Cleaning Operations  
Remove blanks, fill missing, standardize formats
"""
import pandas as pd
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry


class RemoveBlankRowsOperation(BaseOperation):
    """Remove rows that are completely empty"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='clean_remove_blank_rows',
            name='Remove Blank Rows',
            category='Cleaning',
            description='Remove rows where all cells are empty',
            parameters=[],
            excel_equivalent='Go To Special > Blanks > Delete',
            examples=[
                'Clean up imported data with empty rows',
                'Remove spacer rows from reports'
            ],
            tags=['clean', 'blank', 'empty', 'remove']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        return df.dropna(how='all')


class FillMissingValuesOperation(BaseOperation):
    """Fill missing/blank values"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='clean_fill_missing',
            name='Fill Missing Values',
            category='Cleaning',
            description='Replace blank cells with a specified value',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to fill'
                ),
                Parameter(
                    name='fill_value',
                    type='text',
                    description='Value to use for blank cells',
                    default='N/A'
                )
            ],
            excel_equivalent='Find & Replace (blank cells)',
            examples=[
                'Fill empty phone numbers with "N/A"',
                'Replace missing quantities with 0',
                'Fill blank categories with "Uncategorized"'
            ],
            tags=['fill', 'missing', 'blank', 'na', 'null']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        fill_value = params['fill_value']
        
        for col in columns:
            df[col] = df[col].fillna(fill_value)
        
        return df


class RemoveColumnsOperation(BaseOperation):
    """Delete specified columns"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='clean_remove_columns',
            name='Remove Columns',
            category='Cleaning',
            description='Delete one or more columns from the data',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to remove'
                )
            ],
            excel_equivalent='Delete columns',
            examples=[
                'Remove unnecessary ID columns',
                'Delete temporary calculation columns',
                'Clean up imported data'
            ],
            tags=['delete', 'remove', 'columns', 'clean']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        columns = params['columns']
        return df.drop(columns=columns)


class KeepColumnsOperation(BaseOperation):
    """Keep only selected columns (remove all others)"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='clean_keep_columns',
            name='Keep Columns (Remove Everything Else)',
            category='Cleaning',
            description='Keep only selected columns and remove all others',
            parameters=[
                Parameter(
                    name='columns_to_keep',
                    type='column_list',
                    description='Columns to keep'
                )
            ],
            excel_equivalent='Hide/Delete columns (inverse)',
            examples=[
                'Keep only essential data columns',
                'Remove all but key identifier columns',
                'Simplify dataset to specific fields'
            ],
            tags=['keep', 'select', 'columns', 'filter', 'clean']
        )

    def validate_params(self, df: pd.DataFrame, params: Dict) -> tuple[bool, str]:
        """
        Validate parameters with lenient handling of missing columns.
        Operation proceeds if at least one selected column exists.
        """
        # Check required parameters
        if 'columns_to_keep' not in params:
            return False, "Missing required parameter: columns_to_keep"

        columns_to_keep = params['columns_to_keep']

        # Must select at least one column
        if not columns_to_keep or len(columns_to_keep) == 0:
            return False, "No columns selected. Select at least one column to keep."

        # Calculate intersection with actual DataFrame columns
        keep_existing = [col for col in df.columns if col in columns_to_keep]
        missing = [col for col in columns_to_keep if col not in df.columns]

        # If ALL selected columns are missing, fail validation
        if len(keep_existing) == 0:
            missing_list = ', '.join(missing[:5])
            if len(missing) > 5:
                missing_list += f', ... ({len(missing)} total)'
            return False, f"None of the selected columns exist in the data: {missing_list}"

        # If SOME columns are missing, issue a warning but allow execution
        # Note: This creates a soft warning in logs but doesn't block execution
        if missing:
            import logging
            missing_list = ', '.join(missing[:10])
            if len(missing) > 10:
                missing_list += f' (and {len(missing) - 10} more)'
            logging.warning(
                f"Keep Columns: {len(missing)} selected column(s) not found and will be ignored: {missing_list}"
            )

        return True, ""

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        Keep only the selected columns that exist in the DataFrame.
        Preserves the original DataFrame column order (not selection order).
        """
        columns_to_keep = params['columns_to_keep']

        # Determine which columns to keep (intersection with existing columns)
        # Preserve ORIGINAL DataFrame order (user decision 1A)
        keep_existing = [col for col in df.columns if col in columns_to_keep]

        # Handle edge case: if all selected columns were missing
        # (This shouldn't happen due to validation, but defensive programming)
        if not keep_existing:
            import logging
            logging.error("Keep Columns: No valid columns to keep. Returning empty DataFrame.")
            # Return DataFrame with same index but no columns
            return pd.DataFrame(index=df.index)

        # Return DataFrame with only the kept columns (in original order)
        return df[keep_existing].copy()


registry.register(RemoveBlankRowsOperation())
registry.register(FillMissingValuesOperation())
registry.register(RemoveColumnsOperation())
registry.register(KeepColumnsOperation())
