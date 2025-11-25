"""
Authentication Manager
Handles user authentication, password hashing, and session management
"""
import bcrypt
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.db_manager import DatabaseManager
from config import Config

try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATION_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATION_AVAILABLE = False
    # Fallback to simple regex validation
    pass

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages user authentication and session handling"""

    def __init__(self):
        try:
            self.db = DatabaseManager()
        except Exception as e:
            logger.error(f"Failed to initialize AuthManager: {e}")
            raise

    # ===================================================================
    # PASSWORD VALIDATION & HASHING
    # ===================================================================

    @staticmethod
    def validate_password_strength(password):
        """
        Validate password meets requirements

        Requirements:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 special character
        - At least 1 number

        Returns:
            (bool, str) - (is_valid, error_message)
        """
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters"

        if Config.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least 1 uppercase letter"

        if Config.REQUIRE_SPECIAL_CHAR and not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/]', password):
            return False, "Password must contain at least 1 special character"

        if Config.REQUIRE_NUMBER and not re.search(r'\d', password):
            return False, "Password must contain at least 1 number"

        return True, ""

    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt with salt"""
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise

    @staticmethod
    def verify_password(password, hashed_password):
        """Verify password against hashed version"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    @staticmethod
    def validate_email_format(email):
        """
        Validate email format

        Returns:
            (bool, str, str) - (is_valid, normalized_email, error_message)
        """
        if EMAIL_VALIDATION_AVAILABLE:
            try:
                email_info = validate_email(email, check_deliverability=False)
                return True, email_info.normalized, ""
            except EmailNotValidError as e:
                return False, email, f"Invalid email: {str(e)}"
        else:
            # Fallback to simple regex validation
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, email):
                return True, email.lower(), ""
            else:
                return False, email, "Invalid email format"

    # ===================================================================
    # USER REGISTRATION
    # ===================================================================

    def register_user(self, email, password):
        """
        Register new user

        Returns:
            (bool, str) - (success, message)
        """
        # Validate email
        is_valid, normalized_email, error_msg = self.validate_email_format(email)
        if not is_valid:
            return False, error_msg

        email = normalized_email

        # Check if email already exists
        if self.db.get_user_by_email(email):
            return False, "Email already registered. Please use a different email or login."

        # Validate password strength
        is_valid, error_msg = self.validate_password_strength(password)
        if not is_valid:
            return False, error_msg

        # Hash password
        try:
            password_hash = self.hash_password(password)
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            return False, "Registration failed. Please try again."

        # Create user document
        user_data = {
            "email": email.lower(),
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "login_attempts": 0,
            "last_failed_login": None,
            "account_status": "active"
        }

        # Insert into database
        user_id = self.db.create_user(user_data)

        if user_id:
            logger.info(f"User registered successfully: {email}")
            return True, "Registration successful! You can now log in."
        else:
            return False, "Registration failed. Email may already be in use."

    # ===================================================================
    # USER LOGIN
    # ===================================================================

    def login(self, email, password, remember_me=False):
        """
        Authenticate user and create session

        Returns:
            (bool, str, str) - (success, message, session_token)
        """
        # Normalize email
        email = email.lower().strip()

        # Get user from database
        user = self.db.get_user_by_email(email)

        if not user:
            logger.warning(f"Login attempt for non-existent email: {email}")
            self.db.log_audit_event('login_failed_invalid_email', email)
            return False, "Invalid email or password", None

        # Check if account is locked
        login_attempts = user.get('login_attempts', 0)
        if login_attempts >= Config.MAX_LOGIN_ATTEMPTS:
            last_failed = user.get('last_failed_login')
            if last_failed:
                lockout_until = last_failed + timedelta(minutes=Config.LOCKOUT_DURATION_MINUTES)
                if datetime.utcnow() < lockout_until:
                    minutes_left = int((lockout_until - datetime.utcnow()).total_seconds() / 60) + 1
                    msg = f"Account locked due to too many failed attempts.\nTry again in {minutes_left} minute(s)."
                    self.db.log_audit_event('login_failed_account_locked', email)
                    return False, msg, None
                else:
                    # Lockout period expired, reset attempts
                    self.db.reset_login_attempts(email)
                    login_attempts = 0

        # Verify password
        if not self.verify_password(password, user['password_hash']):
            # Increment failed attempts
            self.db.increment_login_attempts(email)
            new_attempts = login_attempts + 1
            remaining = Config.MAX_LOGIN_ATTEMPTS - new_attempts

            if remaining > 0:
                msg = f"Invalid email or password.\n{remaining} attempt(s) remaining before account lockout."
            else:
                msg = f"Invalid email or password.\nAccount locked for {Config.LOCKOUT_DURATION_MINUTES} minutes."

            logger.warning(f"Failed login attempt for: {email} (attempt {new_attempts}/{Config.MAX_LOGIN_ATTEMPTS})")
            return False, msg, None

        # Check account status
        if user.get('account_status') != 'active':
            self.db.log_audit_event('login_failed_inactive_account', email)
            return False, "Account is inactive. Please contact support.", None

        # Reset failed login attempts on successful login
        self.db.reset_login_attempts(email)

        # Update last login time
        self.db.update_user(email, {"last_login": datetime.utcnow()})

        # Create session token
        session_token = self.create_session(email, remember_me)

        if session_token:
            logger.info(f"User logged in successfully: {email}")
            self.db.log_audit_event('login_success', email, {"remember_me": remember_me})
            return True, "Login successful!", session_token
        else:
            return False, "Login failed. Please try again.", None

    # ===================================================================
    # SESSION MANAGEMENT
    # ===================================================================

    def create_session(self, email, remember_me=False):
        """Create session token for authenticated user"""
        try:
            token = secrets.token_urlsafe(32)

            # Set expiration
            if remember_me:
                expires_at = datetime.utcnow() + timedelta(hours=Config.SESSION_TIMEOUT_HOURS)
            else:
                expires_at = datetime.utcnow() + timedelta(hours=Config.SESSION_TIMEOUT_HOURS_NO_REMEMBER)

            session_data = {
                "token": token,
                "email": email.lower(),
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "remember_me": remember_me
            }

            self.db.create_session(session_data)

            # Save token locally if remember_me
            if remember_me:
                self.save_session_locally(token)

            return token
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None

    def verify_session(self, token):
        """
        Verify if session token is valid

        Returns:
            (bool, str) - (is_valid, email)
        """
        if not token:
            return False, None

        try:
            session = self.db.get_session(token)

            if not session:
                return False, None

            # Check if expired
            if session['expires_at'] < datetime.utcnow():
                self.db.delete_session(token)
                logger.info(f"Session expired for: {session['email']}")
                return False, None

            return True, session['email']
        except Exception as e:
            logger.error(f"Error verifying session: {e}")
            return False, None

    def logout(self, token):
        """Logout user and delete session"""
        try:
            session = self.db.get_session(token)
            if session:
                email = session.get('email')
                self.db.delete_session(token)
                self.delete_local_session()
                self.db.log_audit_event('logout', email)
                logger.info(f"User logged out: {email}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False

    def save_session_locally(self, token):
        """Save session token to local file for 'Remember Me'"""
        try:
            session_file = Config.get_app_data_dir() / '.session'
            with open(session_file, 'w') as f:
                f.write(token)
            logger.info("Session saved locally")
        except Exception as e:
            logger.error(f"Failed to save session locally: {e}")

    def load_local_session(self):
        """Load session token from local file"""
        try:
            session_file = Config.get_app_data_dir() / '.session'
            if session_file.exists():
                with open(session_file, 'r') as f:
                    token = f.read().strip()
                    logger.info("Session loaded from local file")
                    return token
        except Exception as e:
            logger.error(f"Failed to load local session: {e}")
        return None

    def delete_local_session(self):
        """Delete local session file"""
        try:
            session_file = Config.get_app_data_dir() / '.session'
            if session_file.exists():
                session_file.unlink()
                logger.info("Local session file deleted")
        except Exception as e:
            logger.error(f"Failed to delete local session: {e}")

    # ===================================================================
    # ACCOUNT MANAGEMENT
    # ===================================================================

    def change_password(self, email, old_password, new_password):
        """
        Change user password

        Returns:
            (bool, str) - (success, message)
        """
        # Verify old password
        user = self.db.get_user_by_email(email)
        if not user:
            return False, "User not found"

        if not self.verify_password(old_password, user['password_hash']):
            return False, "Current password is incorrect"

        # Validate new password
        is_valid, error_msg = self.validate_password_strength(new_password)
        if not is_valid:
            return False, error_msg

        # Hash new password
        try:
            new_password_hash = self.hash_password(new_password)
        except Exception as e:
            logger.error(f"Failed to hash new password: {e}")
            return False, "Password change failed. Please try again."

        # Update password
        self.db.update_user(email, {"password_hash": new_password_hash})
        self.db.log_audit_event('password_changed', email)

        logger.info(f"Password changed for: {email}")
        return True, "Password changed successfully"

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
