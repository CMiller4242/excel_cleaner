# MongoDB Authentication System - Setup Guide

## Overview

The Excel Tool V2 now includes a secure authentication system with MongoDB backend. Users must log in before accessing the application.

## Features

✅ **Secure Password Hashing** - Passwords hashed with bcrypt (12 rounds)
✅ **Email Validation** - Valid email format required
✅ **Password Requirements** - 8+ chars, 1 uppercase, 1 number, 1 special char
✅ **Remember Me** - Session persists for 24 hours
✅ **Account Lockout** - 5 failed attempts = 15-minute lockout
✅ **Session Management** - Auto-logout after timeout
✅ **Audit Logging** - All auth events logged to MongoDB
✅ **Auto-Login** - Remembers session between app restarts

---

## Prerequisites

1. **MongoDB Atlas Account** (free tier works)
2. **Python 3.8+**
3. **Internet connection** (for MongoDB authentication)

---

## Step 1: Set Up MongoDB Atlas

### 1.1 Create MongoDB Account

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Click "Try Free" and create an account
3. Create a free M0 cluster (takes ~5 minutes to provision)

### 1.2 Configure Network Access

1. In Atlas dashboard, go to **Network Access** (left sidebar)
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
4. Click **"Confirm"**

⚠️ **Security Note**: For production, restrict to specific IPs only.

### 1.3 Create Database User

1. Go to **Database Access** (left sidebar)
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Set username and password (e.g., `excelToolAdmin` / `SecurePass123!`)
5. Set privileges to **"Read and write to any database"**
6. Click **"Add User"**

### 1.4 Get Connection String

1. Go to **Database** → **Connect** → **Drivers**
2. Select **"Python"** and version **"3.11 or later"**
3. Copy the connection string, it looks like:
   ```
   mongodb+srv://excelToolAdmin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. **Replace `<password>` with your actual database password!**

---

## Step 2: Configure Application

### 2.1 Create .env File

1. Navigate to project root: `/home/user/excel_cleaner/`
2. Copy the example file:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` in a text editor
4. Replace placeholders with your actual values:

```bash
# MongoDB Atlas Connection String
MONGODB_URI=mongodb+srv://excelToolAdmin:YourActualPassword@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority

# Secret Key (generate with command below)
SECRET_KEY=your_generated_64_character_secret_key_here
```

### 2.2 Generate Secret Key

Run this command to generate a secure random key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as your `SECRET_KEY` in `.env`.

### 2.3 Verify .env is Ignored by Git

Check that `.env` is listed in `.gitignore`:
```bash
grep ".env" .gitignore
```

Output should show `.env` is ignored. ✅

---

## Step 3: Install Dependencies

Install authentication packages:
```bash
pip install pymongo[srv]==4.6.1 bcrypt==4.1.2 email-validator==2.1.0 python-dotenv==1.0.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

---

## Step 4: Test Authentication (Standalone)

Test the login window independently:

```bash
python auth/login_window.py
```

### What to Test:

1. **Register Tab**:
   - Try weak password (should reject)
   - Try invalid email (should reject)
   - Register with valid credentials (should succeed)

2. **Login Tab**:
   - Try wrong password (should fail)
   - Try correct credentials (should succeed)
   - Check "Remember me" and close/reopen (should auto-login)

3. **Account Lockout**:
   - Try logging in with wrong password 5+ times
   - Should see "Account locked for 15 minutes"

---

## Step 5: Integrate with Main Application

### Option A: Basic Integration

Modify your main entry point (e.g., `main_gui_v2_office365.py`):

```python
from auth.login_window import LoginWindow
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def start_application():
    """Start application with authentication"""

    def on_login_success(token, email):
        """Called when user successfully logs in"""
        print(f"✅ User authenticated: {email}")
        print(f"Session token: {token[:20]}...")

        # Start your main application here
        # Pass email to show in UI if desired
        launch_main_app(user_email=email)

    # Show login window
    login_window = LoginWindow(on_success_callback=on_login_success)
    token, email = login_window.run()

    if not token:
        print("❌ Authentication failed or cancelled")
        return

def launch_main_app(user_email=None):
    """Launch the main Excel Tool application"""
    # Your existing main app code here
    print(f"Launching app for user: {user_email}")
    # ... rest of your app initialization

if __name__ == "__main__":
    start_application()
```

### Option B: Class-Based Integration

```python
from auth.login_window import LoginWindow
from auth.auth_manager import AuthManager
import logging

logging.basicConfig(level=logging.INFO)

class ExcelToolApp:
    def __init__(self):
        self.session_token = None
        self.user_email = None
        self.auth_manager = None

    def start(self):
        """Start application with authentication"""
        # Show login window
        login_window = LoginWindow(on_success_callback=self.on_login_success)
        token, email = login_window.run()

        # If login successful, start main app
        if token and email:
            self.start_main_app()

    def on_login_success(self, token, email):
        """Called when user successfully logs in"""
        self.session_token = token
        self.user_email = email
        self.auth_manager = AuthManager()
        logging.info(f"User authenticated: {email}")

    def start_main_app(self):
        """Start the main Excel Tool UI"""
        # Your existing main app code
        # You can display self.user_email in the UI
        pass

    def on_app_close(self):
        """Handle application closing"""
        # Optional: clean up
        if self.auth_manager:
            self.auth_manager.close()

if __name__ == "__main__":
    app = ExcelToolApp()
    app.start()
```

---

## Testing Checklist

### Registration Tests

- [ ] Register with valid email and strong password → ✅ Success
- [ ] Register with weak password (< 8 chars) → ❌ Rejected
- [ ] Register with no uppercase letter → ❌ Rejected
- [ ] Register with no special character → ❌ Rejected
- [ ] Register with no number → ❌ Rejected
- [ ] Register with invalid email format → ❌ Rejected
- [ ] Register with existing email → ❌ "Email already registered"

### Login Tests

- [ ] Login with correct credentials → ✅ Success
- [ ] Login with wrong password → ❌ Failed (attempts counter increments)
- [ ] Login with non-existent email → ❌ "Invalid email or password"
- [ ] Login after 5 failed attempts → ❌ "Account locked for 15 minutes"
- [ ] Login after lockout expires → ✅ Success (attempts reset)

### Session Tests

- [ ] Check "Remember me" → Session persists after app restart
- [ ] Uncheck "Remember me" → Session expires after 2 hours
- [ ] Close app and reopen → Auto-login with saved session
- [ ] Wait for session to expire → Must log in again

### Security Tests

- [ ] Check `.env` file is in `.gitignore` → ✅ Not committed
- [ ] Verify passwords are hashed in MongoDB → ✅ Bcrypt hash visible
- [ ] Check session tokens are random → ✅ Different each time
- [ ] Test account lockout → ✅ Works after 5 failures

---

## MongoDB Collections

The system creates three collections automatically:

### 1. `users`
```javascript
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "password_hash": "$2b$12$...",  // Bcrypt hash
  "created_at": ISODate("2025-01-15T10:30:00Z"),
  "last_login": ISODate("2025-01-20T14:22:00Z"),
  "login_attempts": 0,
  "last_failed_login": null,
  "account_status": "active"
}
```

### 2. `sessions`
```javascript
{
  "_id": ObjectId("..."),
  "token": "secure_random_token_32_bytes",
  "email": "user@example.com",
  "created_at": ISODate("2025-01-20T14:22:00Z"),
  "expires_at": ISODate("2025-01-21T14:22:00Z"),
  "remember_me": true
}
```

### 3. `audit_logs`
```javascript
{
  "_id": ObjectId("..."),
  "event": "login_success",
  "email": "user@example.com",
  "timestamp": ISODate("2025-01-20T14:22:00Z"),
  "metadata": {"remember_me": true}
}
```

---

## Troubleshooting

### "Cannot connect to authentication server"

**Causes:**
1. No internet connection
2. MongoDB URI not set in `.env`
3. MongoDB cluster paused/unavailable
4. Firewall blocking MongoDB

**Solutions:**
1. Check internet connection
2. Verify `.env` file exists with correct `MONGODB_URI`
3. Check MongoDB Atlas dashboard (cluster should be running)
4. Try connection string in MongoDB Compass first

### "Email already registered"

**Solution:** Use a different email or use the existing account to log in.

### "Account locked"

**Solution:** Wait 15 minutes, or manually reset in MongoDB:
```javascript
db.users.updateOne(
  {email: "user@example.com"},
  {$set: {login_attempts: 0, last_failed_login: null}}
)
```

### Session not persisting

**Solution:**
1. Check that "Remember me" checkbox is checked
2. Verify session file is being created: `~/.config/ExcelToolV2/.session` (Linux/Mac) or `%APPDATA%\ExcelToolV2\.session` (Windows)

### ModuleNotFoundError: No module named 'pymongo'

**Solution:**
```bash
pip install -r requirements.txt
```

---

## Security Best Practices

### For Development:

✅ Use `.env` file (already in `.gitignore`)
✅ Use strong SECRET_KEY (64+ characters)
✅ Test with development MongoDB cluster

### For Production:

✅ Use environment variables (not `.env` file)
✅ Restrict MongoDB IP whitelist to specific IPs
✅ Use MongoDB Atlas M10+ cluster for production
✅ Enable MongoDB encryption at rest
✅ Rotate SECRET_KEY periodically
✅ Monitor audit logs for suspicious activity
✅ Implement rate limiting on auth endpoints
✅ Enable 2FA (future enhancement)

---

## Configuration Options

Edit `config.py` to customize:

```python
# Session timeout (hours)
SESSION_TIMEOUT_HOURS = 24  # With "Remember me"
SESSION_TIMEOUT_HOURS_NO_REMEMBER = 2  # Without

# Account lockout
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Password requirements
MIN_PASSWORD_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_SPECIAL_CHAR = True
REQUIRE_NUMBER = True
```

---

## Advanced Features

### Change Password

```python
from auth.auth_manager import AuthManager

auth_manager = AuthManager()
success, message = auth_manager.change_password(
    email="user@example.com",
    old_password="OldPass123!",
    new_password="NewSecure456!"
)
print(message)
```

### Logout from All Devices

```python
from auth.db_manager import DatabaseManager

db = DatabaseManager()
count = db.delete_all_user_sessions("user@example.com")
print(f"Logged out from {count} devices")
```

### View Audit Logs

```python
from auth.db_manager import DatabaseManager

db = DatabaseManager()
logs = db.get_audit_logs(email="user@example.com", limit=50)
for log in logs:
    print(f"{log['timestamp']}: {log['event']}")
```

---

## Support

For issues or questions:
1. Check this guide first
2. Review MongoDB Atlas dashboard
3. Check application logs
4. Contact system administrator

---

## File Structure

```
excel_cleaner/
├── auth/
│   ├── __init__.py
│   ├── auth_manager.py       # Password hashing, login logic
│   ├── db_manager.py          # MongoDB operations
│   └── login_window.py        # Login/Register UI
├── config.py                  # Configuration settings
├── .env                       # YOUR MongoDB URI (don't commit!)
├── .env.example               # Template for .env
├── .gitignore                 # Ensures .env is not committed
├── requirements.txt           # Python dependencies
└── AUTH_SETUP_GUIDE.md        # This file
```

---

## Next Steps

1. ✅ Complete MongoDB Atlas setup
2. ✅ Create and configure `.env` file
3. ✅ Install dependencies
4. ✅ Test standalone authentication
5. ✅ Integrate with main application
6. ✅ Run full testing checklist
7. 🚀 Deploy to production

---

**Security Notice**: Never commit `.env` file, connection strings, or passwords to git. Always use environment variables for production deployments.
