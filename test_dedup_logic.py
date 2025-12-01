#!/usr/bin/env python3
"""
Quick verification test for Keep Best Contact logic
Tests the core deduplication algorithm without pandas
"""

# Simulate the logic
test_data = [
    {'hospital': 'A', 'name': 'John', 'title': 'CEO', 'rank': 1},
    {'hospital': 'A', 'name': 'Jane', 'title': 'Manager', 'rank': 3},
    {'hospital': 'A', 'name': 'Bob', 'title': 'Nurse', 'rank': 5},
    {'hospital': 'B', 'name': 'Alice', 'title': 'Director', 'rank': 2},
    {'hospital': 'B', 'name': 'Charlie', 'title': 'Supervisor', 'rank': 4},
]

print("Original data (5 contacts):")
for row in test_data:
    print(f"  {row['hospital']} - {row['name']} ({row['title']}, rank {row['rank']})")

# Sort by hospital + rank
sorted_data = sorted(test_data, key=lambda x: (x['hospital'], x['rank']))

print("\nAfter sorting by hospital + rank:")
for row in sorted_data:
    print(f"  {row['hospital']} - {row['name']} ({row['title']}, rank {row['rank']})")

# Keep first per hospital (simulates drop_duplicates with keep='first')
seen_hospitals = set()
kept = []
removed = []

for row in sorted_data:
    if row['hospital'] not in seen_hospitals:
        seen_hospitals.add(row['hospital'])
        kept.append(row)
    else:
        removed.append(row)

print("\nKept contacts (best rank per hospital):")
for row in kept:
    print(f"  {row['hospital']} - {row['name']} ({row['title']}, rank {row['rank']})")

print("\nRemoved contacts:")
for row in removed:
    print(f"  {row['hospital']} - {row['name']} ({row['title']}, rank {row['rank']})")

print(f"\nResult: {len(kept)} kept, {len(removed)} removed")

# Verify
assert len(kept) == 2, f"Should keep 2 contacts (one per hospital), got {len(kept)}"
assert len(removed) == 3, f"Should remove 3 contacts, got {len(removed)}"
assert kept[0]['name'] == 'John' and kept[0]['rank'] == 1, "Hospital A should keep CEO (rank 1)"
assert kept[1]['name'] == 'Alice' and kept[1]['rank'] == 2, "Hospital B should keep Director (rank 2)"

print("\n✓ ALL CHECKS PASSED - Logic is correct!")
