"""
Clean Sheet Configuration Manager
Handles MongoDB URI, API keys, and application settings
"""

import os
import sys
import configparser
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

class ConfigManager:
    """Manages application configuration and settings"""

    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.ini"
        self.config = configparser.ConfigParser()

        if self.config_file.exists():
            self.config.read(self.config_file)
        else:
            self.create_default_config()

    def _get_config_dir(self):
        """Get application config directory based on platform"""
        if sys.platform == "win32":
            config_dir = Path(os.getenv('APPDATA')) / 'CleanSheet'
        else:
            config_dir = Path.home() / '.config' / 'CleanSheet'

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def create_default_config(self):
        """Create default configuration file"""
        self.config['Database'] = {
            'mongodb_uri': '',
        }
        self.config['API'] = {
            'anthropic_api_key': '',
            'emailable_api_key': '',
        }
        self.config['App'] = {
            'check_updates': 'true',
            'theme': 'office365',
            'last_update_check': '',
        }
        self.config['Updates'] = {
            'skipped_version': '',
        }
        self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_mongodb_uri(self):
        """Get MongoDB connection URI"""
        return self.config.get('Database', 'mongodb_uri', fallback='')

    def set_mongodb_uri(self, uri):
        """Set MongoDB connection URI"""
        if not self.config.has_section('Database'):
            self.config.add_section('Database')
        self.config.set('Database', 'mongodb_uri', uri)
        self.save_config()

    def get_api_key(self):
        """Get Anthropic API key"""
        return self.config.get('API', 'anthropic_api_key', fallback='')

    def set_api_key(self, key):
        """Set Anthropic API key"""
        if not self.config.has_section('API'):
            self.config.add_section('API')
        self.config.set('API', 'anthropic_api_key', key)
        self.save_config()

    def get_emailable_api_key(self):
        """Get Emailable API key"""
        return self.config.get('API', 'emailable_api_key', fallback='')

    def set_emailable_api_key(self, key):
        """Set Emailable API key"""
        if not self.config.has_section('API'):
            self.config.add_section('API')
        self.config.set('API', 'emailable_api_key', key)
        self.save_config()

    def should_check_updates(self):
        """Check if auto-updates are enabled"""
        return self.config.getboolean('App', 'check_updates', fallback=True)

    def set_check_updates(self, enabled):
        """Enable/disable auto-updates"""
        if not self.config.has_section('App'):
            self.config.add_section('App')
        self.config.set('App', 'check_updates', str(enabled).lower())
        self.save_config()

    def get_skipped_version(self):
        """Get version that user chose to skip"""
        return self.config.get('Updates', 'skipped_version', fallback='')

    def set_skipped_version(self, version):
        """Set version that user chose to skip"""
        if not self.config.has_section('Updates'):
            self.config.add_section('Updates')
        self.config.set('Updates', 'skipped_version', version)
        self.save_config()

    def is_configured(self):
        """Check if essential configuration is complete"""
        return bool(self.get_mongodb_uri())

    def get_config_path(self):
        """Get path to configuration file"""
        return str(self.config_file)


class FirstRunConfigDialog:
    """Configuration dialog for first-time setup"""

    def __init__(self, parent):
        self.result = False
        self.mongodb_uri = None
        self.api_key = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Clean Sheet - First-Time Setup")
        self.dialog.geometry("650x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)

        # Prevent closing without configuration
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._create_widgets()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Force dialog to appear and stay on top
        self.dialog.deiconify()  # Ensure window is visible
        self.dialog.lift()  # Bring to front
        self.dialog.focus_force()  # Force focus
        self.dialog.grab_set()  # Modal dialog

    def _create_widgets(self):
        """Create dialog widgets"""
        # Header
        header_frame = tk.Frame(self.dialog, bg="#0078D4", height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="Welcome to Clean Sheet",
            font=("Segoe UI", 18, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=15)

        tk.Label(
            header_frame,
            text="Professional Data Cleaning Made Simple",
            font=("Segoe UI", 11),
            bg="#0078D4",
            fg="white"
        ).pack()

        # Content
        content_frame = tk.Frame(self.dialog, padx=30, pady=30)
        content_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            content_frame,
            text="Let's get started by configuring your database connection.",
            font=("Segoe UI", 10),
            wraplength=550,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 20))

        # MongoDB URI
        tk.Label(
            content_frame,
            text="MongoDB Connection URI (Required):",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))

        self.mongodb_entry = tk.Entry(content_frame, width=70, font=("Consolas", 9))
        self.mongodb_entry.pack(anchor=tk.W, pady=(0, 5))

        tk.Label(
            content_frame,
            text="Example: mongodb+srv://username:password@cluster.mongodb.net/",
            font=("Segoe UI", 8),
            fg="gray"
        ).pack(anchor=tk.W, pady=(0, 20))

        # API Key
        tk.Label(
            content_frame,
            text="Anthropic API Key (Optional - for AI Assistant):",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))

        self.api_key_entry = tk.Entry(content_frame, width=70, font=("Consolas", 9), show="*")
        self.api_key_entry.pack(anchor=tk.W, pady=(0, 5))

        # Show/Hide API Key
        self.show_api_key_var = tk.BooleanVar()
        tk.Checkbutton(
            content_frame,
            text="Show API Key",
            variable=self.show_api_key_var,
            command=self._toggle_api_key_visibility,
            font=("Segoe UI", 9)
        ).pack(anchor=tk.W, pady=(5, 0))

        tk.Label(
            content_frame,
            text="Leave blank to use without AI features",
            font=("Segoe UI", 8),
            fg="gray"
        ).pack(anchor=tk.W, pady=(5, 0))

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 30))

        self.test_button = tk.Button(
            button_frame,
            text="Test Connection & Continue",
            command=self._test_and_save,
            bg="#0078D4",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.test_button.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            button_frame,
            text="Exit",
            command=self._on_cancel,
            font=("Segoe UI", 10),
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT)

    def _toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.show_api_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")

    def _test_and_save(self):
        """Test MongoDB connection and save configuration"""
        mongodb_uri = self.mongodb_entry.get().strip()
        api_key = self.api_key_entry.get().strip()

        if not mongodb_uri:
            messagebox.showerror(
                "Configuration Error",
                "MongoDB URI is required to use Clean Sheet.",
                parent=self.dialog
            )
            return

        # Test MongoDB connection
        self.test_button.config(state=tk.DISABLED, text="Testing connection...")
        self.dialog.update()

        try:
            from pymongo import MongoClient
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            client.server_info()  # Force connection test
            client.close()

            self.mongodb_uri = mongodb_uri
            self.api_key = api_key
            self.result = True
            self.dialog.destroy()

        except Exception as e:
            self.test_button.config(state=tk.NORMAL, text="Test Connection & Continue")
            messagebox.showerror(
                "Connection Failed",
                f"Failed to connect to MongoDB:\n\n{str(e)}\n\nPlease check your connection URI and try again.",
                parent=self.dialog
            )

    def _on_cancel(self):
        """Handle dialog cancellation"""
        if messagebox.askyesno(
            "Exit Clean Sheet",
            "MongoDB configuration is required to use Clean Sheet.\n\nExit the application?",
            parent=self.dialog
        ):
            sys.exit(0)

    def show(self):
        """Show dialog and return configuration"""
        self.dialog.wait_window()
        return self.result, self.mongodb_uri, self.api_key
