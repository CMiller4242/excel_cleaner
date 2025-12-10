"""
Scrollable Frame Widget for Operation Dialogs
Provides a reusable scrollable container for operation parameter dialogs
"""
import tkinter as tk
from tkinter import ttk


class ScrollableOperationFrame(ttk.Frame):
    """
    A scrollable frame widget designed for operation parameter dialogs.

    This widget creates a canvas with a scrollbar that contains a frame
    where content can be added. The scrollbar only appears when needed.

    Usage:
        scrollable = ScrollableOperationFrame(parent)
        scrollable.pack(fill="both", expand=True)

        # Add widgets to scrollable.scroll_frame instead of parent
        ttk.Label(scrollable.scroll_frame, text="Content").pack()
    """

    def __init__(self, parent, *args, **kwargs):
        """
        Initialize the scrollable frame.

        Args:
            parent: Parent widget
            *args: Additional positional arguments for ttk.Frame
            **kwargs: Additional keyword arguments for ttk.Frame
        """
        super().__init__(parent, *args, **kwargs)

        # Create canvas for scrolling
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg='white')

        # Create vertical scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        # Create the frame that will hold the content
        self.scroll_frame = ttk.Frame(self.canvas)

        # Bind the scroll_frame's configure event to update scroll region
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self._on_frame_configure()
        )

        # Create window in canvas for the scroll_frame
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scroll_frame,
            anchor="nw"
        )

        # Configure canvas to use scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind canvas resize to update window width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Enable mousewheel scrolling
        self._bind_mousewheel()

    def _on_frame_configure(self):
        """Update the scroll region when the frame size changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Show/hide scrollbar based on whether content fits
        bbox = self.canvas.bbox("all")
        if bbox:
            content_height = bbox[3] - bbox[1]
            canvas_height = self.canvas.winfo_height()
            if content_height > canvas_height:
                self.scrollbar.pack(side="right", fill="y")
            else:
                self.scrollbar.pack_forget()

    def _on_canvas_configure(self, event):
        """Update the canvas window width when canvas is resized"""
        # Make the scroll_frame width match the canvas width
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _bind_mousewheel(self):
        """Enable mousewheel scrolling when mouse is over the widget"""
        def _on_mousewheel(event):
            # Scroll the canvas
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")

        # Bind when mouse enters, unbind when it leaves
        self.scroll_frame.bind('<Enter>', _bind_to_mousewheel)
        self.scroll_frame.bind('<Leave>', _unbind_from_mousewheel)

    def scroll_to_top(self):
        """Scroll to the top of the content"""
        self.canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        """Scroll to the bottom of the content"""
        self.canvas.yview_moveto(1)

    def get_content_frame(self):
        """
        Get the frame where content should be added.

        Returns:
            The scroll_frame where widgets should be added
        """
        return self.scroll_frame
