"""
Header Row Detection Module
Automatically detects the correct header row in Excel files where Row 1 may contain metadata
"""

import pandas as pd
import json
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass


@dataclass
class HeaderRowCandidate:
    """Represents a potential header row"""
    row_index: int  # 0-based index
    row_data: List[str]
    confidence_score: float
    standard_columns_found: int
    total_columns: int
    reasoning: str


class HeaderRowDetector:
    """
    Detects the correct header row in Excel files

    Some files have metadata in Row 1 and actual headers in Row 2+
    This class identifies which row contains the real column headers
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize detector with configuration

        Args:
            config_path: Path to standard_format_config.json, or None to use default
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "standard_format_config.json"

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.header_config = self.config.get('header_detection', {})
        self.standard_columns = self.config.get('standard_columns', {})
        self.thresholds = self.config.get('detection_thresholds', {})

        # Build list of all standard column names and aliases for matching
        self.all_standard_names = set()
        for col_config in self.standard_columns.values():
            self.all_standard_names.add(col_config['primary_name'].lower())
            for alias in col_config.get('aliases', []):
                self.all_standard_names.add(alias.lower())

    def detect_header_row(self, file_path: str) -> HeaderRowCandidate:
        """
        Detect which row contains the actual column headers

        Args:
            file_path: Path to Excel file

        Returns:
            HeaderRowCandidate with highest confidence score
        """
        # Read first N rows without assuming headers
        max_rows = self.header_config.get('max_rows_to_scan', 5)

        # Read as plain data, no headers
        df = pd.read_excel(file_path, header=None, nrows=max_rows)

        candidates = []

        # Analyze each row as a potential header
        for idx in range(len(df)):
            candidate = self._analyze_row_as_header(df, idx)
            candidates.append(candidate)

        # Sort by confidence score (highest first)
        candidates.sort(key=lambda x: x.confidence_score, reverse=True)

        return candidates[0] if candidates else None

    def _analyze_row_as_header(self, df: pd.DataFrame, row_idx: int) -> HeaderRowCandidate:
        """
        Analyze a specific row to see if it's a header row

        Args:
            df: DataFrame with no headers
            row_idx: Row index to analyze (0-based)

        Returns:
            HeaderRowCandidate with confidence score
        """
        row_data = df.iloc[row_idx].tolist()
        row_data_str = [str(x).strip() if pd.notna(x) else '' for x in row_data]

        # Filter out empty columns
        non_empty = [x for x in row_data_str if x]

        if len(non_empty) < self.header_config.get('min_columns_for_header', 5):
            # Too few columns to be a real header row
            return HeaderRowCandidate(
                row_index=row_idx,
                row_data=row_data_str,
                confidence_score=0.0,
                standard_columns_found=0,
                total_columns=len(non_empty),
                reasoning="Too few non-empty columns"
            )

        # Check for metadata indicators (Export Date, Report, etc.)
        metadata_score = self._check_metadata_indicators(non_empty)

        # Check how many match standard column names
        standard_matches = self._count_standard_matches(non_empty)

        # Calculate confidence score
        confidence = self._calculate_confidence(
            len(non_empty),
            standard_matches,
            metadata_score,
            row_idx
        )

        # Determine reasoning
        if standard_matches >= self.header_config.get('min_standard_columns_match', 3):
            reasoning = f"Found {standard_matches} standard columns"
        elif metadata_score > 0.5:
            reasoning = "Contains metadata indicators"
        elif len(non_empty) < len(row_data_str) / 2:
            reasoning = "Too many empty columns"
        else:
            reasoning = "Low standard column match"

        return HeaderRowCandidate(
            row_index=row_idx,
            row_data=row_data_str,
            confidence_score=confidence,
            standard_columns_found=standard_matches,
            total_columns=len(non_empty),
            reasoning=reasoning
        )

    def _check_metadata_indicators(self, row_data: List[str]) -> float:
        """
        Check if row contains metadata indicators

        Returns:
            Score 0.0-1.0, higher means more likely metadata (NOT headers)
        """
        metadata_indicators = self.header_config.get('metadata_indicators', [])

        matches = 0
        for value in row_data:
            for indicator in metadata_indicators:
                if indicator.lower() in value.lower():
                    matches += 1
                    break

        # If many metadata indicators found, this is NOT a header row
        return min(1.0, matches / max(1, len(row_data)))

    def _count_standard_matches(self, row_data: List[str]) -> int:
        """
        Count how many values match standard column names

        Args:
            row_data: List of string values

        Returns:
            Number of matches to standard columns
        """
        matches = 0

        for value in row_data:
            value_lower = value.lower().strip()

            # Exact or fuzzy match to standard names
            if value_lower in self.all_standard_names:
                matches += 1
            elif any(std_name in value_lower for std_name in self.all_standard_names):
                matches += 0.5  # Partial match

        return int(matches)

    def _calculate_confidence(
        self,
        total_columns: int,
        standard_matches: int,
        metadata_score: float,
        row_idx: int
    ) -> float:
        """
        Calculate confidence score for a row being the header row

        Args:
            total_columns: Number of non-empty columns
            standard_matches: Number of standard column matches
            metadata_score: 0-1 score of metadata indicators (higher = more metadata)
            row_idx: Row index (0-based)

        Returns:
            Confidence score 0.0-1.0
        """
        # Base score from standard column matches
        if total_columns > 0:
            match_score = standard_matches / total_columns
        else:
            match_score = 0.0

        # Penalty for metadata indicators (metadata means NOT a header)
        metadata_penalty = metadata_score * 0.5

        # Small penalty for not being Row 0 (usually headers are first)
        row_penalty = row_idx * 0.05

        # Calculate final confidence
        confidence = match_score - metadata_penalty - row_penalty

        # Clamp to 0-1
        confidence = max(0.0, min(1.0, confidence))

        return confidence

    def should_skip_row(self, file_path: str) -> Tuple[bool, int]:
        """
        Determine if Row 0 should be skipped when loading the file

        Args:
            file_path: Path to Excel file

        Returns:
            Tuple of (should_skip, correct_header_row_index)
        """
        best_candidate = self.detect_header_row(file_path)

        if best_candidate is None:
            return False, 0

        threshold = self.thresholds.get('header_row_confidence', 0.70)

        # If best candidate is NOT row 0 and has good confidence
        if best_candidate.row_index > 0 and best_candidate.confidence_score >= threshold:
            return True, best_candidate.row_index

        # Row 0 is the header (normal case)
        return False, 0

    def get_header_report(self, file_path: str) -> Dict:
        """
        Get detailed report about header row detection

        Args:
            file_path: Path to Excel file

        Returns:
            Dictionary with detection results and recommendations
        """
        max_rows = self.header_config.get('max_rows_to_scan', 5)
        df = pd.read_excel(file_path, header=None, nrows=max_rows)

        candidates = []
        for idx in range(len(df)):
            candidate = self._analyze_row_as_header(df, idx)
            candidates.append(candidate)

        candidates.sort(key=lambda x: x.confidence_score, reverse=True)

        best = candidates[0]
        threshold = self.thresholds.get('header_row_confidence', 0.70)

        return {
            'recommended_header_row': best.row_index,
            'confidence': best.confidence_score,
            'confidence_level': self._get_confidence_level(best.confidence_score),
            'standard_columns_found': best.standard_columns_found,
            'total_columns': best.total_columns,
            'reasoning': best.reasoning,
            'should_use_different_row': best.row_index > 0 and best.confidence_score >= threshold,
            'row_0_data': candidates[0].row_data if len(candidates) > 0 else [],
            'recommended_row_data': best.row_data,
            'all_candidates': [
                {
                    'row': c.row_index,
                    'confidence': c.confidence_score,
                    'matches': c.standard_columns_found,
                    'reasoning': c.reasoning
                }
                for c in candidates
            ]
        }

    def _get_confidence_level(self, score: float) -> str:
        """Convert confidence score to human-readable level"""
        if score >= 0.90:
            return "Very High"
        elif score >= 0.70:
            return "High"
        elif score >= 0.50:
            return "Medium"
        else:
            return "Low"


def test_header_detection(file_path: str):
    """
    Test function to analyze a file's header row

    Args:
        file_path: Path to Excel file to analyze
    """
    detector = HeaderRowDetector()
    report = detector.get_header_report(file_path)

    print("=" * 60)
    print("HEADER ROW DETECTION REPORT")
    print("=" * 60)
    print(f"\nFile: {file_path}")
    print(f"\nRecommended Header Row: Row {report['recommended_header_row']}")
    print(f"Confidence: {report['confidence']:.2%} ({report['confidence_level']})")
    print(f"Standard Columns Found: {report['standard_columns_found']}/{report['total_columns']}")
    print(f"Reasoning: {report['reasoning']}")

    if report['should_use_different_row']:
        print(f"\n⚠️  WARNING: Row 0 is NOT the header row!")
        print(f"   Use Row {report['recommended_header_row']} instead.")
        print(f"\n   Row 0 contains: {report['row_0_data'][:3]}...")
        print(f"   Row {report['recommended_header_row']} contains: {report['recommended_row_data'][:5]}...")
    else:
        print("\n✓ Row 0 appears to be the correct header row.")

    print("\n" + "=" * 60)
    print("ALL CANDIDATES:")
    print("=" * 60)
    for candidate in report['all_candidates']:
        print(f"  Row {candidate['row']}: {candidate['confidence']:.2%} confidence")
        print(f"    Matches: {candidate['matches']}, {candidate['reasoning']}")

    return report


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_header_detection(sys.argv[1])
    else:
        print("Usage: python header_row_detector.py <excel_file_path>")
