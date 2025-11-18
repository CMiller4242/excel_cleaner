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


# Register all operations
registry.register(VLookupOperation())
registry.register(RemoveDuplicatesOperation())
registry.register(SortDataOperation())
