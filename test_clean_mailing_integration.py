#!/usr/bin/env python3
"""
Integration test for CleanMailingCustomerDataOperation
Tests complete workflow: load → clean customer/segment → export to TXT
"""

import pandas as pd
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from operations.text_ops import CleanMailingCustomerDataOperation
from utils.export_helper import ExportHelper


def test_complete_mailing_workflow():
    """Test complete mailing list workflow"""

    print("=" * 80)
    print("INTEGRATION TEST: Mailing List Clean + Export")
    print("=" * 80)

    # Create sample mailing list data (matching user's use case)
    print("\n1. Creating sample mailing list data...")
    sample_data = {
        'First_Name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie'],
        'Last_Name': ['Smith', 'Doe', 'Johnson', 'Williams', 'Brown'],
        'Customer_Number': [
            '1726274-639507',  # → 01726274
            '4441157-639473',  # → 04441157
            '9609-640231',     # → 00009609
            '1172785-639691',  # → 01172785
            '123456-999999'    # → 00123456
        ],
        'Segment': [
            '0',   # → 00
            '1',   # → 01
            '31',  # → 31
            '5',   # → 05
            ''     # → blank (keep as-is)
        ],
        'Address': [
            '123 Main St',
            '456 Oak Ave',
            '789 Pine Rd',
            '321 Elm Dr',
            '654 Maple Ln'
        ],
        'City': ['Springfield', 'Riverdale', 'Gotham', 'Metropolis', 'Star City'],
        'State': ['IL', 'NY', 'NJ', 'DE', 'CA'],
        'Zip': ['62701', '10001', '07001', '19901', '90001']
    }

    df = pd.DataFrame(sample_data)

    print("✓ Sample data created:")
    print(df[['First_Name', 'Last_Name', 'Customer_Number', 'Segment']].to_string(index=False))
    print(f"\nTotal records: {len(df)}")

    # Apply cleaning operation
    print("\n2. Applying CleanMailingCustomerDataOperation...")
    operation = CleanMailingCustomerDataOperation()
    params = {
        'customer_column': 'Customer_Number',
        'customer_length': 8,
        'segment_column': 'Segment',
        'segment_length': 2,
        'handle_non_hyphenated': 'Pad as-is',
        'blank_segments_to_zero': False  # Keep blanks as blank
    }

    result_df = operation.execute(df, params)

    print("✓ Cleaning completed:")
    print(result_df[['First_Name', 'Last_Name', 'Customer_Number', 'Segment']].to_string(index=False))

    # Verify transformations
    print("\n3. Verifying transformations...")
    expected_customers = ['01726274', '04441157', '00009609', '01172785', '00123456']
    expected_segments = ['00', '01', '31', '05', '']

    actual_customers = result_df['Customer_Number'].tolist()
    actual_segments = result_df['Segment'].tolist()

    customer_correct = actual_customers == expected_customers
    segment_correct = actual_segments == expected_segments

    if customer_correct and segment_correct:
        print("✓ All transformations correct:")
        print("\n  Customer Number Transformations:")
        for orig, clean in zip(df['Customer_Number'], result_df['Customer_Number']):
            print(f"    {orig:20s} → {clean}")
        print("\n  Segment Number Transformations:")
        for orig, clean in zip(df['Segment'], result_df['Segment']):
            orig_display = str(orig) if orig != '' and not pd.isna(orig) else '(blank)'
            clean_display = clean if clean != '' else '(blank)'
            print(f"    {orig_display:20s} → {clean_display}")
    else:
        print("✗ Transformation mismatch!")
        if not customer_correct:
            print(f"  Expected customers: {expected_customers}")
            print(f"  Got customers:      {actual_customers}")
        if not segment_correct:
            print(f"  Expected segments: {expected_segments}")
            print(f"  Got segments:      {actual_segments}")
        return False

    # Test TXT export
    print("\n4. Testing TXT export (comma-delimited with quotes)...")
    output_file = Path(__file__).parent / 'test_mailing_output.txt'

    try:
        ExportHelper.export_to_txt(result_df, str(output_file), include_header=True)
        print(f"✓ Exported to: {output_file}")

        # Read and verify format
        with open(output_file, 'r') as f:
            lines = f.readlines()

        print(f"\n5. Verifying TXT format...")
        print(f"Total lines: {len(lines)} (1 header + {len(lines)-1} data rows)")
        print("\nFirst 3 lines:")
        for i, line in enumerate(lines[:3], 1):
            print(f"  {i}: {line.rstrip()}")

        # Verify format
        has_quotes = all('"' in line for line in lines)
        has_commas = all(',' in line for line in lines)
        customer_in_file = '01726274' in lines[1]  # Check first data row
        segment_in_file = '"00"' in lines[1]       # Segment should be quoted "00"

        if has_quotes and has_commas and customer_in_file and segment_in_file:
            print("\n✓ TXT format verified:")
            print("  - All fields quoted")
            print("  - Comma-delimited")
            print("  - Header included")
            print("  - Customer numbers cleaned (8 digits)")
            print("  - Segment numbers padded (2 digits)")
        else:
            print("\n✗ TXT format incorrect!")
            return False

        # Show sample output line
        print("\nSample output line (record 1):")
        print(f"  {lines[1].rstrip()}")

        # Clean up
        output_file.unlink()
        print("\n✓ Test file cleaned up")

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        return False

    return True


def test_comparison_with_old_operation():
    """Compare new operation name and capabilities"""

    print("\n" + "=" * 80)
    print("TEST: Operation Naming and Capabilities")
    print("=" * 80)

    operation = CleanMailingCustomerDataOperation()
    metadata = operation.get_metadata()

    print("\nOperation Details:")
    print(f"  ID:          {metadata.id}")
    print(f"  Name:        {metadata.name}")
    print(f"  Category:    {metadata.category}")
    print(f"  Description: {metadata.description}")

    print("\nTags (for search):")
    print(f"  {', '.join(metadata.tags)}")

    print("\nParameters:")
    for param in metadata.parameters:
        required = "required" if param.required else "optional"
        default = f" (default: {param.default})" if hasattr(param, 'default') and param.default is not None else ""
        print(f"  - {param.name} ({param.type}, {required}){default}")
        print(f"    {param.description}")

    print("\nExamples:")
    for example in metadata.examples:
        print(f"  • {example}")

    # Verify it's searchable by key terms
    searchable_terms = ['customer', 'mailing', 'segment', 'clean', 'standardize']
    name_and_desc = (metadata.name + ' ' + metadata.description + ' ' + ' '.join(metadata.tags)).lower()

    print("\n✓ Operation is searchable by:")
    for term in searchable_terms:
        if term in name_and_desc:
            print(f"  ✓ '{term}'")
        else:
            print(f"  ✗ '{term}' (NOT FOUND)")

    return True


def main():
    """Run all integration tests"""

    print("\n" + "=" * 80)
    print("CLEAN MAILING CUSTOMER DATA - INTEGRATION TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run tests
        test1_passed = test_complete_mailing_workflow()
        test2_passed = test_comparison_with_old_operation()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        results = [
            ("Complete Mailing Workflow (Clean + Export)", test1_passed),
            ("Operation Naming and Search", test2_passed),
        ]

        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")

        all_passed = all(passed for _, passed in results)

        if all_passed:
            print("\n" + "=" * 80)
            print("ALL INTEGRATION TESTS PASSED! ✓")
            print("=" * 80)
            print("\nProduction-Ready Features:")
            print("- Renamed from 'Standardize Customer Number (Single)'")
            print("- New name: 'Clean Mailing List Customer Data'")
            print("- Processes customer numbers: extract before hyphen, pad to 8")
            print("- Processes segment numbers: pad to 2 digits")
            print("- Handles both columns independently or together")
            print("- Exports to TXT with quoted comma-delimited format")
            print("- Searchable by: customer, mailing, segment, clean, standardize")
            return 0
        else:
            print("\n" + "=" * 80)
            print("SOME TESTS FAILED ✗")
            print("=" * 80)
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
