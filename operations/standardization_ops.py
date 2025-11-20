"""
Standardization Operations
Operations for standardizing data formats (phone, ZIP, state, etc.)
For mailing list cleaning and data normalization
"""

import pandas as pd
import re
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry


# State name to abbreviation mapping
STATE_ABBREVIATIONS = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
    'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
    'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
    'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
    'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC',
    'puerto rico': 'PR', 'virgin islands': 'VI', 'guam': 'GU'
}


class StandardizePhoneOperation(BaseOperation):
    """Standardize phone numbers to pure numeric format"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='standardize_phone',
            name='Standardize Phone Numbers',
            category='Cleaning',
            description='Convert phone numbers to pure numeric format (strips all formatting, country codes, etc.)',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Phone number columns to standardize'
                ),
                Parameter(
                    name='remove_country_code',
                    type='boolean',
                    description='Remove leading 1 (US country code)',
                    required=False,
                    default=True
                )
            ],
            excel_equivalent='Custom formula to strip non-numeric',
            examples=[
                '1-(304)-473-2000 → 3044732000',
                '(402) 572-2366 → 4025722366',
                '833.251.9895 → 8332519895',
                '8508833941.0 → 8508833941'
            ],
            tags=['phone', 'standardize', 'format', 'clean', 'numeric']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        remove_country_code = self.get_param_value(params, 'remove_country_code', True)
        
        for col in columns:
            # Convert to string and strip all non-numeric characters
            df[col] = df[col].astype(str).apply(lambda x: re.sub(r'[^0-9]', '', x))
            
            # Remove .0 from floats that were converted to string
            df[col] = df[col].str.replace(r'\.0$', '', regex=True)
            
            # Remove leading 1 if it's a country code (11 digits starting with 1)
            if remove_country_code:
                df[col] = df[col].apply(
                    lambda x: x[1:] if len(x) == 11 and x.startswith('1') else x
                )
            
            # Handle empty/nan values
            df[col] = df[col].replace('', pd.NA).replace('nan', pd.NA)
            
            # Convert to integer where possible (keeps as string if has issues)
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            except:
                pass  # Keep as string if conversion fails
        
        return df


class StandardizeZipCodeOperation(BaseOperation):
    """Standardize ZIP codes with leading zeros and optional ZIP+4"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='standardize_zip',
            name='Standardize ZIP Codes',
            category='Cleaning',
            description='Standardize ZIP codes with leading zeros. Preserves ZIP+4 format.',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='ZIP code columns to standardize'
                ),
                Parameter(
                    name='format_type',
                    type='choice',
                    description='Output format for ZIP codes',
                    choices=['ZIP+4 (preserve)', '5-digit only', '5-digit with placeholder'],
                    default='ZIP+4 (preserve)'
                )
            ],
            excel_equivalent='TEXT() with custom format or formula',
            examples=[
                '1434 → 01434 (adds leading zero)',
                '06510-3220 → 06510-3220 (preserves ZIP+4)',
                '802 → 00802 (pads short codes)',
                '94602 → 94602-0000 (adds placeholder if selected)'
            ],
            tags=['zip', 'postal', 'standardize', 'format', 'address']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        format_type = self.get_param_value(params, 'format_type', 'ZIP+4 (preserve)')
        
        for col in columns:
            df[col] = df[col].astype(str).apply(
                lambda x: self._standardize_zip(x, format_type)
            )
            
            # Clean up nan values
            df[col] = df[col].replace('nan', pd.NA).replace('', pd.NA)
        
        return df
    
    def _standardize_zip(self, value: str, format_type: str) -> str:
        """Standardize a single ZIP code value"""
        if not value or value.lower() in ('nan', 'none', ''):
            return ''
        
        # Remove any non-alphanumeric except dash
        value = re.sub(r'[^0-9\-]', '', str(value))
        
        # Split on dash to handle ZIP+4
        parts = value.split('-')
        zip5 = parts[0] if parts else ''
        plus4 = parts[1] if len(parts) > 1 else ''
        
        # Pad ZIP to 5 digits with leading zeros
        if zip5:
            zip5 = zip5.zfill(5)
            
            # Ensure it's not more than 5 digits
            if len(zip5) > 5:
                zip5 = zip5[:5]
        
        # Pad plus4 to 4 digits if present
        if plus4:
            plus4 = plus4.zfill(4)
            if len(plus4) > 4:
                plus4 = plus4[:4]
        
        # Format based on selection
        if format_type == '5-digit only':
            return zip5
        elif format_type == '5-digit with placeholder':
            return f"{zip5}-{plus4 if plus4 else '0000'}" if zip5 else ''
        else:  # ZIP+4 (preserve)
            if plus4:
                return f"{zip5}-{plus4}"
            else:
                return zip5


class StandardizeStateOperation(BaseOperation):
    """Convert state names to 2-letter abbreviations"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='standardize_state',
            name='Standardize State Abbreviations',
            category='Cleaning',
            description='Convert full state names to 2-letter abbreviations (e.g., Ohio → OH)',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='State columns to standardize'
                )
            ],
            excel_equivalent='VLOOKUP() with state table',
            examples=[
                'Ohio → OH',
                'Illinois → IL',
                'new york → NY',
                'Vi → VI (fixes case)'
            ],
            tags=['state', 'abbreviation', 'standardize', 'address', 'format']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        
        for col in columns:
            df[col] = df[col].astype(str).apply(self._standardize_state)
            
            # Clean up nan values
            df[col] = df[col].replace('nan', pd.NA).replace('', pd.NA)
        
        return df
    
    def _standardize_state(self, value: str) -> str:
        """Convert state name to abbreviation"""
        if not value or value.lower() in ('nan', 'none', ''):
            return ''
        
        # Clean and lowercase for lookup
        cleaned = value.strip().lower()
        
        # Check if it's already a 2-letter code
        if len(cleaned) == 2:
            return cleaned.upper()
        
        # Look up in state dictionary
        if cleaned in STATE_ABBREVIATIONS:
            return STATE_ABBREVIATIONS[cleaned]
        
        # Try partial matching for common variations
        for state_name, abbrev in STATE_ABBREVIATIONS.items():
            if state_name.startswith(cleaned) or cleaned.startswith(state_name):
                return abbrev
        
        # Return original (uppercased) if no match found
        return value.upper()


class StandardizeColumnNamesOperation(BaseOperation):
    """Rename columns to standard names"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='standardize_column_names',
            name='Rename Columns (Batch)',
            category='Cleaning',
            description='Rename multiple columns at once using a mapping. Format: OldName1=NewName1, OldName2=NewName2',
            parameters=[
                Parameter(
                    name='mapping',
                    type='text',
                    description='Column rename mapping (OldName=NewName, separated by commas)',
                    default='Customer #=Customer, Email Address=Email'
                )
            ],
            excel_equivalent='Rename columns manually',
            examples=[
                'Customer #=Customer',
                'Email Address=Email',
                'OfficePhoneNumber=Phone'
            ],
            tags=['rename', 'columns', 'standardize', 'mapping']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        mapping_str = params['mapping']
        
        # Parse the mapping string
        rename_map = {}
        pairs = mapping_str.split(',')
        
        for pair in pairs:
            if '=' in pair:
                old_name, new_name = pair.split('=', 1)
                old_name = old_name.strip()
                new_name = new_name.strip()
                
                # Only add if old column exists
                if old_name in df.columns:
                    rename_map[old_name] = new_name
        
        if rename_map:
            df = df.rename(columns=rename_map)
        
        return df


class ParseContactNameOperation(BaseOperation):
    """Split a full name into First and Last name columns"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='parse_contact_name',
            name='Parse Contact Name',
            category='Cleaning',
            description='Split a full name column into separate First Name and Last Name columns',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column containing the full name'
                ),
                Parameter(
                    name='first_name_col',
                    type='text',
                    description='Name for the First Name column',
                    default='First Name'
                ),
                Parameter(
                    name='last_name_col',
                    type='text',
                    description='Name for the Last Name column',
                    default='Last Name'
                ),
                Parameter(
                    name='name_format',
                    type='choice',
                    description='Format of the input name',
                    choices=['First Last', 'Last, First', 'Last First'],
                    default='First Last'
                ),
                Parameter(
                    name='remove_original',
                    type='boolean',
                    description='Remove the original name column',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='Text to Columns or formulas',
            examples=[
                'JOHN SMITH → First: JOHN, Last: SMITH',
                'Smith, John → First: John, Last: Smith',
                'JESSICA FERRARO → First: JESSICA, Last: FERRARO'
            ],
            tags=['name', 'parse', 'split', 'contact', 'first', 'last']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        first_col = params['first_name_col']
        last_col = params['last_name_col']
        name_format = self.get_param_value(params, 'name_format', 'First Last')
        remove_original = self.get_param_value(params, 'remove_original', False)
        
        def parse_name(value):
            if not value or str(value).lower() in ('nan', 'none', ''):
                return '', ''
            
            value = str(value).strip()
            
            if name_format == 'Last, First':
                # Handle "Smith, John" format
                if ',' in value:
                    parts = value.split(',', 1)
                    last = parts[0].strip()
                    first = parts[1].strip() if len(parts) > 1 else ''
                else:
                    parts = value.split()
                    first = parts[0] if parts else ''
                    last = ' '.join(parts[1:]) if len(parts) > 1 else ''
            elif name_format == 'Last First':
                # Handle "SMITH JOHN" where last name comes first
                parts = value.split()
                last = parts[0] if parts else ''
                first = ' '.join(parts[1:]) if len(parts) > 1 else ''
            else:  # First Last
                # Handle "John Smith" format
                parts = value.split()
                first = parts[0] if parts else ''
                last = ' '.join(parts[1:]) if len(parts) > 1 else ''
            
            return first, last
        
        # Apply parsing
        parsed = df[column].apply(parse_name)
        df[first_col] = parsed.apply(lambda x: x[0])
        df[last_col] = parsed.apply(lambda x: x[1])
        
        # Remove original if requested
        if remove_original:
            df = df.drop(columns=[column])
        
        return df


class ExtractTextOperation(BaseOperation):
    """Extract portion of text using LEFT, RIGHT, or MID logic"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='extract_text',
            name='Extract Text (LEFT/RIGHT/MID)',
            category='Text',
            description='Extract a portion of text from a column (like Excel LEFT, RIGHT, MID functions)',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column to extract from'
                ),
                Parameter(
                    name='extract_type',
                    type='choice',
                    description='Type of extraction',
                    choices=['LEFT', 'RIGHT', 'MID'],
                    default='LEFT'
                ),
                Parameter(
                    name='num_chars',
                    type='number',
                    description='Number of characters to extract',
                    default=5
                ),
                Parameter(
                    name='start_position',
                    type='number',
                    description='Starting position (for MID only, 1-based)',
                    required=False,
                    default=1
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for the new column with extracted text',
                    default='Extracted'
                )
            ],
            excel_equivalent='LEFT(), RIGHT(), MID()',
            examples=[
                'LEFT 5 chars of "Hello World" → "Hello"',
                'RIGHT 5 chars of "Hello World" → "World"',
                'MID from position 7, 5 chars of "Hello World" → "World"'
            ],
            tags=['text', 'extract', 'left', 'right', 'mid', 'substring']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        extract_type = params['extract_type']
        num_chars = int(params['num_chars'])
        start_pos = int(self.get_param_value(params, 'start_position', 1))
        new_column = params['new_column']
        
        if extract_type == 'LEFT':
            df[new_column] = df[column].astype(str).str[:num_chars]
        elif extract_type == 'RIGHT':
            df[new_column] = df[column].astype(str).str[-num_chars:]
        else:  # MID
            # Convert to 0-based index
            start_idx = max(0, start_pos - 1)
            df[new_column] = df[column].astype(str).str[start_idx:start_idx + num_chars]
        
        return df


class RemoveRowsContainingOperation(BaseOperation):
    """Remove rows that contain specified text patterns"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='remove_rows_containing',
            name='Remove Rows Containing',
            category='Cleaning',
            description='Remove rows where specified columns contain any of the given text patterns. Great for removing PO Boxes, excluded states, etc.',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to search for patterns'
                ),
                Parameter(
                    name='patterns',
                    type='text',
                    description='Text patterns to match (comma-separated). Rows containing ANY of these will be removed.',
                    default='PO BOX, P.O. BOX, P O BOX'
                ),
                Parameter(
                    name='preset',
                    type='choice',
                    description='Use a preset pattern list',
                    choices=[
                        'Custom (use patterns above)',
                        'PO Boxes',
                        'Excluded States (AK, HI, PR, VI, GU)',
                        'Military Addresses (APO, FPO, DPO)',
                        'PO Boxes + Excluded States + Military'
                    ],
                    default='Custom (use patterns above)'
                ),
                Parameter(
                    name='case_sensitive',
                    type='boolean',
                    description='Match case exactly',
                    required=False,
                    default=False
                ),
                Parameter(
                    name='match_whole_cell',
                    type='boolean',
                    description='Only match if entire cell equals pattern (not contains)',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='Filter + Delete Rows',
            examples=[
                'Remove all PO Box addresses',
                'Remove rows with AK, HI, PR states',
                'Remove military APO/FPO addresses',
                'Remove specific company names or values'
            ],
            tags=['remove', 'delete', 'filter', 'contains', 'po box', 'exclude', 'states']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        preset = self.get_param_value(params, 'preset', 'Custom (use patterns above)')
        case_sensitive = self.get_param_value(params, 'case_sensitive', False)
        match_whole_cell = self.get_param_value(params, 'match_whole_cell', False)
        
        # Get patterns based on preset or custom input
        if preset == 'PO Boxes':
            patterns = ['PO BOX', 'P.O. BOX', 'P O BOX', 'P.O BOX', 'PO. BOX', 
                       'POST OFFICE BOX', 'POBOX', 'P.O.BOX']
        elif preset == 'Excluded States (AK, HI, PR, VI, GU)':
            patterns = ['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP', 'FM', 'MH', 'PW',
                       'ALASKA', 'HAWAII', 'PUERTO RICO', 'VIRGIN ISLANDS', 'GUAM']
        elif preset == 'Military Addresses (APO, FPO, DPO)':
            patterns = ['APO', 'FPO', 'DPO', 'APO AE', 'APO AP', 'APO AA', 
                       'FPO AE', 'FPO AP', 'FPO AA']
        elif preset == 'PO Boxes + Excluded States + Military':
            patterns = [
                # PO Boxes
                'PO BOX', 'P.O. BOX', 'P O BOX', 'P.O BOX', 'PO. BOX', 
                'POST OFFICE BOX', 'POBOX', 'P.O.BOX',
                # Excluded states
                'AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP',
                # Military
                'APO', 'FPO', 'DPO'
            ]
        else:
            # Custom patterns from user input
            patterns = [p.strip() for p in params['patterns'].split(',') if p.strip()]
        
        if not patterns:
            return df
        
        # Create mask for rows to keep
        mask = pd.Series([True] * len(df), index=df.index)
        
        for col in columns:
            col_data = df[col].astype(str)
            
            if not case_sensitive:
                col_data = col_data.str.upper()
                check_patterns = [p.upper() for p in patterns]
            else:
                check_patterns = patterns
            
            for pattern in check_patterns:
                if match_whole_cell:
                    # Exact match
                    matches = col_data == pattern
                else:
                    # Contains match
                    matches = col_data.str.contains(pattern, regex=False, na=False)
                
                # Update mask - mark rows with matches for removal
                mask = mask & ~matches

        # Return filtered dataframe WITHOUT reset_index
        # The executor needs original indices to track which rows were removed
        return df[mask]


class FlagRowsContainingOperation(BaseOperation):
    """Flag rows that contain specified patterns (adds a flag column instead of removing)"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='flag_rows_containing',
            name='Flag Rows Containing',
            category='Cleaning',
            description='Add a flag column to mark rows containing specified patterns. Useful for review before removal.',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to search for patterns'
                ),
                Parameter(
                    name='patterns',
                    type='text',
                    description='Text patterns to match (comma-separated)',
                    default='PO BOX, P.O. BOX'
                ),
                Parameter(
                    name='preset',
                    type='choice',
                    description='Use a preset pattern list',
                    choices=[
                        'Custom (use patterns above)',
                        'PO Boxes',
                        'Excluded States (AK, HI, PR, VI, GU)',
                        'Military Addresses (APO, FPO, DPO)',
                        'PO Boxes + Excluded States + Military'
                    ],
                    default='Custom (use patterns above)'
                ),
                Parameter(
                    name='flag_column',
                    type='text',
                    description='Name for the flag column',
                    default='_FLAG_REMOVE'
                ),
                Parameter(
                    name='flag_reason',
                    type='boolean',
                    description='Include which pattern was matched',
                    required=False,
                    default=True
                )
            ],
            excel_equivalent='Add helper column with IF/SEARCH',
            examples=[
                'Flag PO Box rows for review',
                'Flag excluded states before removal',
                'Mark rows for manual review'
            ],
            tags=['flag', 'mark', 'contains', 'review', 'filter']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        columns = params['columns']
        preset = self.get_param_value(params, 'preset', 'Custom (use patterns above)')
        flag_column = params['flag_column']
        flag_reason = self.get_param_value(params, 'flag_reason', True)
        
        # Get patterns based on preset
        if preset == 'PO Boxes':
            patterns = ['PO BOX', 'P.O. BOX', 'P O BOX', 'POST OFFICE BOX']
        elif preset == 'Excluded States (AK, HI, PR, VI, GU)':
            patterns = ['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP']
        elif preset == 'Military Addresses (APO, FPO, DPO)':
            patterns = ['APO', 'FPO', 'DPO']
        elif preset == 'PO Boxes + Excluded States + Military':
            patterns = ['PO BOX', 'P.O. BOX', 'AK', 'HI', 'PR', 'VI', 'GU', 'APO', 'FPO', 'DPO']
        else:
            patterns = [p.strip() for p in params['patterns'].split(',') if p.strip()]
        
        # Initialize flag column
        df[flag_column] = ''
        
        for col in columns:
            col_data = df[col].astype(str).str.upper()
            
            for pattern in patterns:
                pattern_upper = pattern.upper()
                matches = col_data.str.contains(pattern_upper, regex=False, na=False)
                
                if flag_reason:
                    # Add the matched pattern to the flag
                    df.loc[matches, flag_column] = df.loc[matches, flag_column].apply(
                        lambda x: f"{x}, {pattern}" if x else pattern
                    )
                else:
                    df.loc[matches, flag_column] = 'X'
        
        return df


class RemoveFlaggedRowsOperation(BaseOperation):
    """Remove rows that have been flagged"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='remove_flagged_rows',
            name='Remove Flagged Rows',
            category='Cleaning',
            description='Remove all rows where a flag column is not empty. Use after "Flag Rows Containing".',
            parameters=[
                Parameter(
                    name='flag_column',
                    type='column',
                    description='Column containing the flags'
                ),
                Parameter(
                    name='remove_flag_column',
                    type='boolean',
                    description='Also remove the flag column after filtering',
                    required=False,
                    default=True
                )
            ],
            excel_equivalent='Filter by flag column + Delete',
            examples=[
                'Remove all rows flagged for deletion',
                'Clean up after manual flag review'
            ],
            tags=['remove', 'delete', 'flag', 'filter']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        flag_column = params['flag_column']
        remove_flag_col = self.get_param_value(params, 'remove_flag_column', True)
        
        # Keep only rows where flag is empty
        mask = df[flag_column].astype(str).isin(['', 'nan', 'None', 'NaN']) | df[flag_column].isna()
        # Filter WITHOUT reset_index - executor needs original indices for tracking
        df = df[mask]

        # Remove flag column if requested
        if remove_flag_col and flag_column in df.columns:
            df = df.drop(columns=[flag_column])

        return df


# Register all standardization operations
registry.register(StandardizePhoneOperation())
registry.register(StandardizeZipCodeOperation())
registry.register(StandardizeStateOperation())
registry.register(StandardizeColumnNamesOperation())
registry.register(ParseContactNameOperation())
registry.register(ExtractTextOperation())
registry.register(RemoveRowsContainingOperation())
registry.register(FlagRowsContainingOperation())
registry.register(RemoveFlaggedRowsOperation())