"""
Clean Sheet Auto-Update System
Checks for updates once per day via GitHub Releases
"""

import requests
import json
import os
import sys
import hashlib
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from packaging import version
import tkinter as tk
from tkinter import messagebox, ttk


class AutoUpdater:
    """Handles automatic updates from GitHub releases"""

    def __init__(self, current_version, github_repo):
        self.current_version = current_version
        self.github_repo = github_repo
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        self.config_dir = self._get_config_dir()
        self.last_check_file = self.config_dir / "last_update_check.txt"

    def _get_config_dir(self):
        """Get application config directory"""
        if sys.platform == "win32":
            config_dir = Path(os.getenv('APPDATA')) / 'CleanSheet'
        else:
            config_dir = Path.home() / '.config' / 'CleanSheet'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def should_check_for_updates(self):
        """Check if 24 hours have passed since last check"""
        if not self.last_check_file.exists():
            return True

        try:
            last_check = datetime.fromisoformat(
                self.last_check_file.read_text().strip()
            )
            return datetime.now() - last_check > timedelta(hours=24)
        except:
            return True

    def update_last_check_time(self):
        """Record current time as last update check"""
        self.last_check_file.write_text(datetime.now().isoformat())

    def check_for_updates_async(self, callback=None):
        """Check for updates in background thread"""
        def check():
            try:
                result = self.check_for_updates()
                if callback:
                    callback(result)
            except Exception as e:
                print(f"Update check failed: {e}")

        thread = threading.Thread(target=check, daemon=True)
        thread.start()

    def check_for_updates(self):
        """
        Check GitHub releases for new version
        Returns: {
            'update_available': bool,
            'new_version': str,
            'download_url': str,
            'release_notes': str,
            'published_at': str
        }
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()

            release = response.json()
            new_version = release['tag_name'].lstrip('v')

            update_available = version.parse(new_version) > version.parse(self.current_version)

            # Find .exe asset in release
            download_url = None
            asset_size = 0
            for asset in release.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    asset_size = asset.get('size', 0)
                    break

            self.update_last_check_time()

            return {
                'update_available': update_available,
                'new_version': new_version,
                'download_url': download_url,
                'release_notes': release.get('body', ''),
                'published_at': release.get('published_at', ''),
                'asset_size': asset_size
            }

        except Exception as e:
            print(f"Error checking for updates: {e}")
            return {'update_available': False, 'error': str(e)}

    def download_update(self, download_url, progress_callback=None):
        """Download new .exe with progress tracking"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            temp_file = self.config_dir / "CleanSheet_update.exe"

            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            return temp_file

        except Exception as e:
            print(f"Error downloading update: {e}")
            return None

    def install_update(self, new_exe_path):
        """
        Replace current .exe and restart
        Uses Windows batch script to handle running .exe replacement
        """
        if sys.platform != "win32":
            print("Auto-update only supported on Windows")
            return False

        current_exe = sys.executable
        batch_script = self.config_dir / "update_install.bat"

        # Create batch script to replace .exe and restart
        batch_content = f"""@echo off
echo Installing Clean Sheet update...
timeout /t 2 /nobreak > nul
move /y "{new_exe_path}" "{current_exe}"
if %ERRORLEVEL% EQU 0 (
    echo Update installed successfully!
    start "" "{current_exe}"
) else (
    echo Update installation failed!
    pause
)
del "%~f0"
"""
        batch_script.write_text(batch_content)

        # Launch batch script and exit
        subprocess.Popen(['cmd', '/c', str(batch_script)],
                        creationflags=subprocess.CREATE_NO_WINDOW)
        return True


class UpdateNotificationDialog:
    """GUI dialog for update notifications"""

    def __init__(self, parent, update_info):
        self.result = None
        self.update_info = update_info

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Update Available - Clean Sheet")
        self.dialog.geometry("550x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)

        self._create_widgets()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Force dialog to appear and stay on top
        self.dialog.deiconify()
        self.dialog.lift()
        self.dialog.focus_force()
        self.dialog.grab_set()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Header
        header_frame = tk.Frame(self.dialog, bg="#0078D4", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="🎉 Update Available!",
            font=("Segoe UI", 16, "bold"),
            bg="#0078D4",
            fg="white"
        ).pack(pady=20)

        # Content
        content_frame = tk.Frame(self.dialog, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        version_text = f"A new version of Clean Sheet is available:\nVersion {self.update_info['new_version']}"
        tk.Label(
            content_frame,
            text=version_text,
            font=("Segoe UI", 11),
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 10))

        # Release notes
        tk.Label(
            content_frame,
            text="What's New:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))

        notes_frame = tk.Frame(content_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        scrollbar = tk.Scrollbar(notes_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        notes_text = tk.Text(
            notes_frame,
            wrap=tk.WORD,
            height=10,
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 9)
        )
        notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=notes_text.yview)

        notes_text.insert("1.0", self.update_info.get('release_notes', 'No release notes available.'))
        notes_text.config(state=tk.DISABLED)

        # Download size info
        if self.update_info.get('asset_size'):
            size_mb = self.update_info['asset_size'] / (1024 * 1024)
            size_text = f"Download size: {size_mb:.1f} MB"
            tk.Label(
                content_frame,
                text=size_text,
                font=("Segoe UI", 8),
                fg="gray"
            ).pack(anchor=tk.W, pady=(0, 10))

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Button(
            button_frame,
            text="Update Now",
            command=self._update_now,
            bg="#0078D4",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            button_frame,
            text="Remind Me Tomorrow",
            command=self._remind_later,
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            button_frame,
            text="Skip This Version",
            command=self._skip_version,
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT)

    def _update_now(self):
        self.result = "update"
        self.dialog.destroy()

    def _remind_later(self):
        self.result = "later"
        self.dialog.destroy()

    def _skip_version(self):
        self.result = "skip"
        self.dialog.destroy()

    def show(self):
        """Show dialog and return user choice"""
        self.dialog.wait_window()
        return self.result


class UpdateProgressDialog:
    """Progress dialog for downloading updates"""

    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Downloading Update - Clean Sheet")
        self.dialog.geometry("450x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)

        self._create_widgets()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Force dialog to appear
        self.dialog.deiconify()
        self.dialog.lift()
        self.dialog.focus_force()
        self.dialog.grab_set()

    def _create_widgets(self):
        """Create progress widgets"""
        tk.Label(
            self.dialog,
            text="Downloading Clean Sheet update...",
            font=("Segoe UI", 11)
        ).pack(pady=20)

        self.progress_bar = ttk.Progressbar(
            self.dialog,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=10)

        self.status_label = tk.Label(
            self.dialog,
            text="0%",
            font=("Segoe UI", 9)
        )
        self.status_label.pack()

    def update_progress(self, downloaded, total):
        """Update progress bar and status"""
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.progress_bar['value'] = percent

            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            status_text = f"{percent}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)"
            self.status_label.config(text=status_text)

        self.dialog.update()

    def close(self):
        """Close the dialog"""
        self.dialog.destroy()
