"""Preview Generator"""
import pandas as pd

class PreviewGenerator:
    """Generate before/after previews"""
    
    @staticmethod
    def generate_preview(df_before: pd.DataFrame, df_after: pd.DataFrame, max_rows: int = 100):
        """
        Generate a preview showing changes
        
        Returns:
            dict with before, after, and changes
        """
        return {
            'before': df_before.head(max_rows),
            'after': df_after.head(max_rows),
            'rows_changed': len(df_after) - len(df_before),
            'columns_changed': list(set(df_after.columns) - set(df_before.columns))
        }
