"""
Combine Mode Handler for Universal Excel Tool
Handles file type detection, delimiter detection, and combining multiple files

COMBINE_CSV_FIX: Uses proper CSV parsing with csv module to preserve exact formatting
"""

import pandas as pd
import os
import chardet
import csv
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

    # ==================== CSV-AWARE METHODS (COMBINE_CSV_FIX) ====================

    def load_csv_with_csv_module(self, file_path: str, delimiter: str = ',') -> Tuple[List[str], List[List[str]]]:
        """
        Load CSV file using csv module for exact format preservation

        COMBINE_CSV_FIX: Use csv.reader instead of pandas to preserve exact formatting

        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter

        Returns:
            Tuple of (header, rows) where rows is list of lists
        """
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=delimiter, quotechar='"')
                rows = list(reader)

            if not rows:
                raise ValueError(f"File {os.path.basename(file_path)} is empty")

            header = rows[0]
            data_rows = rows[1:]

            logger.info(f"CSV-parsed {os.path.basename(file_path)}: {len(data_rows)} rows, {len(header)} columns")
            return header, data_rows

        except Exception as e:
            logger.error(f"Error reading CSV with csv module: {e}")
            raise

    def validate_csv_headers(self, file_paths: List[str], delimiter: str = ',') -> Tuple[bool, str, Optional[List[str]]]:
        """
        Validate that all CSV files have the same header structure

        COMBINE_CSV_FIX: Ensure headers match across all files

        Args:
            file_paths: List of file paths
            delimiter: CSV delimiter

        Returns:
            Tuple of (is_valid, error_message, master_header)
        """
        try:
            # Read first file's header
            with open(file_paths[0], 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=delimiter, quotechar='"')
                master_header = next(reader)

            # Validate all other files have the same header
            for file_path in file_paths[1:]:
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter=delimiter, quotechar='"')
                    current_header = next(reader)

                if current_header != master_header:
                    return False, (
                        f"Header mismatch detected!\n\n"
                        f"First file has: {', '.join(master_header[:5])}{'...' if len(master_header) > 5 else ''}\n"
                        f"File '{os.path.basename(file_path)}' has: {', '.join(current_header[:5])}{'...' if len(current_header) > 5 else ''}\n\n"
                        f"All files must have identical headers to combine."
                    ), None

            logger.info(f"Header validation passed: {len(file_paths)} files with {len(master_header)} columns")
            return True, "", master_header

        except Exception as e:
            return False, f"Error validating headers: {str(e)}", None

    def combine_csv_files_with_csv_module(self, file_paths: List[str], delimiter: str = ',') -> Tuple[List[str], List[List[str]]]:
        """
        Combine multiple CSV files using csv module for exact format preservation

        COMBINE_CSV_FIX: Read all files with csv.reader, write header once, append all data rows

        Args:
            file_paths: List of CSV file paths
            delimiter: CSV delimiter

        Returns:
            Tuple of (header, combined_rows)
        """
        # Validate headers first
        is_valid, error_msg, master_header = self.validate_csv_headers(file_paths, delimiter)
        if not is_valid:
            raise ValueError(error_msg)

        combined_rows = []
        total_rows = 0

        # Read all files and combine data rows (skip header for each file)
        for file_path in file_paths:
            try:
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter=delimiter, quotechar='"')
                    next(reader)  # Skip header
                    rows = list(reader)
                    combined_rows.extend(rows)
                    total_rows += len(rows)

                logger.info(f"Added {len(rows)} rows from {os.path.basename(file_path)}")

            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                raise

        logger.info(f"Combined {len(file_paths)} files: {total_rows} total data rows")
        return master_header, combined_rows

    def export_csv_with_csv_module(self, output_path: str, header: List[str],
                                    rows: List[List[str]], delimiter: str = ','):
        """
        Export combined data using csv.writer for exact format preservation

        COMBINE_CSV_FIX: Use csv.writer to ensure proper quoting, escaping, and formatting

        Args:
            output_path: Output file path
            header: Column headers
            rows: Data rows
            delimiter: CSV delimiter
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)

                # Write header once
                writer.writerow(header)

                # Write all data rows
                for row in rows:
                    writer.writerow(row)

            logger.info(f"Exported CSV with csv.writer: {len(rows)} rows to {os.path.basename(output_path)}")

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            raise

    # ==================== END CSV-AWARE METHODS ====================

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
