#!/usr/bin/env python3
"""
Validate ZoomInfo Healthcare Preset Operation Flow
Traces through each operation to verify column references are correct
"""

import json
from pathlib import Path

# Expected initial columns from a ZoomInfo Healthcare/EVS export
INITIAL_COLUMNS = [
    "First Name",
    "Last Name",
    "Job Title",
    "Direct Phone Number",
    "Email Address",
    "Person Street",
    "Person City",
    "Person State",
    "Person Zip Code",
    "Company Name",
    "ZoomInfo Contact ID",
    # Plus ~62 other ZoomInfo columns that will be removed
    "Middle Name", "Salutation", "Suffix", "Management Level",
    "Job Start Date", "Job Function", "Department",
    # ... (abbreviated for clarity)
]

def validate_preset():
    """Validate the ZoomInfo preset operation flow"""

    print("=" * 80)
    print("VALIDATING ZOOMINFO HEALTHCARE PRESET")
    print("=" * 80)

    # Load preset
    preset_file = Path("presets/system/zoominfo_healthcare_evs.json")
    with open(preset_file, 'r') as f:
        preset = json.load(f)

    print(f"\nPreset: {preset['name']}")
    print(f"Version: {preset['version']}")
    print(f"Operations: {len(preset['operations'])}")

    # Simulate column state through operations
    columns = set(INITIAL_COLUMNS)  # Start with initial columns

    print("\n" + "=" * 80)
    print("TRACING OPERATION FLOW")
    print("=" * 80)

    for i, op in enumerate(preset['operations'], 1):
        print(f"\n{'='*80}")
        print(f"OPERATION {i}: {op['operation_id']}")
        print(f"{'='*80}")
        print(f"Description: {op['description']}")
        print(f"Enabled: {op['enabled']}")

        params = op.get('parameters', {})
        print(f"\nParameters: {json.dumps(params, indent=2)}")

        print(f"\nColumns BEFORE: {sorted(columns)}")

        # Simulate operation effects on columns
        if op['operation_id'] == 'clean_remove_blank_rows':
            # No column changes
            print("  → No column changes (removes blank rows)")

        elif op['operation_id'] == 'clean_remove_columns':
            # Remove specified columns
            cols_to_remove = params.get('columns', [])
            removed = []
            for col in cols_to_remove:
                if col in columns:
                    columns.remove(col)
                    removed.append(col)
            print(f"  → Removed {len(removed)} columns")
            if removed:
                print(f"     First few: {removed[:5]}")

        elif op['operation_id'] == 'text_concatenate':
            # Check source columns exist
            source_cols = params.get('columns', [])
            new_col = params.get('new_column', '')
            remove_original = params.get('remove_original', False)

            print(f"  → Concatenate: {' + '.join(source_cols)} → {new_col}")

            # Validate source columns exist
            for col in source_cols:
                if col not in columns:
                    print(f"  ❌ ERROR: Source column '{col}' does not exist!")
                    return False
                else:
                    print(f"  ✓ Source column '{col}' exists")

            # Add new column
            columns.add(new_col)
            print(f"  ✓ Added column '{new_col}'")

            # Remove original columns if specified
            if remove_original:
                for col in source_cols:
                    columns.remove(col)
                print(f"  ✓ Removed original columns: {source_cols}")

        elif op['operation_id'] == 'zoominfo_split_address':
            # Check source column exists
            source_col = params.get('source_column', '')
            addr1 = params.get('address1_column', 'Address 1')
            addr2 = params.get('address2_column', 'Address 2')
            remove_original = params.get('remove_original', False)

            print(f"  → Split: {source_col} → {addr1} + {addr2}")

            if source_col not in columns:
                print(f"  ❌ ERROR: Source column '{source_col}' does not exist!")
                return False
            else:
                print(f"  ✓ Source column '{source_col}' exists")

            # Add new columns
            columns.add(addr1)
            columns.add(addr2)
            print(f"  ✓ Added columns '{addr1}' and '{addr2}'")

            # Remove original if specified
            if remove_original:
                columns.remove(source_col)
                print(f"  ✓ Removed original column '{source_col}'")

        elif op['operation_id'] == 'text_rename_batch':
            # Rename multiple columns
            mappings = params.get('mappings', {})

            print(f"  → Rename {len(mappings)} columns")

            for old_name, new_name in mappings.items():
                if old_name not in columns:
                    print(f"  ❌ ERROR: Column '{old_name}' does not exist for renaming!")
                    return False
                else:
                    columns.remove(old_name)
                    columns.add(new_name)
                    print(f"  ✓ Renamed '{old_name}' → '{new_name}'")

        elif op['operation_id'] == 'zoominfo_state_converter':
            # Check column exists
            col = params.get('column', 'State')

            if col not in columns:
                print(f"  ❌ ERROR: Column '{col}' does not exist!")
                return False
            else:
                print(f"  ✓ Column '{col}' exists (will convert state names to codes)")

        elif op['operation_id'] == 'remove_excluded_states':
            # Check column exists
            col = params.get('column', 'State')
            excluded = params.get('excluded_states', '')

            if col not in columns:
                print(f"  ❌ ERROR: Column '{col}' does not exist!")
                return False
            else:
                print(f"  ✓ Column '{col}' exists (will remove rows with: {excluded})")

        elif op['operation_id'] == 'data_remove_rows_if':
            # Check column exists
            col = params.get('column', '')
            condition = params.get('condition', '')

            if col not in columns:
                print(f"  ❌ ERROR: Column '{col}' does not exist!")
                return False
            else:
                print(f"  ✓ Column '{col}' exists (will remove rows where {condition})")

        elif op['operation_id'] == 'data_reorder_columns':
            # Check all columns in order exist
            col_order = params.get('column_order', [])
            keep_unlisted = params.get('keep_unlisted', False)

            print(f"  → Reorder to: {col_order}")
            print(f"  → Keep unlisted: {keep_unlisted}")

            missing = []
            for col in col_order:
                if col not in columns:
                    missing.append(col)

            if missing:
                print(f"  ❌ ERROR: Columns in order that don't exist: {missing}")
                return False
            else:
                print(f"  ✓ All {len(col_order)} columns in order exist")

            if not keep_unlisted:
                # Final columns will be ONLY those in col_order
                columns = set(col_order)
                print(f"  → Final columns (keep_unlisted=False): {sorted(columns)}")

        print(f"\nColumns AFTER: {sorted(columns)}")
        print(f"Total columns: {len(columns)}")

    # Final validation
    print("\n" + "=" * 80)
    print("FINAL VALIDATION")
    print("=" * 80)

    expected_output = preset.get('expected_output', {})
    expected_cols = expected_output.get('column_names', [])

    print(f"\nExpected final columns: {expected_cols}")
    print(f"Actual final columns: {sorted(columns)}")

    if set(columns) == set(expected_cols):
        print("\n✓ SUCCESS: Final columns match expected output!")
        print(f"  {len(columns)} columns: {', '.join(sorted(columns))}")
        return True
    else:
        print("\n❌ MISMATCH!")
        missing = set(expected_cols) - set(columns)
        extra = set(columns) - set(expected_cols)
        if missing:
            print(f"  Missing: {missing}")
        if extra:
            print(f"  Extra: {extra}")
        return False

if __name__ == '__main__':
    print("\nValidating ZoomInfo Healthcare/EVS Preset...")
    success = validate_preset()

    print("\n" + "=" * 80)
    if success:
        print("✓ VALIDATION PASSED")
        print("=" * 80)
        print("\nThe preset is correctly configured:")
        print("  - All operation parameters reference existing columns")
        print("  - Operations execute in correct dependency order")
        print("  - Final output matches expected 10-column format")
        exit(0)
    else:
        print("❌ VALIDATION FAILED")
        print("=" * 80)
        print("\nPlease fix the errors above before using this preset.")
        exit(1)
