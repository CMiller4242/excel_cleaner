"""Math Operations"""
import pandas as pd
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry

class AddColumnsOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='math_add_columns', name='Add Columns', category='Math',
            description='Add two or more columns together',
            parameters=[
                Parameter('columns', 'column_list', 'Columns to add'),
                Parameter('new_column', 'text', 'Name for result column')
            ],
            excel_equivalent='=A1+B1', examples=['Add Quantity + Bonus = Total'],
            tags=['add', 'sum', 'math']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        df[params['new_column']] = df[params['columns']].sum(axis=1)
        return df

class MultiplyColumnsOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='math_multiply', name='Multiply Columns', category='Math',
            description='Multiply two columns (e.g., quantity × price)',
            parameters=[
                Parameter('column1', 'column', 'First column'),
                Parameter('column2', 'column', 'Second column'),
                Parameter('new_column', 'text', 'Name for result')
            ],
            excel_equivalent='=A1*B1', examples=['Quantity × Price = Total'],
            tags=['multiply', 'product', 'math']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        df[params['new_column']] = df[params['column1']] * df[params['column2']]
        return df

registry.register(AddColumnsOperation())
registry.register(MultiplyColumnsOperation())
