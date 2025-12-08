"""
Test script to reproduce the segment padding bug
"""
import pandas as pd
import re

def buggy_standardize_segment(value, length=2, blank_to_zero=False):
    """CURRENT BUGGY VERSION - reproduces the issue"""
    if pd.isna(value) or value == '':
        if blank_to_zero:
            return '0' * length
        else:
            return ""

    value_str = str(value).strip()

    # BUG IS HERE: Remove any non-digit characters
    # When value is 10.0 (float), str(10.0) = "10.0"
    # Then re.sub(r'\D', '', "10.0") = "100" (removes decimal, concatenates digits)
    digits = re.sub(r'\D', '', value_str)

    if not digits:
        if blank_to_zero:
            return '0' * length
        else:
            return ""

    padded = digits.zfill(length)

    return padded

def fixed_standardize_segment(value, length=2, blank_to_zero=False):
    """FIXED VERSION - handles floats correctly"""
    if pd.isna(value) or value == '':
        if blank_to_zero:
            return '0' * length
        else:
            return ""

    # Convert to string, handling floats properly
    # First convert numeric types to int to strip decimal portion
    if isinstance(value, (int, float)):
        # Convert float to int to remove decimal (10.0 → 10)
        value_str = str(int(value))
    else:
        value_str = str(value).strip()

    # Remove any non-digit characters
    digits = re.sub(r'\D', '', value_str)

    if not digits:
        if blank_to_zero:
            return '0' * length
        else:
            return ""

    # Pad with leading zeros to target length
    padded = digits.zfill(length)

    return padded


# Test cases that expose the bug
print("=" * 60)
print("BUGGY VERSION TEST RESULTS")
print("=" * 60)

test_cases = [
    (0, "Segment 0 (int)"),
    (0.0, "Segment 0.0 (float)"),
    (2, "Segment 2 (int)"),
    (2.0, "Segment 2.0 (float)"),
    (10, "Segment 10 (int)"),
    (10.0, "Segment 10.0 (float)"),
    ("10", "Segment '10' (string)"),
    ("2", "Segment '2' (string)"),
    (None, "Segment None (blank)"),
    ("", "Segment '' (empty string)"),
]

for value, description in test_cases:
    result = buggy_standardize_segment(value, length=2, blank_to_zero=False)
    print(f"{description:30} → '{result}'")

print("\n" + "=" * 60)
print("FIXED VERSION TEST RESULTS")
print("=" * 60)

for value, description in test_cases:
    result = fixed_standardize_segment(value, length=2, blank_to_zero=False)
    print(f"{description:30} → '{result}'")

print("\n" + "=" * 60)
print("COMPARISON - PROBLEMATIC CASES")
print("=" * 60)

problematic_cases = [
    (10.0, "Segment 10 should be '10' not '100'"),
    (2.0, "Segment 2 should be '02' not '20'"),
    (0.0, "Segment 0 should be '00' not '00' (works by accident)"),
]

for value, expected in problematic_cases:
    buggy = buggy_standardize_segment(value, length=2, blank_to_zero=False)
    fixed = fixed_standardize_segment(value, length=2, blank_to_zero=False)
    status = "✓" if fixed in expected else "✗"
    print(f"{expected}")
    print(f"  Buggy: '{buggy}' | Fixed: '{fixed}' {status}")

print("\n" + "=" * 60)
print("ROOT CAUSE ANALYSIS")
print("=" * 60)
print("When segment values are stored as floats (Excel default):")
print("  10.0 → str(10.0) = '10.0'")
print("  '10.0' → re.sub(r'\\D', '', '10.0') = '100' (removes '.', leaving '100')")
print("  '100' → '100'.zfill(2) = '100' ❌ WRONG!")
print()
print("Fix: Convert float to int first:")
print("  10.0 → int(10.0) = 10")
print("  10 → str(10) = '10'")
print("  '10' → re.sub(r'\\D', '', '10') = '10'")
print("  '10' → '10'.zfill(2) = '10' ✓ CORRECT!")
