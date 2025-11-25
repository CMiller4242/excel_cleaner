"""Conditional Operations"""
import pandas as pd
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry

class FlagIfContainsOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='conditional_flag_contains', name='Flag If Contains', category='Conditional',
            description='Flag rows where a column contains specific text',
            parameters=[
                Parameter('column', 'column', 'Column to check'),
                Parameter('text', 'text', 'Text to search for'),
                Parameter('flag_column', 'text', 'Name for flag column', required=False, default='Flag')
            ],
            excel_equivalent='=IF(ISNUMBER(SEARCH(...)))',
            examples=['Flag companies containing "LLC"', 'Flag PO Box addresses'],
            tags=['flag', 'conditional', 'contains', 'if']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        df[params['flag_column']] = df[params['column']].astype(str).str.contains(
            params['text'], case=False, na=False
        )
        return df

registry.register(FlagIfContainsOperation())
