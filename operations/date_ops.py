"""Date Operations"""
import pandas as pd
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry

class FormatDateOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='date_format', name='Format Date', category='Dates',
            description='Convert dates to a specific format',
            parameters=[
                Parameter('column', 'column', 'Date column'),
                Parameter('format', 'choice', 'Date format', 
                         choices=['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD'], default='MM/DD/YYYY')
            ],
            excel_equivalent='TEXT(date,"MM/DD/YYYY")',
            examples=['Standardize all dates to MM/DD/YYYY'],
            tags=['date', 'format', 'time']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        col = params['column']
        fmt = params['format']
        df[col] = pd.to_datetime(df[col], errors='coerce')
        format_map = {
            'MM/DD/YYYY': '%m/%d/%Y',
            'DD/MM/YYYY': '%d/%m/%Y',
            'YYYY-MM-DD': '%Y-%m-%d'
        }
        df[col] = df[col].dt.strftime(format_map[fmt])
        return df

registry.register(FormatDateOperation())
