# Universal Excel Tool V2.0 - Complete Edition

## 🚀 Quick Start

```bash
pip install pandas openpyxl anthropic
python main_gui_v2.py
```

## 🌟 Features

### Two Modes
- **Simple Mode** - For beginners (default)
- **Advanced Mode** - For Excel experts

### AI Assistant
- Natural language requests
- Conversational clarifications
- Automatic operation suggestions
- All conversations logged for training

### Accessible Design
- Large fonts (12-18pt)
- High contrast (black on white)
- Big buttons
- Simple language
- Perfect for older users

## 📊 Operations

**31 Total Operations (Enhanced!):**

### Basic (Simple Mode)
- Text: UPPER, lower, Title, Trim, Combine, Split
- Data: Remove Duplicates, Sort, VLOOKUP
- Cleaning: Remove Blanks, Fill Missing
- Math: Add, Multiply

### Advanced (Advanced Mode)
- Text: LEFT, RIGHT, MID, LEN, Phone Formatter, Remove Special Chars, Find/Replace, Prefix/Suffix
- Data: Remove Rows If (conditional deletion)
- Validation: Email Format, State Codes
- Math: SUM, AVERAGE, ROUND, PERCENTAGE
- Conditional: Flag If Contains
- Dates: Format Date

### ✨ Latest Enhancements
- **LEFT/RIGHT/MID** - Extract text portions (zip codes: "62701-1234" → "62701")
- **LEN** - Text length validation
- **Phone Formatter** - Auto-format to (XXX) XXX-XXXX from any input
- **Remove Rows If** - Delete rows by condition (blank, contains, equals, etc.)
- **State Validator** - Validate & convert state codes ("Illinois" → "IL")
- **Standard Mailing List Cleaner** preset - Complete automated workflow

## 🤖 AI Assistant

Enter your Claude API key to enable:
- Natural language: "Make company names uppercase"
- Clarifying questions when needed
- Operation suggestions
- Conversation logging to `logs/conversations/`

## 💾 Presets

Save your workflows:
1. Build operation queue
2. Click "Save as Preset"
3. Reuse anytime with "Load Preset"

## 📝 Requirements

```
pandas>=1.3.0
openpyxl>=3.0.0
anthropic>=0.18.0
```

## 🎯 Use Cases

### Standard Mailing List Cleaning (NEW!)
1. Load ZoomInfo/LinkedIn export
2. Load "Standard Mailing List Cleaner" preset
3. Click RUN
4. Get validated list: formatted names, valid emails, no PO Boxes, no duplicates
5. **Typical result: 188 rows → 82 rows (56% reduction, all validated)**

### Daily Mail List
1. Load file
2. Load "Mail List Cleaner" preset (or build your own)
3. Click RUN
4. Save results

### Custom Analysis
1. Switch to Advanced mode
2. Add operations (VLOOKUP, SUM, etc.)
3. Save as preset
4. Reuse forever

### AI-Assisted
1. Connect AI
2. Type: "Remove duplicates and flag PO Boxes"
3. AI clarifies and suggests operations
4. Run

## 🆘 Troubleshooting

**Import errors?**
```bash
pip install pandas openpyxl anthropic
```

**AI won't connect?**
- Check API key
- Verify internet connection

**Operations fail?**
- Load file first
- Check column names match

## 📞 Support

- Simple Mode: Perfect for daily tasks
- Advanced Mode: All Excel formulas
- AI Mode: Natural language automation

---

**Transform 30 minutes of manual work into 2 minutes of automation!** 🚀
