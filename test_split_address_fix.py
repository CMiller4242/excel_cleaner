"""
Test Split Address Operation Fix
Verify that the operation works with default suite_keywords parameter
"""
import pandas as pd
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from operations.zoominfo_ops import SplitAddressOperation

def test_split_address_with_defaults():
    """Test that operation works without providing suite_keywords"""

    # Create test data
    test_addresses = [
        "400 W Illinois Ave Ste 950",
        "3715 Northside Pkwy NW Bldg 300 Ste 110",
        "123 Main Street",
        "2065 E South Blvd Suites 201 And 301",
        "251 Stenton Ave",
        "",
        None
    ]

    df = pd.DataFrame({
        'Person Street': test_addresses
    })

    # Create operation
    op = SplitAddressOperation()

    # Test validation with minimal parameters (no suite_keywords)
    params = {
        'source_column': 'Person Street'
    }

    is_valid, error = op.validate_params(df, params)

    if not is_valid:
        print(f"❌ VALIDATION FAILED: {error}")
        return False

    print("✅ Validation passed!")

    # Execute operation
    try:
        result_df = op.execute(df, params)
        print("✅ Execution successful!")

        # Display results
        print("\n📊 RESULTS:")
        print("-" * 80)
        for idx, row in result_df.iterrows():
            addr1 = row.get('Address 1', '')
            addr2 = row.get('Address 2', '')
            print(f"Row {idx}:")
            print(f"  Address 1: '{addr1}'")
            print(f"  Address 2: '{addr2}'")
            print()

        # Verify expected results
        expected_results = [
            ("400 W Illinois Ave", "Ste 950"),
            ("3715 Northside Pkwy NW", "Bldg 300 Ste 110"),
            ("123 Main Street", ""),
            ("2065 E South Blvd", "Suites 201 And 301"),
            ("251 Stenton Ave", ""),
            ("", ""),
            ("", "")
        ]

        all_correct = True
        for idx, (expected_addr1, expected_addr2) in enumerate(expected_results):
            actual_addr1 = result_df.iloc[idx]['Address 1']
            actual_addr2 = result_df.iloc[idx]['Address 2']

            if actual_addr1 != expected_addr1 or actual_addr2 != expected_addr2:
                print(f"❌ Row {idx} mismatch!")
                print(f"   Expected: '{expected_addr1}' | '{expected_addr2}'")
                print(f"   Got:      '{actual_addr1}' | '{actual_addr2}'")
                all_correct = False

        if all_correct:
            print("✅ All test cases passed!")
            return True
        else:
            print("❌ Some test cases failed")
            return False

    except Exception as e:
        print(f"❌ EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 80)
    print("Testing Split Address Operation with Default Parameters")
    print("=" * 80)
    print()

    success = test_split_address_with_defaults()

    print()
    print("=" * 80)
    if success:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ TESTS FAILED")
    print("=" * 80)

    sys.exit(0 if success else 1)
