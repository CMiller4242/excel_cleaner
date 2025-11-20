"""
Compare current is_blank implementation vs proposed classify_blank implementation

This test compares:
1. Current implementation: Only pd.isna() (returns True for NaN/None only)
2. Proposed implementation: classify_blank (returns True for NaN/None/empty/"N/A" variants)
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/user/excel_cleaner')

from operations.data_ops import RemoveRowsIfOperation

def classify_blank(value):
    """
    Proposed: Normalize a value into either '(blank)' or 'data'.

    Blank includes:
    - NaN / None
    - Empty strings
    - Strings like: n/a, na, null, none
    """
    if value is None or pd.isna(value):
        return True

    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in ["", "n/a", "na", "null", "none"]:
            return True

    return False

def analyze_column(series: pd.Series):
    """
    Accepts a Pandas Series (a single column) and returns:
    - blank_count using current implementation
    - blank_count using proposed implementation
    """
    # Current implementation (only pd.isna)
    current_blank_count = series.isna().sum()

    # Proposed implementation (classify_blank)
    proposed_labels = series.apply(classify_blank)
    proposed_blank_count = proposed_labels.sum()

    return {
        "current_blank_count": current_blank_count,
        "proposed_blank_count": proposed_blank_count,
        "current_data_count": len(series) - current_blank_count,
        "proposed_data_count": len(series) - proposed_blank_count
    }

def test_with_actual_file():
    """Test both implementations with actual file"""

    print("=" * 100)
    print("COMPARISON: Current is_blank vs Proposed classify_blank")
    print("=" * 100)

    # Load the file
    filename = 'Volunteer Directors 11.20.25.xlsx'
    print(f"\n[1] Loading file: {filename}")
    df = pd.read_excel(filename)
    print(f"    Total rows: {len(df):,}")

    # Analyze Person Street column with both methods
    print(f"\n[2] Analyzing 'Person Street' column:")
    result = analyze_column(df['Person Street'])

    print(f"\n    CURRENT Implementation (pd.isna only):")
    print(f"      Blank values: {result['current_blank_count']:,}")
    print(f"      Data values: {result['current_data_count']:,}")

    print(f"\n    PROPOSED Implementation (classify_blank):")
    print(f"      Blank values: {result['proposed_blank_count']:,}")
    print(f"      Data values: {result['proposed_data_count']:,}")

    print(f"\n    DIFFERENCE:")
    diff = result['proposed_blank_count'] - result['current_blank_count']
    print(f"      Additional values treated as blank: {diff:,}")

    # Test specific values
    print(f"\n[3] Testing specific values:")
    test_values = [
        "6600 N Lincoln Ave Ste 300",
        "2150 Post St",
        "4205 NW 6th St",
        "1718 Patterson St",
        "36 S State St",
        np.nan,
        None,
        "",
        "   ",
        "N/A",
        "n/a",
        "NA",
        "null",
        "None"
    ]

    print(f"\n    {'Value':<40} {'Current':<12} {'Proposed':<12} {'Diff'}")
    print("    " + "-" * 80)

    for val in test_values:
        current = pd.isna(val)
        proposed = classify_blank(val)
        diff_mark = '✗' if current != proposed else ''

        print(f"    {repr(val):<40} {str(current):<12} {str(proposed):<12} {diff_mark}")

    # Test with current operation
    print(f"\n[4] Testing with CURRENT RemoveRowsIfOperation:")
    operation = RemoveRowsIfOperation()
    params = {'column': 'Person Street', 'condition': 'is_blank'}

    current_result_df = operation.execute(df, params)
    current_removed_indices = set(df.index) - set(current_result_df.index)
    current_removed_df = df.loc[list(current_removed_indices)]

    print(f"    Results: {len(current_result_df):,} rows")
    print(f"    Removed: {len(current_removed_df):,} rows")

    current_valid_removed = current_removed_df['Person Street'].notna().sum()
    print(f"    Valid (non-NaN) values in Removed: {current_valid_removed:,}")

    if current_valid_removed > 0:
        print(f"\n    Non-NaN values that were removed:")
        for val in current_removed_df[current_removed_df['Person Street'].notna()]['Person Street'].head(10):
            print(f"      - {repr(val)}")

    # Test with proposed logic
    print(f"\n[5] Testing with PROPOSED classify_blank logic:")
    proposed_mask = df['Person Street'].apply(classify_blank)
    proposed_result_df = df[~proposed_mask].copy()
    proposed_removed_df = df[proposed_mask].copy()

    print(f"    Results: {len(proposed_result_df):,} rows")
    print(f"    Removed: {len(proposed_removed_df):,} rows")

    # Check what additional values the proposed method would remove
    additional_removed_indices = set(proposed_removed_df.index) - set(current_removed_df.index)
    if additional_removed_indices:
        additional_removed = df.loc[list(additional_removed_indices)]
        print(f"\n    Additional values removed by PROPOSED (not by CURRENT): {len(additional_removed):,}")
        print(f"    Examples:")
        for val in additional_removed['Person Street'].head(10):
            print(f"      - {repr(val)}")

    # Check for addresses in removed
    print(f"\n[6] Checking specific problem addresses:")
    problem_addresses = [
        "6600 N Lincoln Ave Ste 300",
        "2150 Post St",
        "4205 NW 6th St",
        "1718 Patterson St",
        "36 S State St"
    ]

    for addr in problem_addresses:
        in_current_removed = addr in current_removed_df['Person Street'].values
        in_proposed_removed = addr in proposed_removed_df['Person Street'].values

        current_status = '✗ REMOVED' if in_current_removed else '✓ KEPT'
        proposed_status = '✗ REMOVED' if in_proposed_removed else '✓ KEPT'

        print(f"    {addr:<35}")
        print(f"      Current:  {current_status}")
        print(f"      Proposed: {proposed_status}")

    # Final recommendation
    print(f"\n{'=' * 100}")
    print("RECOMMENDATION")
    print(f"{'=' * 100}")

    if current_valid_removed == 0:
        print("\n✓ CURRENT implementation is working correctly:")
        print(f"  - Zero false positives (no valid addresses removed)")
        print(f"  - All {len(current_result_df):,} rows with data are kept")
        print(f"  - Only {len(current_removed_df):,} actual NaN values are removed")
        print(f"\nPROPOSED implementation would additionally remove:")
        print(f"  - Empty strings ('')")
        print(f"  - 'N/A', 'na', 'null', 'none' variants")
        print(f"\nRECOMMENDATION: Keep CURRENT implementation (pd.isna only)")
        print("  - It's simpler and more predictable")
        print("  - Users can use 'Remove Rows Containing' for N/A variants if needed")
    else:
        print(f"\n✗ CURRENT implementation has {current_valid_removed} false positives")
        print(f"  PROPOSED implementation may be better - needs investigation")

if __name__ == '__main__':
    test_with_actual_file()
