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


registry.register(RemoveBlankRowsOperation())
registry.register(FillMissingValuesOperation())
registry.register(RemoveColumnsOperation())
