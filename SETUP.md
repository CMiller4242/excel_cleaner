# Clean Sheet v2.1.0 - Setup Guide

## Quick Setup for End Users

### Option 1: Using .env File (Recommended for Development)

1. Create a `.env` file in the same directory as `CleanSheet.exe`:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ANTHROPIC_API_KEY=your_api_key_here
   ```

2. Replace the values:
   - `MONGODB_URI`: Your MongoDB connection string
   - `ANTHROPIC_API_KEY`: (Optional) Your Anthropic API key for AI features

3. Run `CleanSheet.exe`

### Option 2: Using config.ini (Recommended for Production)

1. Create the config directory:
   - **Windows:** `%APPDATA%\CleanSheet\`
   - **Linux/Mac:** `~/.config/CleanSheet/`

2. Create a `config.ini` file:
   ```ini
   [Database]
   mongodb_uri = mongodb+srv://username:password@cluster.mongodb.net/

   [API]
   anthropic_api_key = your_api_key_here

   [App]
   check_updates = true
   theme = office365
   first_run_complete = true
   ```

3. Run `CleanSheet.exe`

---

## Getting MongoDB Connection URI

### Free Option: MongoDB Atlas

1. Sign up at: https://www.mongodb.com/cloud/atlas/register
2. Create a **free M0 cluster** (512MB storage, perfect for Clean Sheet)
3. Click **"Connect"** → **"Connect your application"**
4. Copy the connection string
5. Replace `<password>` with your actual password

**Example:**
```
mongodb+srv://cleansheet:MyPassword123@cluster0.mongodb.net/
```

---

## Getting Anthropic API Key (Optional)

**For AI Assistant features only** - not required for core functionality.

1. Sign up at: https://console.anthropic.com/
2. Go to **API Keys** section
3. Create a new key
4. Copy and paste into configuration

**Note:** AI features require API credits (paid).

---

## First-Time Configuration Steps

### Step 1: MongoDB Setup (5 minutes)

1. Create free MongoDB Atlas account
2. Create cluster (select free M0 tier)
3. Create database user with password
4. Add your IP address to whitelist (or use 0.0.0.0/0 for any IP)
5. Get connection string
6. Add to .env or config.ini

### Step 2: Run Clean Sheet

1. Double-click `CleanSheet.exe`
2. You'll see the login/register screen
3. Create your account
4. Start using Clean Sheet!

---

## Troubleshooting

### "MongoDB connection failed"

**Cause:** Invalid MongoDB URI or connection issue

**Solutions:**
1. Verify MongoDB URI is correct
2. Check internet connection
3. Confirm MongoDB cluster is running
4. Check if IP is whitelisted in MongoDB Atlas

### "Configuration Required" error

**Cause:** No .env file or config.ini found

**Solutions:**
1. Create .env file in app directory, OR
2. Create config.ini in %APPDATA%\CleanSheet\
3. Verify MongoDB URI is present

### Application won't start

**Cause:** Missing configuration or dependencies

**Solutions:**
1. Check .env or config.ini exists
2. Verify MongoDB URI format
3. Check Windows Event Viewer for errors
4. Try running from command line to see error messages

---

## Configuration File Locations

### Windows
- Config: `C:\Users\YourName\AppData\Roaming\CleanSheet\config.ini`
- Presets: `C:\Users\YourName\AppData\Roaming\CleanSheet\presets\`
- Session: `C:\Users\YourName\AppData\Roaming\CleanSheet\.session`

### Linux
- Config: `~/.config/CleanSheet/config.ini`
- Presets: `~/.config/CleanSheet/presets/`
- Session: `~/.config/CleanSheet/.session`

---

## For IT Administrators

### Mass Deployment

1. **Pre-configure** a template config.ini with your MongoDB URI
2. **Distribute** CleanSheet.exe with pre-configured .env file
3. **Place** .env file in same directory as .exe
4. **Users** just run the executable

### Shared MongoDB Instance

All users can share the same MongoDB connection:
- Each user has their own account (email/password)
- Data is isolated per user
- Sessions are user-specific
- Presets can be shared by copying preset files

---

## v2.1.0 Known Issues

### First-Run Configuration Dialog

**Issue:** The graphical configuration dialog doesn't appear in the .exe build

**Workaround:** Manual configuration via .env or config.ini (this guide)

**Status:** Will be fixed in v2.1.1 with auto-update

**Why:** This is a PyInstaller/Tkinter compatibility issue being investigated

---

## Need Help?

- **Documentation:** See USER_GUIDE.md for full manual
- **Issues:** https://github.com/CMiller4242/excel_cleaner/issues
- **Contact:** Chris Miller

---

## Example .env File

Save this as `.env` in the same folder as CleanSheet.exe:

```env
# Clean Sheet Configuration
# Copy this file and update with your values

# MongoDB Connection (REQUIRED)
MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/

# Anthropic API Key (OPTIONAL - for AI features)
ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here...

# Note: Keep this file secure - it contains sensitive credentials
# Do not commit to version control
```

---

**Clean Sheet v2.1.0** - Professional Data Cleaning Made Simple

For updates and documentation: https://github.com/CMiller4242/excel_cleaner
