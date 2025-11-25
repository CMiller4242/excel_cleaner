"""
Login/Register Window
Provides UI for user authentication
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.auth_manager import AuthManager
from config import Config

logger = logging.getLogger(__name__)


class LoginWindow:
    """Login/Register window for authentication"""

    def __init__(self, on_success_callback):
        """
        Args:
            on_success_callback: Function to call with (session_token, email) when login succeeds
        """
        self.on_success = on_success_callback
        self.auth_manager = None
        self.session_token = None
        self.user_email = None

        # Create window
        self.root = tk.Tk()
        self.root.title(f"{Config.APP_NAME} - Login")
        self.root.geometry("500x620")
        self.root.resizable(False, False)

        # Center window on screen
        self.center_window()

        # Initialize auth manager
        try:
            self.auth_manager = AuthManager()
        except Exception as e:
            messagebox.showerror(
                "Connection Error",
                f"Failed to connect to authentication server:\n\n{str(e)}\n\n"
                "Please check your internet connection and MongoDB configuration."
            )
            self.root.destroy()
            return

        # Try auto-login from saved session
        if self.try_auto_login():
            return

        self.create_ui()

    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def try_auto_login(self):
        """Try to auto-login using saved session token"""
        try:
            token = self.auth_manager.load_local_session()
            if token:
                is_valid, email = self.auth_manager.verify_session(token)
                if is_valid:
                    logger.info(f"Auto-login successful for: {email}")
                    self.session_token = token
                    self.user_email = email
                    self.root.destroy()
                    self.on_success(token, email)
                    return True
                else:
                    # Invalid/expired session, delete it
                    self.auth_manager.delete_local_session()
        except Exception as e:
            logger.error(f"Error during auto-login: {e}")

        return False

    def create_ui(self):
        """Create login/register UI"""

        # Main container
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Logo/Title section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(
            title_frame,
            text=Config.APP_NAME,
            font=("Segoe UI", 22, "bold"),
            foreground="#0078D4"
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            title_frame,
            text=f"Version {Config.APP_VERSION}",
            font=("Segoe UI", 10),
            foreground="gray"
        )
        subtitle_label.pack()

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=15)

        # Tabbed interface for Login/Register
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Login Tab
        login_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(login_frame, text="   Login   ")
        self.create_login_tab(login_frame)

        # Register Tab
        register_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(register_frame, text="   Register   ")
        self.create_register_tab(register_frame)

        # Footer
        footer_label = ttk.Label(
            main_frame,
            text="Secure authentication powered by MongoDB",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        footer_label.pack(side=tk.BOTTOM, pady=(15, 0))

    def create_login_tab(self, parent):
        """Create login form"""

        # Email
        ttk.Label(
            parent,
            text="Email Address:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(15, 5))

        self.login_email = ttk.Entry(parent, width=45, font=("Segoe UI", 11))
        self.login_email.pack(pady=(0, 15), ipady=3)
        self.login_email.focus()

        # Password
        ttk.Label(
            parent,
            text="Password:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.login_password = ttk.Entry(parent, width=45, show="●", font=("Segoe UI", 11))
        self.login_password.pack(pady=(0, 15), ipady=3)

        # Remember Me checkbox
        self.remember_var = tk.BooleanVar(value=True)
        remember_frame = ttk.Frame(parent)
        remember_frame.pack(fill=tk.X, pady=(0, 20))

        remember_check = ttk.Checkbutton(
            remember_frame,
            text=f"Remember me for {Config.SESSION_TIMEOUT_HOURS} hours",
            variable=self.remember_var
        )
        remember_check.pack(side=tk.LEFT)

        # Login button
        login_btn = ttk.Button(
            parent,
            text="Login",
            command=self.handle_login,
            style='Accent.TButton'
        )
        login_btn.pack(pady=15, ipady=5, fill=tk.X)

        # Bind Enter key
        self.login_password.bind('<Return>', lambda e: self.handle_login())
        self.login_email.bind('<Return>', lambda e: self.login_password.focus())

        # Status label
        self.login_status = ttk.Label(
            parent,
            text="",
            font=("Segoe UI", 9),
            foreground="red",
            wraplength=400,
            justify=tk.CENTER
        )
        self.login_status.pack(pady=10)

        # Help text
        help_label = ttk.Label(
            parent,
            text="Don't have an account? Click the Register tab above.",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        help_label.pack(pady=(20, 0))

    def create_register_tab(self, parent):
        """Create registration form"""

        # Instructions
        instructions = ttk.Label(
            parent,
            text="Create a new account. Password requirements:",
            font=("Segoe UI", 10, "bold")
        )
        instructions.pack(pady=(10, 5), anchor=tk.W)

        requirements_frame = ttk.Frame(parent)
        requirements_frame.pack(fill=tk.X, pady=(0, 15))

        requirements = [
            f"• At least {Config.MIN_PASSWORD_LENGTH} characters",
            "• At least 1 uppercase letter (A-Z)",
            "• At least 1 number (0-9)",
            "• At least 1 special character (!@#$%^&*...)"
        ]

        for req in requirements:
            ttk.Label(
                requirements_frame,
                text=req,
                font=("Segoe UI", 9),
                foreground="gray"
            ).pack(anchor=tk.W)

        # Email
        ttk.Label(
            parent,
            text="Email Address:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))

        self.register_email = ttk.Entry(parent, width=45, font=("Segoe UI", 11))
        self.register_email.pack(pady=(0, 15), ipady=3)

        # Password
        ttk.Label(
            parent,
            text="Password:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.register_password = ttk.Entry(parent, width=45, show="●", font=("Segoe UI", 11))
        self.register_password.pack(pady=(0, 15), ipady=3)

        # Confirm Password
        ttk.Label(
            parent,
            text="Confirm Password:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.register_confirm = ttk.Entry(parent, width=45, show="●", font=("Segoe UI", 11))
        self.register_confirm.pack(pady=(0, 20), ipady=3)

        # Register button
        register_btn = ttk.Button(
            parent,
            text="Create Account",
            command=self.handle_register,
            style='Accent.TButton'
        )
        register_btn.pack(pady=15, ipady=5, fill=tk.X)

        # Bind Enter key
        self.register_confirm.bind('<Return>', lambda e: self.handle_register())
        self.register_email.bind('<Return>', lambda e: self.register_password.focus())
        self.register_password.bind('<Return>', lambda e: self.register_confirm.focus())

        # Status label
        self.register_status = ttk.Label(
            parent,
            text="",
            font=("Segoe UI", 9),
            foreground="red",
            wraplength=400,
            justify=tk.CENTER
        )
        self.register_status.pack(pady=10)

    def handle_login(self):
        """Handle login button click"""
        email = self.login_email.get().strip()
        password = self.login_password.get()
        remember_me = self.remember_var.get()

        if not email or not password:
            self.login_status.config(
                text="Please enter both email and password",
                foreground="red"
            )
            return

        # Show loading message
        self.login_status.config(text="Authenticating...", foreground="blue")
        self.root.update()

        try:
            # Attempt login
            success, message, token = self.auth_manager.login(email, password, remember_me)

            if success:
                self.login_status.config(text=message, foreground="green")
                self.session_token = token
                self.user_email = email
                logger.info(f"Login successful: {email}")

                # Close window and proceed to main app
                self.root.after(500, lambda: [self.root.destroy(), self.on_success(token, email)])
            else:
                self.login_status.config(text=message, foreground="red")
                self.login_password.delete(0, tk.END)
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.login_status.config(
                text=f"Login failed: {str(e)}",
                foreground="red"
            )

    def handle_register(self):
        """Handle register button click"""
        email = self.register_email.get().strip()
        password = self.register_password.get()
        confirm = self.register_confirm.get()

        if not email or not password or not confirm:
            self.register_status.config(
                text="Please fill in all fields",
                foreground="red"
            )
            return

        if password != confirm:
            self.register_status.config(
                text="Passwords do not match",
                foreground="red"
            )
            self.register_confirm.delete(0, tk.END)
            return

        # Show loading message
        self.register_status.config(text="Creating account...", foreground="blue")
        self.root.update()

        try:
            # Attempt registration
            success, message = self.auth_manager.register_user(email, password)

            if success:
                self.register_status.config(text=message, foreground="green")
                logger.info(f"Registration successful: {email}")

                # Clear fields
                self.register_email.delete(0, tk.END)
                self.register_password.delete(0, tk.END)
                self.register_confirm.delete(0, tk.END)

                # Switch to login tab after 1.5 seconds
                self.root.after(1500, lambda: [
                    self.notebook.select(0),
                    self.login_email.insert(0, email),
                    self.login_password.focus()
                ])
            else:
                self.register_status.config(text=message, foreground="red")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self.register_status.config(
                text=f"Registration failed: {str(e)}",
                foreground="red"
            )

    def run(self):
        """Start the login window"""
        try:
            self.root.mainloop()
            return self.session_token, self.user_email
        except Exception as e:
            logger.error(f"Error running login window: {e}")
            return None, None


# Standalone testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    def on_login_success(token, email):
        print(f"\n✅ Login successful!")
        print(f"Token: {token[:20]}...")
        print(f"Email: {email}")

    login_window = LoginWindow(on_success_callback=on_login_success)
    token, email = login_window.run()

    if token:
        print(f"\nReturned from login window:")
        print(f"Token: {token[:20]}...")
        print(f"Email: {email}")
    else:
        print("\nLogin cancelled or failed")
