"""
Column Mapping Module
Maps incoming column names to Standard Format with confidence scoring
"""

import pandas as pd
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class ColumnMapping:
    """Represents a mapping from original column to standard format"""
    original_name: str
    standard_name: Optional[str]
    confidence: float
    action: str  # 'rename', 'keep', 'remove', 'review'
    reason: str
    matched_alias: Optional[str] = None


class ColumnMapper:
    """
    Maps column names to Standard Format

    Handles variations like:
    - "Email_Address" → "Email"
    - "Customer#" → "Customer"
    - "Phone_Direct" → "Phone"
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize mapper with configuration

        Args:
            config_path: Path to standard_format_config.json
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "standard_format_config.json"

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.standard_columns = self.config.get('standard_columns', {})
        self.optional_columns = self.config.get('optional_enhanced_columns', {})
        self.non_standard_patterns = self.config.get('non_standard_patterns', {})
        self.thresholds = self.config.get('detection_thresholds', {})

        # Build lookup dictionaries
        self._build_lookup_tables()

    def _build_lookup_tables(self):
        """Build lookup tables for fast matching"""
        # Exact matches (lowercase for case-insensitive comparison)
        self.exact_matches = {}

        # Process standard columns
        for col_id, col_config in self.standard_columns.items():
            primary = col_config['primary_name']

            # Add primary name
            self.exact_matches[primary.lower()] = (primary, 1.0, 'exact primary')

            # Add aliases
            for alias in col_config.get('aliases', []):
                self.exact_matches[alias.lower()] = (primary, 0.98, f'exact alias: {alias}')

        # Process optional columns
        for col_id, col_config in self.optional_columns.items():
            primary = col_config['primary_name']
            self.exact_matches[primary.lower()] = (primary, 1.0, 'exact primary (optional)')

            for alias in col_config.get('aliases', []):
                self.exact_matches[alias.lower()] = (primary, 0.98, f'exact alias: {alias} (optional)')

        # Compile non-standard patterns for removal
        self.removal_patterns = []
        for category, pattern_config in self.non_standard_patterns.items():
            for pattern in pattern_config.get('patterns', []):
                # Convert wildcard pattern to regex
                regex_pattern = pattern.replace('*', '.*')
                self.removal_patterns.append((re.compile(regex_pattern, re.IGNORECASE), category))

    def map_columns(self, df: pd.DataFrame) -> Dict[str, ColumnMapping]:
        """
        Map all columns in dataframe to Standard Format

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary of original_name → ColumnMapping
        """
        mappings = {}

        for original_col in df.columns:
            mapping = self._map_single_column(original_col)
            mappings[original_col] = mapping

        return mappings

    def _map_single_column(self, column_name: str) -> ColumnMapping:
        """
        Map a single column name to Standard Format

        Args:
            column_name: Original column name

        Returns:
            ColumnMapping object
        """
        # Clean the column name
        clean_name = str(column_name).strip()

        if not clean_name:
            return ColumnMapping(
                original_name=column_name,
                standard_name=None,
                confidence=0.0,
                action='remove',
                reason='Empty column name'
            )

        # Step 1: Try exact match (case-insensitive)
        exact_match = self._try_exact_match(clean_name)
        if exact_match:
            return exact_match

        # Step 2: Try fuzzy matching
        fuzzy_match = self._try_fuzzy_match(clean_name)
        if fuzzy_match and fuzzy_match.confidence >= self.thresholds.get('fuzzy_match_confidence', 0.85):
            return fuzzy_match

        # Step 3: Check if it should be removed (non-standard patterns)
        removal_check = self._check_removal_patterns(clean_name)
        if removal_check:
            return removal_check

        # Step 4: Unknown column - keep but flag for review
        return ColumnMapping(
            original_name=column_name,
            standard_name=None,
            confidence=0.0,
            action='review',
            reason='Unknown column, not in standard format'
        )

    def _try_exact_match(self, column_name: str) -> Optional[ColumnMapping]:
        """Try exact string match (case-insensitive)"""
        clean_lower = column_name.lower().strip().replace(' ', '_')

        # Try direct lookup
        if clean_lower in self.exact_matches:
            standard_name, confidence, reason = self.exact_matches[clean_lower]

            # If already matches, keep as-is
            if column_name == standard_name:
                return ColumnMapping(
                    original_name=column_name,
                    standard_name=standard_name,
                    confidence=1.0,
                    action='keep',
                    reason='Already in standard format',
                    matched_alias=standard_name
                )

            # Needs renaming
            return ColumnMapping(
                original_name=column_name,
                standard_name=standard_name,
                confidence=confidence,
                action='rename',
                reason=reason,
                matched_alias=column_name
            )

        return None

    def _try_fuzzy_match(self, column_name: str) -> Optional[ColumnMapping]:
        """Try fuzzy string matching"""
        clean_lower = column_name.lower().strip()

        best_match = None
        best_score = 0.0
        best_standard_name = None

        # Try fuzzy matching against all standard names and aliases
        for key, (standard_name, base_confidence, reason) in self.exact_matches.items():
            # Calculate similarity
            similarity = SequenceMatcher(None, clean_lower, key).ratio()

            # Adjust score based on length difference
            len_diff = abs(len(clean_lower) - len(key))
            if len_diff > 5:
                similarity *= 0.9

            if similarity > best_score:
                best_score = similarity
                best_standard_name = standard_name
                best_match = key

        threshold = self.thresholds.get('fuzzy_match_confidence', 0.85)

        if best_score >= threshold:
            return ColumnMapping(
                original_name=column_name,
                standard_name=best_standard_name,
                confidence=best_score,
                action='rename' if best_score >= 0.90 else 'review',
                reason=f'Fuzzy match to {best_match} ({best_score:.1%} similar)',
                matched_alias=best_match
            )

        return None

    def _check_removal_patterns(self, column_name: str) -> Optional[ColumnMapping]:
        """Check if column matches removal patterns"""
        for pattern, category in self.removal_patterns:
            if pattern.search(column_name):
                return ColumnMapping(
                    original_name=column_name,
                    standard_name=None,
                    confidence=0.0,
                    action='remove',
                    reason=f'Matches non-standard pattern: {category}'
                )

        return None

    def apply_mapping(self, df: pd.DataFrame, mappings: Dict[str, ColumnMapping], auto_apply: bool = False) -> pd.DataFrame:
        """
        Apply column mappings to dataframe

        Args:
            df: Original dataframe
            mappings: Dictionary of ColumnMapping objects
            auto_apply: If True, apply high-confidence mappings automatically

        Returns:
            New dataframe with renamed/removed columns
        """
        df_result = df.copy()

        # Step 1: Rename columns
        rename_dict = {}
        for orig_name, mapping in mappings.items():
            if mapping.action == 'rename':
                if auto_apply or mapping.confidence >= 0.95:
                    rename_dict[orig_name] = mapping.standard_name

        if rename_dict:
            df_result = df_result.rename(columns=rename_dict)

        # Step 2: Remove columns
        remove_cols = []
        for orig_name, mapping in mappings.items():
            if mapping.action == 'remove':
                if auto_apply or orig_name in df_result.columns:
                    remove_cols.append(orig_name)

        if remove_cols:
            # Only remove columns that still exist
            existing_remove_cols = [c for c in remove_cols if c in df_result.columns]
            if existing_remove_cols:
                df_result = df_result.drop(columns=existing_remove_cols)

        # Step 3: Reorder columns to standard format
        df_result = self.reorder_columns(df_result)

        return df_result

    def reorder_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reorder columns to match Standard Format sequence

        Args:
            df: DataFrame to reorder

        Returns:
            DataFrame with columns in standard order
        """
        # Get current columns
        current_cols = list(df.columns)

        # Build ordered list of standard columns present in dataframe
        ordered_cols = []
        remaining_cols = current_cols.copy()

        # Add standard columns in order
        for col_id, col_config in sorted(self.standard_columns.items(), key=lambda x: x[1]['order']):
            primary_name = col_config['primary_name']
            if primary_name in current_cols:
                ordered_cols.append(primary_name)
                remaining_cols.remove(primary_name)

        # Add optional columns in order
        for col_id, col_config in sorted(self.optional_columns.items(), key=lambda x: x[1]['order']):
            primary_name = col_config['primary_name']
            if primary_name in current_cols:
                ordered_cols.append(primary_name)
                if primary_name in remaining_cols:
                    remaining_cols.remove(primary_name)

        # Append any remaining columns at the end
        ordered_cols.extend(remaining_cols)

        return df[ordered_cols]

    def get_compliance_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate Standard Format compliance report

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary with compliance statistics
        """
        mappings = self.map_columns(df)

        # Count by action
        rename_count = sum(1 for m in mappings.values() if m.action == 'rename')
        remove_count = sum(1 for m in mappings.values() if m.action == 'remove')
        review_count = sum(1 for m in mappings.values() if m.action == 'review')
        keep_count = sum(1 for m in mappings.values() if m.action == 'keep')

        # Check which standard columns are present
        standard_cols_present = set()
        for mapping in mappings.values():
            if mapping.standard_name:
                standard_cols_present.add(mapping.standard_name)

        # Required standard columns
        required_cols = [
            col_config['primary_name']
            for col_config in self.standard_columns.values()
            if col_config.get('required', False)
        ]

        required_present = [col for col in required_cols if col in standard_cols_present]
        required_missing = [col for col in required_cols if col not in standard_cols_present]

        # Calculate compliance score
        total_standard = len(self.standard_columns)
        found_standard = len(standard_cols_present)
        compliance = (found_standard / total_standard) * 100

        return {
            'total_columns': len(df.columns),
            'standard_columns_found': found_standard,
            'total_standard_columns': total_standard,
            'compliance_percentage': compliance,
            'required_columns_present': required_present,
            'required_columns_missing': required_missing,
            'columns_to_rename': rename_count,
            'columns_to_remove': remove_count,
            'columns_to_review': review_count,
            'columns_already_standard': keep_count,
            'mappings': mappings
        }


def test_column_mapping(file_path: str):
    """
    Test function to analyze a file's column mapping

    Args:
        file_path: Path to Excel file
    """
    df = pd.read_excel(file_path)
    mapper = ColumnMapper()

    print("=" * 60)
    print("COLUMN MAPPING REPORT")
    print("=" * 60)

    mappings = mapper.map_columns(df)

    print(f"\nOriginal Columns ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")

    print("\n" + "=" * 60)
    print("MAPPING ANALYSIS:")
    print("=" * 60)

    for orig_name, mapping in mappings.items():
        action_symbol = {
            'rename': '➡️ ',
            'keep': '✓',
            'remove': '❌',
            'review': '⚠️ '
        }.get(mapping.action, '?')

        if mapping.action == 'rename':
            print(f"\n{action_symbol} {orig_name} → {mapping.standard_name}")
        elif mapping.action == 'remove':
            print(f"\n{action_symbol} {orig_name} (REMOVE)")
        elif mapping.action == 'keep':
            print(f"\n{action_symbol} {orig_name} (OK)")
        elif mapping.action == 'review':
            print(f"\n{action_symbol} {orig_name} (REVIEW)")

        print(f"   Confidence: {mapping.confidence:.1%}")
        print(f"   Reason: {mapping.reason}")

    # Get compliance report
    report = mapper.get_compliance_report(df)

    print("\n" + "=" * 60)
    print("STANDARD FORMAT COMPLIANCE:")
    print("=" * 60)
    print(f"\nCompliance Score: {report['compliance_percentage']:.1f}%")
    print(f"Standard Columns Found: {report['standard_columns_found']}/{report['total_standard_columns']}")
    print(f"\nRequired Columns Present: {len(report['required_columns_present'])}")
    for col in report['required_columns_present']:
        print(f"  ✓ {col}")

    if report['required_columns_missing']:
        print(f"\nRequired Columns MISSING: {len(report['required_columns_missing'])}")
        for col in report['required_columns_missing']:
            print(f"  ✗ {col}")

    print(f"\nActions Needed:")
    print(f"  Rename: {report['columns_to_rename']}")
    print(f"  Remove: {report['columns_to_remove']}")
    print(f"  Review: {report['columns_to_review']}")
    print(f"  Keep: {report['columns_already_standard']}")

    return report


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_column_mapping(sys.argv[1])
    else:
        print("Usage: python column_mapper.py <excel_file_path>")
