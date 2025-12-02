"""
Clean Sheet - Version Information
Professional Data Cleaning Made Simple
"""

__version__ = "2.1.0"
__version_info__ = (2, 1, 0)
__release_date__ = "2025-12-02"
__app_name__ = "Clean Sheet"
__app_tagline__ = "Professional Data Cleaning Made Simple"

# GitHub repository for auto-updates
GITHUB_REPO = "CMiller4242/excel_cleaner"

# Update check settings
CHECK_UPDATE_INTERVAL_HOURS = 24  # Once per day
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Application metadata
APP_DESCRIPTION = """
Clean Sheet is a professional data cleaning tool for Excel and CSV files.
Transform, clean, and standardize your data with 51+ built-in operations.
"""

AUTHOR = "Chris Miller"
COPYRIGHT = "© 2025 Chris Miller. All rights reserved."

# Feature flags
FEATURES = {
    'auto_update': True,
    'ai_assistant': True,
    'data_quality_analyzer': True,
    'preset_management': True,
}
