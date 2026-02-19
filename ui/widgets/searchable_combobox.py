"""
SearchableCombobox – a Combobox that filters its dropdown as the user types.

Usage::

    cb = SearchableCombobox(parent, options=["Alpha", "Beta", "Gamma"], width=30)
    cb.set("Beta")
    value = cb.get()        # "Beta"

Behaviour:
- The internal Entry is always editable (state="normal").
- On each <KeyRelease> the dropdown values are narrowed to options whose
  text contains the typed query (case-insensitive substring).
- "(blank)" is kept as the FIRST item and never filtered out.
- Selecting an option (keyboard or mouse) freezes the value and restores
  the full option list so the next opening shows everything.
- Arrow-key / Tab navigation do not trigger re-filtering.
- On FocusOut the current text is validated; if it doesn't match any known
  option it is reverted to the previous confirmed value (or "(blank)").
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List, Optional


_BLANK = "(blank)"

# Key symbols that should NOT trigger a filter update (navigation / modifiers)
_NAV_KEYS = frozenset({
    "Up", "Down", "Left", "Right", "Prior", "Next", "Home", "End",
    "Tab", "ISO_Left_Tab",
    "Shift_L", "Shift_R", "Control_L", "Control_R",
    "Alt_L", "Alt_R", "Meta_L", "Meta_R",
    "Super_L", "Super_R", "Hyper_L", "Hyper_R",
    "Caps_Lock", "Num_Lock", "Scroll_Lock",
    "Return", "KP_Enter", "Escape",
    "F1", "F2", "F3", "F4", "F5", "F6",
    "F7", "F8", "F9", "F10", "F11", "F12",
})


class SearchableCombobox(ttk.Frame):
    """
    Drop-in replacement for ttk.Combobox with type-to-filter behaviour.

    Parameters
    ----------
    options : list[str]
        The full set of choices (must NOT include "(blank)"; it is prepended
        automatically).
    width : int
        Width hint passed to the inner Combobox.
    **kwargs
        Forwarded to ttk.Frame.
    """

    def __init__(self, parent, options: List[str], width: int = 30, **kwargs):
        super().__init__(parent, **kwargs)

        # Always include blank at position 0
        self._all_options: List[str] = [_BLANK] + [
            o for o in options if o != _BLANK
        ]
        self._confirmed: str = _BLANK   # last user-confirmed value
        self._inhibit_filter = False    # True while programmatically changing value

        self._var = tk.StringVar(value=_BLANK)

        # state="" (normal) – allows the user to type directly into the entry.
        # Do NOT use state="readonly" here; that blocks all keyboard input.
        self._combo = ttk.Combobox(
            self,
            textvariable=self._var,
            values=self._all_options,
            width=width,
            font=("Segoe UI", 9),
            state="normal",
        )
        self._combo.pack(fill="x", expand=True)

        # Use <KeyRelease> to trigger filtering – this fires reliably after the
        # user physically presses a key, unlike a StringVar trace which has
        # focus-detection problems with the internal ttk Entry widget.
        self._combo.bind("<KeyRelease>",        self._on_key_release)
        self._combo.bind("<<ComboboxSelected>>", self._on_select)
        self._combo.bind("<FocusOut>",           self._on_focus_out)
        self._combo.bind("<Return>",             self._on_return)
        self._combo.bind("<KP_Enter>",           self._on_return)
        self._combo.bind("<Escape>",             self._on_escape)

    # ------------------------------------------------------------------
    # Public API (mirrors ttk.Combobox)
    # ------------------------------------------------------------------

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str):
        """Set the widget value without triggering a filter update."""
        self._inhibit_filter = True
        self._var.set(value)
        self._confirmed = value
        # Always restore the full list after a programmatic set
        self._combo["values"] = self._all_options
        self._inhibit_filter = False

    @property
    def textvariable(self) -> tk.StringVar:
        return self._var

    # ------------------------------------------------------------------
    # Internal event handlers
    # ------------------------------------------------------------------

    def _on_key_release(self, event=None):
        """
        Triggered by every physical key release inside the combobox entry.
        Navigation / modifier keys are ignored so arrow-key browsing and
        Tab still work normally.
        """
        if self._inhibit_filter:
            return
        if event is not None and event.keysym in _NAV_KEYS:
            return
        self._filter_options()

    def _filter_options(self):
        """Narrow dropdown values to those matching the current typed query."""
        query = self._var.get().lower().strip()

        if not query or query == _BLANK.lower():
            filtered = self._all_options
        else:
            filtered = [_BLANK] + [
                o for o in self._all_options[1:]
                if query in o.lower()
            ]

        self._inhibit_filter = True
        self._combo["values"] = filtered
        self._inhibit_filter = False

    def _on_select(self, _event=None):
        """User chose an item from the dropdown list."""
        self._confirmed = self._var.get()
        # Restore full list so the next dropdown open shows everything
        self._inhibit_filter = True
        self._combo["values"] = self._all_options
        self._inhibit_filter = False

    def _on_focus_out(self, _event=None):
        """Validate on blur; revert to last confirmed value if text is unrecognised."""
        current = self._var.get()
        if current not in self._all_options:
            self._inhibit_filter = True
            self._var.set(self._confirmed)
            self._combo["values"] = self._all_options
            self._inhibit_filter = False
        else:
            self._confirmed = current
            self._inhibit_filter = True
            self._combo["values"] = self._all_options
            self._inhibit_filter = False

    def _on_return(self, _event=None):
        """Confirm on Enter / KP_Enter."""
        current = self._var.get()
        if current in self._all_options:
            self._confirmed = current
        self._inhibit_filter = True
        self._combo["values"] = self._all_options
        self._inhibit_filter = False

    def _on_escape(self, _event=None):
        """Cancel – revert to last confirmed value."""
        self._inhibit_filter = True
        self._var.set(self._confirmed)
        self._combo["values"] = self._all_options
        self._inhibit_filter = False
