"""
Text Operations
Operations for text manipulation and formatting
"""

import pandas as pd
import re
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter


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
