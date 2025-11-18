"""Validation Operations"""
import pandas as pd
import re
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry

class ValidateEmailOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='validate_email', name='Validate Email Addresses', category='Validation',
            description='Check if email addresses are properly formatted',
            parameters=[
                Parameter('column', 'column', 'Email column'),
                Parameter('flag_invalid', 'boolean', 'Create flag column for invalid emails', default=True)
            ],
            excel_equivalent='Complex IF formula',
            examples=['Flag invalid customer emails'],
            tags=['validate', 'email', 'check']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        col = params['column']
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if params.get('flag_invalid', True):
            df[f'{col}_Valid'] = df[col].astype(str).str.match(pattern)
        
        return df

registry.register(ValidateEmailOperation())
