"""
Filter Operations
Row-filter operations for geographic and data-quality filtering.
"""

import pandas as pd
from typing import Any, Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry


# ---------------------------------------------------------------------------
# Lower-48 constants
# ---------------------------------------------------------------------------

LOWER_48_ABBREV = {
    'AL', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
    'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA',
    'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA',
    'WV', 'WI', 'WY',
}

# DC is deliberately omitted from LOWER_48_ABBREV; added dynamically when
# the user enables the "include_dc" option.

# All 50 states + DC + territories — used for normalization look-ups.
# AK and HI are present so their full names can be normalised then rejected.
STATE_NAME_TO_ABBREV: Dict[str, str] = {
    'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
    'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT',
    'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI',
    'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
    'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME',
    'MARYLAND': 'MD', 'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI',
    'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS', 'MISSOURI': 'MO',
    'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
    'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM',
    'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND',
    'OHIO': 'OH', 'OKLAHOMA': 'OK', 'OREGON': 'OR',
    'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
    'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
    'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA',
    'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY',
    'DISTRICT OF COLUMBIA': 'DC', 'WASHINGTON DC': 'DC',
    'WASHINGTON D.C.': 'DC',
    # Territories (normalise to abbreviation so they can be rejected)
    'PUERTO RICO': 'PR', 'VIRGIN ISLANDS': 'VI', 'GUAM': 'GU',
    'AMERICAN SAMOA': 'AS', 'NORTHERN MARIANA ISLANDS': 'MP',
}

# USA country variants accepted when country-column enforcement is enabled
_USA_VARIANTS = {'US', 'USA', 'UNITED STATES', 'UNITED STATES OF AMERICA'}


# ---------------------------------------------------------------------------
# Normalisation helper
# ---------------------------------------------------------------------------

def normalize_state(value: Any) -> str:
    """
    Normalise a raw state value to an uppercase 2-letter abbreviation.

    Steps
    -----
    1. Return '' for None / NaN / empty.
    2. Convert to str, strip whitespace, uppercase.
    3. Remove periods and collapse multiple spaces.
    4. If already a known 2-letter abbreviation, return it.
    5. Look up full name in STATE_NAME_TO_ABBREV.
    6. If still unresolved, return the cleaned string as-is so it will
       fail the allow-list check.

    Examples
    --------
    >>> normalize_state('New York')  -> 'NY'
    >>> normalize_state('N.Y.')      -> 'NY'
    >>> normalize_state(' ny ')      -> 'NY'
    >>> normalize_state(None)        -> ''
    >>> normalize_state('Canada')    -> 'CANADA'  (will fail allow-list)
    """
    if value is None:
        return ''
    try:
        if pd.isna(value):
            return ''
    except (TypeError, ValueError):
        pass

    cleaned = str(value).strip().upper()
    # Remove periods and collapse extra spaces
    cleaned = cleaned.replace('.', '').replace('  ', ' ').strip()

    if not cleaned:
        return ''

    # Already a valid 2-letter abbreviation?
    if len(cleaned) == 2 and cleaned.isalpha():
        return cleaned  # Return as-is; allow-list check happens later

    # Full-name lookup
    if cleaned in STATE_NAME_TO_ABBREV:
        return STATE_NAME_TO_ABBREV[cleaned]

    # Return cleaned string — it will fail the allow-list check
    return cleaned


# ---------------------------------------------------------------------------
# Operation class
# ---------------------------------------------------------------------------

class FilterLower48Operation(BaseOperation):
    """Keep only rows with a state in the contiguous Lower 48 U.S. states."""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='filter_lower_48',
            name='Filter to Lower 48 States',
            category='Cleaning',
            description=(
                'Keep only contiguous U.S. states (lower 48). '
                'Excludes AK/HI, territories (PR, VI, GU …), '
                'foreign countries, and optionally blank/invalid states.'
            ),
            parameters=[
                Parameter(
                    name='state_column',
                    type='column',
                    description='State column (required)',
                    required=True,
                ),
                Parameter(
                    name='country_column',
                    type='text',
                    description='Country column name (optional — leave blank to skip country check)',
                    required=False,
                    default='',
                ),
                Parameter(
                    name='normalize_states',
                    type='boolean',
                    description='Normalize full state names to abbreviations (e.g. "New York" → "NY")',
                    required=False,
                    default=True,
                ),
                Parameter(
                    name='remove_blank_states',
                    type='boolean',
                    description='Remove rows with blank or unrecognised state',
                    required=False,
                    default=True,
                ),
                Parameter(
                    name='require_usa_country',
                    type='boolean',
                    description='Require USA in Country column (only used when Country column is set)',
                    required=False,
                    default=True,
                ),
                Parameter(
                    name='allow_blank_country',
                    type='boolean',
                    description='Allow rows where Country is blank (only used when Country column is set)',
                    required=False,
                    default=True,
                ),
                Parameter(
                    name='include_dc',
                    type='boolean',
                    description='Include DC (Washington D.C.) in the Lower 48 allow-list',
                    required=False,
                    default=False,
                ),
            ],
            excel_equivalent='Filter by State column → Delete rows',
            examples=[
                'Remove Alaska/Hawaii from a US-only mailing list',
                'Keep only contiguous-US contacts from an international dataset',
                'Filter out Puerto Rico and other territories',
            ],
            tags=[
                'filter', 'remove', 'state', 'lower 48', 'usa', 'geography',
                'alaska', 'hawaii', 'mailing list',
            ],
        )

    # ------------------------------------------------------------------
    # validate_params — override to handle optional country column
    # ------------------------------------------------------------------

    def validate_params(self, df: pd.DataFrame, params: Dict) -> tuple:
        """
        Non-fatal: missing state column → (False, message).
        Missing country column is only an error when enforce is ON and the
        column name is non-empty.
        """
        state_col = params.get('state_column', '')
        if not state_col:
            return False, "State column is required."
        if state_col not in df.columns:
            return False, f"State column '{state_col}' not found in data."

        country_col = params.get('country_column', '').strip()
        if country_col and country_col not in df.columns:
            return False, f"Country column '{country_col}' not found in data."

        return True, ''

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()

        state_col = params['state_column']
        country_col = params.get('country_column', '').strip()
        normalize = self.get_param_value(params, 'normalize_states', True)
        remove_blank = self.get_param_value(params, 'remove_blank_states', True)
        require_usa = self.get_param_value(params, 'require_usa_country', True)
        allow_blank_country = self.get_param_value(params, 'allow_blank_country', True)
        include_dc = self.get_param_value(params, 'include_dc', False)

        # Build the effective allow-list
        allow_set = set(LOWER_48_ABBREV)
        if include_dc:
            allow_set.add('DC')

        # --- normalise state column into a working series ---
        raw_states = df[state_col]
        if normalize:
            norm_states = raw_states.apply(normalize_state)
        else:
            # Still clean but don't do full-name → abbrev mapping
            norm_states = raw_states.apply(
                lambda v: '' if (v is None or (isinstance(v, float) and pd.isna(v)))
                else str(v).strip().upper().replace('.', '')
            )

        # --- build keep mask ---
        # Start: keep everything
        keep = pd.Series(True, index=df.index)

        # 1. Blank / invalid state
        is_blank_state = norm_states == ''
        if remove_blank:
            keep &= ~is_blank_state
        # (if remove_blank is False, blank states pass through untouched)

        # 2. State not in Lower 48 (only for non-blank states)
        not_in_lower48 = ~norm_states.isin(allow_set) & ~is_blank_state
        keep &= ~not_in_lower48

        # 3. Country column enforcement
        if country_col and country_col in df.columns and require_usa:
            raw_country = df[country_col].astype(str).str.strip().str.upper()

            # Blank country check
            is_blank_country = raw_country.isin(['', 'NAN', 'NONE', 'NAT', '<NA>'])

            # Is it a recognised USA variant?
            is_usa = raw_country.isin(_USA_VARIANTS)

            # Row passes country check if:
            #   - it's a USA variant, OR
            #   - it's blank AND allow_blank_country is True
            country_ok = is_usa | (is_blank_country & allow_blank_country)
            keep &= country_ok

        # --- return kept rows WITHOUT resetting index ---
        # (executor compares before/after indices to track removed rows)
        return df[keep]


# Register the operation
registry.register(FilterLower48Operation())
