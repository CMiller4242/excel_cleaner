"""
File Conversion Utilities for Combine Mode
Converts files between CSV and XLSX formats safely using pandas.

Supported conversions:
- CSV / TXT / TSV  →  CSV  (re-encode with UTF-8, comma delimiter)
- CSV / TXT / TSV  →  XLSX (single-sheet workbook)
- XLSX / XLS / XLSM  →  CSV  (one sheet; requires sheet_name if multi-sheet)
- XLSX / XLS / XLSM  →  XLSX (re-save selected sheet as new single-sheet workbook)

Output files are placed next to the original with a predictable suffix so they
can be identified and cleaned up after a session.

Examples:
    contacts.xlsx        → contacts__Sheet1__converted.csv
    orders.xlsx (Sheet2) → orders__Sheet2__converted.csv
    data.csv             → data__converted.xlsx
    archive.txt          → archive__converted.csv
"""

import os
import logging
import chardet
import pandas as pd
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Extensions grouped by logical type
TEXT_EXTENSIONS = {'.csv', '.txt', '.tsv'}
EXCEL_EXTENSIONS = {'.xlsx', '.xls', '.xlsm'}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _converted_path(original_path: str, target_ext: str,
                    sheet_name: Optional[str] = None) -> str:
    """
    Build a predictable output path for a converted file.

    Args:
        original_path: Source file path
        target_ext: Target extension including dot, e.g. '.csv'
        sheet_name: Optional sheet name to embed in the filename

    Returns:
        Absolute path string for the converted file
    """
    p = Path(original_path)
    if sheet_name:
        # Sanitise sheet name for use in filename
        safe_sheet = sheet_name.replace('/', '_').replace('\\', '_').replace(':', '_')
        stem = f"{p.stem}__{safe_sheet}__converted"
    else:
        stem = f"{p.stem}__converted"
    return str(p.parent / (stem + target_ext))


def _detect_encoding(file_path: str) -> str:
    """Detect file encoding using chardet; fall back to utf-8-sig."""
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(20000)
        result = chardet.detect(raw)
        return result.get('encoding') or 'utf-8-sig'
    except Exception:
        return 'utf-8-sig'


def _load_text_file(file_path: str) -> pd.DataFrame:
    """Load CSV / TXT / TSV into a DataFrame, auto-detecting encoding."""
    encoding = _detect_encoding(file_path)
    ext = Path(file_path).suffix.lower()
    # For TSV default to tab, otherwise let pandas sniff via python engine
    if ext == '.tsv':
        sep = '\t'
    else:
        sep = None  # pandas python engine will sniff
    try:
        df = pd.read_csv(file_path, sep=sep, encoding=encoding, engine='python')
    except UnicodeDecodeError:
        # Retry with latin-1 as last resort
        df = pd.read_csv(file_path, sep=sep, encoding='latin-1', engine='python')
    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def convert_file_to_csv(path: str,
                        selected_sheet: Optional[str] = None) -> str:
    """
    Convert a file to CSV format.

    Conversion rules:
    - Excel (xlsx/xls/xlsm): read the specified sheet (or sheet index 0 if
      selected_sheet is None) and write as UTF-8 CSV.
    - Text (csv/txt/tsv): re-read with encoding detection and write as
      UTF-8 CSV with comma delimiter.

    Args:
        path: Absolute path to the source file.
        selected_sheet: Sheet name for Excel files.  If omitted the first
                        sheet is used.  Ignored for text files.

    Returns:
        Absolute path to the newly created CSV file.

    Raises:
        ValueError: Unsupported extension.
        Exception:  Any read / write error is re-raised after logging.
    """
    ext = Path(path).suffix.lower()

    try:
        if ext in EXCEL_EXTENSIONS:
            sheet = selected_sheet if selected_sheet else 0
            df = pd.read_excel(path, sheet_name=sheet)
            out_path = _converted_path(path, '.csv', selected_sheet)
        elif ext in TEXT_EXTENSIONS:
            df = _load_text_file(path)
            out_path = _converted_path(path, '.csv')
        else:
            raise ValueError(f"Unsupported file type for conversion to CSV: '{ext}'")

        df.to_csv(out_path, index=False, encoding='utf-8')
        logger.info(
            f"[FileConversion] Converted '{os.path.basename(path)}' "
            f"→ '{os.path.basename(out_path)}' "
            f"({len(df)} rows, {len(df.columns)} cols)"
        )
        return out_path

    except Exception as e:
        logger.error(f"[FileConversion] convert_file_to_csv failed for '{path}': {e}")
        raise


def convert_file_to_xlsx(path: str,
                         selected_sheet: Optional[str] = None) -> str:
    """
    Convert a file to XLSX format.

    Conversion rules:
    - Text (csv/txt/tsv): read with encoding detection and write as a
      single-sheet XLSX workbook.
    - Excel (xlsx/xls/xlsm): read the specified sheet (or sheet index 0)
      and write as a new single-sheet XLSX workbook.  Useful for stripping
      a specific sheet from a multi-sheet workbook.

    Args:
        path: Absolute path to the source file.
        selected_sheet: Sheet name for Excel input.  Ignored for text files.

    Returns:
        Absolute path to the newly created XLSX file.

    Raises:
        ValueError: Unsupported extension.
        Exception:  Any read / write error is re-raised after logging.
    """
    ext = Path(path).suffix.lower()

    try:
        if ext in TEXT_EXTENSIONS:
            df = _load_text_file(path)
            out_path = _converted_path(path, '.xlsx')
        elif ext in EXCEL_EXTENSIONS:
            sheet = selected_sheet if selected_sheet else 0
            df = pd.read_excel(path, sheet_name=sheet)
            out_path = _converted_path(path, '.xlsx', selected_sheet)
        else:
            raise ValueError(f"Unsupported file type for conversion to XLSX: '{ext}'")

        df.to_excel(out_path, index=False)
        logger.info(
            f"[FileConversion] Converted '{os.path.basename(path)}' "
            f"→ '{os.path.basename(out_path)}' "
            f"({len(df)} rows, {len(df.columns)} cols)"
        )
        return out_path

    except Exception as e:
        logger.error(f"[FileConversion] convert_file_to_xlsx failed for '{path}': {e}")
        raise


def get_extension_format(file_path: str) -> str:
    """
    Return a short human-readable format string from a file extension.

    Examples:
        'file.csv'  → 'CSV'
        'file.xlsx' → 'XLSX'
        'file.tsv'  → 'TSV'
        'file.xls'  → 'XLS'
    """
    return Path(file_path).suffix.lstrip('.').upper() or 'UNKNOWN'
