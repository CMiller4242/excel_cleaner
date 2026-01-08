"""
Settings dialog for CleanSheet application.

Manages API keys and application preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading


class SettingsDialog:
    """Settings dialog for managing application configuration."""

    def __init__(self, parent, config_manager, on_save=None):
        """
        Initialize settings dialog.

        Args:
            parent: Parent Tkinter window
            config_manager: ConfigManager instance
            on_save: Optional callback when settings are saved
        """
        self.parent = parent
        self.config_manager = config_manager
        self.on_save = on_save
        self.result = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("700x550")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._load_current_values()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (550 // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = tk.Frame(self.dialog, bg="#0078D4", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="Settings",
            font=("Segoe UI", 18, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=20)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # API Keys Tab
        api_frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(api_frame, text="API Keys")
        self._create_api_tab(api_frame)

        # General Tab
        general_frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(general_frame, text="General")
        self._create_general_tab(general_frame)

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        tk.Button(
            button_frame,
            text="Save",
            command=self._save_settings,
            bg="#0078D4",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT)

    def _create_api_tab(self, parent):
        """Create API keys configuration tab."""
        # Anthropic API Key
        tk.Label(
            parent,
            text="Anthropic API Key (for AI Assistant):",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))

        anthropic_frame = tk.Frame(parent)
        anthropic_frame.pack(fill=tk.X, pady=(0, 5))

        self.anthropic_key_entry = tk.Entry(
            anthropic_frame,
            width=60,
            font=("Consolas", 9),
            show="*"
        )
        self.anthropic_key_entry.pack(side=tk.LEFT, padx=(0, 5))

        self.show_anthropic_var = tk.BooleanVar()
        tk.Checkbutton(
            anthropic_frame,
            text="Show",
            variable=self.show_anthropic_var,
            command=lambda: self._toggle_visibility(
                self.anthropic_key_entry,
                self.show_anthropic_var
            )
        ).pack(side=tk.LEFT)

        tk.Label(
            parent,
            text="Used for AI-powered features and assistance",
            font=("Segoe UI", 8),
            fg="gray"
        ).pack(anchor=tk.W, pady=(0, 20))

        # Separator
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)

        # Emailable API Key
        tk.Label(
            parent,
            text="Emailable API Key (for Email Validation):",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))

        emailable_frame = tk.Frame(parent)
        emailable_frame.pack(fill=tk.X, pady=(0, 5))

        self.emailable_key_entry = tk.Entry(
            emailable_frame,
            width=60,
            font=("Consolas", 9),
            show="*"
        )
        self.emailable_key_entry.pack(side=tk.LEFT, padx=(0, 5))

        self.show_emailable_var = tk.BooleanVar()
        tk.Checkbutton(
            emailable_frame,
            text="Show",
            variable=self.show_emailable_var,
            command=lambda: self._toggle_visibility(
                self.emailable_key_entry,
                self.show_emailable_var
            )
        ).pack(side=tk.LEFT)

        tk.Label(
            parent,
            text="Sign up at https://emailable.com to get your API key",
            font=("Segoe UI", 8),
            fg="gray"
        ).pack(anchor=tk.W, pady=(0, 5))

        # Test Key Button
        self.test_key_button = tk.Button(
            parent,
            text="Test Emailable Key",
            command=self._test_emailable_key,
            bg="#28a745",
            fg="white",
            font=("Segoe UI", 9),
            padx=15,
            pady=6,
            cursor="hand2"
        )
        self.test_key_button.pack(anchor=tk.W, pady=(10, 0))

        self.test_result_label = tk.Label(
            parent,
            text="",
            font=("Segoe UI", 9),
            fg="gray"
        )
        self.test_result_label.pack(anchor=tk.W, pady=(5, 0))

    def _create_general_tab(self, parent):
        """Create general settings tab."""
        # Auto-update check
        self.check_updates_var = tk.BooleanVar()
        tk.Checkbutton(
            parent,
            text="Check for updates automatically",
            variable=self.check_updates_var,
            font=("Segoe UI", 10)
        ).pack(anchor=tk.W, pady=(10, 5))

        tk.Label(
            parent,
            text="CleanSheet will check for new versions on startup",
            font=("Segoe UI", 8),
            fg="gray"
        ).pack(anchor=tk.W, padx=(25, 0), pady=(0, 20))

    def _load_current_values(self):
        """Load current configuration values."""
        # Load API keys
        anthropic_key = self.config_manager.get_api_key()
        if anthropic_key:
            self.anthropic_key_entry.insert(0, anthropic_key)

        emailable_key = self.config_manager.get_emailable_api_key()
        if emailable_key:
            self.emailable_key_entry.insert(0, emailable_key)

        # Load general settings
        self.check_updates_var.set(self.config_manager.should_check_updates())

    def _toggle_visibility(self, entry_widget, var):
        """Toggle password visibility for an entry widget."""
        if var.get():
            entry_widget.config(show="")
        else:
            entry_widget.config(show="*")

    def _test_emailable_key(self):
        """Test Emailable API key connection."""
        api_key = self.emailable_key_entry.get().strip()

        if not api_key:
            messagebox.showwarning(
                "No API Key",
                "Please enter an Emailable API key first.",
                parent=self.dialog
            )
            return

        # Disable button and show testing status
        self.test_key_button.config(state=tk.DISABLED, text="Testing...")
        self.test_result_label.config(text="Testing connection...", fg="blue")
        self.dialog.update()

        # Run test in background thread to avoid freezing UI
        def test_thread():
            try:
                from integrations.emailable_client import EmailableClient

                client = EmailableClient(api_key)
                success = client.test_connection()
                client.close()

                # Update UI in main thread
                self.dialog.after(0, lambda: self._show_test_result(success))

            except Exception as e:
                self.dialog.after(0, lambda: self._show_test_result(False, str(e)))

        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()

    def _show_test_result(self, success, error_msg=None):
        """Show test result in UI (called in main thread)."""
        self.test_key_button.config(state=tk.NORMAL, text="Test Emailable Key")

        if success:
            self.test_result_label.config(
                text="✓ Connection successful! API key is valid.",
                fg="green"
            )
        else:
            error_text = f"✗ Connection failed"
            if error_msg:
                error_text += f": {error_msg}"
            self.test_result_label.config(text=error_text, fg="red")

    def _save_settings(self):
        """Save settings to configuration."""
        # Save API keys
        anthropic_key = self.anthropic_key_entry.get().strip()
        self.config_manager.set_api_key(anthropic_key)

        emailable_key = self.emailable_key_entry.get().strip()
        self.config_manager.set_emailable_api_key(emailable_key)

        # Save general settings
        self.config_manager.set_check_updates(self.check_updates_var.get())

        # Show success message
        messagebox.showinfo(
            "Settings Saved",
            "Your settings have been saved successfully.",
            parent=self.dialog
        )

        self.result = True

        # Call callback if provided
        if self.on_save:
            self.on_save()

        self.dialog.destroy()

    def _on_cancel(self):
        """Handle dialog cancellation."""
        self.dialog.destroy()

    def show(self):
        """Show dialog and return result."""
        self.dialog.wait_window()
        return self.result
