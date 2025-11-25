# Authentication Integration Fix - Callback Signature Mismatch

## Problem Identified

The authentication system was failing when integrated into `main_gui_v2_office365.py` with the error:

```
"on_login_success() takes 1 positional argument but 2 were given"
```

### Root Cause

The **LoginWindow** class calls the success callback with **TWO arguments**:
- `token` (session token string)
- `email` (user's email address)

However, the callback function in the main application was defined incorrectly, likely accepting only one or zero additional arguments.

---

## Solution Applied

### 1. Added Authentication Imports

**Location:** Lines 33-36 in `main_gui_v2_office365.py`

```python
# Authentication imports
from auth.login_window import LoginWindow
from auth.auth_manager import AuthManager
from config import Config
```

### 2. Modified Class __init__ Signature

**Location:** Lines 49-66

**Before:**
```python
def __init__(self, root):
    self.root = root
    self.root.title("🔷 Universal Excel Tool - Professional Edition")
```

**After:**
```python
def __init__(self, root, session_token=None, user_email=None):
    self.root = root

    # Set title with user info if authenticated
    if user_email:
        self.root.title(f"🔷 Universal Excel Tool - {user_email}")
    else:
        self.root.title("🔷 Universal Excel Tool - Professional Edition")

    self.root.geometry("1600x900")
    self.root.minsize(1200, 800)

    # Authentication
    self.session_token = session_token
    self.user_email = user_email
    self.auth_manager = None
    if session_token:
        self.auth_manager = AuthManager()
```

**Changes:**
- Added `session_token` and `user_email` parameters (both optional for backward compatibility)
- Added authentication attributes to class
- Window title now shows logged-in user's email
- Creates AuthManager instance if session token provided

### 3. Fixed main() Function with Correct Callback Signature

**Location:** Lines 1677-1735

**Key Fix - Callback Signature:**

```python
def on_login_success(token, email):
    """
    Callback invoked when user successfully logs in

    CRITICAL: This function MUST accept TWO arguments (token, email)
    as this is how LoginWindow calls it.

    Args:
        token: Session token string
        email: User's email address
    """
    auth_data['token'] = token
    auth_data['email'] = email
    logging.info(f"✅ User authenticated: {email}")
```

**Complete Flow:**

```python
def main():
    """Main entry point with authentication"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Storage for authentication data
    auth_data = {'token': None, 'email': None}

    def on_login_success(token, email):  # ✅ TWO arguments!
        auth_data['token'] = token
        auth_data['email'] = email
        logging.info(f"✅ User authenticated: {email}")

    # Show login window
    try:
        login_window = LoginWindow(on_success_callback=on_login_success)
        token, email = login_window.run()

        # If authentication failed or was cancelled, exit
        if not token or not email:
            logging.info("Authentication cancelled or failed. Exiting.")
            return

        # Authentication successful - start main application
        logging.info(f"Starting main application for user: {email}")
        root = tk.Tk()
        app = UniversalExcelToolV2Office365(
            root,
            session_token=token,
            user_email=email
        )
        root.mainloop()

    except Exception as e:
        logging.error(f"Application error: {e}", exc_info=True)
        messagebox.showerror(
            "Application Error",
            f"Failed to start application:\n\n{str(e)}\n\n"
            "Please check your MongoDB configuration and try again."
        )
```

---

## How It Works

### Authentication Flow:

1. **User runs:** `python main_gui_v2_office365.py`
2. **Login window appears** (from `LoginWindow` class)
3. **User logs in** or auto-login occurs (Remember Me)
4. **LoginWindow calls callback:** `on_login_success(token, email)`
   - ✅ Callback correctly accepts **TWO arguments**
   - Stores token and email in `auth_data` dictionary
5. **login_window.run() returns:** `(token, email)` tuple
6. **Main application starts:**
   - Creates Tk root window
   - Passes token and email to `UniversalExcelToolV2Office365`
   - Window title shows user's email
   - Auth manager initialized for session verification

### Key Points:

✅ **Callback must accept 2 arguments** - This was the bug!
✅ **Session token and email passed to main app**
✅ **Window title shows logged-in user**
✅ **Auth manager available for session verification**
✅ **Backward compatible** (parameters optional)

---

## Testing the Fix

### 1. Standalone Authentication Test

```bash
python auth/login_window.py
```

**Expected:** Login window appears, register/login works, MongoDB connection succeeds.

### 2. Integrated Application Test

```bash
python main_gui_v2_office365.py
```

**Expected Flow:**
1. Login window appears
2. Enter credentials or auto-login occurs
3. Login window closes
4. Main Excel Tool window opens
5. Window title shows: "🔷 Universal Excel Tool - your@email.com"

### 3. Verify Session Data

Add this debug code temporarily after line 1722:

```python
print(f"✅ App started successfully!")
print(f"Session Token: {app.session_token[:20]}...")
print(f"User Email: {app.user_email}")
print(f"Auth Manager: {app.auth_manager}")
```

**Expected Output:**
```
✅ App started successfully!
Session Token: AbCdEfGhIjKlMnOpQrSt...
User Email: user@example.com
Auth Manager: <auth.auth_manager.AuthManager object at 0x...>
```

---

## Comparison: Wrong vs. Right

### ❌ WRONG (Causes Error):

```python
def on_login_success():  # Missing parameters!
    print("Login successful")

# Or:

def on_login_success(self):  # Only 1 parameter!
    self.token = "something"
```

**Error:**
```
TypeError: on_login_success() takes 0/1 positional argument but 2 were given
```

### ✅ CORRECT:

```python
def on_login_success(token, email):  # TWO parameters!
    print(f"Login successful: {email}")
    print(f"Token: {token}")
```

---

## Why This Error Occurred

The `LoginWindow` class (in `auth/login_window.py`) calls the callback like this:

**Line in login_window.py:**
```python
self.on_success(token, email)  # Passes TWO arguments
```

This happens in two places:
1. `try_auto_login()` - When auto-login succeeds
2. `handle_login()` - When user logs in manually

Therefore, **any callback passed to LoginWindow MUST accept (token, email)**.

---

## Additional Features Available

### Access User Email in Main App

```python
# Inside any method of UniversalExcelToolV2Office365 class:
if self.user_email:
    print(f"Current user: {self.user_email}")
```

### Verify Session is Still Valid

```python
if self.auth_manager and self.session_token:
    is_valid, email = self.auth_manager.verify_session(self.session_token)
    if not is_valid:
        # Session expired, prompt re-login
        messagebox.showwarning("Session Expired", "Please log in again.")
```

### Logout Functionality

Add a logout button to your UI that calls:

```python
def logout(self):
    """Logout and restart app"""
    if self.auth_manager and self.session_token:
        self.auth_manager.logout(self.session_token)

    self.root.destroy()
    main()  # Restart with login screen
```

---

## Troubleshooting

### If you still get the error:

1. **Check callback signature** - Must be `def callback(token, email):`
2. **Check for typos** - Parameter names don't matter, but count does
3. **Verify imports** - Make sure `from auth.login_window import LoginWindow` works
4. **Check indentation** - Python is sensitive to indentation

### If MongoDB connection fails:

1. **Check .env file exists** with `MONGODB_URI`
2. **Verify connection string** is correct
3. **Test internet connection**
4. **Check MongoDB Atlas** cluster is running

### If auto-login doesn't work:

1. **Check "Remember Me"** was checked during login
2. **Verify session file** exists: `~/.config/ExcelToolV2/.session`
3. **Check session expiration** (24 hours by default)

---

## Files Modified

- ✅ `main_gui_v2_office365.py` - Added authentication integration
  - Lines 33-36: Imports
  - Lines 49-66: Class __init__ modifications
  - Lines 1677-1735: main() function with auth

No other files needed modification. All authentication code is in the `auth/` directory.

---

## Summary

**Problem:** Callback signature mismatch
**Root Cause:** Callback didn't accept 2 arguments (token, email)
**Solution:** Fixed callback to accept `(token, email)`
**Result:** Authentication now fully integrated and working

The application now requires login before accessing the Excel Tool, with user info displayed in the title bar and session management fully functional.
