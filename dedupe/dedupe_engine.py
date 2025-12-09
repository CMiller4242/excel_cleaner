"""
Two-File Comparison Engine
Main processing logic for comparing two Excel files and identifying overlaps
"""

import pandas as pd
from datetime import datetime
from .helpers import (
    normalize_email,
    normalize_phone,
    normalize_text,
    fuzzy_match,
    get_match_reason
)

class DeduplicationEngine:
    """
    Engine for comparing two Excel files using tiered matching logic
    """

    def __init__(self, progress_callback=None):
        """
        Initialize comparison engine

        Args:
            progress_callback: Function to call with progress updates (optional)
        """
        self.progress_callback = progress_callback
        self.stats = {
            'file1_count': 0,
            'file2_count': 0,
            'tier1_matches': 0,
            'tier2_matches': 0,
            'tier3_matches': 0,
            'total_duplicates': 0,
            'unique_count': 0,
            'dedup_rate': 0.0
        }
        self.display_name1 = None
        self.display_name2 = None

    def log(self, message):
        """Log progress message"""
        if self.progress_callback:
            self.progress_callback(message)
        print(message)

    def run(self, file1_path, file2_path, column_mapping, sheet1=None, sheet2=None, display_name1=None, display_name2=None):
        """
        Run comparison process

        Args:
            file1_path: Path to master file
            file2_path: Path to secondary file
            column_mapping: Dict mapping logical columns to actual column names
            sheet1: Sheet name for file1 (optional, uses first sheet if None)
            sheet2: Sheet name for file2 (optional, uses first sheet if None)
            display_name1: Display name for file1 (optional, uses filename if None)
            display_name2: Display name for file2 (optional, uses filename if None)

        Returns:
            dict: Results containing all output sheets
                {
                    'summary': DataFrame,
                    'combined_cleaned': DataFrame,
                    'file1_raw': DataFrame,
                    'file2_raw': DataFrame,
                    'duplicates_removed': DataFrame
                }
        """

        # Store display names for use in reports
        import os
        self.display_name1 = display_name1 or os.path.splitext(os.path.basename(file1_path))[0]
        self.display_name2 = display_name2 or os.path.splitext(os.path.basename(file2_path))[0]

        self.log("=" * 60)
        self.log("STARTING TWO-FILE COMPARISON")
        self.log("=" * 60)

        # Load files with sheet selection
        self.log(f"\nLoading master file: {file1_path}")
        if sheet1:
            self.log(f"  Sheet: {sheet1}")
            df1 = pd.read_excel(file1_path, sheet_name=sheet1)
        else:
            df1 = pd.read_excel(file1_path)
        self.stats['file1_count'] = len(df1)
        self.log(f"✓ Loaded {len(df1)} rows from master file")

        self.log(f"\nLoading secondary file: {file2_path}")
        if sheet2:
            self.log(f"  Sheet: {sheet2}")
            df2 = pd.read_excel(file2_path, sheet_name=sheet2)
        else:
            df2 = pd.read_excel(file2_path)
        self.stats['file2_count'] = len(df2)
        self.log(f"✓ Loaded {len(df2)} rows from secondary file")

        # Add source column with display names
        df1['Source'] = self.display_name1
        df2['Source'] = self.display_name2

        # Store raw data
        file1_raw = df1.copy()
        file2_raw = df2.copy()

        # Normalize columns for matching
        self.log("\nNormalizing data for matching...")
        df1_normalized = self._normalize_dataframe(df1, column_mapping, prefix='file1')
        df2_normalized = self._normalize_dataframe(df2, column_mapping, prefix='file2')

        # Run tiered matching
        self.log("\n" + "=" * 60)
        self.log("RUNNING TIERED MATCHING")
        self.log("=" * 60)

        duplicates = []
        unmatched_df2 = df2_normalized.copy()

        # Tier 1: Email matching
        self.log("\nTIER 1: Email Matching")
        self.log("-" * 40)
        unmatched_df2, tier1_dupes = self._tier1_email_match(
            df1_normalized, unmatched_df2, column_mapping
        )
        duplicates.extend(tier1_dupes)
        self.stats['tier1_matches'] = len(tier1_dupes)
        self.log(f"✓ Found {len(tier1_dupes)} email matches")
        self.log(f"  Remaining unmatched: {len(unmatched_df2)}")

        # Tier 2: Phone + Name matching
        self.log("\nTIER 2: Phone + Name Matching")
        self.log("-" * 40)
        unmatched_df2, tier2_dupes = self._tier2_phone_name_match(
            df1_normalized, unmatched_df2, column_mapping
        )
        duplicates.extend(tier2_dupes)
        self.stats['tier2_matches'] = len(tier2_dupes)
        self.log(f"✓ Found {len(tier2_dupes)} phone+name matches")
        self.log(f"  Remaining unmatched: {len(unmatched_df2)}")

        # Tier 3: Company + Location + Name matching
        self.log("\nTIER 3: Company + Location + Name Matching")
        self.log("-" * 40)
        unmatched_df2, tier3_dupes = self._tier3_company_location_match(
            df1_normalized, unmatched_df2, column_mapping
        )
        duplicates.extend(tier3_dupes)
        self.stats['tier3_matches'] = len(tier3_dupes)
        self.log(f"✓ Found {len(tier3_dupes)} company+location matches")
        self.log(f"  Remaining unmatched: {len(unmatched_df2)}")

        # Calculate final statistics
        self.stats['total_duplicates'] = len(duplicates)
        self.stats['unique_count'] = self.stats['file1_count'] + len(unmatched_df2)

        if self.stats['file2_count'] > 0:
            self.stats['dedup_rate'] = (self.stats['total_duplicates'] / self.stats['file2_count']) * 100

        # Create output sheets
        self.log("\n" + "=" * 60)
        self.log("GENERATING OUTPUT SHEETS")
        self.log("=" * 60)

        summary = self._create_summary_report()
        combined_cleaned = self._create_combined_cleaned(df1, unmatched_df2)
        duplicates_removed = self._create_duplicates_sheet(duplicates)

        self.log("\n✓ Summary report created")
        self.log("✓ Combined cleaned data created")
        self.log("✓ Overlapping records list created")

        self.log("\n" + "=" * 60)
        self.log("COMPARISON COMPLETE")
        self.log("=" * 60)
        self.log(f"\nTotal records processed: {self.stats['file1_count'] + self.stats['file2_count']}")
        self.log(f"Overlapping records found: {self.stats['total_duplicates']}")
        self.log(f"Unique records: {self.stats['unique_count']}")
        self.log(f"Overlap rate: {self.stats['dedup_rate']:.2f}%")

        return {
            'summary': summary,
            'combined_cleaned': combined_cleaned,
            'file1_raw': file1_raw,
            'file2_raw': file2_raw,
            'duplicates_removed': duplicates_removed
        }

    def _normalize_dataframe(self, df, column_mapping, prefix):
        """Add normalized columns for matching"""
        df_norm = df.copy()

        # Add normalized email
        if f'{prefix}_email' in column_mapping:
            email_col = column_mapping[f'{prefix}_email']
            if email_col in df.columns:
                df_norm['_norm_email'] = df[email_col].apply(normalize_email)

        # Add normalized phone
        if f'{prefix}_phone' in column_mapping:
            phone_col = column_mapping[f'{prefix}_phone']
            if phone_col in df.columns:
                df_norm['_norm_phone'] = df[phone_col].apply(normalize_phone)

        # Add normalized name
        if f'{prefix}_name' in column_mapping:
            name_col = column_mapping[f'{prefix}_name']
            if name_col in df.columns:
                df_norm['_norm_name'] = df[name_col].apply(normalize_text)

        # Add normalized company
        if f'{prefix}_company' in column_mapping:
            company_col = column_mapping[f'{prefix}_company']
            if company_col in df.columns:
                df_norm['_norm_company'] = df[company_col].apply(normalize_text)

        # Add normalized city
        if f'{prefix}_city' in column_mapping:
            city_col = column_mapping[f'{prefix}_city']
            if city_col in df.columns:
                df_norm['_norm_city'] = df[city_col].apply(normalize_text)

        # Add normalized state
        if f'{prefix}_state' in column_mapping:
            state_col = column_mapping[f'{prefix}_state']
            if state_col in df.columns:
                df_norm['_norm_state'] = df[state_col].apply(normalize_text)

        return df_norm

    def _tier1_email_match(self, df1, df2, column_mapping):
        """Tier 1: Exact email matching"""
        duplicates = []
        unmatched = []

        for idx, row2 in df2.iterrows():
            email2 = row2.get('_norm_email', '')

            if not email2:
                unmatched.append(row2)
                continue

            # Find exact email match in df1
            matches = df1[df1['_norm_email'] == email2]

            if len(matches) > 0:
                # Duplicate found
                duplicate_info = row2.copy()
                duplicate_info['Match_Reason'] = get_match_reason(1)
                duplicate_info['Matched_With_Index'] = matches.index[0]
                duplicates.append(duplicate_info)
            else:
                unmatched.append(row2)

        unmatched_df = pd.DataFrame(unmatched) if unmatched else pd.DataFrame()

        return unmatched_df, duplicates

    def _tier2_phone_name_match(self, df1, df2, column_mapping):
        """Tier 2: Phone + Name matching (fuzzy name ≥85%)"""
        duplicates = []
        unmatched = []

        for idx, row2 in df2.iterrows():
            phone2 = row2.get('_norm_phone', '')
            name2 = row2.get('_norm_name', '')

            if not phone2 or not name2:
                unmatched.append(row2)
                continue

            # Find exact phone match
            phone_matches = df1[df1['_norm_phone'] == phone2]

            found_match = False
            for match_idx, match_row in phone_matches.iterrows():
                name1 = match_row.get('_norm_name', '')

                # Fuzzy name match
                is_match, similarity = fuzzy_match(name1, name2, threshold=85)

                if is_match:
                    duplicate_info = row2.copy()
                    duplicate_info['Match_Reason'] = get_match_reason(
                        2,
                        {'Name_Similarity': similarity}
                    )
                    duplicate_info['Matched_With_Index'] = match_idx
                    duplicates.append(duplicate_info)
                    found_match = True
                    break

            if not found_match:
                unmatched.append(row2)

        unmatched_df = pd.DataFrame(unmatched) if unmatched else pd.DataFrame()

        return unmatched_df, duplicates

    def _tier3_company_location_match(self, df1, df2, column_mapping):
        """Tier 3: Company + City/State + Name matching"""
        duplicates = []
        unmatched = []

        for idx, row2 in df2.iterrows():
            company2 = row2.get('_norm_company', '')
            city2 = row2.get('_norm_city', '')
            state2 = row2.get('_norm_state', '')
            name2 = row2.get('_norm_name', '')

            if not company2 or not city2 or not state2 or not name2:
                unmatched.append(row2)
                continue

            # Find exact city + state match
            location_matches = df1[
                (df1['_norm_city'] == city2) &
                (df1['_norm_state'] == state2)
            ]

            found_match = False
            for match_idx, match_row in location_matches.iterrows():
                company1 = match_row.get('_norm_company', '')
                name1 = match_row.get('_norm_name', '')

                # Company similarity ≥85%
                company_match, company_sim = fuzzy_match(company1, company2, threshold=85)

                if company_match:
                    # Name similarity ≥75%
                    name_match, name_sim = fuzzy_match(name1, name2, threshold=75)

                    if name_match:
                        duplicate_info = row2.copy()
                        duplicate_info['Match_Reason'] = get_match_reason(
                            3,
                            {
                                'Company_Similarity': company_sim,
                                'Name_Similarity': name_sim
                            }
                        )
                        duplicate_info['Matched_With_Index'] = match_idx
                        duplicates.append(duplicate_info)
                        found_match = True
                        break

            if not found_match:
                unmatched.append(row2)

        unmatched_df = pd.DataFrame(unmatched) if unmatched else pd.DataFrame()

        return unmatched_df, duplicates

    def _create_summary_report(self):
        """Create summary report sheet with dynamic file names"""
        summary_data = {
            'Metric': [
                f'{self.display_name1} — Total Records',
                f'{self.display_name2} — Total Records',
                'Exact Email Matches',
                'Phone + Name Matches',
                'Company + Location Matches',
                'Total Overlapping Records',
                'Combined Unique Records',
                'Overlap Rate (%)'
            ],
            'Value': [
                self.stats['file1_count'],
                self.stats['file2_count'],
                self.stats['tier1_matches'],
                self.stats['tier2_matches'],
                self.stats['tier3_matches'],
                self.stats['total_duplicates'],
                self.stats['unique_count'],
                f"{self.stats['dedup_rate']:.2f}%"
            ]
        }

        return pd.DataFrame(summary_data)

    def _create_combined_cleaned(self, df1, unmatched_df2):
        """Create combined cleaned data sheet"""
        # Remove normalization columns
        df1_clean = df1[[col for col in df1.columns if not col.startswith('_norm_')]]
        df2_clean = unmatched_df2[[col for col in unmatched_df2.columns if not col.startswith('_norm_')]]

        # Combine
        combined = pd.concat([df1_clean, df2_clean], ignore_index=True)

        return combined

    def _create_duplicates_sheet(self, duplicates):
        """Create duplicates removed sheet"""
        if not duplicates:
            return pd.DataFrame()

        df_dupes = pd.DataFrame(duplicates)

        # Remove normalization columns
        df_dupes = df_dupes[[col for col in df_dupes.columns if not col.startswith('_norm_')]]

        # Reorder to put Match_Reason first
        if 'Match_Reason' in df_dupes.columns:
            cols = ['Match_Reason'] + [col for col in df_dupes.columns if col != 'Match_Reason']
            df_dupes = df_dupes[cols]

        return df_dupes

def export_results(results, output_path):
    """
    Export comparison results to Excel file with multiple sheets

    Args:
        results: Dict from DeduplicationEngine.run()
        output_path: Output file path
    """
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        results['summary'].to_excel(writer, sheet_name='Summary_Report', index=False)
        results['combined_cleaned'].to_excel(writer, sheet_name='Combined_Cleaned', index=False)
        results['file1_raw'].to_excel(writer, sheet_name='File1_Raw', index=False)
        results['file2_raw'].to_excel(writer, sheet_name='File2_Raw', index=False)
        results['duplicates_removed'].to_excel(writer, sheet_name='Overlapping_Records', index=False)
