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
            description='Join multiple columns together with a separator',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to combine (in order)'
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
            description='Rename multiple columns at once using a mapping dictionary',
            parameters=[
                Parameter(
                    name='mappings',
                    type='dict',
                    description='Dictionary of old_name: new_name mappings',
                    required=True
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
        mappings = params['mappings']

        if not isinstance(mappings, dict):
            raise ValueError("mappings parameter must be a dictionary")

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
