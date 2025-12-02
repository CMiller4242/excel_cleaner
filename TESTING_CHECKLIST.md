# Clean Sheet - Pre-Release Testing Checklist

Complete this checklist before publishing any release of Clean Sheet.

**Version:** v2.1.0
**Tested By:** _______________
**Date:** _______________
**Build:** dist\CleanSheet.exe

---

## 🔧 Build Testing

- [ ] **Icon displays correctly** in .exe file properties
- [ ] **File size reasonable** (<200 MB)
- [ ] **No console window** appears when running
- [ ] **Application starts** without Python installed
- [ ] **Application starts** on clean Windows machine
- [ ] **Runs from any directory** (not just build directory)
- [ ] **Multiple instances** can run simultaneously (different machines)

**Notes:**
```
File size: _____ MB
Start time: _____ seconds
Build date: _______________
```

---

## 🎯 First-Run Experience

- [ ] **Configuration dialog appears** on first launch
- [ ] **MongoDB URI field** accepts input
- [ ] **API key field** accepts input (optional)
- [ ] **Show/hide API key** toggle works
- [ ] **Test Connection** validates MongoDB URI
- [ ] **Invalid URI** shows appropriate error
- [ ] **Connection success** proceeds to login
- [ ] **Cannot exit** without valid MongoDB URI (or explicit exit)
- [ ] **Configuration saved** to %APPDATA%/CleanSheet/config.ini
- [ ] **Second launch** skips configuration (already configured)

**MongoDB URI tested:**
```
URI: _________________________________
Result: ✓ Success / ✗ Failed
```

---

## 🔐 Authentication

### Registration

- [ ] **Registration tab** visible and accessible
- [ ] **Email validation** works (requires valid format)
- [ ] **Password validation** works (min 8 characters)
- [ ] **Duplicate email** shows error
- [ ] **Successful registration** proceeds to login
- [ ] **New account** saved to MongoDB

### Login

- [ ] **Login tab** visible and accessible
- [ ] **Correct credentials** logs in successfully
- [ ] **Incorrect password** shows error
- [ ] **Non-existent email** shows error
- [ ] **Remember Me** checkbox works
- [ ] **Session persists** after restart (with Remember Me)
- [ ] **Account lockout** after 5 failed attempts
- [ ] **Lockout cooldown** (30 minutes) works
- [ ] **Session expiry** (30 days) works

### Logout

- [ ] **Logout button** visible in header
- [ ] **Logout confirmation** dialog appears
- [ ] **Logout successful** returns to login screen
- [ ] **Session deleted** from MongoDB
- [ ] **Remember Me cleared** on logout

**Test Account:**
```
Email: _________________________________
Password: _________________________________
```

---

## 📊 Core Functionality

### File Import

- [ ] **Open Excel** (.xlsx) works
- [ ] **Open CSV** (.csv) works
- [ ] **Open TXT** (tab-delimited) works
- [ ] **Large files** (50k+ rows) load successfully
- [ ] **Special characters** in data handled correctly
- [ ] **Unicode** characters display correctly
- [ ] **Empty columns** handled properly
- [ ] **Empty rows** handled properly
- [ ] **File path** displays correctly

**Test Files:**
```
File 1: _______________  Rows: _____  Cols: _____  Result: ✓/✗
File 2: _______________  Rows: _____  Cols: _____  Result: ✓/✗
File 3: _______________  Rows: _____  Cols: _____  Result: ✓/✗
```

### File Export

- [ ] **Export to Excel** (.xlsx) works
- [ ] **Export to CSV** (.csv) works
- [ ] **Export to TXT** (.txt) works
- [ ] **Multiple sheets** in Excel (Original, Results, Removed)
- [ ] **All data preserved** in export
- [ ] **Special characters** preserved
- [ ] **Large files** export successfully
- [ ] **Export location** can be chosen

### Data Preview

- [ ] **Original tab** shows source data
- [ ] **Results tab** shows processed data
- [ ] **Removed tab** shows removed rows
- [ ] **Horizontal scrolling** works
- [ ] **Vertical scrolling** works
- [ ] **Column headers** visible
- [ ] **Sort by column** works (click header)
- [ ] **Resize columns** works (drag divider)
- [ ] **Row numbers** displayed correctly

---

## ⚙️ Operations

### Adding Operations

- [ ] **Add Operation button** visible and works
- [ ] **Operation dialog** opens
- [ ] **Search operations** works
- [ ] **Browse by category** works
- [ ] **Operation details** display correctly
- [ ] **Parameter fields** accept input
- [ ] **Required parameters** validated
- [ ] **Add to Queue** button works

### Operation Queue

- [ ] **Operations display** in queue
- [ ] **Operation cards** show correct info
- [ ] **Reorder operations** (drag and drop) works
- [ ] **Edit operation** opens edit dialog
- [ ] **Delete operation** removes from queue
- [ ] **Enable/disable** operation toggle works
- [ ] **Clear all operations** works
- [ ] **Queue persists** during session
- [ ] **Queue visual** on bottom panel

### Execution

- [ ] **Run Operations button** visible and works
- [ ] **Progress bar** shows during execution
- [ ] **Progress percentage** updates
- [ ] **Operation order** respected (left to right)
- [ ] **Results** appear in Results tab
- [ ] **Removed rows** appear in Removed tab
- [ ] **Original data** unchanged
- [ ] **Large datasets** process without crashing
- [ ] **Error handling** for failed operations

### Test 10 Operations (Sample)

Test these operations individually:

- [ ] **1. Upper Case** - Converts text to uppercase
- [ ] **2. Remove Blanks** - Removes empty rows
- [ ] **3. Remove Duplicates** - Removes duplicate rows
- [ ] **4. Trim Whitespace** - Removes leading/trailing spaces
- [ ] **5. VLOOKUP** - Lookups values from another column
- [ ] **6. Sort Data** - Sorts by specified column
- [ ] **7. Filter Rows** - Filters based on condition
- [ ] **8. Add Column** - Adds new column
- [ ] **9. Format Dates** - Formats date columns
- [ ] **10. Standardize Phone** - Formats phone numbers

**Notes:**
```
Issues found: _______________________________________________
```

---

## 📋 Presets

### System Presets

- [ ] **Load Preset button** works
- [ ] **System presets** visible (7 total)
- [ ] **Preset descriptions** display correctly
- [ ] **Load system preset** adds operations to queue
- [ ] **System presets** cannot be deleted
- [ ] **System presets** cannot be renamed

**System Presets to Test:**
- [ ] Clean Mailing List
- [ ] Phone Number Cleanup
- [ ] Email Validation
- [ ] Remove Blanks
- [ ] Basic Deduplication
- [ ] Data Standardization
- [ ] Customer Data Cleanup

### Custom Presets

- [ ] **Save Preset button** works
- [ ] **Enter preset name** dialog appears
- [ ] **Preset saved** successfully
- [ ] **Load custom preset** works
- [ ] **Custom preset** in preset list
- [ ] **Right-click preset** shows context menu
- [ ] **Rename preset** works
- [ ] **Delete preset** works (with confirmation)
- [ ] **Presets persist** after restart
- [ ] **Preset location** %APPDATA%/CleanSheet/presets/

**Test Preset:**
```
Name: _________________________________
Operations: _____
Result: ✓ Success / ✗ Failed
```

---

## 🔍 Data Quality Analyzer

- [ ] **Analyze button** visible (ribbon: Review → Analyze)
- [ ] **Analysis runs** on current data
- [ ] **Progress indicator** shows
- [ ] **Issues detected** display in dialog
- [ ] **Issue cards** show:
  - Issue type
  - Description
  - Affected rows/columns
  - Severity
- [ ] **Fix button** adds suggested operations
- [ ] **Close button** closes analyzer
- [ ] **Multiple issues** detected correctly
- [ ] **No issues** message when data is clean

**Test Data Quality Issues:**
- [ ] Missing data detected
- [ ] Duplicates detected
- [ ] Format inconsistencies detected
- [ ] Whitespace issues detected

---

## 🤖 AI Assistant

**Note:** Requires Anthropic API key configured

- [ ] **AI Assistant button** visible (Help → AI Help)
- [ ] **Chat window** opens
- [ ] **Text input** field accepts input
- [ ] **Send button** works
- [ ] **Enter key** sends message
- [ ] **AI responds** to questions
- [ ] **Context awareness** (mentions current data)
- [ ] **Conversation history** preserved
- [ ] **Clear Chat button** works
- [ ] **Chat scrolls** with conversation

**Without API Key:**
- [ ] **Appropriate message** shown when no API key
- [ ] **Link to configure** API key provided

**Test Questions:**
```
Q1: How do I remove duplicates?
Response: _______________________________________________

Q2: Help me clean phone numbers
Response: _______________________________________________
```

---

## 🔄 Auto-Update System

### Automatic Check (24-hour interval)

- [ ] **Update check** runs on startup (after 24 hours)
- [ ] **Last check time** recorded
- [ ] **No notification** if up-to-date
- [ ] **No notification** if checked < 24 hours ago

### Update Notification

**To test:** Create fake newer version in GitHub or temporarily modify version.py

- [ ] **Update notification** appears
- [ ] **Shows new version** number
- [ ] **Shows release notes** in scrollable area
- [ ] **Shows download size**
- [ ] **Three buttons** present:
  - Update Now
  - Remind Me Tomorrow
  - Skip This Version

### Update Now

- [ ] **Download starts** when clicked
- [ ] **Progress dialog** appears
- [ ] **Progress bar** updates (0-100%)
- [ ] **Download size** shown (MB)
- [ ] **Download completes** successfully
- [ ] **Restart prompt** appears
- [ ] **Application restarts** after confirmation
- [ ] **New version** runs successfully
- [ ] **Configuration preserved**
- [ ] **Presets preserved**

### Remind Me Tomorrow

- [ ] **Dialog closes** when clicked
- [ ] **Last check** time reset
- [ ] **Notification appears** on next startup (after 24h)

### Skip This Version

- [ ] **Dialog closes** when clicked
- [ ] **Version recorded** as skipped
- [ ] **No notification** for this version again
- [ ] **Notification appears** for newer versions

### Manual Check

- [ ] **Help → Updates** menu item works
- [ ] **Check runs** immediately (ignores 24h limit)
- [ ] **"Up to date" message** if no updates
- [ ] **Update notification** if updates available

**Testing Notes:**
```
Fake version tested: _______________
Download size: _____ MB
Download time: _____ seconds
Result: ✓ Success / ✗ Failed
```

---

## 📱 User Interface

### Ribbon

- [ ] **All tabs** visible (Home, Data, Transform, Review, Help)
- [ ] **Tab switching** works
- [ ] **Ribbon buttons** all clickable
- [ ] **Button icons** display correctly
- [ ] **Button tooltips** appear on hover
- [ ] **Ribbon groups** properly organized

### Header

- [ ] **App name** and **version** visible
- [ ] **User email** displayed (if logged in)
- [ ] **Mode selector** (Simple/Advanced) works
- [ ] **Logout button** visible and works

### Status Bar

- [ ] **Status messages** display
- [ ] **Row/column count** accurate
- [ ] **Operation status** updates

### Themes

- [ ] **Office 365 theme** applied correctly
- [ ] **Colors** consistent throughout
- [ ] **Fonts** render clearly
- [ ] **Spacing** appropriate
- [ ] **High DPI** displays correctly (if applicable)

---

## 🐛 Edge Cases

### Error Handling

- [ ] **Network loss** during MongoDB operation handled
- [ ] **Invalid file** format shows error
- [ ] **Corrupted file** shows error
- [ ] **Missing columns** in operation handled
- [ ] **Invalid parameters** rejected with message
- [ ] **Out of memory** handled gracefully (if possible)

### Large Data

- [ ] **100k+ rows** process successfully
- [ ] **50+ columns** display correctly
- [ ] **Very long text** (1000+ chars) handled
- [ ] **Special characters** in all positions

### Concurrent Operations

- [ ] **Multiple files** can be opened in sequence
- [ ] **Switch files** mid-operation works
- [ ] **Queue persists** when switching files

### Resource Management

- [ ] **Memory usage** reasonable (<2GB for normal use)
- [ ] **CPU usage** normal (spikes during operations ok)
- [ ] **No memory leaks** (run for extended period)
- [ ] **Temp files** cleaned up

---

## 🎮 User Experience

### Performance

- [ ] **Startup time** < 30 seconds
- [ ] **File load** < 10 seconds (100k rows)
- [ ] **Operation execution** reasonable time
- [ ] **UI responsive** during operations
- [ ] **No freezing** or hanging

### Usability

- [ ] **Intuitive navigation**
- [ ] **Clear labels** and descriptions
- [ ] **Helpful error messages**
- [ ] **Consistent behavior**
- [ ] **Keyboard shortcuts** work (if any)

### Accessibility

- [ ] **Readable fonts** (size and contrast)
- [ ] **Clear visual hierarchy**
- [ ] **Dialogs centered** on screen
- [ ] **Tab order** logical

---

## 🌐 Clean Test Environment

**Critical:** Test on machine WITHOUT:

- [ ] **Python** installed
- [ ] **Previous version** of Clean Sheet
- [ ] **Development dependencies**
- [ ] **MongoDB** installed locally
- [ ] **IDE or development tools**

**Test Machine Specifications:**
```
OS: Windows _____ (10/11)
RAM: _____ GB
Processor: _________________________________
.NET installed: Yes / No
```

---

## ✅ Final Checks

- [ ] **All critical features** tested and working
- [ ] **No unhandled errors** during testing
- [ ] **All documented features** match actual behavior
- [ ] **Performance acceptable** for target use case
- [ ] **User guide** accurate
- [ ] **Version number** correct in:
  - version.py
  - About dialog
  - Window title
  - Login screen

---

## 📝 Sign-Off

**Tester:** _______________________________________________

**Date:** _______________________________________________

**Overall Result:** ✓ Pass / ✗ Fail / ⚠️ Pass with issues

**Critical Issues Found:**
```
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

**Minor Issues Found:**
```
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

**Recommendations:**
```
_______________________________________________
_______________________________________________
_______________________________________________
```

**Approved for Release:** ☐ Yes  ☐ No  ☐ With reservations

---

## 📋 Additional Notes

```
Use this space for any additional observations,
concerns, or recommendations:








```

---

**END OF TESTING CHECKLIST**

Once all items are checked and approved, proceed with release per CREATE_RELEASE.md
