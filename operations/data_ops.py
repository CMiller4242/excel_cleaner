"""
Data Operations
VLOOKUP, merge, join, sort, filter, deduplicate
"""
import pandas as pd
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry


class VLookupOperation(BaseOperation):
    """Lookup values from another file"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_vlookup',
            name='Lookup Values from Another File',
            category='Data Matching',
            description='Find and retrieve values from another spreadsheet based on a matching column',
            parameters=[
                Parameter(
                    name='lookup_column',
                    type='column',
                    description='Column to match on in your data'
                ),
                Parameter(
                    name='lookup_file',
                    type='file',
                    description='File to search in (CSV or Excel)'
                ),
                Parameter(
                    name='lookup_file_column',
                    type='text',
                    description='Column name in lookup file to match'
                ),
                Parameter(
                    name='return_column',
                    type='text',
                    description='Column to retrieve from lookup file'
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for the new column in your data'
                )
            ],
            excel_equivalent='VLOOKUP()',
            examples=[
                'Get pricing from master price list using product code',
                'Find customer details using customer ID',
                'Retrieve employee info using badge number'
            ],
            tags=['vlookup', 'lookup', 'merge', 'match', 'join']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        
        # Load lookup file
        lookup_file = params['lookup_file']
        if lookup_file.endswith('.csv'):
            lookup_df = pd.read_csv(lookup_file)
        else:
            lookup_df = pd.read_excel(lookup_file)
        
        # Perform merge (like VLOOKUP)
        lookup_col = params['lookup_column']
        lookup_file_col = params['lookup_file_column']
        return_col = params['return_column']
        new_col = params['new_column']
        
        # Merge and rename
        merged = df.merge(
            lookup_df[[lookup_file_col, return_col]],
            left_on=lookup_col,
            right_on=lookup_file_col,
            how='left'
        )
        
        merged[new_col] = merged[return_col]
        merged = merged.drop(columns=[return_col, lookup_file_col], errors='ignore')
        
        return merged


class RemoveDuplicatesOperation(BaseOperation):
    """Remove duplicate rows"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_remove_duplicates',
            name='Remove Duplicate Rows',
            category='Data Matching',
            description='Remove duplicate records based on one or more columns',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to check for duplicates (empty = check all columns)'
                ),
                Parameter(
                    name='keep',
                    type='choice',
                    description='Which duplicate to keep',
                    choices=['first', 'last'],
                    default='first'
                )
            ],
            excel_equivalent='Remove Duplicates',
            examples=[
                'Remove duplicate customers by Customer ID',
                'Remove duplicate emails from contact list',
                'Keep only unique product codes'
            ],
            tags=['duplicates', 'unique', 'dedupe', 'remove']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        columns = params.get('columns', [])
        keep = self.get_param_value(params, 'keep', 'first')
        
        if not columns:
            columns = None  # Check all columns
        
        return df.drop_duplicates(subset=columns, keep=keep)


class SortDataOperation(BaseOperation):
    """Sort data by columns"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_sort',
            name='Sort Data',
            category='Data Matching',
            description='Sort rows by one or more columns',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to sort by (in order of priority)'
                ),
                Parameter(
                    name='ascending',
                    type='boolean',
                    description='Sort from small to large (A-Z, 1-9)',
                    default=True
                )
            ],
            excel_equivalent='Sort A-Z or Sort Z-A',
            examples=[
                'Sort by date (newest first)',
                'Sort by customer name alphabetically',
                'Sort by amount (highest first)'
            ],
            tags=['sort', 'order', 'arrange', 'alphabetical']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        columns = params['columns']
        ascending = self.get_param_value(params, 'ascending', True)
        
        return df.sort_values(by=columns, ascending=ascending)


class RemoveRowsIfOperation(BaseOperation):
    """Remove rows based on conditions"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_remove_rows_if',
            name='Remove Rows If',
            category='Data Matching',
            description='Remove rows that match specified conditions',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column to check'
                ),
                Parameter(
                    name='condition',
                    type='choice',
                    description='Condition to match',
                    choices=['is_blank', 'contains', 'equals', 'not_equals', 'is_false'],
                    default='is_blank'
                ),
                Parameter(
                    name='value',
                    type='text',
                    description='Value to match (not needed for is_blank or is_false)',
                    required=False,
                    default=''
                ),
                Parameter(
                    name='case_sensitive',
                    type='boolean',
                    description='Match case exactly (for contains/equals)',
                    required=False,
                    default=False
                ),
                Parameter(
                    name='enhanced_blank_detection',
                    type='boolean',
                    description='Enhanced blank detection: Also treats empty strings and N/A variants as blank (for is_blank condition only)',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='Filter and Delete',
            examples=[
                'Remove rows where Email is blank',
                'Remove rows where Address contains "PO Box"',
                'Remove rows where Email_Valid is FALSE',
                'Remove rows where Status equals "Invalid"'
            ],
            tags=['remove', 'filter', 'delete', 'rows', 'conditional']
        )

    def _is_blank_enhanced(self, value) -> bool:
        """
        Enhanced blank detection that treats the following as blank:
        - NaN / None / pd.NaT
        - Empty strings ("")
        - Whitespace-only strings ("   ")
        - N/A variants: "n/a", "na", "null", "none" (case-insensitive)

        Returns True if value should be considered blank, False otherwise.
        """
        # Check for actual NaN/None first
        if value is None or pd.isna(value):
            return True

        # Check for string-based blanks
        if isinstance(value, str):
            cleaned = value.strip().lower()
            if cleaned in ["", "n/a", "na", "null", "none"]:
                return True

        return False

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        column = params['column']
        condition = params['condition']
        value = self.get_param_value(params, 'value', '')
        case_sensitive = self.get_param_value(params, 'case_sensitive', False)
        enhanced_blank = self.get_param_value(params, 'enhanced_blank_detection', False)

        # Create mask for rows to KEEP (inverse of remove)
        if condition == 'is_blank':
            # Keep rows that are NOT blank
            if enhanced_blank:
                # Enhanced mode: Also treats empty strings and N/A variants as blank
                # Useful for datasets with "N/A" strings or empty string placeholders
                mask = ~df[column].apply(self._is_blank_enhanced)
            else:
                # Standard mode (default): Only check for actual NaN/None values using pd.isna()
                # This is simpler, faster, and works correctly for most datasets
                # If you need to remove empty strings, use Remove Rows Containing operation instead
                mask = ~df[column].isna()

        elif condition == 'contains':
            # Keep rows that do NOT contain the value
            if case_sensitive:
                mask = ~df[column].astype(str).str.contains(value, na=False, regex=False)
            else:
                mask = ~df[column].astype(str).str.contains(value, case=False, na=False, regex=False)

        elif condition == 'equals':
            # Keep rows that do NOT equal the value
            if case_sensitive:
                mask = df[column].astype(str) != value
            else:
                mask = df[column].astype(str).str.lower() != value.lower()

        elif condition == 'not_equals':
            # Keep rows that DO equal the value (double negative)
            if case_sensitive:
                mask = df[column].astype(str) == value
            else:
                mask = df[column].astype(str).str.lower() == value.lower()

        elif condition == 'is_false':
            # Keep rows that are NOT False (True or other values)
            # Handle boolean columns
            mask = ~(df[column].astype(str).str.lower().isin(['false', '0', 'no', 'n']))

        else:
            # Default: keep all rows
            mask = pd.Series([True] * len(df), index=df.index)

        # Return filtered dataframe WITHOUT reset_index
        # The executor needs original indices to track which rows were removed
        return df[mask]


class ReorderColumnsOperation(BaseOperation):
    """Reorder columns to specific sequence"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_reorder_columns',
            name='Reorder Columns',
            category='Data - Organization',
            description='Reorder columns to a specific sequence',
            parameters=[
                Parameter(
                    name='column_order',
                    type='list',
                    description='Ordered list of column names (comma-separated)',
                    required=True
                ),
                Parameter(
                    name='keep_unlisted',
                    type='boolean',
                    description='Keep columns not in the list (add them at the end)',
                    default=False
                )
            ],
            excel_equivalent='Drag columns manually',
            examples=[
                'Put Company, Contact, Email first',
                'Reorder to standard mailing list format',
                'Move ID columns to the end'
            ],
            tags=['reorder', 'organize', 'sort', 'columns']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()

        # Parse column order
        column_order = params['column_order']
        if isinstance(column_order, str):
            column_order = [col.strip() for col in column_order.split(',')]

        keep_unlisted = params.get('keep_unlisted', False)

        # Filter to columns that actually exist
        existing_ordered = [col for col in column_order if col in df.columns]

        if keep_unlisted:
            # Add any columns not in the list to the end
            unlisted_cols = [col for col in df.columns if col not in column_order]
            final_order = existing_ordered + unlisted_cols
        else:
            # Only keep columns in the specified order
            final_order = existing_ordered

        # Reorder
        df = df[final_order]

        return df


# Register all operations
registry.register(VLookupOperation())
registry.register(RemoveDuplicatesOperation())
registry.register(SortDataOperation())
registry.register(RemoveRowsIfOperation())
registry.register(ReorderColumnsOperation())
