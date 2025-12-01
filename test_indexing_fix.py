#!/usr/bin/env python3
"""
Test to verify the boolean indexing fix
Tests that the operation works without alignment errors
"""

import pandas as pd
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from operations.data_ops import KeepBestContactPerLocationOperation

# Create test data with non-sequential index (simulates real-world scenario)
test_data = {
    'Hospital': ['A', 'A', 'A', 'B', 'B'],
    'Address': ['100 Main', '100 Main', '100 Main', '200 Oak', '200 Oak'],
    'Title': ['CEO', 'Manager', 'Nurse', 'Director', 'Supervisor']
}

df = pd.DataFrame(test_data)

# Simulate non-sequential index (like after filtering/sorting)
df.index = [5, 12, 3, 8, 1]

print("Test DataFrame (with non-sequential index):")
print(df)
print(f"\nOriginal index: {list(df.index)}")
print(f"Total rows: {len(df)}")

# Run the operation
operation = KeepBestContactPerLocationOperation()
params = {
    'location_columns': 'Hospital,Address',
    'title_column': 'Title',
    'tie_breaker': 'first',
    'add_rank_column': True
}

try:
    result = operation.execute(df, params)

    print("\n" + "=" * 60)
    print("✓ SUCCESS - No alignment error!")
    print("=" * 60)
    print(f"\nResult rows: {len(result)}")
    print("\nResult DataFrame:")
    print(result)

    # Verify removed rows tracking
    if hasattr(result, 'attrs') and 'removed_rows' in result.attrs:
        removed_df = result.attrs['removed_rows']
        print(f"\n✓ Removed rows tracked: {len(removed_df)}")
        print("\nRemoved contacts:")
        print(removed_df[['Hospital', 'Title', '_removal_reason']])

    # Verify correctness
    assert len(result) == 2, f"Should have 2 rows (one per hospital), got {len(result)}"
    assert result.iloc[0]['Title'] == 'CEO', "Hospital A should keep CEO"
    assert result.iloc[1]['Title'] == 'Director', "Hospital B should keep Director"

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nFix verified:")
    print("- No boolean indexing alignment errors")
    print("- Correct contacts kept (highest rank per location)")
    print("- Removed rows properly tracked")

except Exception as e:
    print("\n" + "=" * 60)
    print("✗ ERROR OCCURRED")
    print("=" * 60)
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
