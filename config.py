"""
Configuration for MongoDB and Authentication
"""
import os
from pathlib import Path

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

    @staticmethod
    def load_env():
        """Load environment variables from .env file if it exists"""
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                # dotenv not installed, skip
                pass

# Load .env on module import
Config.load_env()
