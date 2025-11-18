"""Column Detector - Smart column name detection"""
import pandas as pd
from typing import List, Dict

class ColumnDetector:
    """Detect column types and suggest operations"""
    
    PATTERNS = {
        'email': ['email', 'e-mail', 'mail'],
        'phone': ['phone', 'tel', 'mobile', 'cell'],
        'name': ['name', 'first', 'last', 'contact'],
        'address': ['address', 'street', 'city', 'state', 'zip'],
        'date': ['date', 'time', 'created', 'updated'],
        'amount': ['price', 'cost', 'amount', 'total', 'sum']
    }
    
    @classmethod
    def detect_column_types(cls, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Detect what type each column likely is"""
        results = {}
        
        for col in df.columns:
            col_lower = col.lower()
            for type_name, patterns in cls.PATTERNS.items():
                if any(pattern in col_lower for pattern in patterns):
                    if type_name not in results:
                        results[type_name] = []
                    results[type_name].append(col)
        
        return results
