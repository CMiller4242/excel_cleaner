"""
SearchableCombobox – a Combobox that filters its dropdown as the user types.

Usage::

    cb = SearchableCombobox(parent, options=["Alpha", "Beta", "Gamma"], width=30)
    cb.set("Beta")
    value = cb.get()        # "Beta"

Behaviour:
- The internal Entry is always editable.
- On each KeyRelease the dropdown values are narrowed to options whose
  text contains the typed query (case-insensitive substring).
- "(blank)" is kept as the FIRST item and never filtered out.
- Selecting an option (keyboard or mouse) freezes the value and restores
  the full option list so the next opening shows everything.
- Arrow-key navigation inside the dropdown works normally.
- On FocusOut the current text is validated; if it doesn't match any option
  it is replaced by the previous confirmed value (or "(blank)").
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List, Optional


_BLANK = "(blank)"


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

        self._var = tk.StringVar(value=_BLANK)
        self._var.trace_add("write", self._on_var_write)
        self._inhibit_filter = False     # set True while we're programmatically updating

        self._combo = ttk.Combobox(
            self,
            textvariable=self._var,
            values=self._all_options,
            width=width,
            font=("Segoe UI", 9),
        )
        self._combo.pack(fill="x", expand=True)
        self._combo.bind("<<ComboboxSelected>>", self._on_select)
        self._combo.bind("<FocusOut>",           self._on_focus_out)
        self._combo.bind("<Return>",             self._on_return)
        self._combo.bind("<Escape>",             self._on_escape)

    # ------------------------------------------------------------------
    # Public API (same as ttk.Combobox)
    # ------------------------------------------------------------------

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str):
        """Set the widget value without triggering filter."""
        self._inhibit_filter = True
        self._var.set(value)
        self._confirmed = value
        self._inhibit_filter = False

    @property
    def textvariable(self) -> tk.StringVar:
        return self._var

    # ------------------------------------------------------------------
    # Internal event handlers
    # ------------------------------------------------------------------

    def _on_var_write(self, *_):
        """Called every time the StringVar changes (including user typing)."""
        if self._inhibit_filter:
            return
        # Only filter when the widget has focus (not on programmatic set)
        try:
            focused = self._combo.focus_displayof() == self._combo.winfo_toplevel().focus_get()
        except Exception:
            focused = False

        if focused:
            self._filter_options()

    def _filter_options(self):
        """Narrow dropdown values to those matching the current query."""
        query = self._var.get().lower().strip()

        if not query or query == _BLANK.lower():
            filtered = self._all_options
        else:
            filtered = [_BLANK] + [
                o for o in self._all_options[1:]   # skip "(blank)" slot
                if query in o.lower()
            ]

        self._inhibit_filter = True
        self._combo["values"] = filtered
        self._inhibit_filter = False

        # Open the dropdown if there are results and user typed something
        if len(filtered) > 1 and query:
            try:
                self._combo.event_generate("<Down>")
            except Exception:
                pass

    def _on_select(self, _event=None):
        """User picked an item from the dropdown."""
        self._confirmed = self._var.get()
        # Restore full list so next opening shows everything
        self._inhibit_filter = True
        self._combo["values"] = self._all_options
        self._inhibit_filter = False

    def _on_focus_out(self, _event=None):
        """Validate on blur – revert to confirmed value if text is unrecognised."""
        current = self._var.get()
        if current not in self._all_options:
            # Partial or unrecognised text – revert
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
        """Confirm on Enter key."""
        current = self._var.get()
        if current in self._all_options:
            self._confirmed = current
        self._inhibit_filter = True
        self._combo["values"] = self._all_options
        self._inhibit_filter = False

    def _on_escape(self, _event=None):
        """Cancel – revert to last confirmed."""
        self._inhibit_filter = True
        self._var.set(self._confirmed)
        self._combo["values"] = self._all_options
        self._inhibit_filter = False
