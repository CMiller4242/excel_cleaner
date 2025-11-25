"""
Example: Main Application with Authentication
This shows how to integrate the authentication system with your main app
"""
import tkinter as tk
from tkinter import ttk
import logging
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auth.login_window import LoginWindow
from auth.auth_manager import AuthManager
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ExcelToolWithAuth:
    """Excel Tool Application with Authentication"""

    def __init__(self):
        self.session_token = None
        self.user_email = None
        self.auth_manager = None
        self.main_window = None

    def start(self):
        """Start the application with authentication"""
        logger.info("Starting Excel Tool with Authentication")

        # Show login window first
        login_window = LoginWindow(on_success_callback=self.on_login_success)
        token, email = login_window.run()

        # If login was successful, start main application
        if token and email:
            logger.info(f"Authentication successful, starting main app for: {email}")
            self.start_main_app()
        else:
            logger.info("Authentication cancelled or failed")

    def on_login_success(self, token, email):
        """
        Called when user successfully logs in

        Args:
            token: Session token
            email: User's email address
        """
        self.session_token = token
        self.user_email = email
        self.auth_manager = AuthManager()

        logger.info(f"✅ User authenticated: {email}")
        logger.info(f"Session token: {token[:20]}...")

    def start_main_app(self):
        """Start the main Excel Tool application"""
        logger.info("Launching main application window")

        # Create main window
        self.main_window = tk.Tk()
        self.main_window.title(f"{Config.APP_NAME} - Logged in as {self.user_email}")
        self.main_window.geometry("1200x800")

        # Create UI
        self.create_ui()

        # Handle window close
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start main loop
        self.main_window.mainloop()

    def create_ui(self):
        """Create the main application UI"""

        # Header with user info and logout
        header_frame = ttk.Frame(self.main_window, padding="10")
        header_frame.pack(fill=tk.X)

        ttk.Label(
            header_frame,
            text=f"Welcome to {Config.APP_NAME}",
            font=("Segoe UI", 16, "bold")
        ).pack(side=tk.LEFT)

        # User info and logout button
        user_frame = ttk.Frame(header_frame)
        user_frame.pack(side=tk.RIGHT)

        ttk.Label(
            user_frame,
            text=f"👤 {self.user_email}",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            user_frame,
            text="Logout",
            command=self.logout
        ).pack(side=tk.LEFT)

        ttk.Separator(self.main_window, orient='horizontal').pack(fill=tk.X, pady=10)

        # Main content area
        content_frame = ttk.Frame(self.main_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Placeholder for your actual Excel Tool UI
        ttk.Label(
            content_frame,
            text="🎉 Authentication Successful!\n\n"
                 "This is where your Excel Tool interface would go.\n\n"
                 "Replace this with your actual application code:\n"
                 "- File upload\n"
                 "- Operation queue\n"
                 "- Data preview\n"
                 "- Processing controls",
            font=("Segoe UI", 12),
            justify=tk.CENTER
        ).pack(expand=True)

        # Status bar
        status_frame = ttk.Frame(self.main_window)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        status_text = f"Session active | Logged in as {self.user_email}"
        ttk.Label(
            status_frame,
            text=status_text,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(10, 5)
        ).pack(fill=tk.X)

    def logout(self):
        """Logout user and return to login screen"""
        if self.auth_manager and self.session_token:
            # Logout (deletes session from database and local file)
            self.auth_manager.logout(self.session_token)
            logger.info(f"User logged out: {self.user_email}")

        # Close main window
        if self.main_window:
            self.main_window.destroy()

        # Restart application (show login screen again)
        self.session_token = None
        self.user_email = None
        self.auth_manager = None
        self.start()

    def on_close(self):
        """Handle window close event"""
        logger.info("Application closing")

        # Optional: Logout on close (uncomment if desired)
        # if self.auth_manager and self.session_token:
        #     self.auth_manager.logout(self.session_token)

        # Close auth manager connection
        if self.auth_manager:
            self.auth_manager.close()

        # Destroy window
        if self.main_window:
            self.main_window.destroy()


def main():
    """Main entry point"""
    try:
        app = ExcelToolWithAuth()
        app.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
