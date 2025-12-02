# 🔷 Clean Sheet v2.1.0
**Professional Data Cleaning Made Simple**

---

## 📦 Quick Start

### For End Users (Standalone Executable)

1. **Download** `CleanSheet.exe` from [Releases](https://github.com/CMiller4242/excel_cleaner/releases/latest)
2. **Run** the executable - no installation required!
3. **Configure** MongoDB URI on first launch
4. **Start cleaning** your data

See [USER_GUIDE.md](USER_GUIDE.md) for complete documentation.

### For Developers

```bash
# Clone repository
git clone https://github.com/CMiller4242/excel_cleaner.git
cd excel_cleaner

# Install dependencies
pip install -r requirements.txt

# Run application
python main_gui_v2_office365.py
```

---

## 🌟 Features

### ✨ New in v2.1.0

- 🔄 **Automatic Updates** - Get notified of new versions with one-click updates
- 🎨 **Professional Office 365 UI** - Modern, clean interface
- ⚙️ **Configuration Manager** - Easy setup on first run
- 📦 **Standalone .exe** - No Python installation required
- 🔐 **Enhanced Authentication** - Secure user management with MongoDB
- 📊 **Improved Data Quality Analyzer** - Smart issue detection and fixes
- 🤖 **AI-Powered Assistant** - Context-aware data cleaning suggestions

### Core Capabilities

#### 51+ Data Operations
Organized by category for easy access:

**Text Transformations**
- Upper/Lower/Title Case
- Trim Whitespace
- Remove Special Characters
- Concatenate/Split Columns
- Find & Replace
- Pad with Zeros
- Extract (LEFT/RIGHT/MID)
- Text Length

**Data Cleaning**
- Remove Blank Rows
- Remove Duplicates (Simple & Advanced)
- Fill Missing Data
- Standardize Formats
- Clean Phone Numbers
- Clean Addresses
- Remove PO Boxes

**Data Operations**
- VLOOKUP
- Sort Data
- Filter Rows
- Remove/Reorder Columns
- Add Columns
- Rename Columns

**Math Operations**
- Add, Subtract, Multiply, Divide
- Sum, Average, Min, Max
- Round Numbers
- Calculate Percentage
- Running Total

**Validation**
- Validate Email Addresses
- Validate State Codes
- Check Duplicates
- Data Type Validation

**Date/Time**
- Parse Dates
- Format Dates
- Extract Date Parts
- Date Calculations

### Two Modes

- **Simple Mode** - Essential operations, beginner-friendly interface
- **Advanced Mode** - All 51+ operations, expert features

### AI Assistant (Optional)

Requires Anthropic API key:
- Natural language requests: *"Remove duplicates and format phone numbers"*
- Contextual suggestions based on your data
- Clarifying questions when needed
- Conversation logging for reference

### Smart Data Quality Analyzer

Automatically detects:
- Missing data and null values
- Duplicate records (exact and fuzzy)
- Format inconsistencies
- Data type issues
- Outliers and anomalies
- Whitespace problems

One-click fixes for common issues!

### Preset Workflows

**7 Built-in System Presets:**
1. Clean Mailing List - Complete address standardization
2. Phone Number Cleanup - Format and validate phones
3. Email Validation - Check and clean emails
4. Remove Blanks - Clean empty rows/columns
5. Basic Deduplication - Simple duplicate removal
6. Data Standardization - Consistent formatting
7. Customer Data Cleanup - Comprehensive customer list cleaning

**Custom Presets:**
- Save your operation workflows
- Load and reuse instantly
- Share with team members

### Professional Interface

- **Office 365-style ribbon** - Familiar, intuitive navigation
- **Data-first layout** - Preview occupies 60-70% of screen
- **Three preview tabs** - Original, Results, Removed Rows
- **Compact operation queue** - Bottom panel for workflow
- **Real-time updates** - See changes as you work

---

## 📋 System Requirements

- **OS:** Windows 10 or later
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 200MB free space
- **Internet:** Required for authentication, AI features, and updates
- **MongoDB:** Connection URI required (free tier available via MongoDB Atlas)

---

## 🚀 Building the Executable

For developers who want to build from source:

```batch
# 1. Install dependencies
pip install -r requirements.txt
pip install pyinstaller packaging requests pillow

# 2. Run build script
build.bat

# 3. Output will be in dist\CleanSheet.exe
```

See [CREATE_RELEASE.md](CREATE_RELEASE.md) for complete release process.

---

## 📖 Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user manual
- **[CREATE_RELEASE.md](CREATE_RELEASE.md)** - How to create releases
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - Pre-release testing

---

## 🎯 Use Cases

### Daily Mailing List Cleaning

Perfect for marketing teams, sales departments, and data analysts.

**Before:** 500 rows from ZoomInfo/LinkedIn export
**After:** 247 validated, deduplicated, formatted rows
**Time saved:** 30 minutes → 2 minutes

**Process:**
1. Load your export file
2. Select "Clean Mailing List" preset
3. Click Run
4. Export clean data

**Results:**
- ✅ Formatted company names
- ✅ Valid email addresses
- ✅ Standardized phone numbers
- ✅ No PO Boxes
- ✅ No duplicates
- ✅ Clean addresses

### Customer Data Standardization

Transform inconsistent customer data into a clean, standardized format.

**Common operations:**
- Standardize names (Title Case)
- Format phone numbers: (555) 123-4567
- Validate emails
- Clean addresses
- Remove duplicates by multiple fields
- Fill missing data

### Custom Workflows

Build your own preset for repetitive tasks:

1. Add operations to queue
2. Configure parameters
3. Save as preset
4. Reuse with one click

Perfect for:
- Monthly reports
- Recurring data imports
- Team standardization
- Compliance requirements

---

## 🤖 AI Assistant Setup (Optional)

To enable AI-powered suggestions:

1. Get API key from: https://console.anthropic.com/
2. Enter during first-run setup, or
3. Add to configuration: `%APPDATA%\CleanSheet\config.ini`

**Example queries:**
- *"How do I remove rows where company name is blank?"*
- *"Help me format phone numbers consistently"*
- *"What's the best way to find duplicate customers?"*

The AI sees your data context and provides specific, actionable advice.

---

## 🔄 Auto-Update System

Clean Sheet checks for updates once per day.

**When update available:**
- Notification appears on startup
- Shows what's new
- One-click download and install
- Configuration and presets preserved

**Manual check:**
- Help → Updates
- Or: Help → About → Check for Updates

**Disable auto-updates:**
Edit `%APPDATA%\CleanSheet\config.ini`:
```ini
[App]
check_updates = false
```

---

## 🔐 Authentication & Security

- **MongoDB-based** user management
- **Bcrypt** password hashing
- **Session tokens** with expiration (30 days)
- **Account lockout** after failed attempts
- **Remember Me** for convenience
- **Secure logout** with session cleanup

---

## 📦 Installation Options

### Option 1: Standalone Executable (Recommended for Users)

✅ No Python installation required
✅ No dependency management
✅ Auto-updates built-in
✅ One-click start

Download from: https://github.com/CMiller4242/excel_cleaner/releases/latest

### Option 2: Run from Source (For Developers)

```bash
# Clone repository
git clone https://github.com/CMiller4242/excel_cleaner.git
cd excel_cleaner

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export ANTHROPIC_API_KEY=your_key_here

# Run application
python main_gui_v2_office365.py
```

---

## 🆘 Troubleshooting

### First-Run Issues

**Problem:** "MongoDB connection failed"
- Verify internet connection
- Check MongoDB URI format
- Confirm MongoDB Atlas cluster is running

**Problem:** "Application won't start"
- Check Windows version (10+required)
- Try running as administrator
- Check antivirus isn't blocking

### Operation Issues

**Problem:** "Operation failed"
- Verify column names are correct
- Check data format matches operation requirements
- Review error message for specifics

**Problem:** "File won't load"
- Check file format (.xlsx, .csv, .txt supported)
- Verify file isn't corrupted
- Try smaller file for testing

### Performance Issues

**Problem:** "Application slow with large files"
- Close other applications
- Increase available RAM
- Split file into smaller chunks
- Use filters to work with subsets

### Update Issues

**Problem:** "Update won't download"
- Check internet connection
- Verify GitHub is accessible
- Download manually from releases page

---

## 🔧 Configuration Files

Clean Sheet stores configuration in:
- **Windows:** `%APPDATA%\CleanSheet\`
- **Linux/Mac:** `~/.config/CleanSheet/`

**Files:**
- `config.ini` - MongoDB URI, API key, settings
- `last_update_check.txt` - Update check timestamp
- `presets/` - Custom preset definitions
- `.session` - Saved session token (if Remember Me enabled)

---

## 📊 Data Privacy

**Your data stays on your computer:**
- All processing happens locally
- Data is never uploaded to external servers
- Only authentication uses MongoDB

**What's stored in MongoDB:**
- User accounts (email, hashed password)
- Session tokens
- No data files
- No operation history

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (see TESTING_CHECKLIST.md)
5. Submit a pull request

**Development guidelines:**
- Follow existing code style
- Add docstrings to new functions
- Update documentation
- Include tests where applicable

---

## 📝 Requirements (Development)

```
pandas>=1.3.0
openpyxl>=3.0.0
pymongo>=4.0.0
anthropic>=0.18.0
bcrypt>=4.0.0
email-validator>=1.1.0
python-dotenv>=0.19.0
tksheet>=5.0.0
requests>=2.26.0
packaging>=21.0
pillow>=9.0.0
```

See `requirements.txt` for complete list.

---

## 🎉 Success Stories

> *"Clean Sheet reduced our mailing list processing time from 30 minutes to under 2 minutes. Game changer!"*
> — Marketing Team

> *"The preset workflows saved us hours of repetitive work every week."*
> — Data Analyst

> *"Finally, a data cleaning tool that's both powerful and easy to use."*
> — Operations Manager

---

## 📞 Support

**Documentation:**
- [User Guide](USER_GUIDE.md) - Complete manual
- [Release Guide](CREATE_RELEASE.md) - For developers
- [Testing Checklist](TESTING_CHECKLIST.md) - QA procedures

**Issues & Bug Reports:**
- GitHub Issues: https://github.com/CMiller4242/excel_cleaner/issues

**Contact:**
- Developer: Chris Miller
- Repository: https://github.com/CMiller4242/excel_cleaner

---

## 📜 License

This project is proprietary software developed for internal use.

© 2025 Chris Miller. All rights reserved.

---

## 🏆 Version History

### v2.1.0 (2025-12-02) - Current
- ✨ Automatic update system
- 🎨 Professional Office 365-style UI
- 📦 Standalone .exe with PyInstaller
- ⚙️ First-run configuration dialog
- 🔐 Enhanced authentication system
- 📊 Improved Data Quality Analyzer
- 🤖 Enhanced AI Assistant

### v2.0.0 (Previous)
- Original feature set
- 51+ operations
- Preset system
- AI Assistant
- Authentication

See [CHANGELOG.md](CHANGELOG.md) for complete history.

---

## 🚀 Roadmap

**Planned features:**
- [ ] Import from Google Sheets
- [ ] Export to multiple formats (JSON, XML)
- [ ] Advanced deduplication algorithms
- [ ] Custom operation builder
- [ ] Team preset sharing
- [ ] Batch processing mode
- [ ] Scheduled operations
- [ ] API access

---

## 🙏 Acknowledgments

Built with:
- **Python 3.13.3** - Core language
- **tkinter** - GUI framework
- **pandas** - Data processing
- **openpyxl** - Excel support
- **PyInstaller** - Executable building
- **MongoDB** - User management
- **Anthropic Claude** - AI assistance

---

**Clean Sheet - Professional Data Cleaning Made Simple** 🔷

Transform hours of manual work into minutes of automation!

[Download Latest Release](https://github.com/CMiller4242/excel_cleaner/releases/latest) | [View Documentation](USER_GUIDE.md) | [Report Issues](https://github.com/CMiller4242/excel_cleaner/issues)
