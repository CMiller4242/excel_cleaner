#!/usr/bin/env python3
"""
Test for Smart Duplicate Matching in RemoveDuplicatesOperation
Tests address normalization and fuzzy matching capabilities
"""

import pandas as pd
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from utils.address_normalizer import AddressNormalizer, TextNormalizer
from operations.data_ops import RemoveDuplicatesOperation

def test_address_normalizer():
    """Test AddressNormalizer with various abbreviations"""

    print("=" * 70)
    print("TEST 1: AddressNormalizer")
    print("=" * 70)

    test_cases = [
        # (input, expected_output)
        ("2000 Pepperell Pkwy", "2000 PEPPERELL PARKWAY"),
        ("2000 PEPPERELL PARKWAY", "2000 PEPPERELL PARKWAY"),
        ("123 Main St", "123 MAIN STREET"),
        ("123 MAIN STREET", "123 MAIN STREET"),
        ("456 Oak Ave", "456 OAK AVENUE"),
        ("789 W Broadway", "789 WEST BROADWAY"),
        ("100 N 5th St", "100 NORTH 5TH STREET"),
        ("200 SE Park Blvd", "200 SOUTHEAST PARK BOULEVARD"),
        ("150 Bergen St Ste 1", "150 BERGEN STREET SUITE 1"),
        ("150 BERGEN ST STE 1", "150 BERGEN STREET SUITE 1"),
        ("300 Circle Dr, Apt 5", "300 CIRCLE DRIVE APARTMENT 5"),
    ]

    print("\nTesting address abbreviation expansion:")
    print("-" * 70)

    all_passed = True
    for i, (input_addr, expected) in enumerate(test_cases, 1):
        result = AddressNormalizer.normalize(input_addr)
        status = "✓" if result == expected else "✗"
        print(f"{status} Test {i}:")
        print(f"  Input:    '{input_addr}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")

        if result != expected:
            all_passed = False
            print(f"  MISMATCH!")
        print()

    if all_passed:
        print("✓ ALL ADDRESS NORMALIZATION TESTS PASSED\n")
    else:
        print("✗ SOME TESTS FAILED\n")
        return False

    return True


def test_text_normalizer():
    """Test TextNormalizer for general text"""

    print("=" * 70)
    print("TEST 2: TextNormalizer")
    print("=" * 70)

    test_cases = [
        ("John Smith", "JOHN SMITH"),
        ("john smith", "JOHN SMITH"),
        ("ACME Corp.", "ACME CORP"),
        ("O'Brien & Associates", "O BRIEN ASSOCIATES"),
        ("email@example.com", "EMAIL EXAMPLE COM"),
    ]

    print("\nTesting general text normalization:")
    print("-" * 70)

    all_passed = True
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = TextNormalizer.normalize(input_text)
        status = "✓" if result == expected else "✗"
        print(f"{status} Test {i}: '{input_text}' → '{result}'")

        if result != expected:
            all_passed = False
            print(f"  Expected: '{expected}'")
            print(f"  MISMATCH!")

    print()
    if all_passed:
        print("✓ ALL TEXT NORMALIZATION TESTS PASSED\n")
    else:
        print("✗ SOME TESTS FAILED\n")
        return False

    return True


def test_smart_duplicate_removal():
    """Test RemoveDuplicatesOperation with smart matching"""

    print("=" * 70)
    print("TEST 3: Smart Duplicate Removal")
    print("=" * 70)

    # Create test data with semantic duplicates
    test_data = {
        'Customer ID': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'Name': ['ACME Corp', 'ACME Corp', 'XYZ Inc', 'ABC Company', 'ABC Company'],
        'Address': [
            '2000 Pepperell Pkwy',
            '2000 PEPPERELL PARKWAY',  # Duplicate with abbreviation difference
            '123 Main St',
            '456 W Oak Ave',
            '456 WEST OAK AVENUE'  # Duplicate with directional abbreviation
        ],
        'City': ['Opelika', 'Opelika', 'Auburn', 'Columbus', 'Columbus'],
        'Email': ['contact@acme.com', 'contact@acme.com', 'info@xyz.com',
                  'hello@abc.com', 'hello@abc.com']
    }

    df = pd.DataFrame(test_data)

    print("\n1. ORIGINAL DATA:")
    print("-" * 70)
    print(df.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")

    # Test standard deduplication (should NOT detect semantic duplicates)
    print("\n" + "=" * 70)
    print("TEST 3a: Standard Deduplication (smart_matching=False)")
    print("=" * 70)

    operation = RemoveDuplicatesOperation()
    params_standard = {
        'columns': 'Name,Address',
        'keep': 'first',
        'smart_matching': False
    }

    result_standard = operation.execute(df.copy(), params_standard)

    print("\nRESULT:")
    print("-" * 70)
    print(result_standard.to_string(index=False))
    print(f"\nRows after standard dedup: {len(result_standard)}")
    print(f"Rows removed: {len(df) - len(result_standard)}")

    # Standard should only remove exact duplicates
    expected_standard_rows = 5  # No semantic duplicates detected
    if len(result_standard) == expected_standard_rows:
        print(f"\n✓ PASSED: Standard dedup kept {expected_standard_rows} rows (no semantic matching)")
    else:
        print(f"\n✗ FAILED: Expected {expected_standard_rows} rows, got {len(result_standard)}")
        return False

    # Test smart deduplication (SHOULD detect semantic duplicates)
    print("\n" + "=" * 70)
    print("TEST 3b: Smart Deduplication (smart_matching=True)")
    print("=" * 70)

    params_smart = {
        'columns': 'Name,Address',
        'keep': 'first',
        'smart_matching': True,
        'address_columns': 'Address'
    }

    result_smart = operation.execute(df.copy(), params_smart)

    print("\nRESULT:")
    print("-" * 70)
    print(result_smart.to_string(index=False))
    print(f"\nRows after smart dedup: {len(result_smart)}")
    print(f"Rows removed: {len(df) - len(result_smart)}")

    # Smart should detect semantic duplicates
    expected_smart_rows = 3  # Should detect both address abbreviation duplicates
    if len(result_smart) == expected_smart_rows:
        print(f"\n✓ PASSED: Smart dedup detected semantic duplicates, kept {expected_smart_rows} unique rows")
    else:
        print(f"\n✗ FAILED: Expected {expected_smart_rows} rows, got {len(result_smart)}")
        return False

    # Verify specific duplicates were detected
    print("\n" + "=" * 70)
    print("Verifying Specific Duplicate Detection:")
    print("-" * 70)

    # Should keep first occurrence of each semantic duplicate
    remaining_addresses = result_smart['Address'].tolist()

    checks = [
        ('2000 Pepperell Pkwy' in remaining_addresses,
         "'2000 Pepperell Pkwy' (first occurrence) kept"),
        ('2000 PEPPERELL PARKWAY' not in remaining_addresses,
         "'2000 PEPPERELL PARKWAY' (duplicate) removed"),
        ('456 W Oak Ave' in remaining_addresses,
         "'456 W Oak Ave' (first occurrence) kept"),
        ('456 WEST OAK AVENUE' not in remaining_addresses,
         "'456 WEST OAK AVENUE' (duplicate) removed"),
    ]

    all_checks_passed = True
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"{status} {description}")
        if not check:
            all_checks_passed = False

    if all_checks_passed:
        print("\n✓ ALL DUPLICATE DETECTION CHECKS PASSED")
    else:
        print("\n✗ SOME CHECKS FAILED")
        return False

    return True


def test_multi_level_smart_matching():
    """Test multi-level deduplication with smart matching"""

    print("\n" + "=" * 70)
    print("TEST 4: Multi-Level Smart Deduplication")
    print("=" * 70)

    # Create test data with duplicates at different levels
    test_data = {
        'Name': ['ACME Corp', 'ACME Corp', 'XYZ Inc', 'XYZ Inc'],
        'Address': ['123 Main St', '123 MAIN STREET', '456 Oak Ave', '456 Oak Ave'],
        'Email': ['contact@acme.com', '', 'info@xyz.com', 'sales@xyz.com'],
        'Phone': ['555-1234', '555-1234', '555-5678', '555-9999']
    }

    df = pd.DataFrame(test_data)

    print("\nORIGINAL DATA:")
    print("-" * 70)
    print(df.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")

    operation = RemoveDuplicatesOperation()
    params = {
        'multi_level': True,
        'keep': 'first',
        'smart_matching': True,
        'address_columns': 'Address'
    }

    result = operation.execute(df.copy(), params)

    print("\nRESULT:")
    print("-" * 70)
    print(result.to_string(index=False))
    print(f"\nRows after multi-level smart dedup: {len(result)}")
    print(f"Rows removed: {len(df) - len(result)}")

    # Should detect ACME as duplicate (Name + Address match with normalization)
    expected_rows = 3
    if len(result) == expected_rows:
        print(f"\n✓ PASSED: Multi-level smart dedup correctly identified duplicates")
        return True
    else:
        print(f"\n✗ FAILED: Expected {expected_rows} rows, got {len(result)}")
        return False


def main():
    """Run all tests"""

    print("\n" + "=" * 70)
    print("SMART DUPLICATE MATCHING TEST SUITE")
    print("=" * 70)
    print()

    try:
        # Run all tests
        test1_passed = test_address_normalizer()
        test2_passed = test_text_normalizer()
        test3_passed = test_smart_duplicate_removal()
        test4_passed = test_multi_level_smart_matching()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        results = [
            ("Address Normalization", test1_passed),
            ("Text Normalization", test2_passed),
            ("Smart Duplicate Removal", test3_passed),
            ("Multi-Level Smart Matching", test4_passed),
        ]

        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")

        all_passed = all(passed for _, passed in results)

        if all_passed:
            print("\n" + "=" * 70)
            print("ALL TESTS PASSED! ✓")
            print("=" * 70)
            print("\nSmart matching is working correctly:")
            print("- Address abbreviations normalized (PKWY → PARKWAY)")
            print("- Directional abbreviations normalized (W → WEST)")
            print("- Street types normalized (ST → STREET, AVE → AVENUE)")
            print("- Semantic duplicates detected and removed")
            print("- Multi-level deduplication works with smart matching")
            return 0
        else:
            print("\n" + "=" * 70)
            print("SOME TESTS FAILED ✗")
            print("=" * 70)
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
