"""
Progress Dialog for Long-Running Operations

Shows progress bar, status message, and cancel button.
"""

import tkinter as tk
from tkinter import ttk


class ProgressDialog:
    """
    Modal progress dialog with progress bar and cancel button.
    """

    def __init__(self, parent, title="Processing", cancelable=True):
        """
        Initialize progress dialog.

        Args:
            parent: Parent window
            title: Dialog title
            cancelable: Whether to show cancel button
        """
        self.parent = parent
        self.cancelled = False
        self.on_cancel = None

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Prevent closing with X button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

        self._create_widgets(cancelable)

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self, cancelable):
        """Create dialog widgets."""
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Status message
        self.status_var = tk.StringVar(value="Processing...")
        status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 11),
            wraplength=440,
            justify=tk.LEFT
        )
        status_label.pack(pady=(0, 20))

        # Progress bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=440
        )
        self.progress_bar.pack(pady=(0, 10))

        # Progress text (e.g., "50%")
        self.progress_text_var = tk.StringVar(value="0%")
        progress_text_label = tk.Label(
            main_frame,
            textvariable=self.progress_text_var,
            font=("Segoe UI", 9),
            fg="gray"
        )
        progress_text_label.pack(pady=(0, 20))

        # Cancel button
        if cancelable:
            self.cancel_button = tk.Button(
                main_frame,
                text="Cancel",
                command=self._on_cancel_click,
                font=("Segoe UI", 10),
                padx=20,
                pady=8
            )
            self.cancel_button.pack()

    def update_progress(self, message=None, current=None, total=None):
        """
        Update progress display.

        Args:
            message: Status message
            current: Current progress value
            total: Total progress value (for calculating percentage)
        """
        if message is not None:
            self.status_var.set(message)

        if current is not None and total is not None and total > 0:
            percent = int((current / total) * 100)
            self.progress_var.set(percent)
            self.progress_text_var.set(f"{percent}%")
        elif current is not None:
            # Direct percentage
            self.progress_var.set(current)
            self.progress_text_var.set(f"{current}%")

        self.dialog.update()

    def set_indeterminate(self):
        """Switch progress bar to indeterminate mode."""
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)

    def set_determinate(self):
        """Switch progress bar to determinate mode."""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')

    def _on_cancel_click(self):
        """Handle cancel button click."""
        self.cancelled = True
        self.cancel_button.config(state=tk.DISABLED, text="Cancelling...")
        if self.on_cancel:
            self.on_cancel()

    def _on_close_attempt(self):
        """Handle attempt to close dialog with X button."""
        # Treat as cancel
        if not self.cancelled:
            self._on_cancel_click()

    def close(self):
        """Close the dialog."""
        try:
            self.dialog.destroy()
        except:
            pass

    def is_cancelled(self):
        """Check if user cancelled."""
        return self.cancelled
