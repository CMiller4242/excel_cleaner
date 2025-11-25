"""
Database Manager for MongoDB Operations
Handles all database connections and CRUD operations
"""
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError, ServerSelectionTimeoutError
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles all MongoDB database operations"""

    def __init__(self):
        self.client = None
        self.db = None
        self.users = None
        self.sessions = None
        self.audit_logs = None
        self._connect()

    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            logger.info("Attempting to connect to MongoDB...")

            self.client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )

            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")

            # Get database and collections
            self.db = self.client[Config.DATABASE_NAME]
            self.users = self.db[Config.USERS_COLLECTION]
            self.sessions = self.db[Config.SESSIONS_COLLECTION]
            self.audit_logs = self.db[Config.AUDIT_LOGS_COLLECTION]

            # Create indexes
            self._create_indexes()

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise Exception(
                "Cannot connect to authentication server.\n\n"
                "Possible causes:\n"
                "1. No internet connection\n"
                "2. MongoDB URI not configured in .env file\n"
                "3. MongoDB Atlas cluster is paused or unavailable\n\n"
                f"Error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Email should be unique in users collection
            self.users.create_index([("email", ASCENDING)], unique=True)

            # Session token should be unique
            self.sessions.create_index([("token", ASCENDING)], unique=True)

            # Auto-expire sessions after timeout
            self.sessions.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0
            )

            # Index for faster audit log queries
            self.audit_logs.create_index([("timestamp", ASCENDING)])
            self.audit_logs.create_index([("email", ASCENDING)])

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")

    # =====================================================================
    # USER OPERATIONS
    # =====================================================================

    def create_user(self, user_data):
        """
        Insert new user into database

        Args:
            user_data: dict with keys: email, password_hash, created_at, etc.

        Returns:
            inserted_id or None if email already exists
        """
        try:
            result = self.users.insert_one(user_data)
            logger.info(f"New user created: {user_data['email']}")
            self.log_audit_event('user_registered', user_data['email'])
            return result.inserted_id
        except DuplicateKeyError:
            logger.warning(f"Attempted to create duplicate user: {user_data['email']}")
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    def get_user_by_email(self, email):
        """Get user document by email"""
        try:
            return self.users.find_one({"email": email.lower()})
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None

    def update_user(self, email, update_data):
        """Update user document"""
        try:
            return self.users.update_one(
                {"email": email.lower()},
                {"$set": update_data}
            )
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None

    def increment_login_attempts(self, email):
        """Increment failed login attempts counter"""
        try:
            self.users.update_one(
                {"email": email.lower()},
                {
                    "$inc": {"login_attempts": 1},
                    "$set": {"last_failed_login": datetime.utcnow()}
                }
            )
            self.log_audit_event('login_failed', email)
        except Exception as e:
            logger.error(f"Error incrementing login attempts: {e}")

    def reset_login_attempts(self, email):
        """Reset failed login attempts counter"""
        try:
            self.users.update_one(
                {"email": email.lower()},
                {
                    "$set": {
                        "login_attempts": 0,
                        "last_failed_login": None
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error resetting login attempts: {e}")

    # =====================================================================
    # SESSION OPERATIONS
    # =====================================================================

    def create_session(self, session_data):
        """Create new session token"""
        try:
            result = self.sessions.insert_one(session_data)
            logger.info(f"Session created for: {session_data['email']}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None

    def get_session(self, token):
        """Get session by token"""
        try:
            return self.sessions.find_one({"token": token})
        except Exception as e:
            logger.error(f"Error fetching session: {e}")
            return None

    def delete_session(self, token):
        """Delete session (logout)"""
        try:
            result = self.sessions.delete_one({"token": token})
            logger.info(f"Session deleted: {token[:10]}...")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    def delete_all_user_sessions(self, email):
        """Delete all sessions for a user (logout from all devices)"""
        try:
            result = self.sessions.delete_many({"email": email.lower()})
            logger.info(f"Deleted {result.deleted_count} sessions for: {email}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting user sessions: {e}")
            return 0

    # =====================================================================
    # AUDIT LOGGING
    # =====================================================================

    def log_audit_event(self, event_type, email, metadata=None):
        """Log authentication event for audit trail"""
        try:
            audit_entry = {
                "event": event_type,
                "email": email.lower() if email else None,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            self.audit_logs.insert_one(audit_entry)
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")

    def get_audit_logs(self, email=None, event_type=None, limit=100):
        """Retrieve audit logs with optional filtering"""
        try:
            query = {}
            if email:
                query["email"] = email.lower()
            if event_type:
                query["event"] = event_type

            return list(self.audit_logs.find(query).sort("timestamp", -1).limit(limit))
        except Exception as e:
            logger.error(f"Error fetching audit logs: {e}")
            return []

    # =====================================================================
    # CONNECTION MANAGEMENT
    # =====================================================================

    def is_connected(self):
        """Check if database connection is active"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")

    def __del__(self):
        """Cleanup on object destruction"""
        self.close()
