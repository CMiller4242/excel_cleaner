"""Validation Operations"""
import pandas as pd
import re
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry

class ValidateEmailOperation(BaseOperation):
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='validate_email', name='Validate Email Addresses', category='Validation',
            description='Check if email addresses are properly formatted',
            parameters=[
                Parameter('column', 'column', 'Email column'),
                Parameter('flag_invalid', 'boolean', 'Create flag column for invalid emails', default=True)
            ],
            excel_equivalent='Complex IF formula',
            examples=['Flag invalid customer emails'],
            tags=['validate', 'email', 'check']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        col = params['column']
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if params.get('flag_invalid', True):
            df[f'{col}_Valid'] = df[col].astype(str).str.match(pattern)
        
        return df

class ValidateStateOperation(BaseOperation):
    """Validate and standardize US state codes"""

    # Valid US state codes
    VALID_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    }

    # State name to code mapping
    STATE_NAMES = {
        'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
        'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
        'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID',
        'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
        'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
        'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
        'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
        'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
        'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
        'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
        'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
        'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
        'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC'
    }

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='validate_state',
            name='Validate State Codes',
            category='Validation',
            description='Validate US state codes and optionally convert full names to 2-letter codes',
            parameters=[
                Parameter('column', 'column', 'State column'),
                Parameter('auto_convert', 'boolean', 'Convert full state names to codes', default=True),
                Parameter('flag_invalid', 'boolean', 'Create flag column for invalid states', default=True)
            ],
            excel_equivalent='Complex IF with lookup table',
            examples=[
                'Validate state codes (AL, CA, TX, etc.)',
                'Convert "Illinois" to "IL"',
                'Flag invalid state entries'
            ],
            tags=['validate', 'state', 'standardize', 'geography']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        col = params['column']
        auto_convert = params.get('auto_convert', True)
        flag_invalid = params.get('flag_invalid', True)

        def validate_and_convert_state(state_value):
            """Validate and optionally convert state to 2-letter code"""
            if pd.isna(state_value):
                return state_value, False

            state_str = str(state_value).strip().upper()

            # Already a valid 2-letter code
            if state_str in self.VALID_STATES:
                return state_str, True

            # Try to convert full name to code
            if auto_convert and state_str in self.STATE_NAMES:
                return self.STATE_NAMES[state_str], True

            # Invalid state
            return state_value, False

        # Apply validation and conversion
        results = df[col].apply(validate_and_convert_state)
        df[col] = results.apply(lambda x: x[0])

        if flag_invalid:
            df[f'{col}_Valid'] = results.apply(lambda x: x[1])

        return df

registry.register(ValidateEmailOperation())
registry.register(ValidateStateOperation())
