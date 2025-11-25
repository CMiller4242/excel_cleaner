"""
Configuration for MongoDB and Authentication
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# CRITICAL: Load .env file FIRST before anything else
load_dotenv()

# Setup logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Configuration for MongoDB and authentication"""

    # MongoDB Configuration
    # IMPORTANT: Never commit the actual connection string to git
    # Set MONGODB_URI in .env file or environment variable
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = 'excel_tool_users'
    USERS_COLLECTION = 'users'
    SESSIONS_COLLECTION = 'sessions'
    AUDIT_LOGS_COLLECTION = 'audit_logs'

    # Debug: Log what was loaded (only first 50 chars for security)
    if MONGODB_URI and MONGODB_URI != 'mongodb://localhost:27017/':
        logger.info(f"✓ MongoDB URI loaded from .env: {MONGODB_URI[:50]}...")
    else:
        logger.warning("⚠ MongoDB URI not found in .env, using localhost default")

    # Security Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'CHANGE_THIS_IN_PRODUCTION_USE_SECRETS_TOKEN_HEX')
    SESSION_TIMEOUT_HOURS = 24  # How long "Remember Me" lasts
    SESSION_TIMEOUT_HOURS_NO_REMEMBER = 2  # Without "Remember Me"
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    # Password Requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_SPECIAL_CHAR = True
    REQUIRE_NUMBER = True

    # Application Settings
    APP_NAME = 'ExcelToolV2'
    APP_VERSION = '2.1.0'

    @staticmethod
    def get_app_data_dir():
        """Get directory for storing local session data"""
        if os.name == 'nt':  # Windows
            base = os.getenv('APPDATA')
        else:  # Mac/Linux
            base = os.path.expanduser('~/.config')

        app_dir = Path(base) / 'ExcelToolV2'
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir