"""
Combine Mode Handler for Universal Excel Tool
Handles file type detection, delimiter detection, and combining multiple files
"""

import pandas as pd
import os
import chardet
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CombineModeHandler:
    """
    Handler for Combine Mode functionality

    Features:
    - Automatic file type detection (.csv, .txt, .tsv, Excel)
    - Delimiter detection for text files (comma, pipe, tab)
    - Validation of file type and delimiter consistency
    - Sheet selection for Excel files
    - Column alignment and combining
    """

    # Supported file extensions
    TEXT_EXTENSIONS = {'.csv', '.txt', '.tsv'}
    EXCEL_EXTENSIONS = {'.xlsx', '.xls', '.xlsm'}

    def __init__(self):
        self.loaded_files = []  # List of {'name': str, 'path': str, 'df': DataFrame, 'type': str, 'delimiter': str, 'sheet': str}
        self.detected_file_type = None  # 'text' or 'excel'
        self.detected_delimiter = None  # ',' '|' or '\t' for text files

    def detect_file_type(self, file_path: str) -> str:
        """
        Detect file type based on extension

        Args:
            file_path: Path to the file

        Returns:
            'text' for CSV/TXT/TSV, 'excel' for Excel files, or 'unknown'
        """
        ext = Path(file_path).suffix.lower()

        if ext in self.TEXT_EXTENSIONS:
            return 'text'
        elif ext in self.EXCEL_EXTENSIONS:
            return 'excel'
        else:
            return 'unknown'

    def detect_delimiter(self, file_path: str, sample_lines: int = 5) -> Optional[str]:
        """
        Auto-detect delimiter for text files

        Args:
            file_path: Path to text file
            sample_lines: Number of lines to sample

        Returns:
            Detected delimiter: ',' '|' or '\t', or None if detection fails
        """
        try:
            # Read sample of file
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB

            # Detect encoding
            encoding_result = chardet.detect(raw_data)
            encoding = encoding_result['encoding'] or 'utf-8'

            # Read first few lines
            with open(file_path, 'r', encoding=encoding) as f:
                sample = [f.readline() for _ in range(sample_lines)]

            # Count occurrences of common delimiters
            delimiters = {
                ',': sum(line.count(',') for line in sample),
                '|': sum(line.count('|') for line in sample),
                '\t': sum(line.count('\t') for line in sample)
            }

            # Return delimiter with highest count (if > 0)
            if max(delimiters.values()) > 0:
                detected = max(delimiters, key=delimiters.get)
                logger.info(f"Detected delimiter '{detected}' in {os.path.basename(file_path)}")
                return detected
            else:
                logger.warning(f"Could not detect delimiter in {os.path.basename(file_path)}")
                return None

        except Exception as e:
            logger.error(f"Error detecting delimiter: {e}")
            return None

    def load_file_to_dataframe(self, file_path: str, delimiter: Optional[str] = None,
                               sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load file into a pandas DataFrame

        Args:
            file_path: Path to file
            delimiter: Delimiter for text files (auto-detected if None)
            sheet_name: Sheet name for Excel files (first sheet if None)

        Returns:
            pandas DataFrame
        """
        file_type = self.detect_file_type(file_path)

        if file_type == 'text':
            # Detect delimiter if not provided
            if delimiter is None:
                delimiter = self.detect_delimiter(file_path)
                if delimiter is None:
                    raise ValueError(f"Could not detect delimiter for {os.path.basename(file_path)}")

            # Read with detected/provided delimiter
            df = pd.read_csv(file_path, sep=delimiter, encoding='utf-8-sig', engine='python')
            logger.info(f"Loaded text file: {os.path.basename(file_path)} ({len(df)} rows)")

        elif file_type == 'excel':
            # Read Excel file
            if sheet_name is None:
                # Read first sheet
                df = pd.read_excel(file_path, sheet_name=0)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"Loaded Excel file: {os.path.basename(file_path)} ({len(df)} rows)")

        else:
            raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")

        return df

    def get_excel_sheets(self, file_path: str) -> List[str]:
        """
        Get list of sheet names from an Excel file

        Args:
            file_path: Path to Excel file

        Returns:
            List of sheet names
        """
        try:
            xls = pd.ExcelFile(file_path)
            return xls.sheet_names
        except Exception as e:
            logger.error(f"Error reading Excel sheets: {e}")
            return []

    def validate_files(self, file_infos: List[Dict]) -> Tuple[bool, str]:
        """
        Validate that all files can be combined

        Args:
            file_infos: List of dicts with 'path', 'type', 'delimiter', 'sheet'

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(file_infos) < 2:
            return False, "Please select at least 2 files to combine"

        # Check file types are all the same
        file_types = set(info['type'] for info in file_infos)
        if len(file_types) > 1:
            return False, "All files must be the same type (all CSV/TXT or all Excel). Mixed file types cannot be combined."

        # For text files, check delimiters are the same
        if 'text' in file_types:
            delimiters = set(info['delimiter'] for info in file_infos if info['delimiter'])
            if len(delimiters) > 1:
                delim_names = {',': 'comma', '|': 'pipe', '\t': 'tab'}
                delim_list = [delim_names.get(d, d) for d in delimiters]
                return False, f"All files must use the same delimiter to combine. Found: {', '.join(delim_list)}"

        return True, ""

    def align_columns(self, dataframes: List[pd.DataFrame]) -> List[pd.DataFrame]:
        """
        Align columns across all DataFrames

        All columns from all files are included, preserving the order from the first file.
        Missing columns are filled with empty strings.

        Args:
            dataframes: List of DataFrames to align

        Returns:
            List of aligned DataFrames with same columns in same order
        """
        if not dataframes:
            return []

        # Collect all unique columns, preserving first file's order
        all_columns = []
        first_file_columns = dataframes[0].columns.tolist()

        # Start with first file's columns
        all_columns.extend(first_file_columns)

        # Add any new columns from other files
        for df in dataframes[1:]:
            for col in df.columns:
                if col not in all_columns:
                    all_columns.append(col)

        # Reindex all DataFrames to have the same columns
        aligned_dfs = []
        for df in dataframes:
            aligned_df = df.reindex(columns=all_columns, fill_value='')
            aligned_dfs.append(aligned_df)

        logger.info(f"Aligned {len(dataframes)} DataFrames to {len(all_columns)} columns")

        return aligned_dfs

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

        # Align columns first
        aligned_dfs = self.align_columns(dataframes)

        # Concatenate vertically
        combined_df = pd.concat(aligned_dfs, ignore_index=True)

        logger.info(f"Combined {len(dataframes)} files: {len(combined_df)} total rows × {len(combined_df.columns)} columns")

        return combined_df

    def add_file(self, file_path: str, delimiter: Optional[str] = None,
                 sheet_name: Optional[str] = None) -> Dict:
        """
        Add a file to the combine queue

        Args:
            file_path: Path to file
            delimiter: Delimiter for text files
            sheet_name: Sheet name for Excel files

        Returns:
            File info dictionary
        """
        file_type = self.detect_file_type(file_path)

        if file_type == 'unknown':
            raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")

        # Auto-detect delimiter for text files
        if file_type == 'text' and delimiter is None:
            delimiter = self.detect_delimiter(file_path)

        # Load DataFrame
        df = self.load_file_to_dataframe(file_path, delimiter, sheet_name)

        # Create file info
        file_info = {
            'name': os.path.basename(file_path),
            'path': file_path,
            'df': df,
            'type': file_type,
            'delimiter': delimiter if file_type == 'text' else None,
            'sheet': sheet_name if file_type == 'excel' else None,
            'rows': len(df),
            'columns': len(df.columns)
        }

        self.loaded_files.append(file_info)

        # Update detected type and delimiter
        if self.detected_file_type is None:
            self.detected_file_type = file_type
        if file_type == 'text' and self.detected_delimiter is None:
            self.detected_delimiter = delimiter

        return file_info

    def remove_file(self, file_path: str):
        """Remove a file from the combine queue"""
        self.loaded_files = [f for f in self.loaded_files if f['path'] != file_path]

        # Reset detected values if no files left
        if not self.loaded_files:
            self.detected_file_type = None
            self.detected_delimiter = None

    def clear_files(self):
        """Clear all files from the combine queue"""
        self.loaded_files = []
        self.detected_file_type = None
        self.detected_delimiter = None

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
                'total_columns': 0,
                'file_type': None,
                'delimiter': None
            }

        # Count total rows
        total_rows = sum(f['rows'] for f in self.loaded_files)

        # Count unique columns
        all_columns = set()
        for f in self.loaded_files:
            all_columns.update(f['df'].columns)

        # Get delimiter name
        delimiter_name = None
        if self.detected_delimiter:
            delimiter_map = {',': 'comma (,)', '|': 'pipe (|)', '\t': 'tab (\\t)'}
            delimiter_name = delimiter_map.get(self.detected_delimiter, self.detected_delimiter)

        # Get file type name
        file_type_name = None
        if self.detected_file_type == 'text':
            # Determine specific text type from first file
            first_ext = Path(self.loaded_files[0]['path']).suffix.lower()
            if first_ext == '.csv':
                file_type_name = 'CSV'
            elif first_ext == '.tsv':
                file_type_name = 'TSV'
            else:
                file_type_name = 'TXT'
        elif self.detected_file_type == 'excel':
            file_type_name = 'Excel'

        return {
            'file_count': len(self.loaded_files),
            'total_rows': total_rows,
            'total_columns': len(all_columns),
            'file_type': file_type_name,
            'delimiter': delimiter_name
        }
