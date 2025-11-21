"""
Comprehensive tests for RemoveRowsIfOperation
Tests the fix for the blank address detection bug
"""
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from operations.data_ops import RemoveRowsIfOperation
from engine.executor import OperationExecutor


def test_standard_mode_only_removes_nan():
    """Test that standard mode ONLY removes NaN, not empty strings"""
    print("\n" + "="*80)
    print("TEST 1: Standard Mode - Only NaN")
    print("="*80)

    df = pd.DataFrame({
        'Address': [
            '123 Main St',     # Valid address
            None,              # NaN - should be removed
            '',                # Empty string - should NOT be removed in standard mode
            '   ',             # Whitespace - should NOT be removed in standard mode
            '456 Elm St'       # Valid address
        ]
    })

    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Address',
        'condition': 'is_blank',
        'enhanced_blank_detection': False,
        'smart_address_detection': False  # Disable for this test
    }

    result = operation.execute(df.copy(), params)

    print(f"Input rows: {len(df)}")
    print(f"Output rows: {len(result)}")
    print(f"Removed rows: {len(df) - len(result)}")

    # Should only remove 1 row (the NaN)
    assert len(result) == 4, f"Expected 4 rows (removed only NaN), got {len(result)}"
    # Should keep rows 0, 2, 3, 4 (all non-NaN)
    assert 0 in result.index, "Should keep row 0 (valid address)"
    assert 2 in result.index, "Should keep row 2 (empty string)"
    assert 3 in result.index, "Should keep row 3 (whitespace)"
    assert 4 in result.index, "Should keep row 4 (valid address)"

    print("✅ PASSED: Standard mode only removes NaN, keeps empty strings and whitespace")


def test_enhanced_mode_removes_empty_and_na():
    """Test that enhanced mode removes NaN, empty strings, and N/A variants"""
    print("\n" + "="*80)
    print("TEST 2: Enhanced Mode - NaN + Empty + N/A")
    print("="*80)

    df = pd.DataFrame({
        'Address': [
            '123 Main St',     # Valid address
            None,              # NaN - should be removed
            '',                # Empty string - should be removed in enhanced mode
            '   ',             # Whitespace - should be removed in enhanced mode
            'N/A',             # N/A variant - should be removed in enhanced mode
            'na',              # N/A variant - should be removed in enhanced mode
            '456 Elm St'       # Valid address
        ]
    })

    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Address',
        'condition': 'is_blank',
        'enhanced_blank_detection': True,
        'smart_address_detection': False  # Disable for this test
    }

    result = operation.execute(df.copy(), params)

    print(f"Input rows: {len(df)}")
    print(f"Output rows: {len(result)}")
    print(f"Removed rows: {len(df) - len(result)}")

    # Should only keep 2 rows (the valid addresses)
    assert len(result) == 2, f"Expected 2 rows (only valid addresses), got {len(result)}"
    assert 0 in result.index, "Should keep row 0 (valid address)"
    assert 6 in result.index, "Should keep row 6 (valid address)"

    print("✅ PASSED: Enhanced mode removes NaN, empty strings, whitespace, and N/A")


def test_smart_address_detection_keeps_rows_with_any_address():
    """Test that smart address detection keeps rows with address in ANY related column"""
    print("\n" + "="*80)
    print("TEST 3: Smart Address Detection - Related Columns")
    print("="*80)

    df = pd.DataFrame({
        'Person Street': [
            '123 Main St',      # Has Person address
            None,               # No Person address, but has Company
            '456 Elm St',       # Has Person address
            None,               # No Person address, no Company - should be removed
        ],
        'Company Street Address': [
            '789 Oak Ave',      # Has both
            '999 Pine Rd',      # Has Company address
            None,               # No Company address
            None,               # No address at all - should be removed
        ]
    })

    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': False,
        'smart_address_detection': True  # Enable smart detection
    }

    result = operation.execute(df.copy(), params)

    print(f"Input rows: {len(df)}")
    print(f"Output rows: {len(result)}")
    print(f"Removed rows: {len(df) - len(result)}")
    print(f"\nKept rows:")
    for idx, row in result.iterrows():
        print(f"  Row {idx}: Person='{row['Person Street']}', Company='{row['Company Street Address']}'")

    # Should keep 3 rows (any row with address in Person OR Company)
    assert len(result) == 3, f"Expected 3 rows (has address in Person OR Company), got {len(result)}"
    assert 0 in result.index, "Should keep row 0 (has Person address)"
    assert 1 in result.index, "Should keep row 1 (has Company address)"
    assert 2 in result.index, "Should keep row 2 (has Person address)"
    assert 3 not in result.index, "Should remove row 3 (no address in either column)"

    print("✅ PASSED: Smart address detection keeps rows with address in ANY related column")


def test_smart_address_detection_disabled():
    """Test that disabling smart detection only checks the specified column"""
    print("\n" + "="*80)
    print("TEST 4: Smart Detection Disabled - Only Check Specified Column")
    print("="*80)

    df = pd.DataFrame({
        'Person Street': [
            '123 Main St',      # Has Person address
            None,               # No Person address (even though has Company)
            '456 Elm St',       # Has Person address
        ],
        'Company Street Address': [
            '789 Oak Ave',      # Has both
            '999 Pine Rd',      # Has Company address (but Person is blank)
            None,               # No Company address
        ]
    })

    operation = RemoveRowsIfOperation()
    params = {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': False,
        'smart_address_detection': False  # Disable smart detection
    }

    result = operation.execute(df.copy(), params)

    print(f"Input rows: {len(df)}")
    print(f"Output rows: {len(result)}")
    print(f"Removed rows: {len(df) - len(result)}")

    # Should keep 2 rows (only rows with Person Street data)
    assert len(result) == 2, f"Expected 2 rows (Person Street not blank), got {len(result)}"
    assert 0 in result.index, "Should keep row 0 (has Person address)"
    assert 2 in result.index, "Should keep row 2 (has Person address)"
    assert 1 not in result.index, "Should remove row 1 (Person Street is blank)"

    print("✅ PASSED: When disabled, smart detection only checks the specified column")


def test_actual_volunteer_directors_file():
    """Test with the actual Volunteer Directors file"""
    print("\n" + "="*80)
    print("TEST 5: Actual Volunteer Directors File - Smart Detection")
    print("="*80)

    df = pd.read_excel('Volunteer Directors 11.20.25(2).xlsx')

    print(f"Input DataFrame: {len(df)} rows")
    print(f"Person Street: {df['Person Street'].notna().sum()} non-blank, {df['Person Street'].isna().sum()} blank")
    print(f"Company Street Address: {df['Company Street Address'].notna().sum()} non-blank, {df['Company Street Address'].isna().sum()} blank")

    # Test WITH smart detection (default)
    operation = RemoveRowsIfOperation()
    params_smart = {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': False,
        'smart_address_detection': True  # Enable smart detection
    }

    result_smart = operation.execute(df.copy(), params_smart)

    print(f"\nWITH Smart Detection:")
    print(f"  Kept: {len(result_smart)} rows")
    print(f"  Removed: {len(df) - len(result_smart)} rows")

    # Should keep rows that have address in Person OR Company
    # Expected: ~2027 rows (all but those with neither)
    # Note: May be slightly more if some Company addresses are empty strings (not NaN)
    removed_count = len(df) - len(result_smart)
    print(f"  Rows removed: {removed_count}")
    print(f"  Expected to keep: rows with Person OR Company address")

    # Verify that removed rows have neither Person nor Company addresses (or both are truly blank)
    removed_indices = set(df.index) - set(result_smart.index)
    removed_df = df.loc[list(removed_indices)]
    print(f"\nRemoved rows analysis:")
    print(f"  Person Street NaN: {removed_df['Person Street'].isna().sum()}")
    print(f"  Company Street Address NaN: {removed_df['Company Street Address'].isna().sum()}")
    print(f"  Both NaN: {(removed_df['Person Street'].isna() & removed_df['Company Street Address'].isna()).sum()}")

    # The key test: removed rows should have BOTH columns blank
    both_blank = (removed_df['Person Street'].isna() & removed_df['Company Street Address'].isna())
    assert both_blank.all(), "All removed rows should have BOTH Person and Company addresses blank"

    # We should remove at least a few rows (those with neither address)
    assert removed_count >= 3, f"Expected to remove at least 3 rows, removed {removed_count}"
    assert removed_count <= 20, f"Expected to remove at most 20 rows, removed {removed_count}"

    # Test WITHOUT smart detection (old behavior)
    params_no_smart = {
        'column': 'Person Street',
        'condition': 'is_blank',
        'enhanced_blank_detection': False,
        'smart_address_detection': False  # Disable smart detection
    }

    result_no_smart = operation.execute(df.copy(), params_no_smart)

    print(f"\nWITHOUT Smart Detection (old behavior):")
    print(f"  Kept: {len(result_no_smart)} rows")
    print(f"  Removed: {len(df) - len(result_no_smart)} rows")

    # Should only keep rows with Person Street data
    # Expected: 782 rows
    assert len(result_no_smart) == 782, f"Expected 782 rows without smart detection, got {len(result_no_smart)}"

    print(f"\n✅ PASSED: Smart detection keeps {len(result_smart) - len(result_no_smart)} additional rows with Company addresses")


def test_executor_with_smart_detection():
    """Test that the executor correctly tracks removed rows with smart detection"""
    print("\n" + "="*80)
    print("TEST 6: Executor with Smart Detection - Removed Sheet Validation")
    print("="*80)

    df = pd.read_excel('Volunteer Directors 11.20.25(2).xlsx')

    executor = OperationExecutor()
    operations = [{
        'operation_id': 'data_remove_rows_if',
        'parameters': {
            'column': 'Person Street',
            'condition': 'is_blank',
            'enhanced_blank_detection': False,
            'smart_address_detection': True
        },
        'enabled': True
    }]

    result, removed = executor.execute_queue_with_tracking(df.copy(), operations)

    print(f"\nResults:")
    print(f"  Result sheet: {len(result)} rows")
    print(f"  Removed sheet: {len(removed)} rows")

    if len(removed) > 0:
        print(f"\nRemoved sheet analysis:")
        print(f"  Person Street - NaN: {removed['Person Street'].isna().sum()}, Non-NaN: {removed['Person Street'].notna().sum()}")
        print(f"  Company Street Address - NaN: {removed['Company Street Address'].isna().sum()}, Non-NaN: {removed['Company Street Address'].notna().sum()}")

        # Check for valid addresses in removed sheet
        valid_addresses_in_removed = removed[
            removed['Person Street'].notna() | removed['Company Street Address'].notna()
        ]

        if len(valid_addresses_in_removed) > 0:
            print(f"\n  ⚠️  WARNING: {len(valid_addresses_in_removed)} rows with valid addresses in Removed sheet!")
            assert False, "Should not have valid addresses in Removed sheet with smart detection enabled!"
        else:
            print(f"  ✅ No valid addresses in Removed sheet")

    # Expected: ~10 rows removed (those with neither Person nor Company address)
    assert len(removed) <= 15, f"Expected ~10 rows removed with smart detection, got {len(removed)}"

    print(f"\n✅ PASSED: Executor correctly tracks removed rows with smart detection")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("COMPREHENSIVE TESTS FOR REMOVE ROWS IF BUG FIX")
    print("="*80)

    try:
        test_standard_mode_only_removes_nan()
        test_enhanced_mode_removes_empty_and_na()
        test_smart_address_detection_keeps_rows_with_any_address()
        test_smart_address_detection_disabled()
        test_actual_volunteer_directors_file()
        test_executor_with_smart_detection()

        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        print("\nSUMMARY:")
        print("  ✅ Standard mode only removes NaN (not empty strings)")
        print("  ✅ Enhanced mode removes NaN + empty + N/A variants")
        print("  ✅ Smart address detection keeps rows with ANY address")
        print("  ✅ Smart detection can be disabled for strict column checking")
        print("  ✅ Actual file produces correct results")
        print("  ✅ Executor correctly tracks removed rows")
        print("\n" + "="*80)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
