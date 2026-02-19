"""
AutocompleteCombobox – a ttk.Combobox subclass that filters its values list
as the user types.

Unlike SearchableCombobox (which wraps ttk.Combobox in a ttk.Frame),
this is a *direct* subclass, so it can be placed anywhere a normal
ttk.Combobox can be placed without extra frame-level focus-propagation
issues (important inside scrolled Canvas windows).

Usage::

    cb = AutocompleteCombobox(parent, options=["Alpha", "Beta", "Gamma"], width=32)
    cb.set("Beta")
    value = cb.get()   # "Beta"

Behaviour:
- state="normal" so the user can type directly.
- On each <KeyRelease> the values list is narrowed to entries whose text
  contains the typed substring (case-insensitive).
- "(blank)" is always the first item and is never filtered out.
- Navigation / modifier keys (Up, Down, Tab, Return, Escape, …) do NOT
  trigger re-filtering so arrow-key browsing still works.
- Selecting an option via the dropdown (<<ComboboxSelected>>) or pressing
  Return confirms the value and restores the full values list.
- On <FocusOut> the current text is validated; if it is not a known option
  it is reverted to the last confirmed value (or "(blank)").
- event_generate("<Down>") is intentionally NOT called from _filter_options:
  opening the popup moves keyboard focus to the Listbox Toplevel which
  triggers <FocusOut> on this entry and would immediately revert typed text.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List


_BLANK = "(blank)"

# Keys that must NOT trigger re-filtering.
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


class AutocompleteCombobox(ttk.Combobox):
    """
    Drop-in ttk.Combobox replacement with type-to-filter behaviour.

    Parameters
    ----------
    options : list[str]
        Full set of choices (must NOT include "(blank)"; it is prepended
        automatically).
    **kwargs
        Forwarded to ttk.Combobox (e.g. ``width``, ``font``).
    """

    def __init__(self, parent, options: List[str], **kwargs):
        # Build the full internal options list with blank at position 0.
        self._all_options: List[str] = [_BLANK] + [
            o for o in options if o != _BLANK
        ]
        self._confirmed: str = _BLANK
        self._inhibit = False   # guard against recursive filter triggers

        # Default to state="normal" so the entry is typeable.
        kwargs.setdefault("state", "normal")
        kwargs.setdefault("font", ("Segoe UI", 9))

        super().__init__(parent, values=self._all_options, **kwargs)

        # Seed the StringVar used internally by ttk.Combobox.
        super().set(_BLANK)

        self.bind("<KeyRelease>",        self._on_key_release)
        self.bind("<<ComboboxSelected>>", self._on_select)
        self.bind("<FocusOut>",          self._on_focus_out)
        self.bind("<Return>",            self._on_return)
        self.bind("<KP_Enter>",          self._on_return)
        self.bind("<Escape>",            self._on_escape)
        # Ensure we get keyboard focus when clicked so typing always works.
        self.bind("<Button-1>",          lambda e: self.focus_set())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set(self, value: str) -> None:
        """Set current value without triggering a filter update."""
        self._inhibit = True
        super().set(value)
        self._confirmed = value
        self["values"] = self._all_options
        self._inhibit = False

    # get() is inherited from ttk.Combobox unchanged.

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_key_release(self, event=None) -> None:
        if self._inhibit:
            return
        if event is not None and event.keysym in _NAV_KEYS:
            return
        self._filter_options()

    def _filter_options(self) -> None:
        """Narrow the values list to items matching the typed substring."""
        query = self.get().lower().strip()

        if not query or query == _BLANK.lower():
            filtered = self._all_options
        else:
            filtered = [_BLANK] + [
                o for o in self._all_options[1:]
                if query in o.lower()
            ]

        self._inhibit = True
        self["values"] = filtered
        self._inhibit = False
        # NOTE: We intentionally do NOT call event_generate("<Down>") here.
        # Opening the popup Listbox moves keyboard focus away from this entry,
        # which triggers <FocusOut> and would immediately revert the typed text.

    def _on_select(self, _event=None) -> None:
        """Confirm the selected value and restore the full list."""
        self._confirmed = self.get()
        self._inhibit = True
        self["values"] = self._all_options
        self._inhibit = False

    def _on_focus_out(self, _event=None) -> None:
        """Revert to last confirmed value if the current text is not valid."""
        current = self.get()
        if current not in self._all_options:
            self._inhibit = True
            super().set(self._confirmed)
            self["values"] = self._all_options
            self._inhibit = False
        else:
            self._confirmed = current
            self._inhibit = True
            self["values"] = self._all_options
            self._inhibit = False

    def _on_return(self, _event=None) -> None:
        """Confirm on Enter / KP_Enter."""
        current = self.get()
        if current in self._all_options:
            self._confirmed = current
        self._inhibit = True
        self["values"] = self._all_options
        self._inhibit = False

    def _on_escape(self, _event=None) -> None:
        """Revert to last confirmed value."""
        self._inhibit = True
        super().set(self._confirmed)
        self["values"] = self._all_options
        self._inhibit = False
