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
from .excel_formatting import apply_professional_formatting

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
        self.enabled_fields = None

    def log(self, message):
        """Log progress message"""
        if self.progress_callback:
            self.progress_callback(message)
        print(message)

    def run(self, file1_path, file2_path, column_mapping, sheet1=None, sheet2=None, display_name1=None, display_name2=None, enabled_fields=None):
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
            enabled_fields: Dict of field enabled states (optional, all enabled if None)

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

        # Store enabled fields (default all enabled)
        self.enabled_fields = enabled_fields or {
            'email': True, 'phone': True, 'name': True,
            'company': True, 'city': True, 'state': True
        }

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

        # Tier 1: Email matching (always required)
        self.log("\nTIER 1: Email Matching")
        self.log("-" * 40)
        unmatched_df2, tier1_dupes = self._tier1_email_match(
            df1_normalized, unmatched_df2, column_mapping
        )
        duplicates.extend(tier1_dupes)
        self.stats['tier1_matches'] = len(tier1_dupes)
        self.log(f"✓ Found {len(tier1_dupes)} email matches")
        self.log(f"  Remaining unmatched: {len(unmatched_df2)}")

        # Tier 2: Phone + Name matching (only if both enabled)
        if self.enabled_fields.get('phone') and self.enabled_fields.get('name'):
            self.log("\nTIER 2: Phone + Name Matching")
            self.log("-" * 40)
            unmatched_df2, tier2_dupes = self._tier2_phone_name_match(
                df1_normalized, unmatched_df2, column_mapping
            )
            duplicates.extend(tier2_dupes)
            self.stats['tier2_matches'] = len(tier2_dupes)
            self.log(f"✓ Found {len(tier2_dupes)} phone+name matches")
            self.log(f"  Remaining unmatched: {len(unmatched_df2)}")
        else:
            self.log("\nTIER 2: Phone + Name Matching - SKIPPED (fields disabled)")
            self.stats['tier2_matches'] = 0

        # Tier 3: Company + Location + Name matching (only if company or location fields enabled)
        tier3_enabled = (self.enabled_fields.get('company') or
                        self.enabled_fields.get('city') or
                        self.enabled_fields.get('state'))
        if tier3_enabled:
            self.log("\nTIER 3: Company + Location + Name Matching")
            self.log("-" * 40)
            unmatched_df2, tier3_dupes = self._tier3_company_location_match(
                df1_normalized, unmatched_df2, column_mapping
            )
            duplicates.extend(tier3_dupes)
            self.stats['tier3_matches'] = len(tier3_dupes)
            self.log(f"✓ Found {len(tier3_dupes)} company+location matches")
            self.log(f"  Remaining unmatched: {len(unmatched_df2)}")
        else:
            self.log("\nTIER 3: Company + Location Matching - SKIPPED (fields disabled)")
            self.stats['tier3_matches'] = 0

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

    def run_multi(self, master_file_path, master_sheet, master_display_name, master_mapping,
                  secondary_files, enabled_fields=None):
        """
        Run multi-file comparison process (1 master + multiple secondary files)

        Args:
            master_file_path: Path to master file
            master_sheet: Sheet name for master file
            master_display_name: Display name for master file
            master_mapping: Dict mapping logical fields to master file columns
            secondary_files: List of dicts, each containing:
                {
                    'path': file path,
                    'sheet': sheet name,
                    'display_name': display name,
                    'mapping': dict mapping logical fields to this file's columns
                }
            enabled_fields: Dict of field enabled states (optional, all enabled if None)

        Returns:
            dict: Results containing all output sheets with multi-file data
        """
        import os

        # Store enabled fields (default all enabled)
        self.enabled_fields = enabled_fields or {
            'email': True, 'phone': True, 'name': True,
            'company': True, 'city': True, 'state': True
        }

        # Initialize multi-file statistics
        self.multi_stats = {
            'master_count': 0,
            'secondary_files': [],  # Per-file stats
            'total_overlapping': 0,
            'combined_unique': 0,
            'global_overlap_rate': 0.0
        }

        self.log("=" * 60)
        self.log("STARTING MULTI-FILE COMPARISON")
        self.log("=" * 60)

        # Load master file
        self.log(f"\nLoading MASTER file: {master_file_path}")
        self.log(f"  Sheet: {master_sheet}")
        master_df = pd.read_excel(master_file_path, sheet_name=master_sheet)
        self.multi_stats['master_count'] = len(master_df)
        self.log(f"✓ Loaded {len(master_df)} rows from master file")

        # Add source column to master
        master_df['Source_File'] = master_display_name

        # Store raw master
        master_raw = master_df.copy()

        # Combine all unique records here (starts with master)
        combined_unique_df = master_df.copy()

        # Track all overlapping records across all files
        all_overlapping_records = []

        # Process each secondary file sequentially
        for file_idx, file_info in enumerate(secondary_files):
            self.log("\n" + "=" * 60)
            self.log(f"PROCESSING SECONDARY FILE #{file_idx + 1}: {file_info['display_name']}")
            self.log("=" * 60)

            # Load secondary file
            self.log(f"\nLoading file: {file_info['path']}")
            self.log(f"  Sheet: {file_info['sheet']}")
            secondary_df = pd.read_excel(file_info['path'], sheet_name=file_info['sheet'])
            secondary_count = len(secondary_df)
            self.log(f"✓ Loaded {secondary_count} rows")

            # Add source column
            secondary_df['Source_File'] = file_info['display_name']

            # Normalize both dataframes for matching
            self.log(f"\nNormalizing data for comparison #{file_idx + 1}...")

            # For master, use master_mapping
            master_norm = self._normalize_dataframe_direct(combined_unique_df, master_mapping)

            # For secondary, use this file's mapping
            secondary_norm = self._normalize_dataframe_direct(secondary_df, file_info['mapping'])

            # Run tiered matching
            self.log("\n" + "-" * 40)
            self.log("RUNNING TIERED MATCHING")
            self.log("-" * 40)

            duplicates_this_file = []
            unmatched_secondary = secondary_norm.copy()

            # Tier 1: Email matching (always required)
            self.log("\nTIER 1: Email Matching")
            unmatched_secondary, tier1_dupes = self._tier1_email_match_direct(
                master_norm, unmatched_secondary
            )
            duplicates_this_file.extend(tier1_dupes)
            tier1_count = len(tier1_dupes)
            self.log(f"✓ Found {tier1_count} email matches")
            self.log(f"  Remaining unmatched: {len(unmatched_secondary)}")

            # Tier 2: Phone + Name matching (only if both enabled)
            tier2_count = 0
            if self.enabled_fields.get('phone') and self.enabled_fields.get('name'):
                self.log("\nTIER 2: Phone + Name Matching")
                unmatched_secondary, tier2_dupes = self._tier2_phone_name_match_direct(
                    master_norm, unmatched_secondary
                )
                duplicates_this_file.extend(tier2_dupes)
                tier2_count = len(tier2_dupes)
                self.log(f"✓ Found {tier2_count} phone+name matches")
                self.log(f"  Remaining unmatched: {len(unmatched_secondary)}")
            else:
                self.log("\nTIER 2: Phone + Name Matching - SKIPPED (fields disabled)")

            # Tier 3: Company + Location + Name matching
            tier3_count = 0
            tier3_enabled = (self.enabled_fields.get('company') or
                           self.enabled_fields.get('city') or
                           self.enabled_fields.get('state'))
            if tier3_enabled:
                self.log("\nTIER 3: Company + Location + Name Matching")
                unmatched_secondary, tier3_dupes = self._tier3_company_location_match_direct(
                    master_norm, unmatched_secondary
                )
                duplicates_this_file.extend(tier3_dupes)
                tier3_count = len(tier3_dupes)
                self.log(f"✓ Found {tier3_count} company+location matches")
                self.log(f"  Remaining unmatched: {len(unmatched_secondary)}")
            else:
                self.log("\nTIER 3: Company + Location Matching - SKIPPED (fields disabled)")

            # Calculate stats for this file
            overlapping_count = len(duplicates_this_file)
            unique_from_this_file = len(unmatched_secondary)
            overlap_rate = (overlapping_count / secondary_count * 100) if secondary_count > 0 else 0

            self.multi_stats['secondary_files'].append({
                'display_name': file_info['display_name'],
                'total_records': secondary_count,
                'tier1_matches': tier1_count,
                'tier2_matches': tier2_count,
                'tier3_matches': tier3_count,
                'overlapping': overlapping_count,
                'unique': unique_from_this_file,
                'overlap_rate': overlap_rate
            })

            self.log(f"\n✓ File #{file_idx + 1} comparison complete:")
            self.log(f"  Overlapping: {overlapping_count}")
            self.log(f"  Unique: {unique_from_this_file}")
            self.log(f"  Overlap rate: {overlap_rate:.2f}%")

            # Add overlapping records to global list (with Source_File info)
            all_overlapping_records.extend(duplicates_this_file)

            # Add unique records from this file to combined_unique_df for next iteration
            if len(unmatched_secondary) > 0:
                # Remove normalized columns before adding
                cols_to_drop = [col for col in unmatched_secondary.columns if col.startswith('_norm_')]
                unmatched_clean = unmatched_secondary.drop(columns=cols_to_drop)
                combined_unique_df = pd.concat([combined_unique_df, unmatched_clean], ignore_index=True)
                self.log(f"  Added {len(unmatched_clean)} unique records to master for next comparison")

        # Calculate global statistics
        total_secondary_records = sum(f['total_records'] for f in self.multi_stats['secondary_files'])
        self.multi_stats['total_overlapping'] = len(all_overlapping_records)
        self.multi_stats['combined_unique'] = len(combined_unique_df)
        if total_secondary_records > 0:
            self.multi_stats['global_overlap_rate'] = (
                self.multi_stats['total_overlapping'] / total_secondary_records * 100
            )

        # Create output sheets
        self.log("\n" + "=" * 60)
        self.log("GENERATING OUTPUT SHEETS")
        self.log("=" * 60)

        summary = self._create_multi_summary_report(master_display_name)
        combined_cleaned = combined_unique_df.copy()

        # Remove normalized columns from combined_cleaned
        cols_to_drop = [col for col in combined_cleaned.columns if col.startswith('_norm_')]
        if cols_to_drop:
            combined_cleaned = combined_cleaned.drop(columns=cols_to_drop)

        overlapping_records = self._create_multi_overlapping_sheet(all_overlapping_records)

        self.log("\n✓ Summary report created")
        self.log("✓ Combined cleaned data created")
        self.log("✓ Overlapping records list created")

        self.log("\n" + "=" * 60)
        self.log("MULTI-FILE COMPARISON COMPLETE")
        self.log("=" * 60)
        self.log(f"\nMaster file records: {self.multi_stats['master_count']}")
        self.log(f"Total secondary records: {total_secondary_records}")
        self.log(f"Total overlapping records: {self.multi_stats['total_overlapping']}")
        self.log(f"Combined unique records: {self.multi_stats['combined_unique']}")
        self.log(f"Global overlap rate: {self.multi_stats['global_overlap_rate']:.2f}%")

        # For backward compatibility with the stats property
        self.stats = {
            'total_duplicates': self.multi_stats['total_overlapping'],
            'unique_count': self.multi_stats['combined_unique']
        }

        return {
            'summary': summary,
            'combined_cleaned': combined_cleaned,
            'file1_raw': master_raw,
            'duplicates_removed': overlapping_records
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
        """Create summary report sheet with dynamic file names and active tiers only"""
        metrics = []
        values = []

        # Always include file counts
        metrics.append(f'{self.display_name1} — Total Records')
        values.append(self.stats['file1_count'])

        metrics.append(f'{self.display_name2} — Total Records')
        values.append(self.stats['file2_count'])

        # Include tier 1 (email) - always active
        metrics.append('Exact Email Matches')
        values.append(self.stats['tier1_matches'])

        # Include tier 2 only if it was active
        if self.enabled_fields.get('phone') and self.enabled_fields.get('name'):
            metrics.append('Phone + Name Matches')
            values.append(self.stats['tier2_matches'])

        # Include tier 3 only if it was active
        tier3_enabled = (self.enabled_fields.get('company') or
                        self.enabled_fields.get('city') or
                        self.enabled_fields.get('state'))
        if tier3_enabled:
            metrics.append('Company + Location Matches')
            values.append(self.stats['tier3_matches'])

        # Always include totals
        metrics.append('Total Overlapping Records')
        values.append(self.stats['total_duplicates'])

        metrics.append('Combined Unique Records')
        values.append(self.stats['unique_count'])

        metrics.append('Overlap Rate (%)')
        values.append(f"{self.stats['dedup_rate']:.2f}%")

        summary_data = {
            'Metric': metrics,
            'Value': values
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

    def _normalize_dataframe_direct(self, df, mapping):
        """
        Normalize dataframe using direct field names (no prefix)
        For multi-file processing where mapping is already file-specific
        """
        df_norm = df.copy()

        # Add normalized email
        if 'email' in mapping and mapping['email'] in df.columns:
            df_norm['_norm_email'] = df[mapping['email']].apply(normalize_email)

        # Add normalized phone
        if 'phone' in mapping and mapping['phone'] in df.columns:
            df_norm['_norm_phone'] = df[mapping['phone']].apply(normalize_phone)

        # Add normalized name
        if 'name' in mapping and mapping['name'] in df.columns:
            df_norm['_norm_name'] = df[mapping['name']].apply(normalize_text)

        # Add normalized company
        if 'company' in mapping and mapping['company'] in df.columns:
            df_norm['_norm_company'] = df[mapping['company']].apply(normalize_text)

        # Add normalized city
        if 'city' in mapping and mapping['city'] in df.columns:
            df_norm['_norm_city'] = df[mapping['city']].apply(normalize_text)

        # Add normalized state
        if 'state' in mapping and mapping['state'] in df.columns:
            df_norm['_norm_state'] = df[mapping['state']].apply(normalize_text)

        return df_norm

    def _tier1_email_match_direct(self, master_df, secondary_df):
        """Tier 1 email matching for multi-file mode (direct normalization)"""
        matched_rows = []
        unmatched_rows = []

        for idx, row in secondary_df.iterrows():
            if pd.isna(row.get('_norm_email')) or row.get('_norm_email') == '':
                unmatched_rows.append(row)
                continue

            # Check for exact email match in master
            match = master_df[master_df['_norm_email'] == row['_norm_email']]

            if not match.empty:
                # Found a match
                row_dict = row.to_dict()
                row_dict['Match_Reason'] = 'Email Match'
                row_dict['Overlap_Tier'] = 'Tier 1'
                matched_rows.append(row_dict)
            else:
                unmatched_rows.append(row)

        unmatched_df = pd.DataFrame(unmatched_rows) if unmatched_rows else pd.DataFrame(columns=secondary_df.columns)
        return unmatched_df, matched_rows

    def _tier2_phone_name_match_direct(self, master_df, secondary_df):
        """Tier 2 phone+name matching for multi-file mode"""
        matched_rows = []
        unmatched_rows = []

        for idx, row in secondary_df.iterrows():
            phone = row.get('_norm_phone')
            name = row.get('_norm_name')

            # Skip if either field is missing
            if pd.isna(phone) or phone == '' or pd.isna(name) or name == '':
                unmatched_rows.append(row)
                continue

            # Check for phone+name match in master
            match = master_df[
                (master_df['_norm_phone'] == phone) &
                (master_df['_norm_name'] == name)
            ]

            if not match.empty:
                row_dict = row.to_dict()
                row_dict['Match_Reason'] = 'Phone + Name Match'
                row_dict['Overlap_Tier'] = 'Tier 2'
                matched_rows.append(row_dict)
            else:
                unmatched_rows.append(row)

        unmatched_df = pd.DataFrame(unmatched_rows) if unmatched_rows else pd.DataFrame(columns=secondary_df.columns)
        return unmatched_df, matched_rows

    def _tier3_company_location_match_direct(self, master_df, secondary_df):
        """Tier 3 company+location+name matching for multi-file mode"""
        matched_rows = []
        unmatched_rows = []

        for idx, row in secondary_df.iterrows():
            company = row.get('_norm_company')
            city = row.get('_norm_city')
            state = row.get('_norm_state')
            name = row.get('_norm_name')

            # Need at least company or location, plus name
            has_company = not pd.isna(company) and company != ''
            has_location = (not pd.isna(city) and city != '') or (not pd.isna(state) and state != '')
            has_name = not pd.isna(name) and name != ''

            if not ((has_company or has_location) and has_name):
                unmatched_rows.append(row)
                continue

            # Build match conditions
            conditions = []

            if has_company:
                conditions.append(master_df['_norm_company'] == company)

            if not pd.isna(city) and city != '':
                conditions.append(master_df['_norm_city'] == city)

            if not pd.isna(state) and state != '':
                conditions.append(master_df['_norm_state'] == state)

            if has_name:
                conditions.append(master_df['_norm_name'] == name)

            # Combine all conditions
            if conditions:
                combined_condition = conditions[0]
                for condition in conditions[1:]:
                    combined_condition = combined_condition & condition

                match = master_df[combined_condition]

                if not match.empty:
                    row_dict = row.to_dict()
                    row_dict['Match_Reason'] = 'Company + Location Match'
                    row_dict['Overlap_Tier'] = 'Tier 3'
                    matched_rows.append(row_dict)
                else:
                    unmatched_rows.append(row)
            else:
                unmatched_rows.append(row)

        unmatched_df = pd.DataFrame(unmatched_rows) if unmatched_rows else pd.DataFrame(columns=secondary_df.columns)
        return unmatched_df, matched_rows

    def _create_multi_summary_report(self, master_display_name):
        """Create summary report for multi-file comparison"""
        metrics = []
        values = []

        # Section 1: Master File Overview
        metrics.append('=== MASTER FILE ===')
        values.append('')
        metrics.append(f'{master_display_name} — Total Records')
        values.append(self.multi_stats['master_count'])

        # Section 2: Per-File Comparison Metrics
        for idx, file_stats in enumerate(self.multi_stats['secondary_files']):
            metrics.append('')
            values.append('')
            metrics.append(f'=== SECONDARY FILE #{idx + 1}: {file_stats["display_name"]} ===')
            values.append('')
            metrics.append(f'{file_stats["display_name"]} — Total Records')
            values.append(file_stats['total_records'])

            # Only show tiers that were active
            metrics.append('  Exact Email Matches')
            values.append(file_stats['tier1_matches'])

            if self.enabled_fields.get('phone') and self.enabled_fields.get('name'):
                metrics.append('  Phone + Name Matches')
                values.append(file_stats['tier2_matches'])

            tier3_enabled = (self.enabled_fields.get('company') or
                           self.enabled_fields.get('city') or
                           self.enabled_fields.get('state'))
            if tier3_enabled:
                metrics.append('  Company + Location Matches')
                values.append(file_stats['tier3_matches'])

            metrics.append(f'{file_stats["display_name"]} — Overlapping Records')
            values.append(file_stats['overlapping'])
            metrics.append(f'{file_stats["display_name"]} — Unique Records')
            values.append(file_stats['unique'])
            metrics.append(f'{file_stats["display_name"]} — Overlap Rate (%)')
            values.append(f"{file_stats['overlap_rate']:.2f}%")

        # Section 3: Global Summary
        metrics.append('')
        values.append('')
        metrics.append('=== GLOBAL SUMMARY ===')
        values.append('')
        metrics.append('Total Overlapping Records (All Files)')
        values.append(self.multi_stats['total_overlapping'])
        metrics.append('Combined Unique Records')
        values.append(self.multi_stats['combined_unique'])
        metrics.append('Global Overlap Rate (%)')
        values.append(f"{self.multi_stats['global_overlap_rate']:.2f}%")

        return pd.DataFrame({'Metric': metrics, 'Value': values})

    def _create_multi_overlapping_sheet(self, overlapping_records):
        """Create overlapping records sheet for multi-file comparison"""
        if not overlapping_records:
            return pd.DataFrame()

        df_overlapping = pd.DataFrame(overlapping_records)

        # Remove normalization columns
        df_overlapping = df_overlapping[[col for col in df_overlapping.columns if not col.startswith('_norm_')]]

        # Reorder columns: Source_File, Overlap_Tier, Match_Reason, then rest
        priority_cols = []
        if 'Source_File' in df_overlapping.columns:
            priority_cols.append('Source_File')
        if 'Overlap_Tier' in df_overlapping.columns:
            priority_cols.append('Overlap_Tier')
        if 'Match_Reason' in df_overlapping.columns:
            priority_cols.append('Match_Reason')

        other_cols = [col for col in df_overlapping.columns if col not in priority_cols]
        df_overlapping = df_overlapping[priority_cols + other_cols]

        # Sort by Source_File then Overlap_Tier
        if 'Source_File' in df_overlapping.columns and 'Overlap_Tier' in df_overlapping.columns:
            df_overlapping = df_overlapping.sort_values(['Source_File', 'Overlap_Tier'])

        return df_overlapping

def export_results(results, output_path):
    """
    Export comparison results to Excel file with multiple sheets and professional formatting

    Args:
        results: Dict from DeduplicationEngine.run()
        output_path: Output file path
    """
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Write all sheets
        results['summary'].to_excel(writer, sheet_name='Summary_Report', index=False)
        results['combined_cleaned'].to_excel(writer, sheet_name='Combined_Cleaned', index=False)
        results['file1_raw'].to_excel(writer, sheet_name='File1_Raw', index=False)
        results['file2_raw'].to_excel(writer, sheet_name='File2_Raw', index=False)
        results['duplicates_removed'].to_excel(writer, sheet_name='Overlapping_Records', index=False)

        # Apply professional formatting to all sheets
        apply_professional_formatting(writer.book)
