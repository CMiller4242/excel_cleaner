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
import re
import unicodedata
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

    @staticmethod
    def normalize_header(header_value: str) -> str:
        """
        Normalize header for comparison to handle formatting differences

        Handles:
        - Unicode normalization (BOM, non-breaking spaces)
        - Whitespace trimming
        - Quote removal
        - Multiple spaces collapsed to single space
        - Lowercase for case-insensitive comparison

        Args:
            header_value: Raw header string

        Returns:
            Normalized header string
        """
        # Normalize unicode (handles BOM, non-breaking spaces, etc.)
        h = unicodedata.normalize("NFKC", header_value)

        # Strip whitespace and quotes
        h = h.strip().strip('"').strip("'")

        # Collapse multiple spaces → single space
        h = re.sub(r"\s+", " ", h)

        # Lowercase for comparison
        return h.lower()

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

            # Remove trailing empty fields (from trailing delimiters)
            header = [h for h in rows[0] if h or h == '0']  # Keep '0' but remove ''
            if not header and rows[0]:  # If all were empty, keep original
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

        COMBINE_CSV_FIX: Ensure headers match across all files with normalization

        Uses header normalization to handle formatting differences:
        - Quotes, whitespace, BOM, Unicode variations, capitalization

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
                master_header_raw = next(reader)

            # Remove trailing empty fields from first file
            master_header = [h for h in master_header_raw if h or h == '0']
            if not master_header and master_header_raw:
                master_header = master_header_raw

            # Normalize master header for comparison
            master_header_normalized = [self.normalize_header(h) for h in master_header]

            # Validate all other files have the same header
            for file_path in file_paths[1:]:
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter=delimiter, quotechar='"')
                    current_header_raw = next(reader)

                # Remove trailing empty fields
                current_header = [h for h in current_header_raw if h or h == '0']
                if not current_header and current_header_raw:
                    current_header = current_header_raw

                # Normalize current header
                current_header_normalized = [self.normalize_header(h) for h in current_header]

                # Check column count first
                if len(current_header_normalized) != len(master_header_normalized):
                    return False, (
                        f"Column count mismatch detected!\n\n"
                        f"First file has {len(master_header_normalized)} columns\n"
                        f"File '{os.path.basename(file_path)}' has {len(current_header_normalized)} columns\n\n"
                        f"All files must have the same number of columns to combine."
                    ), None

                # Compare normalized headers
                if current_header_normalized != master_header_normalized:
                    # Find which columns differ
                    diff_indices = [i for i in range(len(master_header_normalized))
                                   if master_header_normalized[i] != current_header_normalized[i]]

                    diff_details = []
                    for i in diff_indices[:3]:  # Show first 3 differences
                        diff_details.append(
                            f"  Column {i+1}: '{master_header[i]}' vs '{current_header[i]}'"
                        )

                    return False, (
                        f"Header mismatch detected!\n\n"
                        f"First file has: {', '.join(master_header[:5])}{'...' if len(master_header) > 5 else ''}\n"
                        f"File '{os.path.basename(file_path)}' has: {', '.join(current_header[:5])}{'...' if len(current_header) > 5 else ''}\n\n"
                        f"Differences:\n" + "\n".join(diff_details) +
                        (f"\n  ...and {len(diff_indices) - 3} more" if len(diff_indices) > 3 else "") +
                        f"\n\nAll files must have identical headers to combine."
                    ), None

                # Check if headers differ visually but normalize to same values
                if current_header != master_header:
                    logger.info(f"[CombineMode] Header variation detected but normalized match. Accepting. File: {os.path.basename(file_path)}")

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
        expected_col_count = len(master_header)

        # Read all files and combine data rows (skip header for each file)
        for file_path in file_paths:
            try:
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter=delimiter, quotechar='"')
                    next(reader)  # Skip header
                    rows = list(reader)

                    # Handle rows with trailing delimiters - trim to expected column count
                    cleaned_rows = []
                    for row in rows:
                        # If row has trailing empty fields, trim to expected column count
                        if len(row) > expected_col_count:
                            # Check if extra fields are all empty
                            extra_fields = row[expected_col_count:]
                            if all(not field for field in extra_fields):
                                row = row[:expected_col_count]
                        cleaned_rows.append(row)

                    combined_rows.extend(cleaned_rows)
                    total_rows += len(cleaned_rows)

                logger.info(f"Added {len(cleaned_rows)} rows from {os.path.basename(file_path)}")

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

    # ==================== RAW TEXT LINE-BASED METHODS ====================

    def combine_text_files_raw(self, file_paths: List[str], delimiter: str = ',') -> Tuple[str, List[str], int]:
        """
        Combine multiple text/CSV files using raw line-based processing

        This method:
        - Reads files as raw text lines (no CSV parsing)
        - Keeps ONLY the header from the first file
        - Removes ALL repeated headers from subsequent files
        - Preserves exact formatting, quoting, whitespace, delimiters
        - Handles BOM and Unicode normalization for header detection

        Args:
            file_paths: List of file paths to combine
            delimiter: Delimiter character for detecting repeated headers

        Returns:
            Tuple of (master_header_line, all_data_lines, total_files_processed)
        """
        if not file_paths:
            raise ValueError("No files provided to combine")

        logger.info(f"[CombineMode] Starting raw text combine for {len(file_paths)} files")

        master_header_line = None
        master_header_fields = None
        master_header_normalized = None
        all_data_lines = []

        for file_index, file_path in enumerate(file_paths):
            try:
                # Read file as raw text lines
                with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
                    lines = f.read().splitlines()

                if not lines:
                    logger.warning(f"[CombineMode] Skipping empty file: {os.path.basename(file_path)}")
                    continue

                # First file: extract and store header
                if file_index == 0:
                    master_header_line = lines[0]
                    master_header_fields = self._parse_delimiter_fields(master_header_line, delimiter)
                    master_header_normalized = self._normalize_header_line(master_header_line, delimiter)

                    logger.info(f"[CombineMode] Using header from first file: {os.path.basename(file_path)}")
                    logger.info(f"[CombineMode] Header fields: {master_header_fields[:3]}... ({len(master_header_fields)} total)")

                    # Add all data lines (skip header), filtering blank rows
                    data_lines = lines[1:]
                    non_blank_lines = [line for line in data_lines if not self.is_blank_record(line, delimiter)]
                    all_data_lines.extend(non_blank_lines)

                    blank_count = len(data_lines) - len(non_blank_lines)
                    if blank_count > 0:
                        logger.info(f"[CombineMode] Filtered {blank_count} blank rows from first file")
                    logger.info(f"[CombineMode] Added {len(non_blank_lines)} data rows from first file")

                # Subsequent files: remove repeated headers
                else:
                    current_file_name = os.path.basename(file_path)
                    current_header_line = lines[0]
                    current_header_normalized = self._normalize_header_line(current_header_line, delimiter)

                    # Check if first line is a repeated header
                    if current_header_normalized == master_header_normalized:
                        logger.info(f"[CombineMode] Skipping repeated header in file: {current_file_name}")
                        data_lines = lines[1:]  # Skip header
                    else:
                        # First line is not a header, keep all lines
                        logger.info(f"[CombineMode] No header detected in file (keeping all rows): {current_file_name}")
                        data_lines = lines

                    # Filter out any additional repeated headers and blank rows in the data
                    filtered_lines = []
                    blank_count = 0
                    for line_num, line in enumerate(data_lines, start=2 if current_header_normalized == master_header_normalized else 1):
                        # Check if line is blank
                        if self.is_blank_record(line, delimiter):
                            blank_count += 1
                            continue

                        line_normalized = self._normalize_header_line(line, delimiter)

                        # Check if this line matches the header
                        if line_normalized == master_header_normalized:
                            logger.info(f"[CombineMode] Skipping repeated header at line {line_num} in file: {current_file_name}")
                            continue

                        # Check if line starts with header prefix (for partial header detection)
                        if self._line_starts_with_header_prefix(line, master_header_fields, delimiter):
                            logger.info(f"[CombineMode] Skipping partial header match at line {line_num} in file: {current_file_name}")
                            continue

                        filtered_lines.append(line)

                    all_data_lines.extend(filtered_lines)
                    if blank_count > 0:
                        logger.info(f"[CombineMode] Filtered {blank_count} blank rows from {current_file_name}")
                    logger.info(f"[CombineMode] Added {len(filtered_lines)} data rows from {current_file_name}")

            except Exception as e:
                logger.error(f"[CombineMode] Error reading {os.path.basename(file_path)}: {e}")
                raise

        logger.info(f"[CombineMode] Raw text combine complete: {len(all_data_lines)} total data rows from {len(file_paths)} files")
        return master_header_line, all_data_lines, len(file_paths)

    def _parse_delimiter_fields(self, line: str, delimiter: str) -> List[str]:
        """
        Parse a line into fields based on delimiter

        Simple split - does not handle quoted fields with embedded delimiters
        This is intentional for header prefix matching

        Args:
            line: Text line
            delimiter: Delimiter character

        Returns:
            List of field values
        """
        return [field.strip() for field in line.split(delimiter)]

    def _normalize_header_line(self, line: str, delimiter: str) -> str:
        """
        Normalize a header line for comparison

        Handles BOM, Unicode, quotes, whitespace, capitalization

        Args:
            line: Header line text
            delimiter: Delimiter character

        Returns:
            Normalized line string for comparison
        """
        # Normalize unicode (BOM, non-breaking spaces, etc.)
        normalized = unicodedata.normalize("NFKC", line)

        # Strip whitespace
        normalized = normalized.strip()

        # Remove common quote variations
        normalized = normalized.replace('"', '').replace("'", '')

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)

        # Lowercase for case-insensitive comparison
        normalized = normalized.lower()

        return normalized

    def _line_starts_with_header_prefix(self, line: str, header_fields: List[str],
                                        delimiter: str, prefix_count: int = 2) -> bool:
        """
        Check if a line starts with the same prefix as the header

        This catches partial header fragments like:
        "KC","Cust No",...  (repeated header start)

        Args:
            line: Line to check
            header_fields: Master header fields
            delimiter: Delimiter character
            prefix_count: Number of fields to check (default 2)

        Returns:
            True if line starts with header prefix
        """
        if not header_fields or len(header_fields) < prefix_count:
            return False

        line_fields = self._parse_delimiter_fields(line, delimiter)

        if len(line_fields) < prefix_count:
            return False

        # Normalize and compare first N fields
        header_prefix_normalized = [self.normalize_header(f) for f in header_fields[:prefix_count]]
        line_prefix_normalized = [self.normalize_header(f) for f in line_fields[:prefix_count]]

        return header_prefix_normalized == line_prefix_normalized

    def is_blank_record(self, line: str, delimiter: str) -> bool:
        """
        Check if a line is a blank record

        Detects:
        - Empty or whitespace-only lines
        - Lines with only delimiters (,,,,,)
        - Lines with only empty quoted fields ("","","")

        Args:
            line: Text line to check
            delimiter: Delimiter character

        Returns:
            True if line is blank, False otherwise
        """
        stripped = line.strip()
        if stripped == "":
            return True

        # Split on delimiter and check if all fields are empty
        fields = [f.strip().strip('"').strip("'") for f in stripped.split(delimiter)]
        return all(f == "" for f in fields)

    def export_text_file_raw(self, output_path: str, header_line: str, data_lines: List[str]):
        """
        Export combined text file using raw text writing

        NO formatting changes - exact preservation of original content

        Args:
            output_path: Output file path
            header_line: Header line (from first file)
            data_lines: All data lines
        """
        try:
            # Combine header + data
            all_lines = [header_line] + data_lines

            # Write as raw text with \n line endings
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                f.write('\n'.join(all_lines))

            logger.info(f"[CombineMode] Exported raw text file: {len(data_lines)} data rows to {os.path.basename(output_path)}")

        except Exception as e:
            logger.error(f"[CombineMode] Error exporting text file: {e}")
            raise

    # ==================== END RAW TEXT LINE-BASED METHODS ====================

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
