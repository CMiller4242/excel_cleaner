"""
Combine Pivot Engine for Universal Excel Tool
Handles combining CSV and XLSX files into pivot-ready datasets

Features:
- Load CSV files with auto-delimiter detection
- Load Excel files with sheet selection
- Validate headers and column counts
- Normalize columns with optional header matching rules
- Combine DataFrames
- Export to CSV or XLSX
"""

import pandas as pd
import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CombinePivotEngine:
    """
    Engine for combining CSV and Excel files into unified datasets
    """

    def __init__(self):
        self.loaded_files = []  # List of {'name', 'path', 'df', 'type', 'delimiter', 'sheet', 'rows', 'columns', 'headers'}
        self.normalize_lowercase = False
        self.normalize_whitespace = True

    def detect_csv_delimiter(self, file_path: str, sample_lines: int = 5) -> str:
        """
        Auto-detect delimiter for CSV files

        Args:
            file_path: Path to CSV file
            sample_lines: Number of lines to sample

        Returns:
            Detected delimiter: ',', ';', or '\t'
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                sample = [f.readline() for _ in range(sample_lines)]

            # Count occurrences of common delimiters
            delimiters = {
                ',': sum(line.count(',') for line in sample),
                ';': sum(line.count(';') for line in sample),
                '\t': sum(line.count('\t') for line in sample)
            }

            detected = max(delimiters, key=delimiters.get)
            logger.info(f"[CombinePivot] Detected delimiter '{detected}' in {os.path.basename(file_path)}")
            return detected

        except Exception as e:
            logger.error(f"[CombinePivot] Error detecting delimiter: {e}")
            return ','  # Default to comma

    def load_csv(self, file_path: str, delimiter: Optional[str] = None) -> pd.DataFrame:
        """
        Load CSV file into DataFrame

        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter (auto-detected if None)

        Returns:
            pandas DataFrame
        """
        try:
            # Auto-detect delimiter if not provided
            if delimiter is None:
                delimiter = self.detect_csv_delimiter(file_path)

            # Read CSV
            df = pd.read_csv(file_path, sep=delimiter, encoding='utf-8-sig', engine='python')

            # Remove completely blank rows
            df = df.dropna(how='all')

            # Remove trailing empty columns
            df = self._trim_trailing_empty_columns(df)

            logger.info(f"[CombinePivot] Loaded CSV: {os.path.basename(file_path)} ({len(df)} rows, {len(df.columns)} columns)")
            return df

        except Exception as e:
            logger.error(f"[CombinePivot] Error loading CSV: {e}")
            raise

    def load_excel(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load Excel file sheet into DataFrame

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to read (first sheet if None)

        Returns:
            pandas DataFrame
        """
        try:
            # Read Excel sheet
            if sheet_name is None:
                df = pd.read_excel(file_path, sheet_name=0)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Remove completely blank rows
            df = df.dropna(how='all')

            # Remove trailing empty columns
            df = self._trim_trailing_empty_columns(df)

            logger.info(f"[CombinePivot] Loaded Excel: {os.path.basename(file_path)}, sheet '{sheet_name or 'first'}' ({len(df)} rows, {len(df.columns)} columns)")
            return df

        except Exception as e:
            logger.error(f"[CombinePivot] Error loading Excel: {e}")
            raise

    def get_excel_sheets(self, file_path: str) -> List[str]:
        """
        Get list of sheet names from Excel file

        Args:
            file_path: Path to Excel file

        Returns:
            List of sheet names
        """
        try:
            xls = pd.ExcelFile(file_path)
            return xls.sheet_names
        except Exception as e:
            logger.error(f"[CombinePivot] Error reading Excel sheets: {e}")
            return []

    def _trim_trailing_empty_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove trailing columns that are completely empty

        Args:
            df: DataFrame to trim

        Returns:
            Trimmed DataFrame
        """
        # Find columns that are completely empty
        empty_cols = df.columns[df.isna().all()].tolist()

        # Only remove trailing empty columns (from the end)
        cols_to_remove = []
        for col in reversed(df.columns):
            if col in empty_cols:
                cols_to_remove.append(col)
            else:
                break  # Stop when we hit a non-empty column

        if cols_to_remove:
            df = df.drop(columns=cols_to_remove)
            logger.info(f"[CombinePivot] Trimmed {len(cols_to_remove)} trailing empty columns")

        return df

    def normalize_header(self, header: str) -> str:
        """
        Normalize header for comparison

        Args:
            header: Header string

        Returns:
            Normalized header string
        """
        normalized = str(header)

        if self.normalize_whitespace:
            normalized = normalized.strip()

        if self.normalize_lowercase:
            normalized = normalized.lower()

        return normalized

    def validate_headers(self, dataframes: List[pd.DataFrame]) -> Tuple[bool, str]:
        """
        Validate that all DataFrames have identical headers and column counts

        Args:
            dataframes: List of DataFrames to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not dataframes:
            return False, "No files loaded"

        if len(dataframes) == 1:
            return True, ""

        # Get master headers from first file
        master_headers = [self.normalize_header(h) for h in dataframes[0].columns.tolist()]
        master_count = len(master_headers)

        # Validate all other files
        for i, df in enumerate(dataframes[1:], start=2):
            current_headers = [self.normalize_header(h) for h in df.columns.tolist()]
            current_count = len(current_headers)

            # Check column count
            if current_count != master_count:
                return False, (
                    f"Column count mismatch detected!\n\n"
                    f"File 1 has {master_count} columns\n"
                    f"File {i} has {current_count} columns\n\n"
                    f"All files must have the same number of columns."
                )

            # Check header names
            if current_headers != master_headers:
                # Find differences
                diff_indices = [idx for idx in range(len(master_headers))
                               if master_headers[idx] != current_headers[idx]]

                diff_details = []
                for idx in diff_indices[:5]:  # Show first 5 differences
                    diff_details.append(
                        f"  Column {idx+1}: '{dataframes[0].columns[idx]}' vs '{df.columns[idx]}'"
                    )

                return False, (
                    f"Header mismatch detected!\n\n"
                    f"File 1 headers: {', '.join([str(h) for h in dataframes[0].columns[:5].tolist()])}{'...' if master_count > 5 else ''}\n"
                    f"File {i} headers: {', '.join([str(h) for h in df.columns[:5].tolist()])}{'...' if current_count > 5 else ''}\n\n"
                    f"Differences:\n" + "\n".join(diff_details) +
                    (f"\n  ...and {len(diff_indices) - 5} more" if len(diff_indices) > 5 else "") +
                    f"\n\nAll files must have identical headers to combine."
                )

        logger.info(f"[CombinePivot] Header validation passed: {len(dataframes)} files with {master_count} columns")
        return True, ""

    def combine_dataframes(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Combine multiple DataFrames vertically

        Args:
            dataframes: List of DataFrames to combine

        Returns:
            Combined DataFrame
        """
        if not dataframes:
            return pd.DataFrame()

        # Combine vertically with reset index
        combined_df = pd.concat(dataframes, ignore_index=True)

        # Remove any blank rows that may have been introduced
        combined_df = combined_df.dropna(how='all')

        logger.info(f"[CombinePivot] Combined {len(dataframes)} files: {len(combined_df)} total rows × {len(combined_df.columns)} columns")

        return combined_df

    def export_csv(self, df: pd.DataFrame, output_path: str):
        """
        Export DataFrame to CSV

        Args:
            df: DataFrame to export
            output_path: Output file path
        """
        try:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"[CombinePivot] Exported CSV: {len(df)} rows to {os.path.basename(output_path)}")
        except Exception as e:
            logger.error(f"[CombinePivot] Error exporting CSV: {e}")
            raise

    def export_excel(self, df: pd.DataFrame, output_path: str):
        """
        Export DataFrame to Excel

        Args:
            df: DataFrame to export
            output_path: Output file path
        """
        try:
            df.to_excel(output_path, index=False, engine='openpyxl')
            logger.info(f"[CombinePivot] Exported Excel: {len(df)} rows to {os.path.basename(output_path)}")
        except Exception as e:
            logger.error(f"[CombinePivot] Error exporting Excel: {e}")
            raise

    def add_file(self, file_path: str, sheet_name: Optional[str] = None) -> Dict:
        """
        Add a file to the combine queue

        Args:
            file_path: Path to file
            sheet_name: Sheet name for Excel files (first sheet if None)

        Returns:
            File info dictionary
        """
        ext = Path(file_path).suffix.lower()

        # Load file based on type
        if ext in ['.csv', '.txt', '.tsv']:
            file_type = 'csv'
            delimiter = self.detect_csv_delimiter(file_path)
            df = self.load_csv(file_path, delimiter)
        elif ext in ['.xlsx', '.xls', '.xlsm']:
            file_type = 'excel'
            delimiter = None
            df = self.load_excel(file_path, sheet_name)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # Create file info
        file_info = {
            'name': os.path.basename(file_path),
            'path': file_path,
            'df': df,
            'type': file_type,
            'delimiter': delimiter,
            'sheet': sheet_name,
            'rows': len(df),
            'columns': len(df.columns),
            'headers': df.columns.tolist()
        }

        self.loaded_files.append(file_info)
        logger.info(f"[CombinePivot] Added file: {file_info['name']} ({file_info['rows']} rows, {file_info['columns']} columns)")

        return file_info

    def remove_file(self, file_path: str):
        """Remove a file from the combine queue"""
        self.loaded_files = [f for f in self.loaded_files if f['path'] != file_path]
        logger.info(f"[CombinePivot] Removed file from queue")

    def clear_files(self):
        """Clear all files from the combine queue"""
        self.loaded_files = []
        logger.info(f"[CombinePivot] Cleared all files")

    def get_summary(self) -> Dict:
        """
        Get summary of files to be combined

        Returns:
            Dictionary with summary information
        """
        if not self.loaded_files:
            return {
                'file_count': 0,
                'total_rows': 0,
                'column_count': 0,
                'headers': []
            }

        total_rows = sum(f['rows'] for f in self.loaded_files)

        # All files should have same columns after validation
        column_count = self.loaded_files[0]['columns']
        headers = self.loaded_files[0]['headers']

        return {
            'file_count': len(self.loaded_files),
            'total_rows': total_rows,
            'column_count': column_count,
            'headers': headers
        }
