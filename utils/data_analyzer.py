"""Data Analyzer - Analyze DataFrame properties"""
import pandas as pd
from typing import Dict

class DataAnalyzer:
    """Analyze data properties"""
    
    @staticmethod
    def analyze(df: pd.DataFrame) -> Dict:
        """Analyze DataFrame and return statistics"""
        return {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing_values': df.isnull().sum().to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'duplicates': df.duplicated().sum()
        }
