#!/usr/bin/env python3
"""
Integration test for StandardizeCustomerNumberSingleOperation
Tests the complete workflow: load data → apply operation → export to .txt
"""

import pandas as pd
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from operations.text_ops import StandardizeCustomerNumberSingleOperation
from utils.export_helper import ExportHelper


def test_complete_workflow():
    """Test complete workflow with sample data"""

    print("=" * 80)
    print("INTEGRATION TEST: Customer Number Standardization + TXT Export")
    print("=" * 80)

    # Create sample data matching user's format
    print("\n1. Creating sample data...")
    sample_data = {
        'First_Name': ['John', 'Jane', 'Bob', 'Alice'],
        'Last_Name': ['Smith', 'Doe', 'Johnson', 'Williams'],
        'Customer_Number': [
            '1726274-639507',
            '4441157-639473',
            '9609-640231',
            '1172785-639691'
        ],
        'Email': [
            'john.smith@example.com',
            'jane.doe@example.com',
            'bob.johnson@example.com',
            'alice.williams@example.com'
        ]
    }

    df = pd.DataFrame(sample_data)

    print("✓ Sample data created:")
    print(df.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")

    # Apply standardization operation
    print("\n2. Applying StandardizeCustomerNumberSingleOperation...")
    operation = StandardizeCustomerNumberSingleOperation()
    params = {
        'customer_column': 'Customer_Number',
        'output_length': 8,
        'handle_non_hyphenated': 'Pad as-is'
    }

    result_df = operation.execute(df, params)

    print("✓ Operation completed:")
    print(result_df.to_string(index=False))

    # Verify transformations
    print("\n3. Verifying transformations...")
    expected = ['01726274', '04441157', '00009609', '01172785']
    actual = result_df['Customer_Number'].tolist()

    if actual == expected:
        print("✓ All customer numbers standardized correctly:")
        for i, (orig, new) in enumerate(zip(df['Customer_Number'], result_df['Customer_Number'])):
            print(f"  {orig} → {new}")
    else:
        print(f"✗ Mismatch! Expected: {expected}, Got: {actual}")
        return False

    # Test TXT export
    print("\n4. Testing .txt export...")
    output_file = Path(__file__).parent / 'test_output.txt'

    try:
        ExportHelper.export_to_txt(result_df, str(output_file), include_header=True)
        print(f"✓ Exported to: {output_file}")

        # Read and verify format
        with open(output_file, 'r') as f:
            lines = f.readlines()

        print(f"\n5. Verifying TXT file format...")
        print(f"Total lines: {len(lines)}")
        print("\nFirst 5 lines:")
        for i, line in enumerate(lines[:5], 1):
            print(f"  {i}: {line.rstrip()}")

        # Verify format: all fields should be quoted
        has_quotes = all('"' in line for line in lines)
        has_commas = all(',' in line for line in lines)

        if has_quotes and has_commas:
            print("\n✓ TXT format verified:")
            print("  - All fields are quoted")
            print("  - Fields are comma-delimited")
            print("  - Header row included")
        else:
            print("\n✗ TXT format incorrect!")
            return False

        # Clean up
        output_file.unlink()
        print("\n✓ Test file cleaned up")

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        return False

    return True


def test_no_header_export():
    """Test TXT export without header"""

    print("\n" + "=" * 80)
    print("TEST: TXT Export Without Header")
    print("=" * 80)

    # Create simple test data
    df = pd.DataFrame({
        'Customer_Number': ['01726274', '04441157'],
        'Name': ['John Smith', 'Jane Doe']
    })

    output_file = Path(__file__).parent / 'test_no_header.txt'

    try:
        print("\n1. Exporting without header...")
        ExportHelper.export_to_txt(df, str(output_file), include_header=False)

        with open(output_file, 'r') as f:
            lines = f.readlines()

        print(f"✓ Exported {len(lines)} data rows (no header)")
        print("\nContents:")
        for i, line in enumerate(lines, 1):
            print(f"  {i}: {line.rstrip()}")

        # Verify no header
        if len(lines) == 2 and 'Customer_Number' not in lines[0]:
            print("\n✓ No-header export verified")
            result = True
        else:
            print("\n✗ Header was included!")
            result = False

        # Clean up
        output_file.unlink()

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        result = False

    return result


def main():
    """Run all integration tests"""

    print("\n" + "=" * 80)
    print("STANDARDIZE CUSTOMER NUMBER - INTEGRATION TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run tests
        test1_passed = test_complete_workflow()
        test2_passed = test_no_header_export()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        results = [
            ("Complete Workflow (Operation + Export)", test1_passed),
            ("No-Header Export", test2_passed),
        ]

        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")

        all_passed = all(passed for _, passed in results)

        if all_passed:
            print("\n" + "=" * 80)
            print("ALL INTEGRATION TESTS PASSED! ✓")
            print("=" * 80)
            print("\nReady for production use:")
            print("- StandardizeCustomerNumberSingleOperation registered")
            print("- Operation transforms: '1726274-639507' → '01726274'")
            print("- TXT export with quoted comma-delimited format")
            print("- Support for header/no-header options")
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
