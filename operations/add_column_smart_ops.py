"""
Add New Column (Smart) Operations
Create new columns with constant values, timestamps, or smart/derived values
"""
import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry


class AddColumnSmartOperation(BaseOperation):
    """Create a new column with constant, timestamp, or smart/derived values"""

    # Valid US state abbreviations
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        'DC'  # District of Columbia
    }

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='add_column_smart',
            name='Add New Column (Smart)',
            category='Data Transformation',
            description='''Create a new column with values populated in three ways:

1. CONSTANT VALUE: Fill all rows with the same value
2. TIMESTAMP: Auto-generate the current date/time
3. SMART / DERIVED: Generate values based on other columns
   - Detect country from City/State/ZIP (currently supports USA only)
   - Extract domain from email (user@company.com → company.com)
   - Parse a full name into first or last name

This operation is different from Add Columns (math), which performs calculations.''',
            parameters=[
                Parameter(
                    name='new_column_name',
                    type='text',
                    description='Name for the new column'
                ),
                Parameter(
                    name='mode',
                    type='choice',
                    description='How to populate the column',
                    choices=['constant', 'timestamp', 'smart'],
                    default='constant'
                ),
                # Constant mode parameters
                Parameter(
                    name='constant_value',
                    type='text',
                    description='Value to fill (for Constant mode)',
                    required=False,
                    default=''
                ),
                # Timestamp mode parameters
                Parameter(
                    name='timestamp_format',
                    type='choice',
                    description='Date/time format (for Timestamp mode)',
                    choices=['YYYY-MM-DD', 'MM/DD/YYYY', 'ISO'],
                    required=False,
                    default='YYYY-MM-DD'
                ),
                # Smart mode parameters
                Parameter(
                    name='smart_rule',
                    type='choice',
                    description='Smart rule to apply (for Smart mode)',
                    choices=['country_from_location', 'email_domain', 'parse_name'],
                    required=False,
                    default='country_from_location'
                ),
                # Column mappings for smart rules
                Parameter(
                    name='city_column',
                    type='column',
                    description='City column (for country detection)',
                    required=False
                ),
                Parameter(
                    name='state_column',
                    type='column',
                    description='State column (for country detection)',
                    required=False
                ),
                Parameter(
                    name='zip_column',
                    type='column',
                    description='ZIP code column (for country detection)',
                    required=False
                ),
                Parameter(
                    name='email_column',
                    type='column',
                    description='Email column (for domain extraction)',
                    required=False
                ),
                Parameter(
                    name='full_name_column',
                    type='column',
                    description='Full name column (for name parsing)',
                    required=False
                ),
                Parameter(
                    name='name_part',
                    type='choice',
                    description='Choose which name part to extract',
                    choices=['first', 'last'],
                    required=False,
                    default='first'
                )
            ],
            excel_equivalent='Not directly equivalent — combines multiple functions',
            examples=[
                'Add "Source" column with value "Web Import"',
                'Add "Import Date" column with current date',
                'Add "Country" column detecting USA from state/ZIP',
                'Add "Company" column extracting domain from email',
                'Add "First Name" column parsing full name'
            ],
            tags=['add', 'column', 'smart', 'derived', 'timestamp', 'constant']
        )

    def validate_params(self, df: pd.DataFrame, params: Dict) -> tuple[bool, str]:
        """Validate parameters before execution"""
        # Base validation
        is_valid, error_msg = super().validate_params(df, params)
        if not is_valid:
            return False, error_msg

        mode = params.get('mode', 'constant')

        # Mode-specific validation
        if mode == 'constant':
            if 'constant_value' not in params:
                return False, "Constant value is required for Constant mode"

        elif mode == 'smart':
            smart_rule = params.get('smart_rule')
            if not smart_rule:
                return False, "Smart rule is required for Smart mode"

            # Validate required columns for each rule
            if smart_rule == 'country_from_location':
                city_col = params.get('city_column')
                state_col = params.get('state_column')
                zip_col = params.get('zip_column')

                missing = []
                if not city_col or not city_col.strip():
                    missing.append('City')
                if not state_col or not state_col.strip():
                    missing.append('State')
                if not zip_col or not zip_col.strip():
                    missing.append('ZIP')

                if missing:
                    return False, f"Country detection requires City, State, and ZIP columns. Please select all three. Missing: {', '.join(missing)}"

                # Validate columns exist in dataframe
                if city_col not in df.columns:
                    return False, f"City column '{city_col}' not found in data"
                if state_col not in df.columns:
                    return False, f"State column '{state_col}' not found in data"
                if zip_col not in df.columns:
                    return False, f"ZIP column '{zip_col}' not found in data"

            elif smart_rule == 'email_domain':
                email_col = params.get('email_column')
                if not email_col or not email_col.strip():
                    return False, "Email domain extraction requires selecting an Email column."
                if email_col not in df.columns:
                    return False, f"Email column '{email_col}' not found in data"

            elif smart_rule == 'parse_name':
                name_col = params.get('full_name_column')
                name_part = params.get('name_part')

                if not name_col or not name_col.strip():
                    return False, "Name parsing requires a Full Name column and selecting whether to extract 'first' or 'last'."
                if not name_part or name_part not in ['first', 'last']:
                    return False, "Name parsing requires selecting whether to extract 'first' or 'last'."
                if name_col not in df.columns:
                    return False, f"Full Name column '{name_col}' not found in data"

        return True, ""

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()

        new_col = params['new_column_name']
        mode = params.get('mode', 'constant')

        if mode == 'constant':
            # Constant value mode
            value = params.get('constant_value', '')
            df[new_col] = value

        elif mode == 'timestamp':
            # Timestamp mode
            timestamp_format = params.get('timestamp_format', 'YYYY-MM-DD')
            current_time = datetime.now()

            if timestamp_format == 'YYYY-MM-DD':
                df[new_col] = current_time.strftime('%Y-%m-%d')
            elif timestamp_format == 'MM/DD/YYYY':
                df[new_col] = current_time.strftime('%m/%d/%Y')
            elif timestamp_format == 'ISO':
                df[new_col] = current_time.isoformat()
            else:
                df[new_col] = current_time.strftime('%Y-%m-%d')

        elif mode == 'smart':
            # Smart/Derived mode
            smart_rule = params.get('smart_rule', 'country_from_location')

            if smart_rule == 'country_from_location':
                df[new_col] = self._detect_country(df, params)

            elif smart_rule == 'email_domain':
                df[new_col] = self._extract_email_domain(df, params)

            elif smart_rule == 'parse_name':
                df[new_col] = self._parse_name(df, params)

        return df

    def _detect_country(self, df: pd.DataFrame, params: Dict) -> pd.Series:
        """Detect country based on city/state/ZIP code"""
        result = pd.Series([''] * len(df), index=df.index)

        city_col = params.get('city_column')
        state_col = params.get('state_column')
        zip_col = params.get('zip_column')

        for idx, row in df.iterrows():
            is_usa = False

            # Check state column
            if state_col and state_col in df.columns:
                state_value = str(row[state_col]).strip().upper()
                if state_value in self.US_STATES:
                    is_usa = True

            # Check ZIP column (US ZIP codes are 5 or 9 digits)
            if not is_usa and zip_col and zip_col in df.columns:
                zip_value = str(row[zip_col]).strip()
                # Remove any dashes or spaces
                zip_clean = re.sub(r'[^0-9]', '', zip_value)
                # US ZIP is 5 digits or 9 digits (ZIP+4)
                if len(zip_clean) == 5 or len(zip_clean) == 9:
                    is_usa = True

            if is_usa:
                result.iloc[idx] = 'USA'

        return result

    def _extract_email_domain(self, df: pd.DataFrame, params: Dict) -> pd.Series:
        """Extract domain from email address"""
        email_col = params.get('email_column')

        if not email_col or email_col not in df.columns:
            return pd.Series([''] * len(df), index=df.index)

        def extract_domain(email):
            if pd.isna(email):
                return ''
            email_str = str(email).strip()
            if '@' in email_str:
                return email_str.split('@')[-1].lower()
            return ''

        return df[email_col].apply(extract_domain)

    def _parse_name(self, df: pd.DataFrame, params: Dict) -> pd.Series:
        """Parse full name into first or last name"""
        name_col = params.get('full_name_column')
        name_part = params.get('name_part', 'first')

        if not name_col or name_col not in df.columns:
            return pd.Series([''] * len(df), index=df.index)

        def parse_name(full_name):
            if pd.isna(full_name):
                return ''

            name_str = str(full_name).strip()
            if not name_str:
                return ''

            # Split by whitespace
            parts = name_str.split()

            if not parts:
                return ''

            if name_part == 'first':
                return parts[0]
            elif name_part == 'last':
                return parts[-1] if len(parts) > 1 else ''

            return ''

        return df[name_col].apply(parse_name)


# Register the operation
registry.register(AddColumnSmartOperation())
