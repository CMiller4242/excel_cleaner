# Creating a GitHub Release for Clean Sheet

This guide explains how to create and publish a new release of Clean Sheet with automatic update support.

## Prerequisites

- ✅ CleanSheet.exe built and tested (see TESTING_CHECKLIST.md)
- ✅ Version updated in version.py
- ✅ Release notes prepared
- ✅ All tests passing
- ✅ Changes committed to git

## Release Process

### Step 1: Update Version Number

Edit `version.py`:

```python
__version__ = "2.1.0"  # Update this
__version_info__ = (2, 1, 0)  # Update this
__release_date__ = "2025-12-02"  # Update this
```

### Step 2: Commit Version Changes

```bash
git add version.py
git commit -m "Release v2.1.0"
git push origin claude/package-exe-auto-update-01Sks8hy8oFrsLUyCdpxwUTz
```

### Step 3: Build the Executable

```batch
build.bat
```

Verify that `dist\CleanSheet.exe` is created successfully.

### Step 4: Test the Build

Test the executable thoroughly:

1. Run CleanSheet.exe on a clean machine (no Python installed)
2. Test first-run configuration
3. Test authentication (login/register)
4. Test file operations (import/export)
5. Test all 51 operations
6. Test presets
7. Test AI Assistant
8. Test Data Quality Analyzer

See TESTING_CHECKLIST.md for complete testing instructions.

### Step 5: Create Git Tag

```bash
git tag v2.1.0
git push origin v2.1.0
```

**Important:** The tag must start with 'v' (e.g., v2.1.0, not 2.1.0)

### Step 6: Create GitHub Release

1. Go to: https://github.com/CMiller4242/excel_cleaner/releases/new

2. Fill in the release form:

   **Tag:** v2.1.0 (select the tag you just created)

   **Release title:** Clean Sheet v2.1.0

   **Description:** (See template below)

3. Upload `dist\CleanSheet.exe`:
   - Drag the file to the "Attach binaries by dropping them here or selecting them" area
   - Wait for upload to complete

4. Check "Set as the latest release"

5. Click "Publish release"

## Release Notes Template

```markdown
## Clean Sheet v2.1.0

### 🎉 What's New

- Automatic update system - get notified of new versions
- Professional Office 365-style interface
- Improved data quality analyzer
- Enhanced preset management
- [Add other new features]

### ✨ Improvements

- Faster operation execution
- Better error handling
- Improved UI responsiveness
- [Add other improvements]

### 🐛 Bug Fixes

- Fixed issue with [specific bug]
- Resolved problem with [specific problem]
- [Add other fixes]

### 📦 Installation

**First-time installation:**
1. Download `CleanSheet.exe` below
2. Run the executable (no installation required)
3. Configure MongoDB connection URI on first launch

**Upgrading from previous version:**
- Simply download and run the new CleanSheet.exe
- Or use the built-in "Check for Updates" feature (Help → Updates)
- Your configuration and presets will be preserved

### 🔧 Requirements

- Windows 10 or later
- 4GB RAM minimum (8GB recommended)
- MongoDB connection URI
- (Optional) Anthropic API key for AI features

### 📚 Documentation

- [User Guide](USER_GUIDE.md)
- [Testing Checklist](TESTING_CHECKLIST.md)
- [Repository](https://github.com/CMiller4242/excel_cleaner)

---

**Full Changelog:** https://github.com/CMiller4242/excel_cleaner/compare/v2.0.0...v2.1.0
```

## After Publishing

### Verify Auto-Update Works

1. Keep v2.0.0 (or previous version) installed
2. Change version.py temporarily to an older version
3. Build and run
4. Verify update notification appears
5. Test "Update Now" functionality
6. Verify executable downloads and installs correctly

### Notify Users

Internal distribution:
- Email announcement to team
- Post in company chat/Teams
- Update internal documentation

External distribution (if applicable):
- Social media announcement
- Update website
- Send newsletter

## Versioning Guidelines

Clean Sheet uses **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR (X.0.0):** Breaking changes, major UI overhaul
- **MINOR (2.X.0):** New features, non-breaking changes
- **PATCH (2.1.X):** Bug fixes, minor improvements

Examples:
- Bug fix: 2.1.0 → 2.1.1
- New operation: 2.1.0 → 2.2.0
- Complete rewrite: 2.1.0 → 3.0.0

## Rollback Process

If you need to rollback a release:

1. Mark the problematic release as "Pre-release" in GitHub
2. Re-publish the previous stable version as "Latest release"
3. Users will be notified to "update" back to the stable version
4. Fix the issue and create a new patch release

## Troubleshooting

### Release Not Detected by Auto-Updater

**Check:**
- Tag starts with 'v' (e.g., v2.1.0)
- CleanSheet.exe is attached to the release
- Release is marked as "Latest release" (not pre-release)
- GitHub API is accessible (not rate-limited)

**Test manually:**
```bash
curl https://api.github.com/repos/CMiller4242/excel_cleaner/releases/latest
```

### Users Not Getting Update Notification

**Reasons:**
- Last check was less than 24 hours ago
- User skipped this version
- Network connectivity issues
- User disabled auto-updates

**Solution:**
- Users can manually check: Help → Updates
- Or download directly from GitHub releases page

### Exe Size Too Large

**Current size:** ~50-150 MB (depends on dependencies)

**To reduce size:**
1. Review excluded packages in clean_sheet.spec
2. Remove unused dependencies from requirements.txt
3. Enable UPX compression (already enabled)
4. Consider splitting into multiple files (not recommended for auto-update)

## Security Considerations

### Code Signing (Optional but Recommended)

For production releases, consider code signing the .exe:

1. Obtain a code signing certificate
2. Use `signtool` to sign the executable:
   ```batch
   signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com CleanSheet.exe
   ```
3. Windows will trust the executable without warnings

### Checksum Verification

Include SHA-256 checksums in release notes:

```bash
# On Windows
certutil -hashfile dist\CleanSheet.exe SHA256

# On Linux/Mac
sha256sum dist/CleanSheet.exe
```

Add to release notes:
```
SHA-256: abc123...
```

Users can verify the download before running.

## Support

For issues with the release process:
- Check build logs in build output
- Review PyInstaller documentation
- Contact: [Your Email]
- Internal: Chris Miller / IT Department
