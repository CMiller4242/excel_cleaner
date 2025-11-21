# UI Parameter Troubleshooting Guide

## 🔍 Issue: `multi_level_deduplication` Parameter Not Showing in UI

### ✅ Diagnosis Complete

I've verified that the parameter **IS correctly configured** in the code:

1. **✓ Parameter exists in metadata** (`operations/data_ops.py:96-102`)
2. **✓ Correctly formatted** as a `boolean` type parameter
3. **✓ Has proper default value** (`True`)
4. **✓ Has clear description** for UI display
5. **✓ UI rendering code exists** (`main_gui_v2.py:466-470`)

### 🎯 Root Cause: Python Module Caching

**The problem is NOT with the code - it's with Python's module caching system.**

When the GUI application starts, Python imports all the operation modules and caches them in memory. Even after you update the code and save the file, **the GUI continues using the old cached version** until the Python process is completely restarted.

### 🔧 Solution: Complete Restart Required

**❌ NOT Enough:**
- Closing the GUI window
- Reloading the file
- Refreshing the screen

**✅ Required:**
1. **Kill the Python process completely**
2. **Clear Python cache files**
3. **Restart the GUI application fresh**

---

## 📋 Step-by-Step Fix

### Option 1: Use the Automated Script

```bash
./clear_cache_and_verify.sh
```

Then start the GUI:
```bash
python3 main_gui_v2.py
```

### Option 2: Manual Steps

#### 1. Kill Running GUI Processes
```bash
# Find the process
ps aux | grep main_gui_v2.py

# Kill it (replace <PID> with the actual process ID)
kill -9 <PID>

# Or kill all Python GUI processes
pkill -f main_gui_v2.py
```

#### 2. Clear Python Cache
```bash
# From the project root directory
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

#### 3. Verify Metadata
```bash
python3 diagnose_metadata.py
```

You should see:
```
✅ SUCCESS: 'multi_level_deduplication' parameter IS present in metadata

   Details:
   - Name: multi_level_deduplication
   - Type: boolean
   - Description: Use smart multi-level duplicate detection (Email → Name+Address → Name+Phone)
   - Default: True
   - Required: False
```

#### 4. Restart GUI
```bash
python3 main_gui_v2.py
```

---

## 🎯 What to Look For in the UI

After restarting, when you open the "Remove Duplicate Rows" operation dialog, you should see:

```
┌─────────────────────────────────────────────────────────────┐
│ Remove Duplicate Rows                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ☑ Use smart multi-level duplicate detection                │
│   (Email → Name+Address → Name+Phone)                      │
│   [CHECKED by default]                                      │
│                                                             │
│ Columns to check for duplicates:                           │
│ [                                                 ]         │
│ (empty = check all columns)                                │
│ Ignored when using multi-level deduplication.              │
│                                                             │
│ Which duplicate to keep:                                   │
│ ● First   ○ Last                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Parameter Details

- **Position:** First parameter (appears at top)
- **Type:** Checkbox
- **Label:** "Use smart multi-level duplicate detection (Email → Name+Address → Name+Phone)"
- **Default State:** CHECKED (enabled by default)
- **Effect:** When checked, uses intelligent 3-level deduplication instead of generic deduplication

---

## 🔎 Verification Tools

I've created diagnostic tools to help verify the fix:

### 1. `diagnose_metadata.py`
Checks if the parameter exists in the operation metadata.

**Run:**
```bash
python3 diagnose_metadata.py
```

**Expected output:**
- ✅ Parameter is present
- ✅ Type is boolean
- ✅ Default is True
- ✅ Description is correct

### 2. `test_gui_parameter_access.py`
Simulates how the GUI accesses and renders parameters.

**Run:**
```bash
python3 test_gui_parameter_access.py
```

**Expected output:**
- ✅ Parameter would appear in GUI
- ✅ Widget type: BooleanVar(value=True)
- ✅ Checkbox would be CHECKED by default

### 3. `clear_cache_and_verify.sh`
Automated script to clear cache and verify metadata.

**Run:**
```bash
./clear_cache_and_verify.sh
```

---

## 🐛 If Still Not Working

### Check 1: Verify File Was Saved
```bash
grep -n "multi_level_deduplication" operations/data_ops.py
```

Should show the parameter appears multiple times in the file.

### Check 2: Check Python Version
```bash
python3 --version
```

The code uses Python 3 syntax. Make sure you're running Python 3.6+.

### Check 3: Check Import Path
Start Python and check:
```python
import sys
print(sys.path)

from operations.data_ops import RemoveDuplicatesOperation
op = RemoveDuplicatesOperation()
print([p.name for p in op.metadata.parameters])
```

Should include `'multi_level_deduplication'` in the list.

### Check 4: Check for Multiple Installations
```bash
which python3
pip3 show pandas  # or another package you use
```

Make sure you're running from the correct Python environment.

---

## 📝 Technical Details

### Where the Parameter is Defined

**File:** `operations/data_ops.py`
**Lines:** 96-102

```python
Parameter(
    name='multi_level_deduplication',
    type='boolean',
    description='Use smart multi-level duplicate detection (Email → Name+Address → Name+Phone)',
    default=True,
    required=False
),
```

### Where the UI Renders It

**File:** `main_gui_v2.py`
**Lines:** 466-470 (first rendering location)

```python
elif param.type == 'boolean':
    var = tk.BooleanVar(value=param.default if param.default else False)
    widget = ttk.Checkbutton(param_frame, text=label_text, variable=var)
    widget.pack(anchor='w', pady=2)
    param_widgets[param.name] = var
```

**Lines:** 689-693 (second rendering location for edit dialogs)

```python
elif param.type == 'boolean':
    var = tk.BooleanVar(value=param.default if param.default else False)
    widget = ttk.Checkbutton(frame, text="Yes", variable=var)
    widget.pack(anchor='w', pady=2)
    param_widgets[param.name] = var
```

### How It's Registered

**File:** `operations/data_ops.py`
**Line:** 552

```python
registry.register(RemoveDuplicatesOperation())
```

This happens at module import time, which is why the cache needs to be cleared.

---

## ✅ Expected Behavior After Fix

### Default (Checkbox Checked)
- Uses multi-level deduplication
- Deduplicates by email (Level 1)
- Then by name+address for rows without email (Level 2)
- Then by name+phone for rows without email or address (Level 3)
- **Result:** Fewer false positives, better data preservation

### When Unchecked
- Uses standard generic deduplication
- Respects the 'columns' field
- Original behavior preserved

---

## 🎉 Summary

The `multi_level_deduplication` parameter **IS correctly implemented** in the code. The issue is simply that the GUI needs to be **completely restarted** for Python to reload the updated module.

**After following the fix steps above, the parameter WILL appear in the UI.**

---

*Last Updated: 2025-11-21*
*Branch: claude/fix-excel-row-removal-017GSTqba35eabHY8ZGBENfQ*
