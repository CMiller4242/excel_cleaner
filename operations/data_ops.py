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
    """Remove duplicate rows"""
    
    def get_metadata(self) -> OperationMetadata:
        return OperationMetadata(
            id='data_remove_duplicates',
            name='Remove Duplicate Rows',
            category='Data Matching',
            description='Remove duplicate records based on one or more columns',
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
                )
            ],
            excel_equivalent='Remove Duplicates',
            examples=[
                'Remove duplicate customers by Customer ID',
                'Remove duplicate emails from contact list',
                'Keep only unique product codes',
                'Smart deduplication: by email, then by name+address, then by name+phone'
            ],
            tags=['duplicates', 'unique', 'dedupe', 'remove']
        )
    
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        keep = self.get_param_value(params, 'keep', 'first')
        multi_level = self.get_param_value(params, 'multi_level_deduplication', True)

        # If multi-level deduplication is not enabled, use standard logic
        if not multi_level:
            columns = params.get('columns', [])
            if not columns:
                columns = None  # Check all columns
            return df.drop_duplicates(subset=columns, keep=keep)

        # Multi-level deduplication logic
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
            import sys
            print(f"Warning: Multi-level deduplication requires columns: {all_required_cols}", file=sys.stderr)
            print(f"Missing columns: {missing_cols}", file=sys.stderr)
            print(f"Falling back to standard deduplication", file=sys.stderr)
            columns = params.get('columns', [])
            return df.drop_duplicates(subset=columns if columns else None, keep=keep)

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

        # Process each group separately and collect results
        results = []

        # Level 1: Deduplicate by Email Address (for rows with non-blank email)
        if group1_mask.any():
            group1_df = df[group1_mask]
            group1_deduped = group1_df.drop_duplicates(subset=[email_col], keep=keep)
            results.append(group1_deduped)

        # Level 2: Deduplicate by Name + Address (for rows with blank email but non-blank address)
        if group2_mask.any():
            group2_df = df[group2_mask]
            dedupe_cols_level2 = name_cols + address_cols
            group2_deduped = group2_df.drop_duplicates(subset=dedupe_cols_level2, keep=keep)
            results.append(group2_deduped)

        # Level 3: Deduplicate by Name + Phone (for rows with blank email and blank address)
        if group3_mask.any():
            group3_df = df[group3_mask]
            dedupe_cols_level3 = name_cols + [phone_col]
            group3_deduped = group3_df.drop_duplicates(subset=dedupe_cols_level3, keep=keep)
            results.append(group3_deduped)

        # Combine all deduplicated groups
        if results:
            result_df = pd.concat(results, axis=0)
            # Sort by original index to maintain order
            result_df = result_df.sort_index()
            return result_df
        else:
            # Return empty dataframe with same structure if no groups had data
            return df.iloc[:0].copy()


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


# Register all operations
registry.register(VLookupOperation())
registry.register(RemoveDuplicatesOperation())
registry.register(SortDataOperation())
registry.register(RemoveRowsIfOperation())
registry.register(ReorderColumnsOperation())
