#!/bin/bash

echo "================================================================================"
echo "CLEARING PYTHON CACHE AND VERIFYING METADATA"
echo "================================================================================"
echo ""

# Step 1: Kill any running GUI processes
echo "Step 1: Checking for running GUI processes..."
if pgrep -f "main_gui_v2.py" > /dev/null; then
    echo "  ⚠️  Found running GUI process(es). Killing them..."
    pkill -f "main_gui_v2.py"
    sleep 1
    echo "  ✓ Processes killed"
else
    echo "  ✓ No running GUI processes found"
fi
echo ""

# Step 2: Clear Python cache
echo "Step 2: Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "  ✓ Cache cleared"
echo ""

# Step 3: Verify metadata
echo "Step 3: Verifying operation metadata..."
python3 diagnose_metadata.py 2>&1 | grep -A 10 "multi_level_deduplication parameter"
echo ""

echo "================================================================================"
echo "CACHE CLEARED SUCCESSFULLY"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Start the GUI application: python3 main_gui_v2.py"
echo "  2. Navigate to: Operations → Data Matching → Remove Duplicate Rows"
echo "  3. Look for the checkbox:"
echo "     ☑ Use smart multi-level duplicate detection (Email → Name+Address → Name+Phone)"
echo ""
echo "The checkbox should now appear and be CHECKED by default."
echo "================================================================================"
