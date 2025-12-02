"""Export Helper - Export results to files"""
import pandas as pd
from pathlib import Path

class ExportHelper:
    """Helper for exporting results"""
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame, filepath: str, sheet_name: str = 'Sheet1'):
        """Export DataFrame to Excel"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame, filepath: str):
        """Export DataFrame to CSV"""
        df.to_csv(filepath, index=False)

    @staticmethod
    def export_to_txt(df: pd.DataFrame, filepath: str, include_header: bool = True):
        """
        Export DataFrame to TXT with quoted comma-delimited format

        Args:
            df: DataFrame to export
            filepath: Output file path
            include_header: Whether to include header row (default True)

        Format: "value1","value2","value3"
        - Field delimiter: Comma (,)
        - Text qualifier: Double quotes (")
        - All values are quoted
        """
        df.to_csv(
            filepath,
            index=False,
            header=include_header,
            quoting=1,  # QUOTE_ALL - quote all fields
            quotechar='"',
            sep=','
        )

    @staticmethod
    def export_multiple_sheets(dataframes: dict, filepath: str):
        """Export multiple DataFrames to Excel sheets"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
