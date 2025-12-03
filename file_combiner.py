"""
Clean Sheet - File Combiner
Handles combining multiple files with column matching and grouping
"""

import pandas as pd
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class FileCombiner:
    """
    Combine multiple files with various strategies

    Features:
    - Merge all files into one
    - Group files by column value
    - Column mismatch detection and handling
    - Flexible column matching strategies
    """

    def __init__(self):
        self.combined_data = None
        self.column_mismatch_info = None

    def check_column_compatibility(self, files: List[Dict]) -> Tuple[bool, Dict]:
        """
        Check if all files have compatible columns

        Args:
            files: List of file dictionaries with 'name' and 'df'

        Returns:
            Tuple of (is_compatible, mismatch_info)
            where mismatch_info contains details about column differences
        """
        if not files:
            return True, {}

        # Get columns from each file
        file_columns = {}
        for file_obj in files:
            file_columns[file_obj['name']] = set(file_obj['df'].columns)

        # Find common and unique columns
        all_columns = set()
        for cols in file_columns.values():
            all_columns.update(cols)

        # Check each file
        mismatch_info = {
            'all_columns': sorted(all_columns),
            'common_columns': sorted(set.intersection(*file_columns.values())),
            'file_details': {}
        }

        for filename, cols in file_columns.items():
            missing = all_columns - cols
            unique = cols - all_columns

            mismatch_info['file_details'][filename] = {
                'columns': sorted(cols),
                'missing_columns': sorted(missing) if missing else [],
                'unique_columns': sorted(unique) if unique else []
            }

        # Files are compatible if all have the same columns
        is_compatible = len(mismatch_info['common_columns']) == len(all_columns)

        self.column_mismatch_info = mismatch_info

        logger.info(f"Column compatibility check: {'✓ Compatible' if is_compatible else '✗ Incompatible'}")
        logger.info(f"Common columns: {len(mismatch_info['common_columns'])}/{len(all_columns)}")

        return is_compatible, mismatch_info

    def combine_files_simple(self, files: List[Dict],
                            column_strategy: str = 'all') -> pd.DataFrame:
        """
        Combine all files into a single dataframe

        Args:
            files: List of file dictionaries with 'df'
            column_strategy: How to handle column mismatches
                           - 'all': Include all columns (fill missing with NaN)
                           - 'common': Only include common columns
                           - 'first': Use columns from first file

        Returns:
            Combined pandas DataFrame
        """
        if not files:
            return pd.DataFrame()

        logger.info(f"Combining {len(files)} files with strategy: {column_strategy}")

        dataframes = [f['df'] for f in files]

        if column_strategy == 'all':
            # Include all columns, fill missing with NaN
            combined = pd.concat(dataframes, ignore_index=True, sort=False)

        elif column_strategy == 'common':
            # Only use columns present in all files
            common_columns = set(dataframes[0].columns)
            for df in dataframes[1:]:
                common_columns &= set(df.columns)

            common_columns = sorted(common_columns)

            if not common_columns:
                raise ValueError("No common columns found across all files")

            # Select only common columns from each dataframe
            filtered_dfs = [df[common_columns] for df in dataframes]
            combined = pd.concat(filtered_dfs, ignore_index=True)

        elif column_strategy == 'first':
            # Use columns from first file
            reference_columns = dataframes[0].columns.tolist()

            # Reindex all dataframes to match first one
            aligned_dfs = [df.reindex(columns=reference_columns) for df in dataframes]
            combined = pd.concat(aligned_dfs, ignore_index=True)

        else:
            raise ValueError(f"Unknown column strategy: {column_strategy}")

        logger.info(f"Combined result: {len(combined)} rows × {len(combined.columns)} columns")

        self.combined_data = combined
        return combined

    def combine_and_group_by_column(self, files: List[Dict], group_column: str,
                                   column_strategy: str = 'all') -> Dict[str, pd.DataFrame]:
        """
        Combine files and split by column value

        Args:
            files: List of file dictionaries
            group_column: Column name to group by
            column_strategy: How to handle column mismatches

        Returns:
            Dictionary mapping group values to dataframes
            Example: {'Group_EM2C': df1, 'Group_P02': df2}
        """
        logger.info(f"Combining and grouping {len(files)} files by column: {group_column}")

        # First, combine all files
        combined = self.combine_files_simple(files, column_strategy)

        # Check if group column exists
        if group_column not in combined.columns:
            raise ValueError(f"Group column '{group_column}' not found in combined data")

        # Group by the specified column
        groups = {}
        unique_values = combined[group_column].dropna().unique()

        for value in sorted(unique_values):
            # Filter rows for this value
            group_df = combined[combined[group_column] == value].copy()

            # Create group name (clean for filename)
            group_name = f"Group_{str(value).strip().replace(' ', '_')}"

            groups[group_name] = group_df

            logger.info(f"  {group_name}: {len(group_df)} rows")

        logger.info(f"Created {len(groups)} groups")

        return groups

    def get_groupable_columns(self, files: List[Dict]) -> List[str]:
        """
        Get list of columns suitable for grouping

        Args:
            files: List of file dictionaries

        Returns:
            List of column names that exist in all files and have
            categorical data (not too many unique values)
        """
        if not files:
            return []

        # Find common columns
        common_columns = set(files[0]['df'].columns)
        for file_obj in files[1:]:
            common_columns &= set(file_obj['df'].columns)

        # For each common column, check if it's suitable for grouping
        groupable = []

        for col in sorted(common_columns):
            # Sample values from first file
            sample_df = files[0]['df']

            # Skip if too many unique values (more than 50% of rows)
            unique_count = sample_df[col].nunique()
            total_count = len(sample_df)

            if unique_count <= 100 and unique_count < total_count * 0.5:
                # Good candidate for grouping
                groupable.append(col)

        logger.info(f"Found {len(groupable)} groupable columns: {groupable}")

        return groupable

    def generate_column_mismatch_report(self) -> str:
        """
        Generate a user-friendly report about column mismatches

        Returns:
            String report describing column incompatibilities
        """
        if not self.column_mismatch_info:
            return "No column mismatch analysis available"

        info = self.column_mismatch_info

        report = []
        report.append("COLUMN MISMATCH DETECTED\n")
        report.append(f"Total unique columns: {len(info['all_columns'])}")
        report.append(f"Common columns: {len(info['common_columns'])}\n")

        if info['common_columns']:
            report.append(f"Common: {', '.join(info['common_columns'][:10])}")
            if len(info['common_columns']) > 10:
                report.append(f"  ...and {len(info['common_columns']) - 10} more\n")
            else:
                report.append("")

        report.append("\nPer-file details:")

        for filename, details in info['file_details'].items():
            report.append(f"\n  {filename}:")
            report.append(f"    Columns: {len(details['columns'])}")

            if details['missing_columns']:
                report.append(f"    Missing: {', '.join(details['missing_columns'][:5])}")
                if len(details['missing_columns']) > 5:
                    report.append(f"      ...and {len(details['missing_columns']) - 5} more")

        report.append("\nOptions:")
        report.append("  - Include all columns (missing values will be blank)")
        report.append("  - Use only common columns")
        report.append("  - Cancel and fix files manually")

        return "\n".join(report)
