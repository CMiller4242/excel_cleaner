"""
Data Operations
VLOOKUP, merge, join, sort, filter, deduplicate
"""
import pandas as pd
from typing import Dict
from .base import BaseOperation, OperationMetadata, Parameter
from .registry import registry


class VLookupOperation(BaseOperation):
    """Lookup values from another file"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_vlookup',
            name='Lookup Values from Another File',
            category='Data Matching',
            description='Find and retrieve values from another spreadsheet based on a matching column',
            parameters=[
                Parameter(
                    name='lookup_column',
                    type='column',
                    description='Column to match on in your data'
                ),
                Parameter(
                    name='lookup_file',
                    type='file',
                    description='File to search in (CSV or Excel)'
                ),
                Parameter(
                    name='lookup_file_column',
                    type='text',
                    description='Column name in lookup file to match'
                ),
                Parameter(
                    name='return_column',
                    type='text',
                    description='Column to retrieve from lookup file'
                ),
                Parameter(
                    name='new_column',
                    type='text',
                    description='Name for the new column in your data'
                )
            ],
            excel_equivalent='VLOOKUP()',
            examples=[
                'Get pricing from master price list using product code',
                'Find customer details using customer ID',
                'Retrieve employee info using badge number'
            ],
            tags=['vlookup', 'lookup', 'merge', 'match', 'join']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()
        
        # Load lookup file
        lookup_file = params['lookup_file']
        if lookup_file.endswith('.csv'):
            lookup_df = pd.read_csv(lookup_file)
        else:
            lookup_df = pd.read_excel(lookup_file)
        
        # Perform merge (like VLOOKUP)
        lookup_col = params['lookup_column']
        lookup_file_col = params['lookup_file_column']
        return_col = params['return_column']
        new_col = params['new_column']
        
        # Merge and rename
        merged = df.merge(
            lookup_df[[lookup_file_col, return_col]],
            left_on=lookup_col,
            right_on=lookup_file_col,
            how='left'
        )
        
        merged[new_col] = merged[return_col]
        merged = merged.drop(columns=[return_col, lookup_file_col], errors='ignore')
        
        return merged


class RemoveDuplicatesOperation(BaseOperation):
    """Remove duplicate rows with optional smart matching"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_remove_duplicates',
            name='Remove Duplicate Rows',
            category='Data Matching',
            description='''Remove duplicate records based on one or more columns.

SMART MATCHING (when enabled):
- Normalizes addresses: "PKWY"→"PARKWAY", "ST"→"STREET", "AVE"→"AVENUE"
- Removes extra spaces and punctuation
- Case-insensitive comparison
- Detects semantic duplicates that exact matching would miss

Example without smart matching:
  "2000 PEPPERELL PKWY" ≠ "2000 PEPPERELL PARKWAY" (kept as separate)

Example with smart matching:
  "2000 PEPPERELL PKWY" = "2000 PEPPERELL PARKWAY" (duplicate removed)
''',
            parameters=[
                Parameter(
                    name='multi_level_deduplication',
                    type='boolean',
                    description='Use smart multi-level duplicate detection (Email → Name+Address → Name+Phone)',
                    default=True,
                    required=False
                ),
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to check for duplicates (empty = check all columns). Ignored when using multi-level deduplication.'
                ),
                Parameter(
                    name='keep',
                    type='choice',
                    description='Which duplicate to keep',
                    choices=['first', 'last'],
                    default='first'
                ),
                Parameter(
                    name='smart_matching',
                    type='boolean',
                    description='Enable smart matching (normalizes addresses and text for better duplicate detection)',
                    required=False,
                    default=False
                ),
                Parameter(
                    name='address_columns',
                    type='text',
                    description='Address columns to normalize (comma-separated, e.g., "Address 1,Address 2"). Only used if smart matching is enabled.',
                    required=False,
                    default=''
                )
            ],
            excel_equivalent='Remove Duplicates',
            examples=[
                'Remove duplicate customers by Customer ID',
                'Remove duplicate emails from contact list',
                'Keep only unique product codes',
                'Smart deduplication: by email, then by name+address, then by name+phone',
                'Smart matching: "2000 PEPPERELL PKWY" = "2000 PEPPERELL PARKWAY"'
            ],
            tags=['duplicates', 'unique', 'dedupe', 'remove']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        import sys

        keep = self.get_param_value(params, 'keep', 'first')
        multi_level = self.get_param_value(params, 'multi_level_deduplication', True)
        smart_matching = self.get_param_value(params, 'smart_matching', False)
        address_columns_str = self.get_param_value(params, 'address_columns', '')

        # Parse address columns
        if address_columns_str and address_columns_str.strip():
            address_columns = [col.strip() for col in address_columns_str.split(',')]
        else:
            address_columns = []

        # DEBUG: Log parameter values
        print(f"\n{'='*80}", file=sys.stderr)
        print(f"RemoveDuplicatesOperation.execute() DEBUG", file=sys.stderr)
        print(f"{'='*80}", file=sys.stderr)
        print(f"Input DataFrame: {len(df)} rows", file=sys.stderr)
        print(f"Parameters:", file=sys.stderr)
        print(f"  keep: {keep}", file=sys.stderr)
        print(f"  multi_level_deduplication: {multi_level} (type: {type(multi_level)})", file=sys.stderr)
        print(f"  smart_matching: {smart_matching}", file=sys.stderr)
        print(f"  address_columns: {address_columns}", file=sys.stderr)
        print(f"  columns: {params.get('columns', [])}", file=sys.stderr)

        # If smart matching is enabled, normalize columns first
        if smart_matching:
            print(f"\n→ Using SMART MATCHING", file=sys.stderr)
            from utils.address_normalizer import AddressNormalizer, TextNormalizer

            df_work = df.copy()

            # Determine which columns to check for duplicates
            if multi_level:
                # For multi-level, we need to normalize the specific columns used
                columns_to_normalize = []
                email_col = 'Email Address'
                name_cols = ['First Name', 'Last Name']
                address_cols = ['Person Street', 'Person City', 'Person State']
                phone_col = 'Direct Phone Number'

                # Check if these columns exist
                if email_col in df.columns:
                    columns_to_normalize.append(email_col)
                columns_to_normalize.extend([col for col in name_cols if col in df.columns])
                columns_to_normalize.extend([col for col in address_cols if col in df.columns])
                if phone_col in df.columns:
                    columns_to_normalize.append(phone_col)
            else:
                columns_param = params.get('columns', [])
                columns_to_normalize = columns_param if columns_param else df.columns.tolist()

            # Normalize columns
            for col in columns_to_normalize:
                # Check if this column should be treated as an address
                is_address_col = (col in address_columns or
                                any(addr_hint in col.lower() for addr_hint in ['address', 'street', 'ave', 'road']))

                if is_address_col:
                    print(f"  Normalizing address column: {col}", file=sys.stderr)
                    df_work[f'_normalized_{col}'] = AddressNormalizer.normalize_dataframe_column(df[col])
                else:
                    print(f"  Normalizing text column: {col}", file=sys.stderr)
                    df_work[f'_normalized_{col}'] = df[col].apply(TextNormalizer.normalize)

            # Now perform deduplication on normalized columns
            if multi_level:
                result = self._execute_multi_level_smart(df_work, df, keep, sys)
            else:
                result = self._execute_standard_smart(df_work, df, params, keep, columns_to_normalize, sys)

            print(f"{'='*80}\n", file=sys.stderr)
            return result

        # If multi-level deduplication is not enabled, use standard logic
        if not multi_level:
            print(f"\n→ Using STANDARD deduplication", file=sys.stderr)
            columns = params.get('columns', [])
            if not columns:
                columns = None  # Check all columns
            print(f"  Deduplicating by columns: {columns}", file=sys.stderr)
            result = df.drop_duplicates(subset=columns, keep=keep)
            print(f"  Result: {len(result)} rows (removed {len(df) - len(result)} duplicates)", file=sys.stderr)
            print(f"{'='*80}\n", file=sys.stderr)
            return result

        # Multi-level deduplication logic (existing code)
        print(f"\n→ Using MULTI-LEVEL deduplication", file=sys.stderr)

        # Define required columns
        email_col = 'Email Address'
        name_cols = ['First Name', 'Last Name']
        address_cols = ['Person Street', 'Person City', 'Person State']
        phone_col = 'Direct Phone Number'

        # Check if required columns exist
        all_required_cols = [email_col] + name_cols + address_cols + [phone_col]
        missing_cols = [col for col in all_required_cols if col not in df.columns]

        if missing_cols:
            # Fall back to standard deduplication if required columns are missing
            print(f"  ⚠️  Missing required columns: {missing_cols}", file=sys.stderr)
            print(f"  Falling back to standard deduplication", file=sys.stderr)
            columns = params.get('columns', [])
            result = df.drop_duplicates(subset=columns if columns else None, keep=keep)
            print(f"  Result: {len(result)} rows (removed {len(df) - len(result)} duplicates)", file=sys.stderr)
            print(f"{'='*80}\n", file=sys.stderr)
            return result

        print(f"  ✓ All required columns present", file=sys.stderr)

        # Create masks to identify different groups of rows
        has_email = df[email_col].notna()
        no_email = df[email_col].isna()
        has_address = df['Person Street'].notna()
        no_address = df['Person Street'].isna()

        # Group 1: Rows with Email Address (deduplicate by email)
        group1_mask = has_email

        # Group 2: Rows without Email but with Address (deduplicate by name + address)
        group2_mask = no_email & has_address

        # Group 3: Rows without Email and without Address (deduplicate by name + phone)
        group3_mask = no_email & no_address

        print(f"\n  Group breakdown:", file=sys.stderr)
        print(f"    Level 1 (has email): {group1_mask.sum()} rows", file=sys.stderr)
        print(f"    Level 2 (no email, has address): {group2_mask.sum()} rows", file=sys.stderr)
        print(f"    Level 3 (no email, no address): {group3_mask.sum()} rows", file=sys.stderr)
        print(f"    Total: {group1_mask.sum() + group2_mask.sum() + group3_mask.sum()} rows", file=sys.stderr)

        # Process each group separately and collect results
        results = []
        total_removed = 0

        # Level 1: Deduplicate by Email Address (for rows with non-blank email)
        if group1_mask.any():
            group1_df = df[group1_mask]
            print(f"\n  Level 1: Deduplicating by Email Address", file=sys.stderr)
            print(f"    Input: {len(group1_df)} rows", file=sys.stderr)
            print(f"    Columns: ['{email_col}']", file=sys.stderr)

            group1_deduped = group1_df.drop_duplicates(subset=[email_col], keep=keep)
            removed_level1 = len(group1_df) - len(group1_deduped)
            total_removed += removed_level1

            print(f"    Output: {len(group1_deduped)} rows", file=sys.stderr)
            print(f"    Removed: {removed_level1} duplicates", file=sys.stderr)

            results.append(group1_deduped)

        # Level 2: Deduplicate by Name + Address (for rows with blank email but non-blank address)
        if group2_mask.any():
            group2_df = df[group2_mask]
            dedupe_cols_level2 = name_cols + address_cols

            print(f"\n  Level 2: Deduplicating by Name + Address", file=sys.stderr)
            print(f"    Input: {len(group2_df)} rows", file=sys.stderr)
            print(f"    Columns: {dedupe_cols_level2}", file=sys.stderr)

            group2_deduped = group2_df.drop_duplicates(subset=dedupe_cols_level2, keep=keep)
            removed_level2 = len(group2_df) - len(group2_deduped)
            total_removed += removed_level2

            print(f"    Output: {len(group2_deduped)} rows", file=sys.stderr)
            print(f"    Removed: {removed_level2} duplicates", file=sys.stderr)

            results.append(group2_deduped)

        # Level 3: Deduplicate by Name + Phone (for rows with blank email and blank address)
        if group3_mask.any():
            group3_df = df[group3_mask]
            dedupe_cols_level3 = name_cols + [phone_col]

            print(f"\n  Level 3: Deduplicating by Name + Phone", file=sys.stderr)
            print(f"    Input: {len(group3_df)} rows", file=sys.stderr)
            print(f"    Columns: {dedupe_cols_level3}", file=sys.stderr)

            group3_deduped = group3_df.drop_duplicates(subset=dedupe_cols_level3, keep=keep)
            removed_level3 = len(group3_df) - len(group3_deduped)
            total_removed += removed_level3

            print(f"    Output: {len(group3_deduped)} rows", file=sys.stderr)
            print(f"    Removed: {removed_level3} duplicates", file=sys.stderr)

            results.append(group3_deduped)

        # Combine all deduplicated groups
        if results:
            result_df = pd.concat(results, axis=0)
            # Sort by original index to maintain order
            result_df = result_df.sort_index()

            print(f"\n  Final Result:", file=sys.stderr)
            print(f"    Total input: {len(df)} rows", file=sys.stderr)
            print(f"    Total output: {len(result_df)} rows", file=sys.stderr)
            print(f"    Total removed: {total_removed} duplicates", file=sys.stderr)
            print(f"{'='*80}\n", file=sys.stderr)

            return result_df
        else:
            # Return empty dataframe with same structure if no groups had data
            print(f"  ⚠️  No groups had data, returning empty dataframe", file=sys.stderr)
            print(f"{'='*80}\n", file=sys.stderr)
            return df.iloc[:0].copy()

    def _execute_standard_smart(self, df_work, df_original, params, keep, columns_to_normalize, sys):
        """Execute standard deduplication with smart matching"""
        print(f"\n→ Standard deduplication with smart matching", file=sys.stderr)

        # Use normalized columns for deduplication
        normalized_cols = [f'_normalized_{col}' for col in columns_to_normalize]
        print(f"  Deduplicating by normalized columns: {normalized_cols}", file=sys.stderr)

        # Find duplicates based on normalized columns
        mask = df_work.duplicated(subset=normalized_cols, keep=keep)

        # Return original rows that are not duplicates
        result = df_original[~mask].copy()
        print(f"  Result: {len(result)} rows (removed {len(df_original) - len(result)} duplicates)", file=sys.stderr)

        return result

    def _execute_multi_level_smart(self, df_work, df_original, keep, sys):
        """Execute multi-level deduplication with smart matching"""
        print(f"\n→ Multi-level deduplication with smart matching", file=sys.stderr)

        # Define required columns (normalized versions)
        email_col = '_normalized_Email Address'
        name_cols = ['_normalized_First Name', '_normalized_Last Name']
        address_cols = ['_normalized_Person Street', '_normalized_Person City', '_normalized_Person State']
        phone_col = '_normalized_Direct Phone Number'

        # Check if normalized columns exist
        all_required_norm_cols = [email_col] + name_cols + address_cols + [phone_col]
        missing_norm_cols = [col for col in all_required_norm_cols if col not in df_work.columns]

        if missing_norm_cols:
            print(f"  ⚠️  Missing normalized columns: {missing_norm_cols}", file=sys.stderr)
            print(f"  Falling back to standard smart deduplication", file=sys.stderr)
            # Use all normalized columns
            norm_cols = [col for col in df_work.columns if col.startswith('_normalized_')]
            mask = df_work.duplicated(subset=norm_cols, keep=keep)
            result = df_original[~mask].copy()
            print(f"  Result: {len(result)} rows (removed {len(df_original) - len(result)} duplicates)", file=sys.stderr)
            return result

        # Create masks based on original columns
        has_email = df_original['Email Address'].notna()
        no_email = df_original['Email Address'].isna()
        has_address = df_original['Person Street'].notna()
        no_address = df_original['Person Street'].isna()

        group1_mask = has_email
        group2_mask = no_email & has_address
        group3_mask = no_email & no_address

        print(f"\n  Group breakdown:", file=sys.stderr)
        print(f"    Level 1 (has email): {group1_mask.sum()} rows", file=sys.stderr)
        print(f"    Level 2 (no email, has address): {group2_mask.sum()} rows", file=sys.stderr)
        print(f"    Level 3 (no email, no address): {group3_mask.sum()} rows", file=sys.stderr)

        results = []
        total_removed = 0

        # Level 1: Deduplicate by normalized email
        if group1_mask.any():
            group1_work = df_work[group1_mask]
            group1_orig = df_original[group1_mask]

            print(f"\n  Level 1: Deduplicating by normalized Email Address", file=sys.stderr)
            print(f"    Input: {len(group1_orig)} rows", file=sys.stderr)

            mask_dup = group1_work.duplicated(subset=[email_col], keep=keep)
            group1_deduped = group1_orig[~mask_dup]
            removed_level1 = len(group1_orig) - len(group1_deduped)
            total_removed += removed_level1

            print(f"    Output: {len(group1_deduped)} rows", file=sys.stderr)
            print(f"    Removed: {removed_level1} duplicates", file=sys.stderr)

            results.append(group1_deduped)

        # Level 2: Deduplicate by normalized name + address
        if group2_mask.any():
            group2_work = df_work[group2_mask]
            group2_orig = df_original[group2_mask]
            dedupe_cols_level2 = name_cols + address_cols

            print(f"\n  Level 2: Deduplicating by normalized Name + Address", file=sys.stderr)
            print(f"    Input: {len(group2_orig)} rows", file=sys.stderr)

            mask_dup = group2_work.duplicated(subset=dedupe_cols_level2, keep=keep)
            group2_deduped = group2_orig[~mask_dup]
            removed_level2 = len(group2_orig) - len(group2_deduped)
            total_removed += removed_level2

            print(f"    Output: {len(group2_deduped)} rows", file=sys.stderr)
            print(f"    Removed: {removed_level2} duplicates", file=sys.stderr)

            results.append(group2_deduped)

        # Level 3: Deduplicate by normalized name + phone
        if group3_mask.any():
            group3_work = df_work[group3_mask]
            group3_orig = df_original[group3_mask]
            dedupe_cols_level3 = name_cols + [phone_col]

            print(f"\n  Level 3: Deduplicating by normalized Name + Phone", file=sys.stderr)
            print(f"    Input: {len(group3_orig)} rows", file=sys.stderr)

            mask_dup = group3_work.duplicated(subset=dedupe_cols_level3, keep=keep)
            group3_deduped = group3_orig[~mask_dup]
            removed_level3 = len(group3_orig) - len(group3_deduped)
            total_removed += removed_level3

            print(f"    Output: {len(group3_deduped)} rows", file=sys.stderr)
            print(f"    Removed: {removed_level3} duplicates", file=sys.stderr)

            results.append(group3_deduped)

        # Combine results
        if results:
            result_df = pd.concat(results, axis=0)
            result_df = result_df.sort_index()

            print(f"\n  Final Result:", file=sys.stderr)
            print(f"    Total input: {len(df_original)} rows", file=sys.stderr)
            print(f"    Total output: {len(result_df)} rows", file=sys.stderr)
            print(f"    Total removed: {total_removed} duplicates", file=sys.stderr)

            return result_df
        else:
            print(f"  ⚠️  No groups had data, returning empty dataframe", file=sys.stderr)
            return df_original.iloc[:0].copy()


class SortDataOperation(BaseOperation):
    """Sort data by columns"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_sort',
            name='Sort Data',
            category='Data Matching',
            description='Sort rows by one or more columns',
            parameters=[
                Parameter(
                    name='columns',
                    type='column_list',
                    description='Columns to sort by (in order of priority)'
                ),
                Parameter(
                    name='ascending',
                    type='boolean',
                    description='Sort from small to large (A-Z, 1-9)',
                    default=True
                )
            ],
            excel_equivalent='Sort A-Z or Sort Z-A',
            examples=[
                'Sort by date (newest first)',
                'Sort by customer name alphabetically',
                'Sort by amount (highest first)'
            ],
            tags=['sort', 'order', 'arrange', 'alphabetical']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        columns = params['columns']
        ascending = self.get_param_value(params, 'ascending', True)
        
        return df.sort_values(by=columns, ascending=ascending)


class RemoveRowsIfOperation(BaseOperation):
    """Remove rows based on conditions"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_remove_rows_if',
            name='Remove Rows If',
            category='Data Matching',
            description='Remove rows that match specified conditions',
            parameters=[
                Parameter(
                    name='column',
                    type='column',
                    description='Column to check'
                ),
                Parameter(
                    name='condition',
                    type='choice',
                    description='Condition to match',
                    choices=['is_blank', 'contains', 'equals', 'not_equals', 'is_false'],
                    default='is_blank'
                ),
                Parameter(
                    name='value',
                    type='text',
                    description='Value to match (not needed for is_blank or is_false)',
                    required=False,
                    default=''
                ),
                Parameter(
                    name='case_sensitive',
                    type='boolean',
                    description='Match case exactly (for contains/equals)',
                    required=False,
                    default=False
                ),
                Parameter(
                    name='enhanced_blank_detection',
                    type='boolean',
                    description='Enhanced blank detection: Also treats empty strings and N/A variants as blank (for is_blank condition only)',
                    required=False,
                    default=False
                ),
                Parameter(
                    name='smart_address_detection',
                    type='boolean',
                    description='Smart address detection: When checking address columns (Person Street, Company Street Address), check if ANY related address column has data before removing (for is_blank condition only)',
                    required=False,
                    default=True
                )
            ],
            excel_equivalent='Filter and Delete',
            examples=[
                'Remove rows where Email is blank',
                'Remove rows where Address contains "PO Box"',
                'Remove rows where Email_Valid is FALSE',
                'Remove rows where Status equals "Invalid"'
            ],
            tags=['remove', 'filter', 'delete', 'rows', 'conditional']
        )

    def _get_related_address_columns(self, df: pd.DataFrame, column: str) -> list:
        """
        Find related address columns for smart blank detection.

        For example, if checking "Person Street", also return "Company Street Address"
        so we can check if there's an address in ANY related column.
        """
        if 'street' not in column.lower() and 'address' not in column.lower():
            return []  # Not an address column

        related = []
        address_keywords = ['street', 'address']

        for col in df.columns:
            if col == column:
                continue  # Don't include the same column

            col_lower = col.lower()
            # Check if this is an address-related column
            if any(keyword in col_lower for keyword in address_keywords):
                # Exclude email addresses
                if 'email' not in col_lower:
                    related.append(col)

        return related

    def _is_blank_enhanced(self, value) -> bool:
        """
        Enhanced blank detection that treats the following as blank:
        - NaN / None / pd.NaT
        - Empty strings ("")
        - Whitespace-only strings ("   ")
        - N/A variants: "n/a", "na", "null", "none" (case-insensitive)

        Returns True if value should be considered blank, False otherwise.
        """
        # Check for actual NaN/None first
        if value is None or pd.isna(value):
            return True

        # Check for string-based blanks
        if isinstance(value, str):
            cleaned = value.strip().lower()
            if cleaned in ["", "n/a", "na", "null", "none"]:
                return True

        return False

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        column = params['column']
        condition = params['condition']
        value = self.get_param_value(params, 'value', '')
        case_sensitive = self.get_param_value(params, 'case_sensitive', False)
        enhanced_blank = self.get_param_value(params, 'enhanced_blank_detection', False)
        # Smart address detection: check related address columns (e.g., Person Street + Company Street Address)
        smart_address_detection = self.get_param_value(params, 'smart_address_detection', True)

        # Create mask for rows to KEEP (inverse of remove)
        if condition == 'is_blank':
            # Keep rows that are NOT blank
            if enhanced_blank:
                # Enhanced mode: Also treats empty strings and N/A variants as blank
                # Useful for datasets with "N/A" strings or empty string placeholders

                if smart_address_detection:
                    # Check related address columns
                    related_cols = self._get_related_address_columns(df, column)
                    if related_cols:
                        # Keep row if ANY related address column has non-blank data
                        def has_any_address(row):
                            # Check main column
                            if not self._is_blank_enhanced(row[column]):
                                return True
                            # Check related columns
                            for col in related_cols:
                                if col in row.index and not self._is_blank_enhanced(row[col]):
                                    return True
                            return False

                        mask = df.apply(has_any_address, axis=1)
                    else:
                        # No related columns, check only the specified column
                        mask = ~df[column].apply(self._is_blank_enhanced)
                else:
                    # Smart detection disabled, check only the specified column
                    mask = ~df[column].apply(self._is_blank_enhanced)

                # Validation: Check if we're accidentally removing valid data
                false_positives = df[~mask & df[column].notna()]
                if len(false_positives) > 0:
                    # Some non-NaN values are being marked as blank
                    # This is expected in enhanced mode if they are "", "N/A", etc.
                    # But we should warn if actual addresses are being removed
                    non_empty_removed = false_positives[
                        (false_positives[column].astype(str).str.strip() != '') &
                        (~false_positives[column].astype(str).str.lower().isin(['n/a', 'na', 'null', 'none']))
                    ]
                    if len(non_empty_removed) > 0:
                        # This is a BUG - valid non-empty, non-N/A strings are being removed
                        import sys
                        print(f"\n{'='*80}", file=sys.stderr)
                        print(f"WARNING: Enhanced blank detection removing valid data!", file=sys.stderr)
                        print(f"Column: {column}", file=sys.stderr)
                        print(f"Valid values being removed: {len(non_empty_removed)}", file=sys.stderr)
                        print(f"Examples: {non_empty_removed[column].head(5).tolist()}", file=sys.stderr)
                        print(f"{'='*80}\n", file=sys.stderr)
            else:
                # Standard mode (default): ONLY treat NaN/None as blank
                # According to requirements: "Empty strings or whitespace should NOT be treated as blank"
                # This is the safest default - only remove actual missing data (NaN)

                if smart_address_detection:
                    # Check related address columns for smart detection
                    related_cols = self._get_related_address_columns(df, column)
                    if related_cols:
                        # Keep row if ANY related address column has non-NaN data
                        def has_any_address_standard(row):
                            # Check main column
                            if pd.notna(row[column]):
                                return True
                            # Check related columns
                            for col in related_cols:
                                if col in row.index and pd.notna(row[col]):
                                    return True
                            return False

                        mask = df.apply(has_any_address_standard, axis=1)
                    else:
                        # No related columns, check only specified column for NaN
                        mask = df[column].notna()
                else:
                    # Smart detection disabled, check only specified column for NaN
                    mask = df[column].notna()

                # Validation: Check if we're removing valid non-NaN data
                removed_mask = ~mask
                if removed_mask.any():
                    removed_values = df.loc[removed_mask, column]
                    # Check for non-NaN values that are being removed
                    non_nan_removed = removed_values.notna()
                    if non_nan_removed.any():
                        # CRITICAL BUG - standard mode is removing non-NaN values!
                        import sys
                        print(f"\n{'='*80}", file=sys.stderr)
                        print(f"CRITICAL ERROR: Standard mode removing non-NaN values!", file=sys.stderr)
                        print(f"This should NEVER happen!", file=sys.stderr)
                        print(f"Column: {column}", file=sys.stderr)
                        print(f"Non-NaN values marked for removal: {non_nan_removed.sum()}", file=sys.stderr)
                        print(f"Examples: {removed_values[non_nan_removed].head(10).tolist()}", file=sys.stderr)
                        print(f"{'='*80}\n", file=sys.stderr)

        elif condition == 'contains':
            # Keep rows that do NOT contain the value
            if case_sensitive:
                mask = ~df[column].astype(str).str.contains(value, na=False, regex=False)
            else:
                mask = ~df[column].astype(str).str.contains(value, case=False, na=False, regex=False)

        elif condition == 'equals':
            # Keep rows that do NOT equal the value
            if case_sensitive:
                mask = df[column].astype(str) != value
            else:
                mask = df[column].astype(str).str.lower() != value.lower()

        elif condition == 'not_equals':
            # Keep rows that DO equal the value (double negative)
            if case_sensitive:
                mask = df[column].astype(str) == value
            else:
                mask = df[column].astype(str).str.lower() == value.lower()

        elif condition == 'is_false':
            # Keep rows that are NOT False (True or other values)
            # Handle boolean columns
            mask = ~(df[column].astype(str).str.lower().isin(['false', '0', 'no', 'n']))

        else:
            # Default: keep all rows
            mask = pd.Series([True] * len(df), index=df.index)

        # Return filtered dataframe WITHOUT reset_index
        # The executor needs original indices to track which rows were removed
        return df[mask]


class ReorderColumnsOperation(BaseOperation):
    """Reorder columns to specific sequence"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_reorder_columns',
            name='Reorder Columns',
            category='Data - Organization',
            description='Reorder columns to a specific sequence',
            parameters=[
                Parameter(
                    name='column_order',
                    type='list',
                    description='Ordered list of column names (comma-separated)',
                    required=True
                ),
                Parameter(
                    name='keep_unlisted',
                    type='boolean',
                    description='Keep columns not in the list (add them at the end)',
                    default=False
                )
            ],
            excel_equivalent='Drag columns manually',
            examples=[
                'Put Company, Contact, Email first',
                'Reorder to standard mailing list format',
                'Move ID columns to the end'
            ],
            tags=['reorder', 'organize', 'sort', 'columns']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        df = df.copy()

        # Parse column order
        column_order = params['column_order']
        if isinstance(column_order, str):
            column_order = [col.strip() for col in column_order.split(',')]

        keep_unlisted = params.get('keep_unlisted', False)

        # Filter to columns that actually exist
        existing_ordered = [col for col in column_order if col in df.columns]

        if keep_unlisted:
            # Add any columns not in the list to the end
            unlisted_cols = [col for col in df.columns if col not in column_order]
            final_order = existing_ordered + unlisted_cols
        else:
            # Only keep columns in the specified order
            final_order = existing_ordered

        # Reorder
        df = df[final_order]

        return df


class SetHeaderRowOperation(BaseOperation):
    """Set which row contains column headers"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_set_header_row',
            name='Set Header Row',
            category='Transform',
            description='Specify which row contains column headers and remove rows above it',
            parameters=[
                Parameter(
                    name='header_row_number',
                    type='number',
                    description='Row number to use as headers (1-based, e.g., row 2 = enter "2")',
                    required=True,
                    default=2
                ),
                Parameter(
                    name='remove_above',
                    type='boolean',
                    description='Remove all rows above the new header row',
                    required=False,
                    default=True
                )
            ],
            excel_equivalent='Data → Remove Top Rows + Promote Headers',
            examples=[
                'File has title in row 1, headers in row 2 - use row 2 as headers',
                'Skip first 3 rows of metadata and use row 4 as column names',
                'Correct files with "Unnamed: 0" columns by using row 2'
            ],
            tags=['headers', 'columns', 'metadata', 'rows', 'transform']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        Set header row and optionally remove rows above it.

        Args:
            df: Input dataframe
            params: {
                'header_row_number': int (1-based row number),
                'remove_above': bool (remove rows above new headers)
            }

        Returns:
            Dataframe with new headers
        """
        header_row_number = int(params.get('header_row_number', 2))
        remove_above = params.get('remove_above', True)

        # Convert to 0-based index
        header_row_idx = header_row_number - 1

        # Validate row number
        if header_row_idx < 0 or header_row_idx >= len(df):
            raise ValueError(
                f"Invalid row number: {header_row_number}. "
                f"Must be between 1 and {len(df)}"
            )

        # Get the row that will become headers
        new_headers = df.iloc[header_row_idx].values

        # Create new dataframe
        if remove_above:
            # Start from the row AFTER the new header row
            new_df = df.iloc[header_row_idx + 1:].copy()
        else:
            # Keep all rows but set new headers
            new_df = df.copy()

        # Set new column names
        new_df.columns = new_headers

        # Reset index
        new_df.reset_index(drop=True, inplace=True)

        return new_df


class KeepBestContactPerLocationOperation(BaseOperation):
    """
    Keep only the highest-ranking contact per location.

    Groups contacts by location (hospital/facility) and keeps only the contact
    with the highest-ranking title (CEO > Director > Manager > Supervisor > Clinical).
    """

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_keep_best_contact_per_location',
            name='Keep Best Contact Per Location',
            category='Data Matching',
            description='Keep only the highest-ranking contact per location (deduplicates by facility, prioritizing executives/directors over managers/clinical staff)',
            parameters=[
                Parameter(
                    name='location_columns',
                    type='text',
                    description='Location identifier columns (comma-separated, e.g., "Hospital Name,Address,City")',
                    required=True,
                    default='Hospital Name,Address'
                ),
                Parameter(
                    name='title_column',
                    type='column',
                    description='Column containing job titles',
                    required=True
                ),
                Parameter(
                    name='tie_breaker',
                    type='choice',
                    description='If multiple contacts have same rank, how to choose',
                    required=False,
                    choices=['first', 'last'],
                    default='first'
                ),
                Parameter(
                    name='add_rank_column',
                    type='boolean',
                    description='Add a column showing the title rank (1=Executive, 2=Director, etc.)',
                    required=False,
                    default=True
                )
            ],
            excel_equivalent='Group by Location + Custom Ranking',
            examples=[
                'Keep only the CEO per hospital (remove managers/nurses)',
                'Deduplicate facility contacts, prioritizing executives',
                'Get highest-authority contact for each location'
            ],
            tags=['dedupe', 'rank', 'title', 'healthcare', 'contacts', 'location']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        Keep best contact per location based on title ranking.
        REMOVES all lower-ranked contacts and tracks them.

        Args:
            df: Input dataframe
            params: {
                'location_columns': comma-separated column names,
                'title_column': column with job titles,
                'tie_breaker': 'first' or 'last',
                'add_rank_column': bool
            }

        Returns:
            Dataframe with ONLY highest-ranked contact per location
        """
        import logging
        from utils.title_ranker import HealthcareTitleRanker

        location_cols_str = params.get('location_columns', '')
        title_column = params.get('title_column')
        tie_breaker = params.get('tie_breaker', 'first')
        add_rank_column = params.get('add_rank_column', True)

        # Parse location columns
        if not location_cols_str or not location_cols_str.strip():
            raise ValueError("Location columns are required")

        location_columns = [col.strip() for col in location_cols_str.split(',')]

        # Validate columns exist
        for col in location_columns:
            if col not in df.columns:
                raise ValueError(f"Location column '{col}' not found")

        if title_column not in df.columns:
            raise ValueError(f"Title column '{title_column}' not found")

        logging.info("=" * 80)
        logging.info("KEEP BEST CONTACT PER LOCATION OPERATION")
        logging.info("=" * 80)
        logging.info(f"Input rows: {len(df)}")
        logging.info(f"Location columns: {location_columns}")
        logging.info(f"Title column: {title_column}")
        logging.info(f"Tie breaker: {tie_breaker}")

        # Create a working copy with reset index to avoid alignment issues
        df_work = df.copy().reset_index(drop=True)

        # Store original row ID mapping
        df_work['_original_row_id'] = range(len(df_work))

        # Add rank columns
        df_work['_rank_number'] = df_work[title_column].apply(HealthcareTitleRanker.get_rank_number)
        df_work['_rank_category'] = df_work[title_column].apply(HealthcareTitleRanker.get_rank_name)

        # Sort by location columns + rank number (lower rank = higher priority)
        sort_by = location_columns + ['_rank_number']
        df_sorted = df_work.sort_values(by=sort_by, ascending=True)

        logging.info(f"After ranking and sorting:")
        logging.info(f"  Sorted rows: {len(df_sorted)}")
        logging.info(f"  Unique locations: {df_sorted[location_columns].drop_duplicates().shape[0]}")

        # Keep only the FIRST (best ranked) contact per location group
        df_kept = df_sorted.drop_duplicates(subset=location_columns, keep=tie_breaker).copy()

        logging.info(f"After drop_duplicates:")
        logging.info(f"  Kept rows: {len(df_kept)}")
        logging.info(f"  Removed rows: {len(df_sorted) - len(df_kept)}")

        # Get kept row IDs
        kept_row_ids = set(df_kept['_original_row_id'].values)

        # Get removed rows using row IDs (not boolean indexing on misaligned indices)
        df_removed = df_work[~df_work['_original_row_id'].isin(kept_row_ids)].copy()

        logging.info(f"Removed contacts breakdown:")
        if len(df_removed) > 0:
            rank_counts = df_removed['_rank_category'].value_counts()
            for rank, count in rank_counts.items():
                logging.info(f"  {rank}: {count} contacts")

            # Build a lookup dict for kept contacts by location
            # This avoids boolean filtering issues
            kept_lookup = {}
            for _, row in df_kept.iterrows():
                location_key = tuple(row[col] for col in location_columns)
                kept_lookup[location_key] = {
                    'rank_category': row['_rank_category'],
                    'title': row[title_column]
                }

            # Add removal reasons using lookup dict
            def get_removal_reason(row):
                location_key = tuple(row[col] for col in location_columns)
                if location_key in kept_lookup:
                    kept_info = kept_lookup[location_key]
                    return f"Lower rank ({row['_rank_category']}) - Kept: {kept_info['rank_category']}"
                return "Duplicate location - lower priority"

            df_removed['_removal_reason'] = df_removed.apply(get_removal_reason, axis=1)

        # Prepare result dataframe
        result_df = df_kept.copy()

        # Add rank column if requested
        if add_rank_column:
            result_df['Title Rank'] = result_df['_rank_category']

        # Clean up temporary columns from result
        temp_cols = ['_rank_number', '_rank_category', '_original_row_id']
        result_df = result_df.drop(columns=[col for col in temp_cols if col in result_df.columns])

        # Reset index
        result_df.reset_index(drop=True, inplace=True)

        # CRITICAL: Attach removed rows metadata for UI to display
        if len(df_removed) > 0:
            # Clean up removed dataframe
            df_removed_clean = df_removed.drop(columns=[col for col in temp_cols if col in df_removed.columns])

            # Store removed rows in result metadata
            result_df.attrs['removed_rows'] = df_removed_clean
            result_df.attrs['removed_count'] = len(df_removed_clean)
            result_df.attrs['removal_operation'] = 'Keep Best Contact Per Location'

            logging.info(f"Attached {len(df_removed_clean)} removed rows to result metadata")

        logging.info("=" * 80)

        return result_df


class AnalyzeTitleRanksOperation(BaseOperation):
    """Add title rank columns for analysis"""

    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_analyze_title_ranks',
            name='Analyze Title Rankings',
            category='Analysis',
            description='Add columns showing title rank number and category (for verification)',
            parameters=[
                Parameter(
                    name='title_column',
                    type='column',
                    description='Column containing job titles',
                    required=True
                )
            ],
            excel_equivalent='Helper function',
            examples=[
                'Show rank distribution before deduplication',
                'Verify title ranking logic',
                'Debug contact selection'
            ],
            tags=['analysis', 'rank', 'title', 'debug', 'healthcare']
        )

    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """Add rank columns"""
        from utils.title_ranker import HealthcareTitleRanker

        title_column = params.get('title_column')

        if title_column not in df.columns:
            raise ValueError(f"Title column '{title_column}' not found")

        # Make a copy
        df = df.copy()

        # Add rank columns
        df['Title Rank Number'] = df[title_column].apply(HealthcareTitleRanker.get_rank_number)
        df['Title Rank Category'] = df[title_column].apply(HealthcareTitleRanker.get_rank_name)

        return df


# Register all operations
registry.register(VLookupOperation())
registry.register(RemoveDuplicatesOperation())
registry.register(SortDataOperation())
registry.register(RemoveRowsIfOperation())
registry.register(ReorderColumnsOperation())
registry.register(SetHeaderRowOperation())
registry.register(KeepBestContactPerLocationOperation())
registry.register(AnalyzeTitleRanksOperation())
