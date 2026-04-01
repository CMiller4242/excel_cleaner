"""
Formstack-Specific Operations
Operations designed for processing Formstack-style partial survey submissions
"""
import math
import re
import pandas as pd
from typing import Dict, Optional, Tuple
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry

# Map Excel month abbreviations back to month numbers (for Excel date-conversion bug)
_MONTH_ABBR_MAP = {
    'jan': '1', 'feb': '2', 'mar': '3', 'apr': '4',
    'may': '5', 'jun': '6', 'jul': '7', 'aug': '8',
    'sep': '9', 'oct': '10', 'nov': '11', 'dec': '12',
}


def normalize_range_text(value) -> Optional[str]:
    """Convert value to stripped string; return None for blank/NaN."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    return text if text else None


def fix_excel_date_range(text: str) -> str:
    """
    Excel sometimes auto-converts '1-50' → 'Jan-50'.
    Detect that pattern and convert back to numeric form.

    Matches: <MonthAbbr>-<number>  e.g. 'Jan-50', 'Feb-250'
    """
    pattern = re.compile(
        r'^([A-Za-z]{3})-(\d+)$'
    )
    match = pattern.match(text.strip())
    if match:
        abbr = match.group(1).lower()
        rest = match.group(2)
        if abbr in _MONTH_ABBR_MAP:
            return f"{_MONTH_ABBR_MAP[abbr]}-{rest}"
    return text


def parse_numeric_range(text: str) -> Optional[Tuple[float, float]]:
    """
    Parse a range string and return (low, high).

    Supported formats:
      - '1-50'          → (1, 50)
      - '100-250'       → (100, 250)
      - '$5-$10'        → (5, 10)
      - '$5 - $10'      → (5, 10)
      - '10-20'         → (10, 20)
      - '500+'          → (500, 500)   # plus = use value itself as both bounds

    Returns None if the text cannot be parsed.
    """
    if not text:
        return None

    text = text.strip()

    # Handle "plus" values like '500+' or '$500+'
    plus_match = re.match(r'^\$?\s*(\d+(?:\.\d+)?)\s*\+$', text)
    if plus_match:
        val = float(plus_match.group(1))
        return (val, val)

    # Remove all dollar signs and spaces around the dash separator
    # Normalise: '$5 - $10' → '5-10'
    cleaned = re.sub(r'\$', '', text)
    # Collapse whitespace around the dash so '5 - 10' becomes '5-10'
    cleaned = re.sub(r'\s*-\s*', '-', cleaned).strip()

    range_match = re.match(r'^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$', cleaned)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return (low, high)

    return None


def floor_average_range(text: str) -> Optional[int]:
    """
    Parse a range string and return the floor of the midpoint average.

    '1-50'   → floor((1+50)/2)  = floor(25.5) = 25
    '10-20'  → floor((10+20)/2) = floor(15.0) = 15
    '500+'   → 500
    Returns None if unparseable.
    """
    # Fix Excel date-conversion issue before parsing
    text = fix_excel_date_range(text)

    bounds = parse_numeric_range(text)
    if bounds is None:
        return None

    low, high = bounds
    return math.floor((low + high) / 2)


def detect_entity_type(column_name: str) -> str:
    """
    Detect the entity type keyword from the quantity column name.

    Rules (case-insensitive, checked in order):
      'student'  → 'Students'
      'employee' → 'Employees'
      'staff'    → 'Staff'
      default    → 'Employees'
    """
    lower = column_name.lower()
    if 'student' in lower:
        return 'Students'
    if 'employee' in lower:
        return 'Employees'
    if 'staff' in lower:
        return 'Staff'
    return 'Employees'


class FormstackPartialLeadScoringOperation(BaseOperation):
    """
    Formstack Partial Lead Scoring

    Reads two user-selected range columns (quantity and budget),
    computes floor-averaged values, and produces three output columns:
      - Average Number of {Type}
      - Budget per {Type}
      - Lead Score  (= quantity_avg * budget_avg, always integer)

    Output column names adapt based on keywords found in the quantity column name
    (student → Students, employee → Employees, staff → Staff, default → Employees).
    """

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='formstack_partial_lead_scoring',
            name='Formstack Partial Lead Scoring',
            category='Formstack',
            description=(
                'Calculate lead scores from Formstack survey range columns.\n\n'
                'Parses quantity (e.g. number-of-employees) and budget range columns, '
                'computes floor averages, and outputs:\n'
                '  • Average Number of {Type}\n'
                '  • Budget per {Type}\n'
                '  • Lead Score\n\n'
                'Handles Excel date-conversion bug (e.g. "Jan-50" → "1-50").\n'
                'All values are floored integers — no decimals.'
            ),
            parameters=[
                Parameter(
                    name='quantity_column',
                    type='column',
                    description='Select the column containing number-of-employees/students range (e.g. "1-50", "100-250", "500+")'
                ),
                Parameter(
                    name='budget_column',
                    type='column',
                    description='Select the column containing budget-per-unit range (e.g. "$5-$10", "$20 - $30")'
                ),
            ],
            excel_equivalent='Custom formula: =FLOOR((LEFT+RIGHT)/2, 1) * budget_avg',
            examples=[
                'Qty "1-50" + Budget "$5-$10" → Avg Qty=25, Avg Budget=7, Lead Score=175',
                'Qty "100-250" + Budget "$10-$20" → Avg Qty=175, Avg Budget=15, Lead Score=2625',
                'Qty "500+" + Budget "$20-$30" → Avg Qty=500, Avg Budget=25, Lead Score=12500',
                'Excel date bug: "Jan-50" treated as "1-50" automatically',
            ],
            tags=['formstack', 'lead', 'score', 'survey', 'range', 'budget', 'employees', 'students']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()

        qty_col = params['quantity_column']
        budget_col = params['budget_column']

        # Determine dynamic entity type from quantity column name
        entity_type = detect_entity_type(qty_col)

        avg_qty_col = f'Average Number of {entity_type}'
        avg_budget_col = f'Budget per {entity_type}'
        lead_score_col = 'Lead Score'

        def compute_qty(value) -> Optional[int]:
            text = normalize_range_text(value)
            if text is None:
                return None
            return floor_average_range(text)

        def compute_budget(value) -> Optional[int]:
            text = normalize_range_text(value)
            if text is None:
                return None
            return floor_average_range(text)

        df[avg_qty_col] = df[qty_col].apply(compute_qty)
        df[avg_budget_col] = df[budget_col].apply(compute_budget)

        def compute_lead_score(row) -> Optional[int]:
            qty = row[avg_qty_col]
            budget = row[avg_budget_col]
            if pd.isna(qty) or pd.isna(budget):
                return None
            return int(qty) * int(budget)

        df[lead_score_col] = df.apply(compute_lead_score, axis=1)

        # Ensure integer dtype where possible (keeps NaN rows as nullable int)
        for col in (avg_qty_col, avg_budget_col, lead_score_col):
            df[col] = pd.array(df[col], dtype=pd.Int64Dtype())

        return df

    def validate_params(self, df: pd.DataFrame, params: Dict) -> tuple:
        qty_col = params.get('quantity_column')
        budget_col = params.get('budget_column')

        if not qty_col:
            return False, "Quantity Range Column is required."
        if not budget_col:
            return False, "Budget Range Column is required."
        if qty_col not in df.columns:
            return False, f"Quantity column '{qty_col}' not found in data."
        if budget_col not in df.columns:
            return False, f"Budget column '{budget_col}' not found in data."

        return True, ""


# Register the operation
registry.register(FormstackPartialLeadScoringOperation())
