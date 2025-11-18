"""Advanced Math Operations - Excel formulas"""
import pandas as pd
import numpy as np
from typing import Dict
from operations.base import BaseOperation, OperationMetadata, Parameter
from operations.registry import registry

class SumOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='math_sum', name='SUM - Total of Multiple Columns', category='Math - Advanced',
            description='Add up values across multiple columns',
            parameters=[
                Parameter('columns', 'column_list', 'Columns to sum'),
                Parameter('new_column', 'text', 'Name for result column')
            ],
            excel_equivalent='SUM(A1:E1)', examples=['Total sales across regions'],
            tags=['sum', 'total', 'add', 'advanced']
        )
    def execute(self, df, params):
        df = df.copy()
        df[params['new_column']] = df[params['columns']].sum(axis=1, numeric_only=True)
        return df

class AverageOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='math_average', name='AVERAGE - Mean of Multiple Columns', category='Math - Advanced',
            description='Calculate average across columns',
            parameters=[
                Parameter('columns', 'column_list', 'Columns to average'),
                Parameter('new_column', 'text', 'Name for result')
            ],
            excel_equivalent='AVERAGE(A1:E1)', examples=['Average score across tests'],
            tags=['average', 'mean', 'advanced']
        )
    def execute(self, df, params):
        df = df.copy()
        df[params['new_column']] = df[params['columns']].mean(axis=1, numeric_only=True)
        return df

class RoundOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='math_round', name='ROUND - Round Numbers', category='Math - Advanced',
            description='Round numbers to specified decimal places',
            parameters=[
                Parameter('column', 'column', 'Column to round'),
                Parameter('decimals', 'number', 'Number of decimal places'),
                Parameter('new_column', 'text', 'Name for result (optional)', required=False)
            ],
            excel_equivalent='ROUND(number, decimals)', examples=['Round currency to 2 decimals'],
            tags=['round', 'decimal', 'advanced']
        )
    def execute(self, df, params):
        df = df.copy()
        col = params['column']
        decimals = int(params['decimals'])
        new_col = params.get('new_column', col)
        df[new_col] = pd.to_numeric(df[col], errors='coerce').round(decimals)
        return df

class PercentageOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='math_percentage', name='Calculate Percentage', category='Math - Advanced',
            description='Calculate what percentage one number is of another',
            parameters=[
                Parameter('numerator_column', 'column', 'Part (numerator)'),
                Parameter('denominator_column', 'column', 'Whole (denominator)'),
                Parameter('new_column', 'text', 'Name for percentage column'),
                Parameter('multiply_by_100', 'boolean', 'Show as 0-100 (not 0-1)', default=True)
            ],
            excel_equivalent='=(A1/B1)*100', examples=['Calculate completion percentage'],
            tags=['percentage', 'percent', 'ratio', 'advanced']
        )
    def execute(self, df, params):
        df = df.copy()
        num = pd.to_numeric(df[params['numerator_column']], errors='coerce')
        denom = pd.to_numeric(df[params['denominator_column']], errors='coerce')
        result = (num / denom)
        if params.get('multiply_by_100', True):
            result = result * 100
        df[params['new_column']] = result.round(2)
        return df

registry.register(SumOperation())
registry.register(AverageOperation())
registry.register(RoundOperation())
registry.register(PercentageOperation())
