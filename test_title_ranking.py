#!/usr/bin/env python3
"""
Test for Healthcare Title Ranking System
Tests title ranking and Keep Best Contact Per Location operation
"""

import pandas as pd
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from utils.title_ranker import HealthcareTitleRanker
from operations.data_ops import KeepBestContactPerLocationOperation, AnalyzeTitleRanksOperation


def test_title_ranker():
    """Test HealthcareTitleRanker with various job titles"""

    print("=" * 80)
    print("TEST 1: HealthcareTitleRanker - Title Ranking")
    print("=" * 80)

    test_cases = [
        # (title, expected_rank, expected_category)
        ("Chief Executive Officer", 1, "Executive Leadership"),
        ("CEO", 1, "Executive Leadership"),
        ("Chief Nursing Officer", 1, "Executive Leadership"),
        ("CNO", 1, "Executive Leadership"),
        ("Vice President of Operations", 1, "Executive Leadership"),
        ("VP of Nursing", 1, "Executive Leadership"),
        ("President", 1, "Executive Leadership"),

        ("Executive Director", 2, "Senior Director"),
        ("Director of Nursing", 2, "Senior Director"),
        ("Senior Director of Operations", 2, "Senior Director"),
        ("Director", 2, "Senior Director"),
        ("Department Head", 2, "Senior Director"),

        ("Nursing Manager", 3, "Manager/Administrator"),
        ("Manager", 3, "Manager/Administrator"),
        ("Administrator", 3, "Manager/Administrator"),
        ("Office Manager", 3, "Manager/Administrator"),
        ("Practice Manager", 3, "Manager/Administrator"),
        ("Coordinator", 3, "Manager/Administrator"),

        ("Supervisor", 4, "Supervisor/Lead"),
        ("Nursing Supervisor", 4, "Supervisor/Lead"),
        ("Team Lead", 4, "Supervisor/Lead"),
        ("Charge Nurse", 4, "Supervisor/Lead"),

        ("Registered Nurse", 5, "Clinical"),
        ("RN", 5, "Clinical"),
        ("Nurse Practitioner", 5, "Clinical"),
        ("NP", 5, "Clinical"),
        ("Physician Assistant", 5, "Clinical"),
        ("PA", 5, "Clinical"),
        ("Licensed Practical Nurse", 5, "Clinical"),
        ("LPN", 5, "Clinical"),
        ("Medical Assistant", 5, "Clinical"),
        ("Technician", 5, "Clinical"),
        ("Therapist", 5, "Clinical"),

        ("Administrative Assistant", 6, "Administrative Support"),
        ("Executive Assistant", 6, "Administrative Support"),
        ("Receptionist", 6, "Administrative Support"),
        ("Secretary", 6, "Administrative Support"),

        ("Unknown Title", 7, "Unknown/Other"),
        ("", 7, "Unknown"),
        (None, 7, "Unknown"),
    ]

    print("\nTesting title ranking:")
    print("-" * 80)

    all_passed = True
    for i, (title, expected_rank, expected_category) in enumerate(test_cases, 1):
        rank_num, rank_name = HealthcareTitleRanker.rank_title(title)
        status = "✓" if (rank_num == expected_rank and rank_name == expected_category) else "✗"

        if rank_num != expected_rank or rank_name != expected_category:
            all_passed = False
            print(f"{status} Test {i}: '{title}'")
            print(f"  Expected: Rank {expected_rank} - {expected_category}")
            print(f"  Got:      Rank {rank_num} - {rank_name}")
            print()
        else:
            print(f"{status} Test {i}: '{title}' → Rank {rank_num} ({rank_name})")

    if all_passed:
        print("\n✓ ALL TITLE RANKING TESTS PASSED\n")
    else:
        print("\n✗ SOME TESTS FAILED\n")
        return False

    return True


def test_keep_best_contact():
    """Test KeepBestContactPerLocationOperation"""

    print("=" * 80)
    print("TEST 2: Keep Best Contact Per Location")
    print("=" * 80)

    # Create test data
    test_data = {
        'Hospital Name': [
            'Memorial Hospital', 'Memorial Hospital', 'Memorial Hospital',
            'St. Mary Medical Center', 'St. Mary Medical Center',
            'City General Hospital', 'City General Hospital', 'City General Hospital', 'City General Hospital',
            'Regional Medical Center'
        ],
        'Address 1': [
            '100 Main St', '100 Main St', '100 Main St',
            '200 Oak Ave', '200 Oak Ave',
            '300 Elm St', '300 Elm St', '300 Elm St', '300 Elm St',
            '400 Park Blvd'
        ],
        'City': [
            'Springfield', 'Springfield', 'Springfield',
            'Lakeville', 'Lakeville',
            'Riverside', 'Riverside', 'Riverside', 'Riverside',
            'Westfield'
        ],
        'State': [
            'IL', 'IL', 'IL',
            'OH', 'OH',
            'MI', 'MI', 'MI', 'MI',
            'IN'
        ],
        'First Name': [
            'John', 'Jane', 'Bob',
            'Alice', 'Charlie',
            'David', 'Emma', 'Frank', 'Grace',
            'Henry'
        ],
        'Last Name': [
            'Doe', 'Smith', 'Johnson',
            'Williams', 'Brown',
            'Jones', 'Davis', 'Miller', 'Wilson',
            'Moore'
        ],
        'Job Title': [
            'Chief Nursing Officer', 'Nursing Manager', 'Registered Nurse',
            'Director of Nursing', 'Nursing Supervisor',
            'CEO', 'VP of Operations', 'Nursing Manager', 'RN',
            'Registered Nurse'
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nORIGINAL DATA (10 contacts):")
    print("-" * 80)
    print(df[['Hospital Name', 'First Name', 'Last Name', 'Job Title', 'City']].to_string(index=False))
    print(f"\nTotal rows: {len(df)}")

    # Test the operation
    operation = KeepBestContactPerLocationOperation()
    params = {
        'location_columns': 'Hospital Name,Address 1,City,State',
        'title_column': 'Job Title',
        'tie_breaker': 'first',
        'add_rank_column': True
    }

    result = operation.execute(df, params)

    print("\n" + "=" * 80)
    print("RESULT (After keeping best contact per location):")
    print("-" * 80)
    print(result[['Hospital Name', 'First Name', 'Last Name', 'Job Title', 'Title Rank', 'City']].to_string(index=False))
    print(f"\nTotal rows: {len(result)}")
    print(f"Rows removed: {len(df) - len(result)}")

    # Verify results
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("-" * 80)

    checks = [
        # Should have exactly 4 hospitals (4 unique locations)
        (len(result) == 4, "Should have 4 contacts (one per hospital)"),

        # Memorial Hospital: Should keep CNO (rank 1) not Manager or RN
        (result[result['Hospital Name'] == 'Memorial Hospital']['Job Title'].values[0] == 'Chief Nursing Officer',
         "Memorial Hospital: Kept CNO (rank 1)"),

        # St. Mary: Should keep Director (rank 2) not Supervisor
        (result[result['Hospital Name'] == 'St. Mary Medical Center']['Job Title'].values[0] == 'Director of Nursing',
         "St. Mary Medical Center: Kept Director (rank 2)"),

        # City General: Should keep CEO (rank 1) not VP, Manager, or RN
        (result[result['Hospital Name'] == 'City General Hospital']['Job Title'].values[0] == 'CEO',
         "City General Hospital: Kept CEO (rank 1)"),

        # Regional Medical: Only has one contact (RN)
        (result[result['Hospital Name'] == 'Regional Medical Center']['Job Title'].values[0] == 'Registered Nurse',
         "Regional Medical Center: Kept only contact (RN)"),

        # Title Rank column added
        ('Title Rank' in result.columns, "Title Rank column added"),
    ]

    all_checks_passed = True
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"{status} {description}")
        if not check:
            all_checks_passed = False

    if all_checks_passed:
        print("\n✓ ALL VERIFICATION CHECKS PASSED")
    else:
        print("\n✗ SOME CHECKS FAILED")
        return False

    return True


def test_analyze_title_ranks():
    """Test AnalyzeTitleRanksOperation"""

    print("\n" + "=" * 80)
    print("TEST 3: Analyze Title Ranks Operation")
    print("=" * 80)

    # Create test data
    test_data = {
        'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams'],
        'Job Title': [
            'Chief Executive Officer',
            'Director of Nursing',
            'Nursing Manager',
            'Registered Nurse'
        ]
    }

    df = pd.DataFrame(test_data)

    print("\nORIGINAL DATA:")
    print("-" * 80)
    print(df.to_string(index=False))

    # Test the operation
    operation = AnalyzeTitleRanksOperation()
    params = {'title_column': 'Job Title'}

    result = operation.execute(df, params)

    print("\nRESULT (With rank columns added):")
    print("-" * 80)
    print(result.to_string(index=False))

    # Verify
    checks = [
        ('Title Rank Number' in result.columns, "Title Rank Number column added"),
        ('Title Rank Category' in result.columns, "Title Rank Category column added"),
        (result['Title Rank Number'].tolist() == [1, 2, 3, 5], "Ranks are correct [1, 2, 3, 5]"),
        (result['Title Rank Category'].tolist()[0] == 'Executive Leadership', "CEO ranked as Executive"),
        (result['Title Rank Category'].tolist()[1] == 'Senior Director', "Director ranked as Senior Director"),
    ]

    all_checks_passed = True
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"{status} {description}")
        if not check:
            all_checks_passed = False

    if all_checks_passed:
        print("\n✓ ALL VERIFICATION CHECKS PASSED")
    else:
        print("\n✗ SOME CHECKS FAILED")
        return False

    return True


def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("HEALTHCARE TITLE RANKING TEST SUITE")
    print("=" * 80)
    print()

    try:
        # Run all tests
        test1_passed = test_title_ranker()
        test2_passed = test_keep_best_contact()
        test3_passed = test_analyze_title_ranks()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        results = [
            ("Title Ranking", test1_passed),
            ("Keep Best Contact Per Location", test2_passed),
            ("Analyze Title Ranks", test3_passed),
        ]

        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")

        all_passed = all(passed for _, passed in results)

        if all_passed:
            print("\n" + "=" * 80)
            print("ALL TESTS PASSED! ✓")
            print("=" * 80)
            print("\nTitle ranking system is working correctly:")
            print("- All 7 rank tiers correctly identified")
            print("- Keep Best Contact operation selects highest-ranking titles")
            print("- Analyze Title Ranks adds verification columns")
            print("- Ready for use with Definitive Healthcare contact lists")
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
