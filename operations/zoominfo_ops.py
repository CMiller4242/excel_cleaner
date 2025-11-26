"""
ZoomInfo-Specific Operations
Operations designed for cleaning ZoomInfo export files
"""
import pandas as pd
import re
from typing import Dict, List
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry


class SplitAddressOperation(BaseOperation):
    """
    Splits address into Address 1 (street) and Address 2 (suite/unit)

    Two modes:
    1. Split Full Address: Split one column into Address 1 + Address 2 (NEW columns)
    2. Extract Suite from Address 1: Extract suite from Address 1 → move to Address 2 (EXISTING columns)

    Logic:
    1. Find LAST occurrence of any suite keyword (case-insensitive)
    2. Split at that point
    3. Address 1 = everything before suite keyword (trimmed)
    4. Address 2 = suite keyword + everything after (trimmed)
    5. If no suite keyword found: Address 1 = full address, Address 2 = blank
    """

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='zoominfo_split_address',
            name='Split Address - Street/Suite',
            category='ZoomInfo',
            description='''Split address into street and suite components.

TWO MODES:

1. Split Full Address (for unsplit addresses)
   Input: "150 BERGEN ST STE 1"
   Output: Address 1: "150 BERGEN ST"
           Address 2: "STE 1"

2. Extract Suite from Address 1 (for pre-split addresses)
   Input Address 1: "150 BERGEN ST STE 1"
   Input Address 2: "EVS"
   Output Address 1: "150 BERGEN ST"
          Address 2: "STE 1"
''',
            parameters=[
                Parameter(
                    name='mode',
                    type='choice',
                    description='Operation mode',
                    required=True,
                    choices=['Split Full Address', 'Extract Suite from Address 1'],
                    default='Split Full Address'
                ),
                Parameter(
                    name='source_column',
                    type='column',
                    description='Source column (full address OR Address 1)'
                ),
                Parameter(
                    name='address2_column',
                    type='column',
                    description='Address 2 column (for Extract Suite mode - where to put extracted suite)',
                    required=False
                ),
                Parameter(
                    name='suite_keywords',
                    type='text',
                    description='Suite keywords (comma-separated)',
                    required=False,
                    default='Ste,Suite,Suites,Unit,Units,Apt,Apartment,Bldg,Building,Floor,Flr,#,Room,Rm'
                ),
                Parameter(
                    name='address1_output',
                    type='text',
                    description='Output column name for street address (Split Full Address mode only)',
                    required=False,
                    default='Address 1'
                ),
                Parameter(
                    name='address2_output',
                    type='text',
                    description='Output column name for suite/unit (Split Full Address mode only)',
                    required=False,
                    default='Address 2'
                ),
                Parameter(
                    name='remove_original',
                    type='boolean',
                    description='Remove original column after split (Split Full Address mode only)',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='Text to Columns + Find/Replace',
            examples=[
                'Split "150 BERGEN ST STE 1" → "150 BERGEN ST" + "STE 1"',
                'Extract suite from Address 1 containing "150 BERGEN ST STE 1" → move "STE 1" to Address 2',
                'Split "3715 Northside Pkwy NW Bldg 300 Ste 110" → "3715 Northside Pkwy NW" + "Bldg 300 Ste 110"',
                'No suite: "251 Stenton Ave" → "251 Stenton Ave" + ""'
            ],
            tags=['zoominfo', 'address', 'split', 'suite', 'unit']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Execute address splitting based on selected mode"""
        df = df.copy()

        mode = params.get('mode', 'Split Full Address')
        source_col = params['source_column']

        # Parse suite keywords
        suite_keywords = params.get('suite_keywords',
            'Ste,Suite,Suites,Unit,Units,Apt,Apartment,Bldg,Building,Floor,Flr,#,Room,Rm')
        if isinstance(suite_keywords, str):
            suite_keywords = [kw.strip() for kw in suite_keywords.split(',')]

        # Validate source column
        if source_col not in df.columns:
            raise ValueError(f"Source column '{source_col}' not found")

        if mode == 'Split Full Address':
            return self._split_full_address(df, params, source_col, suite_keywords)
        else:  # Extract Suite from Address 1
            return self._extract_suite_from_address1(df, params, source_col, suite_keywords)

    def _split_full_address(self, df, params, source_col, suite_keywords):
        """
        Mode 1: Split full address into NEW Address 1 + Address 2 columns

        Example:
        Input: "150 BERGEN ST STE 1"
        Output: Address 1: "150 BERGEN ST", Address 2: "STE 1"
        """
        address1_col = params.get('address1_output', 'Address 1')
        address2_col = params.get('address2_output', 'Address 2')
        remove_original = params.get('remove_original', False)

        # Create pattern for finding suite keywords (case-insensitive)
        pattern_parts = [r'\b' + re.escape(kw) + r'\b' for kw in suite_keywords]
        pattern = '(' + '|'.join(pattern_parts) + ')'

        def split_address(address_str):
            if pd.isna(address_str) or str(address_str).strip() == '':
                return '', ''

            address_str = str(address_str).strip()

            # Find all matches of suite keywords
            matches = list(re.finditer(pattern, address_str, re.IGNORECASE))

            if not matches:
                # No suite keyword found - entire address goes to Address 1
                return address_str, ''

            # Use the LAST match (rightmost suite keyword)
            last_match = matches[-1]
            split_pos = last_match.start()

            # Everything before the suite keyword
            address1 = address_str[:split_pos].strip()

            # Suite keyword and everything after
            address2 = address_str[split_pos:].strip()

            return address1, address2

        # Apply splitting
        split_results = df[source_col].apply(split_address)
        df[address1_col] = split_results.apply(lambda x: x[0])
        df[address2_col] = split_results.apply(lambda x: x[1])

        # Remove original column if requested
        if remove_original and source_col in df.columns:
            df = df.drop(columns=[source_col])

        return df

    def _extract_suite_from_address1(self, df, params, address1_col, suite_keywords):
        """
        Mode 2: Extract suite from EXISTING Address 1 → move to Address 2

        Example:
        Input Address 1: "150 BERGEN ST STE 1"
        Input Address 2: "EVS" (or empty)

        Output Address 1: "150 BERGEN ST"
        Output Address 2: "STE 1"
        """
        address2_col = params.get('address2_column')

        if not address2_col or address2_col not in df.columns:
            raise ValueError(
                "For 'Extract Suite from Address 1' mode, you must specify the Address 2 column "
                "where extracted suite info will be moved."
            )

        # Create pattern for finding suite keywords (case-insensitive)
        pattern_parts = [r'\b' + re.escape(kw) + r'\b' for kw in suite_keywords]
        pattern = '(' + '|'.join(pattern_parts) + ')'

        def split_address(address_str):
            if pd.isna(address_str) or str(address_str).strip() == '':
                return '', ''

            address_str = str(address_str).strip()

            # Find all matches of suite keywords
            matches = list(re.finditer(pattern, address_str, re.IGNORECASE))

            if not matches:
                # No suite keyword found - leave address as-is
                return address_str, ''

            # Use the LAST match (rightmost suite keyword)
            last_match = matches[-1]
            split_pos = last_match.start()

            # Everything before the suite keyword
            street = address_str[:split_pos].strip()

            # Suite keyword and everything after
            suite = address_str[split_pos:].strip()

            return street, suite

        # Process each row
        for idx in df.index:
            address1 = df.at[idx, address1_col]

            if pd.isna(address1) or not str(address1).strip():
                continue

            # Split the address
            street, suite = split_address(str(address1))

            # Update Address 1 (remove suite)
            df.at[idx, address1_col] = street

            # Update Address 2 (add suite if found)
            if suite:
                df.at[idx, address2_col] = suite

        return df


class StateConverterOperation(BaseOperation):
    """
    Converts full state names to 2-letter codes

    Handles:
    - Full names: "Ohio" → "OH"
    - Abbreviations: "Ill." → "IL"
    - Case-insensitive: "ohio" → "OH"
    - Already 2-letter: "IL" → "IL" (no change)
    """

    # Comprehensive state mapping
    STATE_MAPPING = {
        # Full names
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
        'WISCONSIN': 'WI', 'WYOMING': 'WY',
        # District of Columbia
        'DISTRICT OF COLUMBIA': 'DC', 'WASHINGTON DC': 'DC', 'WASHINGTON D.C.': 'DC',
        # Territories
        'PUERTO RICO': 'PR', 'VIRGIN ISLANDS': 'VI', 'GUAM': 'GU',
        'AMERICAN SAMOA': 'AS', 'NORTHERN MARIANA ISLANDS': 'MP',
        # Common abbreviations
        'ALA': 'AL', 'ARIZ': 'AZ', 'ARK': 'AR', 'CALIF': 'CA', 'COLO': 'CO',
        'CONN': 'CT', 'DEL': 'DE', 'FLA': 'FL', 'ILL': 'IL', 'IND': 'IN',
        'KANS': 'KS', 'KAN': 'KS', 'KY': 'KY', 'LA': 'LA', 'MASS': 'MA',
        'MICH': 'MI', 'MINN': 'MN', 'MISS': 'MS', 'MO': 'MO', 'MONT': 'MT',
        'NEBR': 'NE', 'NEB': 'NE', 'NEV': 'NV', 'OKLA': 'OK', 'ORE': 'OR',
        'PENN': 'PA', 'PA': 'PA', 'TENN': 'TN', 'TEX': 'TX', 'VT': 'VT',
        'VA': 'VA', 'WASH': 'WA', 'WIS': 'WI', 'WYO': 'WY',
        # With periods
        'ALA.': 'AL', 'ARIZ.': 'AZ', 'ARK.': 'AR', 'CALIF.': 'CA', 'COLO.': 'CO',
        'CONN.': 'CT', 'DEL.': 'DE', 'FLA.': 'FL', 'ILL.': 'IL', 'IND.': 'IN',
        'KANS.': 'KS', 'MASS.': 'MA', 'MICH.': 'MI', 'MINN.': 'MN', 'MISS.': 'MS',
        'MONT.': 'MT', 'NEBR.': 'NE', 'NEV.': 'NV', 'OKLA.': 'OK', 'ORE.': 'OR',
        'PENN.': 'PA', 'TENN.': 'TN', 'TEX.': 'TX', 'WASH.': 'WA', 'WIS.': 'WI',
        'WYO.': 'WY',
    }

    # Valid 2-letter codes (for validation)
    VALID_CODES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        'DC', 'PR', 'VI', 'GU', 'AS', 'MP'
    }

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='zoominfo_state_converter',
            name='Convert State Names to Codes',
            category='ZoomInfo',
            description='Convert full state names to 2-letter codes (e.g., "Ohio" → "OH")',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column containing state names or codes'
                ),
                Parameter(
                    name='flag_unconverted',
                    type='boolean',
                    description='Create flag column for values that could not be converted',
                    required=False,
                    default=False
                )
            ],
            excel_equivalent='VLOOKUP or Find & Replace (manual)',
            examples=[
                'Convert "Ohio" to "OH"',
                'Convert "Illinois" to "IL"',
                'Convert "Virgin Islands" to "VI"',
                'Leave "IL" as "IL" (already correct)',
                'Handle "Ill." → "IL"'
            ],
            tags=['zoominfo', 'state', 'convert', 'standardize']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        column = params['column']
        flag_unconverted = params.get('flag_unconverted', False)

        def convert_state(state_value):
            if pd.isna(state_value):
                return state_value, False

            state_str = str(state_value).strip().upper()

            # If already a valid 2-letter code, return as-is
            if state_str in self.VALID_CODES:
                return state_str, True

            # Try to find in mapping
            if state_str in self.STATE_MAPPING:
                return self.STATE_MAPPING[state_str], True

            # Could not convert
            return state_value, False

        # Apply conversion
        results = df[column].apply(convert_state)
        df[column] = results.apply(lambda x: x[0])

        if flag_unconverted:
            df[f'{column}_Converted'] = results.apply(lambda x: x[1])

        return df


class RemoveExcludedStatesOperation(BaseOperation):
    """
    Removes rows where state code is in excluded list
    Default excludes: AK, HI, PR, VI (Alaska, Hawaii, Puerto Rico, Virgin Islands)
    """

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='remove_excluded_states',
            name='Remove Excluded States',
            category='ZoomInfo',
            description='Remove rows with specific state codes (e.g., AK, HI, PR, VI)',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column containing state codes'
                ),
                Parameter(
                    name='excluded_states',
                    type='list',
                    description='State codes to exclude (comma-separated)',
                    required=False,
                    default='AK,HI,PR,VI'
                )
            ],
            excel_equivalent='Filter and delete rows',
            examples=[
                'Remove Alaska (AK) and Hawaii (HI) for mainland-only campaigns',
                'Remove territories (PR, VI, GU)',
                'Custom exclusions based on shipping restrictions'
            ],
            tags=['zoominfo', 'state', 'filter', 'remove', 'exclude']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        column = params['column']

        # Parse excluded states
        excluded_states = params.get('excluded_states', 'AK,HI,PR,VI')
        if isinstance(excluded_states, str):
            excluded_states = [state.strip().upper() for state in excluded_states.split(',')]
        else:
            excluded_states = [state.upper() for state in excluded_states]

        # Filter out excluded states (case-insensitive)
        mask = ~df[column].astype(str).str.upper().isin(excluded_states)

        # Return filtered dataframe WITHOUT reset_index
        # The executor needs original indices to track which rows were removed
        return df[mask]


# Register all ZoomInfo operations
registry.register(SplitAddressOperation())
registry.register(StateConverterOperation())
registry.register(RemoveExcludedStatesOperation())
