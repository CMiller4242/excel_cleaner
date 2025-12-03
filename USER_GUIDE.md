# Clean Sheet - User Guide
**Professional Data Cleaning Made Simple**

Version 2.1.0

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [First-Time Setup](#first-time-setup)
3. [Login & Authentication](#login--authentication)
4. [Main Interface](#main-interface)
5. [Working with Data](#working-with-data)
6. [Multi-File Handling](#multi-file-handling) ⭐ NEW in 2.1.0
7. [Operations](#operations)
8. [Presets](#presets)
9. [Data Quality Analyzer](#data-quality-analyzer)
10. [AI Assistant](#ai-assistant)
11. [Auto-Updates](#auto-updates)
12. [Troubleshooting](#troubleshooting)
13. [FAQ](#faq)

---

## Getting Started

### Installation

Clean Sheet is a standalone application - no installation required!

1. **Download** `CleanSheet.exe` from the releases page
2. **Save** to any location on your computer
3. **Double-click** to run

**System Requirements:**
- Windows 10 or later
- 4GB RAM minimum (8GB recommended for large files)
- 200MB free disk space
- Internet connection (for MongoDB, AI features, and updates)

### First Launch

On first launch, you'll see a welcome screen prompting you to configure:

1. **MongoDB Connection URI** (required)
2. **Anthropic API Key** (optional - for AI features)

---

## First-Time Setup

### MongoDB Configuration

Clean Sheet requires a MongoDB database to store user accounts and session data.

**Where to get MongoDB URI:**

1. **MongoDB Atlas** (Free Cloud Option):
   - Sign up at: https://www.mongodb.com/cloud/atlas/register
   - Create a free cluster
   - Click "Connect" → "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your actual password

2. **Example URI format:**
   ```
   mongodb+srv://username:password@cluster0.mongodb.net/
   ```

### API Key Configuration (Optional)

For AI-powered data cleaning suggestions:

1. Get an API key from: https://console.anthropic.com/
2. Enter it in the setup dialog
3. Or leave blank to use without AI features

**Note:** You can add the API key later via configuration.

---

## Login & Authentication

### Creating an Account

1. Click the **"Register"** tab
2. Enter your email address
3. Create a secure password (min 8 characters)
4. Click **"Register"**

### Logging In

1. Enter your email and password
2. Check **"Remember Me"** to stay logged in
3. Click **"Login"**

### Security Features

- Passwords are hashed using bcrypt
- Sessions expire after 30 days of inactivity
- Account lockout after 5 failed login attempts (30 min cooldown)
- Remember Me option for convenient access

---

## Main Interface

Clean Sheet uses a modern Office 365-style interface with ribbon navigation.

### Interface Overview

```
┌──────────────────────────────────────────────────┐
│  🔷 Clean Sheet v2.1.0                    [User] │
├──────────────────────────────────────────────────┤
│  [Home] [Data] [Transform] [Review] [Help]       │
├──────────────────────────────────────────────────┤
│                                                   │
│              DATA PREVIEW AREA                    │
│           (60-70% of screen space)                │
│                                                   │
│     [Original] [Results] [Removed Rows]          │
│                                                   │
├──────────────────────────────────────────────────┤
│           OPERATION QUEUE (Bottom)                │
│  [Op 1] [Op 2] [Op 3] ...                        │
└──────────────────────────────────────────────────┘
```

### Ribbon Tabs

- **Home:** File operations, quick actions
- **Data:** Import, export, data quality
- **Transform:** Add operations, run queue
- **Review:** Preview, validate results
- **Help:** About, updates, AI assistant

### Mode Selector

Toggle between **Simple** and **Advanced** mode:

- **Simple:** Basic operations, streamlined interface
- **Advanced:** All operations, expert features

---

## Working with Data

### Importing Data

**Supported formats:**
- Excel (.xlsx, .xls)
- CSV (.csv)
- TXT (tab or comma delimited)

**To import:**
1. Click **File → Open** (or ribbon: Home → Open)
2. Select your file
3. Data appears in the preview area

**Large Files:**
- Files up to 1 million rows supported
- Performance depends on your computer's RAM
- Consider splitting very large files

### Viewing Data

**Three preview tabs:**

1. **Original:** Your source data (unchanged)
2. **Results:** Data after operations applied
3. **Removed Rows:** Rows removed by operations

**Navigation:**
- Scroll horizontally/vertically
- Sort columns by clicking headers
- Resize columns by dragging dividers

### Exporting Data

**To export:**
1. Click **File → Export** (or ribbon: Data → Export)
2. Choose format:
   - **Excel (.xlsx):** Multiple sheets (Original, Results, Removed)
   - **CSV (.csv):** Results only
   - **TXT (.txt):** Results only (tab-delimited)
3. Choose location and filename
4. Click **Save**

---

## Multi-File Handling

Clean Sheet 2.1.0 introduces comprehensive batch processing capabilities for handling multiple files at once.

### Processing Modes

Clean Sheet operates in two modes:

1. **Single File Mode** (default): Process one file at a time
2. **Batch Mode**: Process multiple files simultaneously

**To switch modes:**
- Use the **"Files"** dropdown in the top-right header
- Select **"single"** or **"batch"**

### Batch Processing

Process multiple files with the same operation queue.

**How it works:**

1. **Switch to Batch Mode**
   - Set **Files: batch** in header

2. **Load Multiple Files**
   - Go to **Data** tab in ribbon
   - Click **"Load Files"** in Batch group
   - Select multiple files (Ctrl+Click or Shift+Click)

3. **Add Operations**
   - Build your workflow queue normally
   - All operations will be applied to each file

4. **Process Batch**
   - Click **"Process Batch"** in Data tab
   - Confirm the operation
   - Progress is displayed for each file

5. **Export Results**
   - Choose export format (.xlsx, .csv, .txt)
   - Choose export method:
     - **ZIP Archive:** All files in one .zip
     - **Individual Files:** Separate folder with all files
   - Optionally include removed rows

**Example Use Cases:**
- Clean 50 contact lists with same operations
- Apply standard formatting to monthly reports
- Process weekly data exports consistently

### File Combining

Merge multiple files into a single output.

**How to combine files:**

1. **Load Files in Batch Mode**
   - Switch to Batch mode
   - Load multiple files

2. **Click "Combine Files"**
   - Opens combine options dialog

3. **Choose Column Strategy:**
   - **All columns:** Include all columns from all files (blanks where missing)
   - **Common columns only:** Only columns present in all files
   - **First file's columns:** Use first file as template

4. **Optional: Group by Column**
   - Select a column to group data by (e.g., "Department", "Keycode")
   - Creates separate files for each unique value
   - Example: Group by "Region" creates files for "Region_East", "Region_West", etc.

5. **Export Combined Data**
   - Single combined file, or
   - Multiple grouped files

**Column Mismatch Handling:**
- Clean Sheet automatically detects column differences
- Shows detailed mismatch report
- Offers strategies to resolve conflicts
- Proceeds with your chosen strategy

**Example Workflows:**

**Workflow 1: Combine Monthly Reports**
```
1. Load: January.xlsx, February.xlsx, March.xlsx
2. Strategy: All columns
3. Group by: (No grouping)
4. Result: Q1_Combined.xlsx
```

**Workflow 2: Merge and Split by Region**
```
1. Load: ContactList1.xlsx, ContactList2.xlsx, ContactList3.xlsx
2. Strategy: Common columns only
3. Group by: State
4. Result: State_CA.xlsx, State_NY.xlsx, State_TX.xlsx...
```

### Multi-File Export Options

After processing or combining files, you have flexible export options:

**Export Formats:**
- Excel (.xlsx)
- CSV (.csv)
- Text (.txt) - quoted, comma-delimited

**Delivery Options:**

1. **ZIP Archive**
   - All files packaged in one .zip
   - Easy to share via email
   - Preserves folder structure
   - Optionally includes removed rows files

2. **Individual Files to Folder**
   - Select destination folder
   - Each file saved separately
   - Naming: `OriginalName_processed.xlsx`
   - Removed rows: `OriginalName_removed.xlsx`

3. **Single Combined File**
   - All data merged into one file
   - Ideal for master lists
   - Preserves all column data

**Tips:**
- Use ZIP for sending results to colleagues
- Use folder export for archiving
- Use combined file for analysis

### Performance Considerations

**Recommended Limits:**
- **Batch Processing:** Up to 100 files at once
- **File Combining:** Up to 50 files with <10,000 rows each
- **Large Files:** Process individually or in smaller batches

**Best Practices:**
- Test your workflow on 2-3 files first
- Save presets for repeated batch operations
- Close other applications for large batches
- Monitor progress status bar

---

## Operations

Clean Sheet includes 51+ data operations organized by category.

### Adding Operations

**Method 1: Ribbon**
- Click ribbon button for specific operation
- Example: Transform → Upper Case

**Method 2: Add Operation Dialog**
1. Click **"Add Operation"** button
2. Browse or search operations
3. Configure parameters
4. Click **"Add to Queue"**

### Operation Categories

#### Text Transformations
- Upper Case, Lower Case, Title Case
- Trim Whitespace
- Remove Special Characters
- Concatenate Columns
- Split Column
- Replace Text
- Pad with Zeros

#### Data Cleaning
- Remove Blank Rows
- Remove Duplicates (simple & advanced)
- Fill Missing Data
- Standardize Formats
- Clean Phone Numbers
- Clean Addresses

#### Data Operations
- VLOOKUP
- Sort Data
- Filter Rows
- Remove Columns
- Reorder Columns
- Add Column
- Rename Column

#### Math Operations
- Add/Subtract/Multiply/Divide
- Sum, Average, Min, Max
- Round Numbers
- Calculate Percentage
- Running Total

#### Validation
- Validate Email
- Validate State Codes
- Check Duplicates
- Data Quality Check

#### Date/Time
- Parse Dates
- Format Dates
- Extract Date Parts
- Calculate Date Differences

### Configuring Operations

Each operation has specific parameters:

**Example: Upper Case**
- **Column:** Select which column to transform
- **Create new column:** Optional - preserve original

**Example: Remove Duplicates**
- **Columns:** Select which columns to check
- **Keep:** First or last occurrence
- **Case sensitive:** Yes/No

### Operation Queue

Operations execute in order from left to right.

**Queue Management:**
- **Reorder:** Drag operations to reorder
- **Edit:** Click operation card → "Edit"
- **Delete:** Click operation card → "Delete"
- **Enable/Disable:** Toggle operation on/off
- **Clear All:** Remove all operations

### Running Operations

**To execute:**
1. Build your operation queue
2. Click **"Run Operations"** (large green button)
3. Monitor progress bar
4. Review results in "Results" tab

**Execution:**
- Operations run sequentially
- Results of each operation feed into the next
- Original data is never modified
- You can undo by clearing the queue and re-running

---

## Presets

Presets are saved workflows - sequences of operations you use frequently.

### Using System Presets

Clean Sheet includes 7 built-in presets:

1. **Clean Mailing List:** Address standardization, deduplication
2. **Phone Number Cleanup:** Format and validate phone numbers
3. **Email Validation:** Check and clean email addresses
4. **Remove Blanks:** Remove empty rows and columns
5. **Basic Deduplication:** Simple duplicate removal
6. **Data Standardization:** Consistent formatting
7. **Customer Data Cleanup:** Comprehensive customer list cleaning

**To load a preset:**
1. Click **"Load Preset"** button
2. Select preset from list
3. Operations added to queue
4. Click **"Run Operations"**

### Creating Custom Presets

**To save your workflow:**
1. Build operation queue
2. Click **"Save Preset"** button
3. Enter preset name
4. Click **"Save"**

Your preset is saved for future use.

### Managing Presets

**Edit/Delete custom presets:**
1. Click **"Load Preset"**
2. Right-click your preset
3. Choose **"Rename"** or **"Delete"**

**Note:** System presets cannot be deleted or modified.

---

## Data Quality Analyzer

The Data Quality Analyzer automatically detects issues in your data and suggests fixes.

### Running Analysis

**To analyze data:**
1. Load your data file
2. Click **"Analyze Data Quality"** (ribbon: Review → Analyze)
3. Wait for analysis to complete
4. Review detected issues

### Issue Types Detected

- **Missing Data:** Empty cells, null values
- **Duplicates:** Exact and fuzzy duplicates
- **Format Issues:** Inconsistent date/phone/email formats
- **Data Type Issues:** Text in number columns, etc.
- **Outliers:** Unusual values that may be errors
- **Whitespace Issues:** Leading/trailing spaces

### Applying Fixes

**Quick Fix:**
1. Click **"Fix"** button on issue card
2. Recommended operations added to queue
3. Review and run operations

**Manual Review:**
1. Review suggested operations
2. Modify parameters if needed
3. Add additional operations
4. Run when ready

---

## AI Assistant

AI-powered help for data cleaning questions.

**Note:** Requires Anthropic API key

### Asking Questions

**Examples:**
- "How do I remove duplicates based on email?"
- "What operations should I use to clean phone numbers?"
- "Help me standardize customer addresses"

**To use:**
1. Click **AI Assistant** button (ribbon: Help → AI Help)
2. Type your question
3. Press **Enter** or click **Send**
4. Review AI response

### Context-Aware Suggestions

The AI Assistant sees:
- Your current data (columns, row count)
- Operations in your queue
- Data quality issues detected

This enables specific, actionable advice.

### Conversation History

- All conversations are logged
- Scroll up to review previous messages
- Click **"Clear Chat"** to start fresh

---

## Auto-Updates

Clean Sheet automatically checks for updates once per day.

### Update Notifications

When a new version is available:

1. Update notification appears on startup
2. Shows version number and what's new
3. Options:
   - **Update Now:** Download and install immediately
   - **Remind Me Tomorrow:** Check again tomorrow
   - **Skip This Version:** Don't notify about this version

### Manual Update Check

**To check manually:**
1. Go to ribbon: **Help → Updates**
2. Or click **Help → About → Check for Updates**
3. If update available, choose to install

### Update Process

1. Click **"Update Now"**
2. Update downloads (progress shown)
3. Confirm restart
4. Application restarts with new version

**Your data is safe:**
- Current work is not lost
- Configuration preserved
- Presets retained

### Disabling Auto-Updates

To disable automatic update checks:

1. Edit configuration file: `%APPDATA%\CleanSheet\config.ini`
2. Set: `check_updates = false`
3. You can still check manually via Help menu

---

## Troubleshooting

### Connection Issues

**Problem:** "MongoDB connection failed"

**Solutions:**
1. Check your internet connection
2. Verify MongoDB URI is correct
3. Confirm MongoDB cluster is running (if using Atlas)
4. Check firewall settings

**Problem:** "Authentication server unavailable"

**Solutions:**
1. Check internet connection
2. Try again in a few minutes
3. Contact your administrator

### Performance Issues

**Problem:** Application slow with large files

**Solutions:**
1. Close other applications
2. Increase available RAM
3. Split file into smaller chunks
4. Use filters to work with subsets

**Problem:** Operations take too long

**Solutions:**
1. Run fewer operations at once
2. Remove unnecessary operations
3. Simplify complex operations
4. Work with filtered data first

### Data Issues

**Problem:** Results not as expected

**Solutions:**
1. Check operation parameters
2. Review operation order (matters!)
3. Test with small sample first
4. Use preview tabs to debug

**Problem:** Data lost after operation

**Solutions:**
1. Check "Removed Rows" tab
2. Original data always preserved in "Original" tab
3. Clear queue and start over if needed

### Update Issues

**Problem:** Update check fails

**Solutions:**
1. Check internet connection
2. Verify GitHub is accessible
3. Try manual check: Help → Updates
4. Download directly from releases page

**Problem:** Update won't install

**Solutions:**
1. Close any running instances
2. Run as administrator
3. Check antivirus isn't blocking
4. Download new version manually

---

## FAQ

### General

**Q: Is Clean Sheet free?**
A: Yes, Clean Sheet is free to use. You may need paid services for MongoDB (free tier available) and AI features (optional).

**Q: Does Clean Sheet work offline?**
A: No, internet connection required for authentication, AI features, and updates. However, data processing happens locally.

**Q: Is my data secure?**
A: Yes. Your data is processed locally on your computer and is never uploaded to external servers (except MongoDB for authentication).

**Q: Can multiple people use Clean Sheet?**
A: Yes, each user creates their own account. Presets and configuration are user-specific.

### Technical

**Q: What Python version is required?**
A: For the .exe, no Python installation is required. For development: Python 3.13.3+

**Q: How big can my files be?**
A: Up to 1 million rows supported, depending on your computer's RAM. Larger files may require more memory.

**Q: Can I use without MongoDB?**
A: No, MongoDB is required for user authentication and session management.

**Q: Can I use without API key?**
A: Yes, the AI Assistant feature requires an API key, but all other features work without it.

### Operations

**Q: In what order do operations execute?**
A: Left to right (or top to bottom), in the order shown in the queue.

**Q: Can I undo operations?**
A: Clear the queue and reload your file, or export results and re-import as needed.

**Q: Why don't I see my custom operation?**
A: Custom operations must be added to the operations registry. Contact your developer.

**Q: Can I run the same operation twice?**
A: Yes, add the same operation to the queue multiple times with different parameters.

---

## Support

### Getting Help

**Within the application:**
- Click **Help → AI Assistant** for immediate help
- Click **Help → About** for version information

**External resources:**
- GitHub Repository: https://github.com/CMiller4242/excel_cleaner
- Issues/Bug Reports: https://github.com/CMiller4242/excel_cleaner/issues

**Internal support:**
- Contact: Chris Miller
- Email: [Your Email]
- Department: [Your Department]

### Reporting Bugs

When reporting issues, please include:

1. Clean Sheet version (Help → About)
2. Steps to reproduce the problem
3. Expected vs actual behavior
4. Screenshots if applicable
5. Error messages (if any)

### Feature Requests

We welcome feedback and feature requests!

Submit via:
- GitHub Issues: https://github.com/CMiller4242/excel_cleaner/issues
- Email: [Your Email]
- Internal: Company suggestion system

---

## Version History

**Version 2.1.0** (2025-12-02)
- ✨ Automatic update system
- 🎨 Professional Office 365-style UI
- 🤖 Enhanced AI Assistant
- 📊 Improved Data Quality Analyzer
- 🔧 Bug fixes and performance improvements

**Previous versions:**
- See CHANGELOG.md for complete history
- Or visit: https://github.com/CMiller4242/excel_cleaner/releases

---

## Credits

**Clean Sheet** - Professional Data Cleaning Made Simple

Developed by: Chris Miller

Built with:
- Python 3.13.3
- tkinter (UI)
- pandas (data processing)
- openpyxl (Excel support)
- PyInstaller (executable building)

---

**Thank you for using Clean Sheet!** 🎉

For the latest updates and documentation, visit:
https://github.com/CMiller4242/excel_cleaner
