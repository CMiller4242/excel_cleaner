"""
Text Operations
Operations for text manipulation and formatting
"""

import pandas as pd
import re
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry


class UppercaseOperation(BaseOperation):
    """Convert text to UPPERCASE"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_uppercase',
            name='Convert to UPPERCASE',
            category='Text',
            description='Convert all text in selected columns to UPPERCASE',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to convert to uppercase'
                )
            ],
            excel_equivalent='UPPER()',
            examples=[
                'Convert company names to uppercase',
                'Standardize state codes to uppercase'
            ],
            tags=['text', 'format', 'uppercase', 'standardize']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        
        for col in columns:
            df[col] = df[col].astype(str).str.upper()
        
        return df


class LowercaseOperation(BaseOperation):
    """Convert text to lowercase"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_lowercase',
            name='Convert to lowercase',
            category='Text',
            description='Convert all text in selected columns to lowercase',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to convert to lowercase'
                )
            ],
            excel_equivalent='LOWER()',
            examples=[
                'Convert email addresses to lowercase',
                'Standardize usernames to lowercase'
            ],
            tags=['text', 'format', 'lowercase', 'standardize']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        
        for col in columns:
            df[col] = df[col].astype(str).str.lower()
        
        return df


class TitleCaseOperation(BaseOperation):
    """Convert text to Title Case"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_titlecase',
            name='Convert to Title Case',
            category='Text',
            description='Convert text to Title Case (First Letter Of Each Word Capitalized)',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to convert to title case'
                )
            ],
            excel_equivalent='PROPER()',
            examples=[
                'Format names properly: "john smith" → "John Smith"',
                'Format addresses in title case'
            ],
            tags=['text', 'format', 'titlecase', 'proper']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        
        for col in columns:
            df[col] = df[col].astype(str).str.title()
        
        return df


class TrimWhitespaceOperation(BaseOperation):
    """Remove extra whitespace"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_trim',
            name='Remove Extra Whitespace',
            category='Text',
            description='Remove leading, trailing, and extra spaces from text',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to trim'
                )
            ],
            excel_equivalent='TRIM()',
            examples=[
                'Clean up addresses with extra spaces',
                'Remove spacing issues from imported data'
            ],
            tags=['text', 'clean', 'trim', 'whitespace']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        
        for col in columns:
            # Remove leading/trailing spaces and reduce multiple spaces to single
            df[col] = df[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
        
        return df


class ConcatenateColumnsOperation(BaseOperation):
    """Combine multiple columns"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_concatenate',
            name='Combine Columns',
            category='Text',
            description='Join multiple columns together with a separator. Columns are combined in the order you select them.',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to combine (select in desired order)'
                ),
                Parameter(
                    name='separator',
                    type='text',
                    description='Text to put between values',
                    required=False,
                    default=' '
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for the new combined column'
                ),
                Parameter(
                    name='remove_original',
                    type='boolean',
                    description='Remove the original columns after combining',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='CONCATENATE() or TEXTJOIN()',
            examples=[
                'Combine First Name and Last Name with a space',
                'Create full address from street, city, state, zip',
                'Combine product code and description with a dash'
            ],
            tags=['text', 'combine', 'concatenate', 'join', 'merge']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        separator = self.get_param_value(params, 'separator', ' ')
        new_column = params['new_column']
        remove_original = self.get_param_value(params, 'remove_original', False)
        
        # Combine columns with separator
        df[new_column] = df[columns].astype(str).agg(separator.join, axis=1)
        
        # Remove original columns if requested
        if remove_original:
            df = df.drop(columns=columns)
        
        return df


class SplitColumnOperation(BaseOperation):
    """Split one column into multiple"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_split',
            name='Split Column',
            category='Text',
            description='Split one column into multiple columns based on a separator',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column to split'
                ),
                Parameter(
                    name='separator',
                    type='text',
                    description='Character or text to split on',
                    default=','
                ),
                Parameter(
                    name='new_columns',
                    type='text',
                    description='Names for new columns (comma-separated)',
                ),
                Parameter(
                    name='remove_original',
                    type='boolean',
                    description='Remove the original column after splitting',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='Text to Columns',
            examples=[
                'Split "Last, First" into separate Last Name and First Name columns',
                'Split full address into Street, City, State',
                'Split "Product-Code" by dash'
            ],
            tags=['text', 'split', 'separate', 'parse']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        separator = params['separator']
        new_columns = [col.strip() for col in params['new_columns'].split(',')]
        remove_original = self.get_param_value(params, 'remove_original', False)
        
        # Split the column
        split_data = df[column].astype(str).str.split(separator, expand=True)
        
        # Assign to new columns (only as many as we have names for)
        for i, new_col in enumerate(new_columns):
            if i < len(split_data.columns):
                df[new_col] = split_data[i]
        
        # Remove original column if requested
        if remove_original:
            df = df.drop(columns=[column])
        
        return df


class RemoveSpecialCharsOperation(BaseOperation):
    """Remove special characters"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_remove_special',
            name='Remove Special Characters',
            category='Text',
            description='Remove symbols and special characters from text',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to clean'
                ),
                Parameter(
                    name='keep_spaces',
                    type='boolean',
                    description='Keep spaces',
                    required=False,
                    default=True
                ),
                Parameter(
                    name='keep_numbers',
                    type='boolean',
                    description='Keep numbers',
                    required=False,
                    default=True
                )
            ],
            excel_equivalent='SUBSTITUTE() or REGEX',
            examples=[
                'Clean addresses: "123 Main St #5" → "123 Main St 5"',
                'Remove symbols from product codes',
                'Clean phone numbers to digits only'
            ],
            tags=['text', 'clean', 'remove', 'special', 'characters']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        keep_spaces = self.get_param_value(params, 'keep_spaces', True)
        keep_numbers = self.get_param_value(params, 'keep_numbers', True)
        
        for col in columns:
            # Build regex pattern
            if keep_spaces and keep_numbers:
                # Keep letters, numbers, spaces
                pattern = r'[^a-zA-Z0-9\s]'
            elif keep_spaces:
                # Keep letters and spaces only
                pattern = r'[^a-zA-Z\s]'
            elif keep_numbers:
                # Keep letters and numbers only
                pattern = r'[^a-zA-Z0-9]'
            else:
                # Keep letters only
                pattern = r'[^a-zA-Z]'
            
            df[col] = df[col].astype(str).str.replace(pattern, '', regex=True)
        
        return df


class FindReplaceOperation(BaseOperation):
    """Find and replace text"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_find_replace',
            name='Find and Replace',
            category='Text',
            description='Find specific text and replace it with something else',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to search in'
                ),
                Parameter(
                    name='find_text',
                    type='text',
                    description='Text to find'
                ),
                Parameter(
                    name='replace_text',
                    type='text',
                    description='Text to replace with'
                ),
                Parameter(
                    name='case_sensitive',
                    type='boolean',
                    description='Match case exactly',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='Find & Replace or SUBSTITUTE()',
            examples=[
                'Replace "St" with "Street"',
                'Change "N/A" to empty',
                'Standardize abbreviations'
            ],
            tags=['text', 'find', 'replace', 'substitute']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        find_text = params['find_text']
        replace_text = params['replace_text']
        case_sensitive = self.get_param_value(params, 'case_sensitive', False)
        
        for col in columns:
            df[col] = df[col].astype(str).str.replace(
                find_text, 
                replace_text, 
                case=case_sensitive,
                regex=False
            )
        
        return df


class AddPrefixSuffixOperation(BaseOperation):
    """Add prefix or suffix to text"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_add_prefix_suffix',
            name='Add Prefix or Suffix',
            category='Text',
            description='Add text to the beginning or end of values',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to modify'
                ),
                Parameter(
                    name='prefix',
                    type='text',
                    description='Text to add at the beginning',
                    required=False,
                    default=''
                ),
                Parameter(
                    name='suffix',
                    type='text',
                    description='Text to add at the end',
                    required=False,
                    default=''
                )
            ],
            excel_equivalent='CONCATENATE() or &',
            examples=[
                'Add "Mr. " prefix to names',
                'Add ".com" suffix to domain names',
                'Add "$" prefix to prices'
            ],
            tags=['text', 'add', 'prefix', 'suffix', 'prepend', 'append']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        prefix = self.get_param_value(params, 'prefix', '')
        suffix = self.get_param_value(params, 'suffix', '')
        
        for col in columns:
            if prefix:
                df[col] = prefix + df[col].astype(str)
            if suffix:
                df[col] = df[col].astype(str) + suffix

        return df


class LeftOperation(BaseOperation):
    """Extract first N characters from text"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_left',
            name='LEFT - Extract First Characters',
            category='Text - Advanced',
            description='Extract the first N characters from text',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column to extract from'
                ),
                Parameter(
                    name='length',
                    type='number',
                    description='Number of characters to extract'
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for result column (optional - overwrites if not specified)',
                    required=False
                )
            ],
            excel_equivalent='LEFT(text, num_chars)',
            examples=[
                'Extract first 5 digits of zip code: "62701-1234" → "62701"',
                'Get area code from phone: "(555) 123-4567" → "(555)"',
                'Extract state from "IL-Chicago" → "IL"'
            ],
            tags=['text', 'extract', 'left', 'substring', 'advanced']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        length = int(params['length'])
        new_column = self.get_param_value(params, 'new_column', column)

        df[new_column] = df[column].astype(str).str[:length]

        return df


class RightOperation(BaseOperation):
    """Extract last N characters from text"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_right',
            name='RIGHT - Extract Last Characters',
            category='Text - Advanced',
            description='Extract the last N characters from text',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column to extract from'
                ),
                Parameter(
                    name='length',
                    type='number',
                    description='Number of characters to extract'
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for result column (optional - overwrites if not specified)',
                    required=False
                )
            ],
            excel_equivalent='RIGHT(text, num_chars)',
            examples=[
                'Extract last 4 digits of phone: "(555) 123-4567" → "4567"',
                'Get file extension: "document.pdf" → "pdf" (with length=3)',
                'Extract last 10 digits from phone number'
            ],
            tags=['text', 'extract', 'right', 'substring', 'advanced']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        length = int(params['length'])
        new_column = self.get_param_value(params, 'new_column', column)

        df[new_column] = df[column].astype(str).str[-length:]

        return df


class MidOperation(BaseOperation):
    """Extract middle portion of text"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_mid',
            name='MID - Extract Middle Characters',
            category='Text - Advanced',
            description='Extract characters from the middle of text',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column to extract from'
                ),
                Parameter(
                    name='start',
                    type='number',
                    description='Starting position (1-based, like Excel)'
                ),
                Parameter(
                    name='length',
                    type='number',
                    description='Number of characters to extract'
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for result column (optional - overwrites if not specified)',
                    required=False
                )
            ],
            excel_equivalent='MID(text, start, length)',
            examples=[
                'Extract middle 3 digits of phone: "(555) 123-4567" → "123" (start=8, length=3)',
                'Extract month from date: "2025-11-18" → "11" (start=6, length=2)',
                'Parse product code middle section'
            ],
            tags=['text', 'extract', 'mid', 'substring', 'advanced']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        start = int(params['start']) - 1  # Convert from 1-based (Excel) to 0-based (Python)
        length = int(params['length'])
        new_column = self.get_param_value(params, 'new_column', column)

        df[new_column] = df[column].astype(str).str[start:start+length]

        return df


class PhoneFormatterOperation(BaseOperation):
    """Format phone numbers to standard (XXX) XXX-XXXX format"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_phone_format',
            name='Format Phone Numbers',
            category='Text - Advanced',
            description='Standardize phone numbers to (XXX) XXX-XXXX format',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column containing phone numbers'
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for formatted column (optional - overwrites if not specified)',
                    required=False
                ),
                Parameter(
                    name='remove_invalid',
                    type='boolean',
                    description='Replace invalid phone numbers with blank',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='Complex formula with SUBSTITUTE and TEXT',
            examples=[
                '1234567890 → (123) 456-7890',
                '123-456-7890 → (123) 456-7890',
                '+1-123-456-7890 → (123) 456-7890',
                '(123) 456-7890 → (123) 456-7890',
                '123.456.7890 → (123) 456-7890'
            ],
            tags=['text', 'phone', 'format', 'standardize', 'advanced']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        new_column = self.get_param_value(params, 'new_column', column)
        remove_invalid = self.get_param_value(params, 'remove_invalid', False)

        def format_phone(phone_str):
            """Format a phone number string to (XXX) XXX-XXXX"""
            if pd.isna(phone_str):
                return '' if remove_invalid else phone_str

            # Convert to string and remove all non-numeric characters
            digits_only = re.sub(r'\D', '', str(phone_str))

            # Take the rightmost 10 digits (handles +1 country code)
            if len(digits_only) >= 10:
                digits_only = digits_only[-10:]
            elif len(digits_only) < 10:
                # Not enough digits - return blank if remove_invalid, else original
                return '' if remove_invalid else str(phone_str)

            # Format as (XXX) XXX-XXXX
            formatted = f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:10]}"
            return formatted

        df[new_column] = df[column].apply(format_phone)

        return df


class LenOperation(BaseOperation):
    """Get text length"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_len',
            name='LEN - Get Text Length',
            category='Text - Advanced',
            description='Count the number of characters in text',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column to measure'
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for result column'
                )
            ],
            excel_equivalent='LEN(text)',
            examples=[
                'Validate zip code length (should be 5 or 9)',
                'Check phone number has 10 digits after cleaning',
                'Find records with suspiciously short/long values'
            ],
            tags=['text', 'length', 'count', 'validate', 'advanced']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        new_column = params['new_column']

        df[new_column] = df[column].astype(str).str.len()

        return df


class RenameColumnOperation(BaseOperation):
    """Rename a column to a new name"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_rename_column',
            name='Rename Column',
            category='Text - Basic',
            description='Rename a column to a new name',
            parameters=[
                Parameter(
                    name='old_name',
                    type='column',
                    description='Current column name'
                ),
                Parameter(
                    name='new_name',
                    type='text',
                    description='New column name'
                )
            ],
            excel_equivalent='Right-click column > Rename',
            examples=[
                'Rename "Email_Address" to "Email"',
                'Standardize column names to match format',
                'Fix typos in column names'
            ],
            tags=['rename', 'column', 'standardize', 'basic']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        old_name = params['old_name']
        new_name = params['new_name']

        # Check if old column exists
        if old_name not in df.columns:
            raise ValueError(f"Column '{old_name}' not found in dataframe")

        # Check if new name already exists (and isn't the same as old name)
        if new_name in df.columns and new_name != old_name:
            raise ValueError(f"Column '{new_name}' already exists")

        df = df.rename(columns={old_name: new_name})

        return df


class BatchRenameColumnsOperation(BaseOperation):
    """Rename multiple columns at once"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_rename_batch',
            name='Rename Multiple Columns',
            category='Text - Basic',
            description='Rename multiple columns at once with an intuitive interface',
            parameters=[
                Parameter(
                    name='column_mappings',
                    type='column_rename_list',
                    description='Column rename mappings',
                    required=True,
                    default=[]
                )
            ],
            excel_equivalent='Right-click columns > Rename (multiple times)',
            examples=[
                'Rename Person City → City, Person State → State, Person Zip → Zip',
                'Standardize multiple column names to match format',
                'Bulk rename ZoomInfo columns to standard format'
            ],
            tags=['rename', 'column', 'standardize', 'batch', 'bulk']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()

        # Support both old dict format and new list format for backwards compatibility
        if 'column_mappings' in params:
            # New format: list of {old_name, new_name} dicts
            column_mappings = params['column_mappings']

            if not isinstance(column_mappings, list):
                raise ValueError("column_mappings parameter must be a list")

            # Convert to dict format
            mappings = {}
            for mapping in column_mappings:
                old_name = mapping.get('old_name', '').strip()
                new_name = mapping.get('new_name', '').strip()

                if not old_name or not new_name:
                    continue

                mappings[old_name] = new_name

        elif 'mappings' in params:
            # Old format: dict (for backwards compatibility)
            mappings = params['mappings']

            if not isinstance(mappings, dict):
                raise ValueError("mappings parameter must be a dictionary")
        else:
            raise ValueError("No column mappings provided")

        if not mappings:
            raise ValueError("No valid column mappings provided")

        # Validate all old columns exist
        missing_columns = [old_name for old_name in mappings.keys() if old_name not in df.columns]
        if missing_columns:
            raise ValueError(f"Columns not found in dataframe: {', '.join(missing_columns)}")

        # Check for conflicts (new names that already exist, unless it's the same column)
        conflicts = []
        for old_name, new_name in mappings.items():
            if new_name in df.columns and new_name != old_name and new_name not in mappings.keys():
                conflicts.append(f"{old_name} → {new_name} ('{new_name}' already exists)")

        if conflicts:
            raise ValueError(f"Rename conflicts: {'; '.join(conflicts)}")

        # Apply all renames
        df = df.rename(columns=mappings)

        return df


class StandardizeCustomerNumbersOperation(BaseOperation):
    """
    Standardize customer numbers and segments to company format.

    Company Standard:
    - Customer Number: 8 digits with leading zeros (e.g., 00005164)
    - Segment: 2 digits with leading zeros (e.g., 06, or 00 if blank)
    """

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_standardize_customer_numbers',
            name='Standardize Customer Numbers',
            category='Text',
            description='Pad customer numbers (8 digits) and segments (2 digits) with leading zeros',
            parameters=[
                Parameter(
                    name='customer_number_column',
                    type='column',
                    description='Customer Number column (will be padded to 8 digits)'
                ),
                Parameter(
                    name='segment_column',
                    type='column',
                    description='Segment column (will be padded to 2 digits)'
                ),
                Parameter(
                    name='customer_length',
                    type='number',
                    description='Customer number length (default: 8)',
                    required=False,
                    default=8
                ),
                Parameter(
                    name='segment_length',
                    type='number',
                    description='Segment length (default: 2)',
                    required=False,
                    default=2
                ),
                Parameter(
                    name='blank_segment_value',
                    type='text',
                    description='Value for blank segments (default: "00")',
                    required=False,
                    default='00'
                )
            ],
            excel_equivalent='TEXT() function with format codes',
            examples=[
                'Pad 5164 → 00005164 (8 digits)',
                'Pad segment 6 → 06 (2 digits)',
                'Blank segment → 00',
                'Already correct: 00005164 → 00005164 (unchanged)'
            ],
            tags=['customer', 'number', 'pad', 'zeros', 'format', 'standardize']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        Standardize customer numbers and segments with leading zeros.

        Args:
            df: Input dataframe
            params: {
                'customer_number_column': str,
                'segment_column': str,
                'customer_length': int (default 8),
                'segment_length': int (default 2),
                'blank_segment_value': str (default '00')
            }

        Returns:
            Dataframe with standardized customer numbers and segments
        """
        df = df.copy()

        customer_col = params.get('customer_number_column')
        segment_col = params.get('segment_column')
        customer_length = int(params.get('customer_length', 8))
        segment_length = int(params.get('segment_length', 2))
        blank_segment_value = params.get('blank_segment_value', '00')

        # Validate columns exist
        if customer_col not in df.columns:
            raise ValueError(f"Customer number column '{customer_col}' not found")
        if segment_col not in df.columns:
            raise ValueError(f"Segment column '{segment_col}' not found")

        # Standardize Customer Numbers
        df[customer_col] = df[customer_col].apply(
            lambda x: self._pad_with_zeros(x, customer_length)
        )

        # Standardize Segments (handle blanks specially)
        df[segment_col] = df[segment_col].apply(
            lambda x: self._pad_segment(x, segment_length, blank_segment_value)
        )

        return df

    def _pad_with_zeros(self, value, length):
        """
        Pad a number with leading zeros to specified length.

        Args:
            value: Number or string to pad
            length: Target length

        Returns:
            String padded with leading zeros
        """
        # Handle NaN/None
        if pd.isna(value):
            return '0' * length

        # Convert to string and remove any decimals
        value_str = str(value).strip()

        # Remove decimal point if present (e.g., "5164.0" → "5164")
        if '.' in value_str:
            value_str = value_str.split('.')[0]

        # Remove any non-digit characters except leading minus
        if value_str.startswith('-'):
            sign = '-'
            value_str = value_str[1:]
        else:
            sign = ''

        # Keep only digits
        value_str = ''.join(c for c in value_str if c.isdigit())

        # If empty after cleaning, return zeros
        if not value_str:
            return '0' * length

        # Pad with leading zeros
        padded = value_str.zfill(length)

        # If result is longer than target (value already longer), return as-is
        # This preserves data integrity
        return sign + padded

    def _pad_segment(self, value, length, blank_value):
        """
        Pad segment with leading zeros, treating blanks specially.

        Args:
            value: Segment number or blank
            length: Target length (default 2)
            blank_value: Value to use for blanks (default '00')

        Returns:
            String padded with leading zeros, or blank_value if empty
        """
        # Handle NaN/None/empty as blank segment (00)
        if pd.isna(value) or str(value).strip() == '':
            return blank_value

        # Use standard padding for non-blank values
        return self._pad_with_zeros(value, length)


class StandardizePhoneNumbersOperation(BaseOperation):
    """
    Standardize phone numbers by removing formatting and applying consistent format.

    Handles various input formats:
    - Periods: 386.917.5481 → 3869175481
    - Dashes: 941-766-4125 → 9417664125
    - Parentheses: (256) 429-4000 → 2564294000
    - Spaces: 256 429 4000 → 2564294000
    - Mixed: (256) 429.4000 → 2564294000
    """

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_standardize_phone_numbers',
            name='Standardize Phone Numbers',
            category='Text',
            description='Clean and format phone numbers consistently (remove periods, dashes, spaces, parentheses)',
            parameters=[
                Parameter(
                    name='phone_column',
                    type='column',
                    description='Column containing phone numbers',
                    required=True
                ),
                Parameter(
                    name='output_format',
                    type='choice',
                    description='Output format',
                    required=True,
                    choices=[
                        'Digits Only (2564294000)',
                        'US Format (256) 429-4000',
                        'US Format with Dashes (256-429-4000)',
                        'International +1 (256) 429-4000'
                    ],
                    default='Digits Only (2564294000)'
                ),
                Parameter(
                    name='handle_extensions',
                    type='boolean',
                    description='Preserve extensions (e.g., "x123", "ext 123")',
                    required=False,
                    default=False
                ),
                Parameter(
                    name='remove_country_code',
                    type='boolean',
                    description='Remove country code (e.g., +1, 1) from start',
                    required=False,
                    default=True
                ),
                Parameter(
                    name='validate_length',
                    type='boolean',
                    description='Add validation column marking invalid phone numbers (not 10 digits)',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='Find & Replace + Text formatting',
            examples=[
                '386.917.5481 → 3869175481',
                '(256) 429-4000 → 2564294000',
                '256-429-4000 → 2564294000',
                '+1 (256) 429-4000 → 2564294000',
                '256 429 4000 → 2564294000'
            ],
            tags=['phone', 'format', 'standardize', 'clean', 'numbers']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        Standardize phone numbers in specified column.

        Args:
            df: Input dataframe
            params: Operation parameters

        Returns:
            Dataframe with standardized phone numbers
        """
        df = df.copy()

        phone_column = params.get('phone_column')
        output_format = params.get('output_format', 'Digits Only (2564294000)')
        handle_extensions = params.get('handle_extensions', False)
        remove_country_code = params.get('remove_country_code', True)
        validate_length = params.get('validate_length', False)

        if phone_column not in df.columns:
            raise ValueError(f"Phone column '{phone_column}' not found")

        # Apply standardization
        df[phone_column] = df[phone_column].apply(
            lambda x: self._standardize_phone(
                x,
                output_format,
                handle_extensions,
                remove_country_code
            )
        )

        # Add validation column if requested
        if validate_length:
            df['_Phone_Valid'] = df[phone_column].apply(self._is_valid_phone)

        return df

    def _standardize_phone(self, phone, output_format, handle_extensions, remove_country_code):
        """
        Standardize a single phone number.

        Args:
            phone: Phone number string
            output_format: Desired output format
            handle_extensions: Whether to preserve extensions
            remove_country_code: Whether to remove +1 or 1 prefix

        Returns:
            Standardized phone number string
        """
        if pd.isna(phone) or not phone:
            return ""

        phone_str = str(phone).strip()

        # Extract extension if present
        extension = ""
        if handle_extensions:
            ext_match = re.search(r'(x|ext|extension)[\s:.]?(\d+)', phone_str, re.IGNORECASE)
            if ext_match:
                extension = f" x{ext_match.group(2)}"
                # Remove extension from phone string
                phone_str = phone_str[:ext_match.start()].strip()

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_str)

        # Remove country code if present (1 at start)
        if remove_country_code:
            if digits.startswith('1') and len(digits) == 11:
                digits = digits[1:]  # Remove leading 1

        # Handle invalid lengths
        if len(digits) != 10:
            # Return as-is if not 10 digits
            return phone_str + extension

        # Format based on output_format
        if output_format == 'Digits Only (2564294000)':
            return digits + extension

        elif output_format == 'US Format (256) 429-4000':
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}" + extension

        elif output_format == 'US Format with Dashes (256-429-4000)':
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}" + extension

        elif output_format == 'International +1 (256) 429-4000':
            return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}" + extension

        else:
            # Default: digits only
            return digits + extension

    def _is_valid_phone(self, phone):
        """Check if phone number is valid (10 digits)"""
        if pd.isna(phone) or not phone:
            return False

        digits = re.sub(r'\D', '', str(phone))
        return len(digits) == 10


class CleanMailingCustomerDataOperation(BaseOperation):
    """
    Clean customer and segment data from mailing list files.

    Processes customer numbers and segment numbers for mailing list standardization:
    - Customer Number: "1726274-639507" → "01726274" (8 digits, extract before hyphen)
    - Segment Number: "0" → "00" or "1" → "01" (2 digits, pad existing value)

    This operation is designed for cleaning data from mailing list exports
    that need standardized customer and segment formatting.
    """

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='text_clean_mailing_customer_data',
            name='Clean Mailing List Customer Data',
            category='Text',
            description='Clean customer and segment numbers from mailing list files (customer: extract & pad to 8, segment: pad to 2)',
            parameters=[
                Parameter(
                    name='customer_column',
                    type='column',
                    description='Column containing hyphenated customer numbers (e.g., "1726274-639507")',
                    required=True
                ),
                Parameter(
                    name='customer_length',
                    type='number',
                    description='Target length for customer number padding (default: 8 digits)',
                    required=False,
                    default=8
                ),
                Parameter(
                    name='segment_column',
                    type='column',
                    description='(Optional) Column containing segment numbers to pad (e.g., "0" → "00")',
                    required=False
                ),
                Parameter(
                    name='segment_length',
                    type='number',
                    description='Target length for segment number padding (default: 2 digits)',
                    required=False,
                    default=2
                ),
                Parameter(
                    name='handle_non_hyphenated',
                    type='choice',
                    description='How to handle customer numbers without hyphens',
                    required=False,
                    choices=['Pad as-is', 'Mark as error', 'Leave unchanged'],
                    default='Pad as-is'
                ),
                Parameter(
                    name='blank_segments_to_zero',
                    type='boolean',
                    description='Convert blank segment values to "00" (if unchecked, keeps blank)',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='LEFT() + TEXT() with format codes, multiple columns',
            examples=[
                'Customer: "1726274-639507" → "01726274"',
                'Customer: "9609-640231" → "00009609"',
                'Segment: "0" → "00"',
                'Segment: "1" → "01"',
                'Segment: "31" → "31"'
            ],
            tags=['customer', 'mailing', 'segment', 'standardize', 'pad', 'zeros', 'extract', 'hyphen', 'list']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        Clean customer and segment data from mailing list files.

        Args:
            df: Input dataframe
            params: {
                'customer_column': str,
                'customer_length': int (default 8),
                'segment_column': str (optional),
                'segment_length': int (default 2),
                'handle_non_hyphenated': str (default 'Pad as-is'),
                'blank_segments_to_zero': bool (default False)
            }

        Returns:
            Dataframe with standardized customer and segment numbers
        """
        df = df.copy()

        customer_col = params.get('customer_column')
        customer_length = int(params.get('customer_length', 8))
        segment_col = params.get('segment_column')
        segment_length = int(params.get('segment_length', 2))
        handle_non_hyphenated = params.get('handle_non_hyphenated', 'Pad as-is')
        blank_segments_to_zero = params.get('blank_segments_to_zero', False)

        if customer_col not in df.columns:
            raise ValueError(f"Customer column '{customer_col}' not found")

        # Process customer numbers
        df[customer_col] = df[customer_col].apply(
            lambda x: self._standardize_customer(x, customer_length, handle_non_hyphenated)
        )

        # Process segment numbers (if column specified)
        if segment_col and segment_col in df.columns:
            df[segment_col] = df[segment_col].apply(
                lambda x: self._standardize_segment(x, segment_length, blank_segments_to_zero)
            )

        return df

    def _standardize_customer(self, value, length, handle_non_hyphenated):
        """
        Standardize a single customer number by extracting and padding.

        Extracts the part BEFORE the hyphen and pads to target length.
        CRITICAL FIX: Handles numeric types (int, float) properly to avoid the bug
        where floats like 1726274.0 become "1726274.0" → "17262740" when regex strips decimal.

        Expected behavior:
        - "1726274-639507" → extract "1726274" → pad to "01726274"
        - "9609-640231" → extract "9609" → pad to "00009609"
        - 5164.0 or 5164 → "00005164"
        - "5164" → "00005164"

        Args:
            value: Customer number value (e.g., "1726274-639507", 5164, 5164.0)
            length: Target length (default 8)
            handle_non_hyphenated: How to handle non-hyphenated values

        Returns:
            Standardized customer number string with leading zero padding
        """
        if pd.isna(value) or not value:
            return ""

        # CRITICAL FIX: Convert numeric types to int BEFORE string conversion
        # This prevents floats like 1726274.0 from becoming "1726274.0" which becomes "17262740"
        if isinstance(value, (int, float)):
            try:
                value_str = str(int(value))
            except (ValueError, OverflowError):
                value_str = str(value).strip()
        else:
            value_str = str(value).strip()

        # Check if hyphen exists
        if '-' in value_str:
            # Extract part before hyphen
            before_hyphen = value_str.split('-')[0].strip()
        else:
            # No hyphen found
            if handle_non_hyphenated == 'Mark as error':
                return f"ERROR: {value_str}"
            elif handle_non_hyphenated == 'Leave unchanged':
                return value_str
            else:  # 'Pad as-is'
                before_hyphen = value_str

        # Remove any non-digit characters
        digits = re.sub(r'\D', '', before_hyphen)

        # If empty after cleaning, return zeros
        if not digits:
            return '0' * length

        # Pad with leading zeros to target length using zfill()
        padded = digits.zfill(length)

        return padded

    def _standardize_segment(self, value, length, blank_to_zero):
        """
        Standardize a single segment number by padding to target length.

        CRITICAL FIX: Handles numeric types (int, float) properly to avoid the bug
        where floats like 10.0 become "10.0" → "100" when regex strips the decimal.

        Expected behavior:
        - 0 or 0.0 → "00"
        - 2 or 2.0 → "02"
        - 10 or 10.0 → "10" (NOT "100")
        - "10" → "10"
        - Blank → "" or "00" (depending on blank_to_zero)

        Args:
            value: Segment number value (e.g., 0, 10, 2, "0", "10", "2")
            length: Target length (default 2)
            blank_to_zero: Whether to convert blank values to zeros

        Returns:
            Standardized segment number string with leading zero padding
        """
        # Handle None, NaN, or empty string
        if pd.isna(value) or value == '':
            if blank_to_zero:
                return '0' * length
            else:
                return ""

        # CRITICAL FIX: Convert numeric types to int BEFORE string conversion
        # This prevents floats like 10.0 from becoming "10.0" which then becomes "100"
        if isinstance(value, (int, float)):
            # Convert to int to strip decimal portion (10.0 → 10)
            # This ensures str(10) = "10" not "10.0"
            try:
                value_str = str(int(value))
            except (ValueError, OverflowError):
                # Handle edge cases like NaN, inf
                value_str = str(value).strip()
        else:
            # Already a string or other type
            value_str = str(value).strip()

        # Remove any non-digit characters (handles strings like "10a" or "-5")
        digits = re.sub(r'\D', '', value_str)

        # If empty after cleaning
        if not digits:
            if blank_to_zero:
                return '0' * length
            else:
                return ""

        # Pad with leading zeros to target length using zfill()
        # "10".zfill(2) → "10" (already 2 digits)
        # "2".zfill(2) → "02" (pads to 2 digits)
        padded = digits.zfill(length)

        return padded


# Register all text operations
registry.register(UppercaseOperation())
registry.register(LowercaseOperation())
registry.register(TitleCaseOperation())
registry.register(TrimWhitespaceOperation())
registry.register(ConcatenateColumnsOperation())
registry.register(SplitColumnOperation())
registry.register(RemoveSpecialCharsOperation())
registry.register(FindReplaceOperation())
registry.register(AddPrefixSuffixOperation())
registry.register(LeftOperation())
registry.register(RightOperation())
registry.register(MidOperation())
registry.register(PhoneFormatterOperation())
registry.register(LenOperation())
registry.register(RenameColumnOperation())
registry.register(BatchRenameColumnsOperation())
registry.register(StandardizeCustomerNumbersOperation())
registry.register(StandardizePhoneNumbersOperation())
registry.register(CleanMailingCustomerDataOperation())
