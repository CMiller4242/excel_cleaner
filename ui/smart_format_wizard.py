"""
Smart Format Wizard – Mail File Standard

Five-step modal wizard:
  Step 1 – Confirm target schema + detected column summary
  Step 2 – Mapping review table (searchable comboboxes)
  Step 3 – Summary of missing columns / conflicts
  Step 4 – Operations Builder (dedupe, remove rows, remove blank rows)
  Step 5 – Final review & apply

Supports:
  • Edit mode  – pass existing_config to pre-populate prior selections
  • Preset controls – load/save Smart Format presets from the header
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Dict, List, Optional

from utils.smart_mapping import (
    REQUIRED_SCHEMA, BCC_REQUIRED_SCHEMA, PO_REQUIRED_SCHEMA,
    TYPICALLY_BLANK, BCC_TYPICALLY_BLANK, PO_TYPICALLY_BLANK,
    PO_CONCAT_RULES,
    MappingResult,
    infer_mapping, infer_mapping_bcc, infer_mapping_po,
)
from ui.widgets.autocomplete_combobox import AutocompleteCombobox
from utils.smart_preset_manager import (
    SmartPresetManager, TEMPLATE_ID_MAIL_STANDARD, TEMPLATE_ID_BCC_MAIL,
    TEMPLATE_ID_POST_OFFICE,
)


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

_CONF_COLOR = {
    "high": "#107C10",   # green
    "med":  "#FF8C00",   # orange
    "low":  "#D83B01",   # red
}
_CONF_LABEL = {
    "high": "High",
    "med":  "Med",
    "low":  "Low / None",
}

_DEFAULT_DEDUPE_PRIORITY = [
    "Email Address", "Company", "Address1", "Zip", "Contact",
]
_BCC_DEFAULT_DEDUPE_PRIORITY = [
    "FULLNAME", "COMPANY", "DELADDR", "ZIP+4",
]
_PO_DEFAULT_DEDUPE_PRIORITY = [
    "Contact", "Company", "Address 1", "City, State, Zip",
]


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _fmt_list(items, limit: int = 10) -> str:
    """Return a safe, comma-separated display string from any iterable.

    Converts every item to ``str`` so the function never raises
    ``TypeError: sequence item N: expected str instance, int found``
    when column labels happen to be non-strings (e.g. integer indices
    from a headerless CSV).

    Args:
        items:  Any iterable of column identifiers (may be int, str, …).
        limit:  Maximum number of items to show before appending an
                "…+N more" suffix.  Pass ``None`` to show all.

    Returns:
        A plain string suitable for use in a ``tk.Label``.  Returns
        ``"(none)"`` for falsy / empty input.
    """
    if not items:
        return "(none)"
    lst = [str(x) for x in items]
    if limit is not None and len(lst) > limit:
        return ", ".join(lst[:limit]) + f"  …+{len(lst) - limit} more"
    return ", ".join(lst)


# ---------------------------------------------------------------------------
# Main wizard class
# ---------------------------------------------------------------------------

class SmartFormatWizard:
    """
    Modal wizard that guides the user through mapping a raw DataFrame to the
    24-column mail-file standard.

    Usage::

        wizard = SmartFormatWizard(parent, raw_columns=df.columns.tolist())
        config = wizard.show()   # blocks; returns mapping_config dict or None

    For edit mode (re-opens with prior selections pre-populated)::

        wizard = SmartFormatWizard(parent, raw_columns=df.columns.tolist(),
                                   existing_config=sheet_state.smart_format)

    Result dict (on Apply)::

        {
          "template_id":      "MAIL_STANDARD_V1",
          "column_map":       {target: source_or_None},
          "derivation_plan":  "use_contact"|"build_first_last"|"blank",
          "first_col":        str|None,
          "last_col":         str|None,
          "operations_plan":  {
              "dedupe":                  {"enabled": bool, "keys": [...]},
              "remove_rows_containing":  {"enabled": bool, "columns": [...],
                                          "patterns": str, "match_type": str},
              "remove_blank_rows":       {"enabled": bool, "columns": [...]},
          },
          "preset_name":      str|None,   # if loaded from / saved to a preset
        }
    """

    STEPS = [
        "1. Schema Overview",
        "2. Column Mapping",
        "3. Summary",
        "4. Operations",
        "5. Apply",
    ]

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        parent: tk.Widget,
        raw_columns: List[str],
        existing_config: Optional[Dict] = None,
        schema: Optional[List[str]] = None,
        template_id: Optional[str] = None,
    ):
        self.parent = parent

        # Normalise raw column labels to strings so that downstream UI
        # rendering (str.join, f-strings) never crashes on int/float labels,
        # which can occur when a DataFrame was read without a header row.
        non_str = [c for c in raw_columns if not isinstance(c, str)]
        if non_str:
            import logging as _log
            _log.warning(
                "[SmartFormatWizard] %d non-string column label(s) detected "
                "and coerced to str (sample types: %s).  "
                "First few: %s",
                len(non_str),
                ", ".join(sorted({type(c).__name__ for c in non_str})),
                non_str[:5],
            )
        self.raw_columns: List[str] = [str(c) for c in raw_columns]

        self._result: Optional[Dict] = None
        self.current_step = 0

        # Schema configuration
        if template_id == TEMPLATE_ID_BCC_MAIL or schema is BCC_REQUIRED_SCHEMA:
            self._template_id = TEMPLATE_ID_BCC_MAIL
            self._schema = BCC_REQUIRED_SCHEMA if schema is None else schema
            self._typically_blank = BCC_TYPICALLY_BLANK
            self._dedupe_priority = _BCC_DEFAULT_DEDUPE_PRIORITY
            self.mapping_result: MappingResult = infer_mapping_bcc(self.raw_columns)
        elif template_id == TEMPLATE_ID_POST_OFFICE:
            self._template_id = TEMPLATE_ID_POST_OFFICE
            self._schema = PO_REQUIRED_SCHEMA if schema is None else schema
            self._typically_blank = PO_TYPICALLY_BLANK
            self._dedupe_priority = _PO_DEFAULT_DEDUPE_PRIORITY
            self.mapping_result: MappingResult = infer_mapping_po(self.raw_columns)
        else:
            self._template_id = template_id or TEMPLATE_ID_MAIL_STANDARD
            self._schema = schema if schema is not None else REQUIRED_SCHEMA
            self._typically_blank = TYPICALLY_BLANK
            self._dedupe_priority = _DEFAULT_DEDUPE_PRIORITY
            self.mapping_result: MappingResult = infer_mapping(self.raw_columns)

        # Source options for dropdowns (use the normalised list)
        self._source_options = list(self.raw_columns)   # "(blank)" added by AutocompleteCombobox

        # Per-target widgets for step 2 (AutocompleteCombobox or special mode var)
        self._target_vars: Dict[str, AutocompleteCombobox] = {}
        self._contact_mode_var = tk.StringVar()
        self._first_var = tk.StringVar()
        self._last_var  = tk.StringVar()

        # City/State/Zip sub-component comboboxes (Post Office Mailings schema)
        self._csz_city_cb:  Optional[AutocompleteCombobox] = None
        self._csz_state_cb: Optional[AutocompleteCombobox] = None
        self._csz_zip_cb:   Optional[AutocompleteCombobox] = None

        # Operations builder vars (step 4)
        self._dedupe_enabled      = tk.BooleanVar(value=False)
        self._dedupe_keys_lb: Optional[tk.Listbox] = None

        self._remove_rows_enabled = tk.BooleanVar(value=False)
        self._remove_rows_cols_lb: Optional[tk.Listbox] = None
        self._remove_rows_text    = tk.StringVar()
        self._remove_rows_match   = tk.StringVar(value="contains")

        self._remove_blank_enabled = tk.BooleanVar(value=False)
        self._remove_blank_cols_lb: Optional[tk.Listbox] = None

        # Preset management
        self._preset_manager = SmartPresetManager()
        self._loaded_preset_name: Optional[str] = None

        # Existing config (for edit mode)
        self._existing_config = existing_config

        self._build_dialog()

        # Pre-populate from existing config after widgets are built
        if existing_config:
            self._populate_from_config(existing_config)

    # ------------------------------------------------------------------
    # Dialog construction
    # ------------------------------------------------------------------

    def _build_dialog(self):
        if self._template_id == TEMPLATE_ID_BCC_MAIL:
            _schema_label = "BCC Mail File Config"
        elif self._template_id == TEMPLATE_ID_POST_OFFICE:
            _schema_label = "Post Office Mailings"
        else:
            _schema_label = "Mail File Standard"

        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"✨ Smart Format — {_schema_label}")
        self.dialog.geometry("860x680")
        self.dialog.minsize(720, 540)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)

        # ---- Header ----
        header = tk.Frame(self.dialog, bg="#0078D4", height=56)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"✨  Smart Format — {_schema_label}",
            font=("Segoe UI", 14, "bold"),
            bg="#0078D4", fg="white",
        ).pack(side=tk.LEFT, padx=16, pady=12)

        # Preset buttons (right side of header)
        preset_bar = tk.Frame(header, bg="#0078D4")
        preset_bar.pack(side=tk.RIGHT, padx=12)

        tk.Button(
            preset_bar,
            text="💾 Save Preset",
            font=("Segoe UI", 8),
            bg="#005A9E", fg="white",
            bd=0, padx=8, pady=3,
            cursor="hand2",
            relief="flat",
            activebackground="#004578",
            command=self._save_preset,
        ).pack(side=tk.RIGHT, padx=3)

        tk.Button(
            preset_bar,
            text="📂 Load Preset",
            font=("Segoe UI", 8),
            bg="#005A9E", fg="white",
            bd=0, padx=8, pady=3,
            cursor="hand2",
            relief="flat",
            activebackground="#004578",
            command=self._load_preset,
        ).pack(side=tk.RIGHT, padx=3)

        # Step indicator
        self._step_label = tk.Label(
            header,
            text="Step 1 of 5",
            font=("Segoe UI", 10),
            bg="#0078D4", fg="#BDD7F5",
        )
        self._step_label.pack(side=tk.RIGHT, padx=16)

        # ---- Button bar (bottom) ----
        btn_bar = tk.Frame(self.dialog, bg="#F3F2F1", bd=0)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(btn_bar, bg="#EDEBE9", height=1).pack(fill=tk.X)

        inner_btns = tk.Frame(btn_bar, bg="#F3F2F1")
        inner_btns.pack(pady=10, padx=16, anchor=tk.E)

        self._cancel_btn = ttk.Button(inner_btns, text="Cancel", width=10,
                                      command=self._on_cancel)
        self._cancel_btn.pack(side=tk.LEFT, padx=4)

        self._back_btn = ttk.Button(inner_btns, text="◀  Back", width=10,
                                    command=self._go_back, state=tk.DISABLED)
        self._back_btn.pack(side=tk.LEFT, padx=4)

        self._next_btn = ttk.Button(inner_btns, text="Next  ▶", width=14,
                                    command=self._go_next)
        self._next_btn.pack(side=tk.LEFT, padx=4)

        # ---- Content area (middle) ----
        self._content = tk.Frame(self.dialog, bg="white")
        self._content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Build all step frames
        self._step_frames = [
            self._build_step1(),
            self._build_step2(),
            self._build_step3(),
            self._build_step4(),
            self._build_step5(),
        ]

        self._show_step(0)

    # ------------------------------------------------------------------
    # Step builders
    # ------------------------------------------------------------------

    def _build_step1(self) -> tk.Frame:
        """Schema overview: target schema list + raw column summary."""
        frame = tk.Frame(self._content, bg="white")

        _step1_title = (
            f"BCC Mail File Config — {len(self._schema)}-Column Schema"
            if self._template_id == TEMPLATE_ID_BCC_MAIL
            else f"Target Schema: {len(self._schema)}-Column Mail File Standard"
        )
        tk.Label(
            frame,
            text=_step1_title,
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#323130",
        ).pack(anchor=tk.W, padx=20, pady=(20, 4))

        n_raw   = len(self.raw_columns)
        n_found = sum(1 for v in self.mapping_result.suggested_map.values() if v)
        n_blank = len(self._schema) - n_found

        tk.Label(
            frame,
            text=(f"Raw file: {n_raw} columns detected  •  "
                  f"{n_found}/{len(self._schema)} target columns auto-matched  •  "
                  f"{n_blank} will be created blank"),
            font=("Segoe UI", 10),
            bg="white", fg="#605E5C",
            wraplength=800, justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=20, pady=(0, 12))

        # Scrollable schema list
        canvas_frame = tk.Frame(frame, bg="white")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        sb = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg="white")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        win = canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))

        hdr = tk.Frame(inner, bg="#F3F2F1")
        hdr.pack(fill=tk.X, pady=(0, 2))
        for txt, w in [("#", 4), ("Target Column", 22), ("Best Match", 28), ("Confidence", 10)]:
            tk.Label(hdr, text=txt, width=w, bg="#F3F2F1",
                     font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=4)

        for idx, target in enumerate(self._schema):
            source = self.mapping_result.suggested_map.get(target)
            conf   = self.mapping_result.confidences.get(target, "low")
            row_bg = "white" if idx % 2 == 0 else "#FAFAFA"
            row = tk.Frame(inner, bg=row_bg)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=str(idx + 1), width=4,  bg=row_bg, font=("Segoe UI", 9), anchor=tk.W).pack(side=tk.LEFT, padx=4)
            tk.Label(row, text=target,        width=22, bg=row_bg, font=("Segoe UI", 9), anchor=tk.W).pack(side=tk.LEFT, padx=4)

            if source == "__derived__":
                src_text = "⚙ Derived from First + Last"
            elif source:
                src_text = source
            else:
                src_text = "— (will create blank)"

            tk.Label(row, text=src_text, width=28, bg=row_bg,
                     font=("Segoe UI", 9), anchor=tk.W,
                     fg="#323130" if source else "#A19F9D").pack(side=tk.LEFT, padx=4)

            conf_color = _CONF_COLOR.get(conf, "#A19F9D") if source else "#A19F9D"
            conf_txt   = _CONF_LABEL.get(conf, conf) if source else "—"
            tk.Label(row, text=conf_txt, width=10, bg=row_bg,
                     font=("Segoe UI", 9), anchor=tk.W,
                     fg=conf_color).pack(side=tk.LEFT, padx=4)

        if self.mapping_result.conflicts:
            note = tk.Frame(frame, bg="#FFF4CE")
            note.pack(fill=tk.X, padx=20, pady=(4, 0))
            tk.Label(
                note,
                text=(f"⚠  {len(self.mapping_result.conflicts)} mapping conflict(s) detected – "
                      f"review in Step 2."),
                font=("Segoe UI", 9),
                bg="#FFF4CE", fg="#7A5C00",
                anchor=tk.W,
            ).pack(anchor=tk.W, padx=8, pady=4)

        return frame

    def _build_step2(self) -> tk.Frame:
        """Mapping review: one row per target column with searchable dropdown."""
        frame = tk.Frame(self._content, bg="white")

        tk.Label(
            frame,
            text="Review and Adjust Column Mapping",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#323130",
        ).pack(anchor=tk.W, padx=20, pady=(20, 2))

        tk.Label(
            frame,
            text="For each target column choose the source column from your file (or '(blank)'). Type to search.",
            font=("Segoe UI", 9),
            bg="white", fg="#605E5C",
        ).pack(anchor=tk.W, padx=20, pady=(0, 10))

        outer = tk.Frame(frame, bg="white")
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 8))

        canvas = tk.Canvas(outer, bg="white", highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        table = tk.Frame(canvas, bg="white")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        win = canvas.create_window((0, 0), window=table, anchor=tk.NW)
        table.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))

        # Header
        hdr = tk.Frame(table, bg="#F3F2F1")
        hdr.pack(fill=tk.X, pady=(0, 2))
        tk.Label(hdr, text="Target Column", width=20, bg="#F3F2F1", font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=6)
        tk.Label(hdr, text="Source Column",  width=32, bg="#F3F2F1", font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=6)
        tk.Label(hdr, text="Conf",           width=8,  bg="#F3F2F1", font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=6)
        tk.Label(hdr, text="Note",           width=22, bg="#F3F2F1", font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=6)

        mr = self.mapping_result

        for idx, target in enumerate(self._schema):
            source = mr.suggested_map.get(target)
            conf   = mr.confidences.get(target, "low")
            row_bg = "white" if idx % 2 == 0 else "#FAFAFA"

            row = tk.Frame(table, bg=row_bg)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=target, width=20, bg=row_bg,
                     font=("Segoe UI", 9), anchor=tk.W).pack(side=tk.LEFT, padx=6)

            if target == "Contact" and "Contact" in self._schema:
                self._build_contact_row(row, row_bg)
                continue

            if target == "City, State, Zip" and "City, State, Zip" in self._schema:
                self._build_csz_row(row, row_bg)
                continue

            # Searchable combobox
            cb = AutocompleteCombobox(row, options=self._source_options, width=32)

            if source and source != "__derived__" and source in self.raw_columns:
                cb.set(source)
            else:
                cb.set("(blank)")

            cb.pack(side=tk.LEFT, padx=6)
            self._target_vars[target] = cb

            conf_color = _CONF_COLOR.get(conf, "#A19F9D") if source else "#A19F9D"
            conf_txt   = _CONF_LABEL.get(conf, "") if source else "—"
            tk.Label(row, text=conf_txt, width=8, bg=row_bg,
                     font=("Segoe UI", 9), fg=conf_color, anchor=tk.W).pack(side=tk.LEFT, padx=6)

            conflict_for = [c for c in mr.conflicts if c["target_col"] == target]
            note_txt = ""
            if conflict_for:
                other = [x for x in conflict_for[0]["candidates"] if x != source]
                note_txt = f"⚠ conflict with: {', '.join(other[:2])}"
            elif target in self._typically_blank and not source:
                note_txt = "Optional – will be blank"

            if note_txt:
                tk.Label(row, text=note_txt, width=28, bg=row_bg,
                         font=("Segoe UI", 8),
                         fg="#7A5C00" if "conflict" in note_txt else "#A19F9D",
                         anchor=tk.W).pack(side=tk.LEFT, padx=6)

        return frame

    def _build_contact_row(self, row: tk.Frame, row_bg: str):
        """Contact row with mode selector (special case)."""
        mr = self.mapping_result

        if mr.derivation_plan == "use_contact":
            initial_mode = "Use existing Contact column"
        elif mr.derivation_plan == "build_first_last":
            initial_mode = "Build from First + Last Name"
        else:
            initial_mode = "(blank)"

        self._contact_mode_var.set(initial_mode)

        modes = [
            "Use existing Contact column",
            "Build from First + Last Name",
            "(blank)",
        ]

        cb = ttk.Combobox(row, textvariable=self._contact_mode_var,
                          values=modes, width=30, state="readonly",
                          font=("Segoe UI", 9))
        cb.pack(side=tk.LEFT, padx=6)

        first_txt = mr.first_col or "(not found)"
        last_txt  = mr.last_col  or "(not found)"
        self._first_var.set(first_txt)
        self._last_var.set(last_txt)

        tk.Label(
            row,
            text=f"First='{first_txt}'  Last='{last_txt}'",
            font=("Segoe UI", 8), bg=row_bg, fg="#605E5C",
        ).pack(side=tk.LEFT, padx=6)

    def _build_csz_row(self, row: tk.Frame, row_bg: str):
        """City, State, Zip row with three sub-source comboboxes."""
        mr = self.mapping_result

        sub_frame = tk.Frame(row, bg=row_bg)
        sub_frame.pack(side=tk.LEFT, padx=6)

        for label_txt, key, attr in [
            ("City:",  "__csz_city__",  "_csz_city_cb"),
            ("State:", "__csz_state__", "_csz_state_cb"),
            ("Zip:",   "__csz_zip__",   "_csz_zip_cb"),
        ]:
            src = mr.suggested_map.get(key)
            tk.Label(
                sub_frame, text=label_txt,
                font=("Segoe UI", 8, "bold"), bg=row_bg,
            ).pack(side=tk.LEFT, padx=(4, 2))
            cb = AutocompleteCombobox(sub_frame, options=self._source_options, width=14)
            if src and src in self.raw_columns:
                cb.set(src)
            else:
                cb.set("(blank)")
            cb.pack(side=tk.LEFT, padx=(0, 4))
            setattr(self, attr, cb)

        tk.Label(
            row,
            text="→ built as 'City, State Zip'",
            font=("Segoe UI", 8, "italic"),
            bg=row_bg, fg="#605E5C",
        ).pack(side=tk.LEFT, padx=6)

    def _build_step3(self) -> tk.Frame:
        """Summary of missing columns and conflicts (populated when shown)."""
        frame = tk.Frame(self._content, bg="white")
        self._step3_frame = frame
        return frame

    def _populate_step3(self):
        """Rebuild step 3 from current Step 2 selections."""
        frame = self._step3_frame
        for w in frame.winfo_children():
            w.destroy()

        tk.Label(
            frame,
            text="Mapping Summary",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#323130",
        ).pack(anchor=tk.W, padx=20, pady=(20, 4))

        col_map, derivation_plan, first_col, last_col = self._collect_mapping()

        blank_targets  = [t for t, s in col_map.items() if not s]
        mapped_targets = [t for t, s in col_map.items() if s]
        conflicts = self.mapping_result.conflicts
        dropped   = self.mapping_result.dropped_columns

        lines = [
            f"✓  {len(mapped_targets)} columns mapped from source",
            f"○  {len(blank_targets)} required columns will be created blank",
        ]
        if derivation_plan == "build_first_last":
            lines.append(f"⚙  Contact will be derived: First='{first_col}'  Last='{last_col}'")
        if conflicts:
            lines.append(f"⚠  {len(conflicts)} mapping conflict(s) (auto-resolved)")
        if dropped:
            lines.append(f"✂  {len(dropped)} extra source column(s) will be dropped")

        for line in lines:
            fg = "#7A5C00" if line.startswith("⚠") else "#323130"
            tk.Label(frame, text=line, font=("Segoe UI", 10),
                     bg="white", fg=fg, anchor=tk.W).pack(anchor=tk.W, padx=20, pady=2)

        if blank_targets:
            tk.Label(
                frame,
                text="Blank columns: " + _fmt_list(blank_targets, limit=None),
                font=("Segoe UI", 9), bg="white", fg="#605E5C",
                wraplength=790, justify=tk.LEFT, anchor=tk.W,
            ).pack(anchor=tk.W, padx=32, pady=(0, 4))

        if dropped:
            tk.Label(
                frame,
                text="Dropped: " + _fmt_list(dropped),
                font=("Segoe UI", 9), bg="white", fg="#A19F9D",
                wraplength=790, justify=tk.LEFT, anchor=tk.W,
            ).pack(anchor=tk.W, padx=32, pady=(0, 8))

        tk.Label(
            frame,
            text="Click 'Next' to configure optional clean-up operations.",
            font=("Segoe UI", 9, "italic"),
            bg="white", fg="#605E5C",
        ).pack(anchor=tk.W, padx=20, pady=(8, 0))

    def _build_step4(self) -> tk.Frame:
        """Operations Builder step."""
        frame = tk.Frame(self._content, bg="white")

        tk.Label(
            frame,
            text="Operations Builder (Optional)",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#323130",
        ).pack(anchor=tk.W, padx=20, pady=(20, 2))

        tk.Label(
            frame,
            text="Choose clean-up operations to run automatically after applying the mail standard.",
            font=("Segoe UI", 9),
            bg="white", fg="#605E5C",
        ).pack(anchor=tk.W, padx=20, pady=(0, 10))

        # Scrollable container for the ops
        outer = tk.Frame(frame, bg="white")
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 8))

        canvas = tk.Canvas(outer, bg="white", highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg="white")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        win = canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))

        # ---- 1. Dedupe ----
        self._dedupe_keys_lb = self._build_dedupe_section(inner)

        ttk.Separator(inner, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # ---- 2. Remove rows containing ----
        self._remove_rows_cols_lb = self._build_remove_rows_section(inner)

        ttk.Separator(inner, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # ---- 3. Remove blank rows ----
        self._remove_blank_cols_lb = self._build_remove_blank_section(inner)

        return frame

    def _build_dedupe_section(self, parent: tk.Frame) -> tk.Listbox:
        """Build the Dedupe sub-section in step 4. Returns the keys Listbox."""
        section = tk.Frame(parent, bg="white")
        section.pack(fill=tk.X, pady=4)

        hdr = tk.Frame(section, bg="white")
        hdr.pack(fill=tk.X)
        tk.Checkbutton(
            hdr,
            text="Remove Duplicate Rows (Dedupe)",
            variable=self._dedupe_enabled,
            font=("Segoe UI", 10, "bold"),
            bg="white", fg="#323130",
            command=lambda: self._toggle_section(body, self._dedupe_enabled),
        ).pack(side=tk.LEFT)

        body = tk.Frame(section, bg="white")
        body.pack(fill=tk.X, padx=20)

        tk.Label(
            body,
            text="Dedupe keys – hold Ctrl/Shift to select multiple:",
            font=("Segoe UI", 9),
            bg="white", fg="#605E5C",
        ).pack(anchor=tk.W, pady=(4, 2))

        lb_frame = tk.Frame(body, bg="white")
        lb_frame.pack(anchor=tk.W)

        sb = ttk.Scrollbar(lb_frame, orient=tk.VERTICAL)
        lb = tk.Listbox(
            lb_frame,
            selectmode=tk.MULTIPLE,
            font=("Segoe UI", 9),
            height=6,
            width=36,
            yscrollcommand=sb.set,
            exportselection=False,
        )
        sb.config(command=lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.pack(side=tk.LEFT)

        # Populate with target schema columns
        for col in self._schema:
            lb.insert(tk.END, col)

        # Default selection: priority columns if they're in schema
        for i, col in enumerate(self._schema):
            if col in self._dedupe_priority:
                lb.selection_set(i)

        # Start disabled
        self._toggle_section(body, self._dedupe_enabled)
        return lb

    def _build_remove_rows_section(self, parent: tk.Frame) -> tk.Listbox:
        """Build Remove Rows Containing sub-section. Returns the columns Listbox."""
        section = tk.Frame(parent, bg="white")
        section.pack(fill=tk.X, pady=4)

        hdr = tk.Frame(section, bg="white")
        hdr.pack(fill=tk.X)
        tk.Checkbutton(
            hdr,
            text="Remove Rows Containing (text filter)",
            variable=self._remove_rows_enabled,
            font=("Segoe UI", 10, "bold"),
            bg="white", fg="#323130",
            command=lambda: self._toggle_section(body, self._remove_rows_enabled),
        ).pack(side=tk.LEFT)

        body = tk.Frame(section, bg="white")
        body.pack(fill=tk.X, padx=20)

        # Column selector
        tk.Label(body, text="Target column(s):", font=("Segoe UI", 9),
                 bg="white", fg="#605E5C").pack(anchor=tk.W, pady=(4, 2))

        lb_frame = tk.Frame(body, bg="white")
        lb_frame.pack(anchor=tk.W)

        sb = ttk.Scrollbar(lb_frame, orient=tk.VERTICAL)
        lb = tk.Listbox(
            lb_frame,
            selectmode=tk.MULTIPLE,
            font=("Segoe UI", 9),
            height=4,
            width=36,
            yscrollcommand=sb.set,
            exportselection=False,
        )
        sb.config(command=lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.pack(side=tk.LEFT)

        for col in self._schema:
            lb.insert(tk.END, col)

        # Text entry
        text_row = tk.Frame(body, bg="white")
        text_row.pack(fill=tk.X, pady=(6, 2))
        tk.Label(text_row, text="Remove rows where column contains:",
                 font=("Segoe UI", 9), bg="white", fg="#605E5C").pack(side=tk.LEFT)

        text_frame = tk.Frame(body, bg="white")
        text_frame.pack(fill=tk.X, pady=(0, 4))
        tk.Entry(text_frame, textvariable=self._remove_rows_text,
                 font=("Segoe UI", 9), width=40).pack(side=tk.LEFT)
        tk.Label(text_frame, text=" (comma-separated)",
                 font=("Segoe UI", 8), bg="white", fg="#A19F9D").pack(side=tk.LEFT)

        # Match type
        match_row = tk.Frame(body, bg="white")
        match_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(match_row, text="Match type:", font=("Segoe UI", 9),
                 bg="white", fg="#605E5C").pack(side=tk.LEFT)
        for val, lbl in [("contains", "Contains"), ("equals", "Equals (exact)"),
                          ("startswith", "Starts with")]:
            tk.Radiobutton(match_row, text=lbl, variable=self._remove_rows_match,
                           value=val, bg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=6)

        self._toggle_section(body, self._remove_rows_enabled)
        return lb

    def _build_remove_blank_section(self, parent: tk.Frame) -> tk.Listbox:
        """Build Remove Blank Rows sub-section. Returns the columns Listbox."""
        section = tk.Frame(parent, bg="white")
        section.pack(fill=tk.X, pady=4)

        hdr = tk.Frame(section, bg="white")
        hdr.pack(fill=tk.X)
        tk.Checkbutton(
            hdr,
            text="Remove Blank Rows",
            variable=self._remove_blank_enabled,
            font=("Segoe UI", 10, "bold"),
            bg="white", fg="#323130",
            command=lambda: self._toggle_section(body, self._remove_blank_enabled),
        ).pack(side=tk.LEFT)

        body = tk.Frame(section, bg="white")
        body.pack(fill=tk.X, padx=20)

        tk.Label(
            body,
            text="Remove row only if ALL of these columns are blank:",
            font=("Segoe UI", 9), bg="white", fg="#605E5C",
        ).pack(anchor=tk.W, pady=(4, 2))

        lb_frame = tk.Frame(body, bg="white")
        lb_frame.pack(anchor=tk.W)

        sb = ttk.Scrollbar(lb_frame, orient=tk.VERTICAL)
        lb = tk.Listbox(
            lb_frame,
            selectmode=tk.MULTIPLE,
            font=("Segoe UI", 9),
            height=4,
            width=36,
            yscrollcommand=sb.set,
            exportselection=False,
        )
        sb.config(command=lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.pack(side=tk.LEFT)

        for col in self._schema:
            lb.insert(tk.END, col)

        self._toggle_section(body, self._remove_blank_enabled)
        return lb

    @staticmethod
    def _toggle_section(body: tk.Frame, var: tk.BooleanVar):
        """Enable/disable all widgets inside a section body frame."""
        state = tk.NORMAL if var.get() else tk.DISABLED
        for child in body.winfo_children():
            try:
                child.config(state=state)
            except tk.TclError:
                pass
            # Recurse into sub-frames
            for grandchild in child.winfo_children():
                try:
                    grandchild.config(state=state)
                except tk.TclError:
                    pass

    def _build_step5(self) -> tk.Frame:
        """Final apply confirmation (populated dynamically)."""
        frame = tk.Frame(self._content, bg="white")
        self._step5_frame = frame
        return frame

    def _populate_step5(self):
        """Rebuild step 5 based on current selections from steps 2 & 4."""
        frame = self._step5_frame
        for w in frame.winfo_children():
            w.destroy()

        tk.Label(
            frame,
            text="Review & Apply",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#323130",
        ).pack(anchor=tk.W, padx=20, pady=(20, 4))

        col_map, derivation_plan, first_col, last_col = self._collect_mapping()
        ops_plan = self._collect_ops_plan()

        blank_targets  = [t for t, s in col_map.items() if not s]
        mapped_targets = [t for t, s in col_map.items() if s]
        conflicts = self.mapping_result.conflicts
        dropped   = self.mapping_result.dropped_columns

        # Mapping summary
        tk.Label(frame, text="Mapping:", font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#323130").pack(anchor=tk.W, padx=20, pady=(8, 2))

        lines = [
            f"  ✓  {len(mapped_targets)} columns mapped from source",
            f"  ○  {len(blank_targets)} required columns will be created blank",
        ]
        if derivation_plan == "build_first_last":
            lines.append(f"  ⚙  Contact derived from First ('{first_col}') + Last ('{last_col}')")
        if conflicts:
            lines.append(f"  ⚠  {len(conflicts)} conflict(s) auto-resolved")
        if dropped:
            lines.append(f"  ✂  {len(dropped)} extra column(s) will be dropped")

        for line in lines:
            fg = "#7A5C00" if "⚠" in line else "#323130"
            tk.Label(frame, text=line, font=("Segoe UI", 9),
                     bg="white", fg=fg, anchor=tk.W).pack(anchor=tk.W, padx=20, pady=1)

        # Operations summary
        tk.Label(frame, text="Operations to run after mapping:",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#323130").pack(anchor=tk.W, padx=20, pady=(10, 2))

        ops_lines = []
        if ops_plan.get("dedupe", {}).get("enabled"):
            keys = ops_plan["dedupe"].get("keys", [])
            ops_lines.append(f"  ✓  Dedupe  (keys: {_fmt_list(keys) if keys else 'none selected'})")

        rrc = ops_plan.get("remove_rows_containing", {})
        if rrc.get("enabled"):
            cols = rrc.get("columns", [])
            pats = rrc.get("patterns", "")
            ops_lines.append(f"  ✓  Remove rows containing '{pats}' in: {_fmt_list(cols) if cols else 'no columns'}")

        rbr = ops_plan.get("remove_blank_rows", {})
        if rbr.get("enabled"):
            cols = rbr.get("columns", [])
            ops_lines.append(f"  ✓  Remove blank rows  (columns: {_fmt_list(cols) if cols else 'none selected'})")

        if not ops_lines:
            ops_lines.append("  (none selected)")

        for line in ops_lines:
            tk.Label(frame, text=line, font=("Segoe UI", 9),
                     bg="white", fg="#323130", anchor=tk.W).pack(anchor=tk.W, padx=20, pady=1)

        if self._loaded_preset_name:
            tk.Label(
                frame,
                text=f'📂 Preset loaded: "{self._loaded_preset_name}"',
                font=("Segoe UI", 9, "italic"),
                bg="white", fg="#605E5C",
            ).pack(anchor=tk.W, padx=20, pady=(6, 0))

        tk.Label(
            frame,
            text="\nClick 'Apply' to transform the active sheet. Reversible via Undo.",
            font=("Segoe UI", 9, "italic"),
            bg="white", fg="#605E5C",
        ).pack(anchor=tk.W, padx=20, pady=(4, 0))

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _show_step(self, step: int):
        for f in self._step_frames:
            f.pack_forget()
        self._step_frames[step].pack(fill=tk.BOTH, expand=True)
        self._step_label.config(text=f"Step {step + 1} of {len(self.STEPS)}")

        self._back_btn.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
        if step == len(self.STEPS) - 1:
            self._next_btn.config(text="✔  Apply")
        else:
            self._next_btn.config(text="Next  ▶")

    def _go_next(self):
        if self.current_step == len(self.STEPS) - 1:
            self._apply()
            return

        # On leaving step 2 → populate step 3 summary
        if self.current_step == 1:
            self._populate_step3()

        # On leaving step 4 → populate step 5 final review
        if self.current_step == 3:
            self._populate_step5()

        self.current_step += 1
        self._show_step(self.current_step)

    def _go_back(self):
        self.current_step -= 1
        self._show_step(self.current_step)

    def _on_cancel(self):
        self._result = None
        self.dialog.destroy()

    # ------------------------------------------------------------------
    # Collect mapping from Step 2 widgets
    # ------------------------------------------------------------------

    def _collect_mapping(self):
        """Read Step 2 widgets; return (col_map, derivation_plan, first_col, last_col)."""
        col_map: Dict[str, Optional[str]] = {}

        for target in self._schema:
            if target == "Contact" and "Contact" in self._schema:
                continue  # handled separately below
            if target == "City, State, Zip" and "City, State, Zip" in self._schema:
                continue  # computed field — handled separately below
            cb = self._target_vars.get(target)
            if cb is None:
                col_map[target] = None
                continue
            val = cb.get()
            col_map[target] = None if val in ("(blank)", "") else val

        # Contact derivation — Mail Standard only
        if "Contact" in self._schema:
            mode = self._contact_mode_var.get()
            mr = self.mapping_result
            if mode == "Use existing Contact column":
                derivation_plan = "use_contact"
                contact_src = mr.suggested_map.get("Contact")
                if contact_src == "__derived__" or not contact_src:
                    contact_src = None
                    for rc in self.raw_columns:
                        from utils.smart_mapping import normalize_header
                        if normalize_header(rc) in {"contact", "contact name", "full name"}:
                            contact_src = rc
                            break
                col_map["Contact"] = contact_src
                first_col = mr.first_col
                last_col  = mr.last_col
            elif mode == "Build from First + Last Name":
                derivation_plan = "build_first_last"
                col_map["Contact"] = "__derived__"
                first_col = mr.first_col
                last_col  = mr.last_col
            else:
                derivation_plan = "blank"
                col_map["Contact"] = None
                first_col = None
                last_col  = None
        else:
            # BCC and other schemas without Contact derivation
            derivation_plan = "blank"
            first_col = None
            last_col  = None

        # City, State, Zip composite field (Post Office schema)
        if "City, State, Zip" in self._schema:
            col_map["City, State, Zip"] = None  # always built via concat_rules, not direct map

        return col_map, derivation_plan, first_col, last_col

    # ------------------------------------------------------------------
    # Collect operations plan from Step 4 widgets
    # ------------------------------------------------------------------

    def _collect_ops_plan(self) -> Dict:
        ops: Dict = {}

        # Dedupe
        if self._dedupe_enabled.get() and self._dedupe_keys_lb:
            sel_indices = self._dedupe_keys_lb.curselection()
            keys = [self._dedupe_keys_lb.get(i) for i in sel_indices]
            ops["dedupe"] = {"enabled": True, "keys": keys}
        else:
            ops["dedupe"] = {"enabled": False, "keys": []}

        # Remove rows containing
        if self._remove_rows_enabled.get() and self._remove_rows_cols_lb:
            sel_indices = self._remove_rows_cols_lb.curselection()
            cols = [self._remove_rows_cols_lb.get(i) for i in sel_indices]
            ops["remove_rows_containing"] = {
                "enabled": True,
                "columns": cols,
                "patterns": self._remove_rows_text.get(),
                "match_type": self._remove_rows_match.get(),
            }
        else:
            ops["remove_rows_containing"] = {
                "enabled": False,
                "columns": [],
                "patterns": "",
                "match_type": "contains",
            }

        # Remove blank rows
        if self._remove_blank_enabled.get() and self._remove_blank_cols_lb:
            sel_indices = self._remove_blank_cols_lb.curselection()
            cols = [self._remove_blank_cols_lb.get(i) for i in sel_indices]
            ops["remove_blank_rows"] = {"enabled": True, "columns": cols}
        else:
            ops["remove_blank_rows"] = {"enabled": False, "columns": []}

        return ops

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def _apply(self):
        col_map, derivation_plan, first_col, last_col = self._collect_mapping()
        ops_plan = self._collect_ops_plan()

        self._result = {
            "template_id":     self._template_id,
            "column_map":      col_map,
            "derivation_plan": derivation_plan,
            "first_col":       first_col,
            "last_col":        last_col,
            "operations_plan": ops_plan,
            "preset_name":     self._loaded_preset_name,
        }

        # City/State/Zip sub-sources (Post Office schema)
        if "City, State, Zip" in self._schema:
            def _cb_val(cb: Optional[AutocompleteCombobox]) -> Optional[str]:
                if cb is None:
                    return None
                v = cb.get()
                return None if v in ("(blank)", "") else v
            self._result["csz_city"]  = _cb_val(self._csz_city_cb)
            self._result["csz_state"] = _cb_val(self._csz_state_cb)
            self._result["csz_zip"]   = _cb_val(self._csz_zip_cb)

        self.dialog.destroy()

    # ------------------------------------------------------------------
    # Preset load / save
    # ------------------------------------------------------------------

    def _load_preset(self):
        """Show preset picker dialog and populate wizard from chosen preset."""
        presets = self._preset_manager.list_presets()
        if not presets:
            messagebox.showinfo(
                "No Smart Presets",
                "No Smart Format presets found.\n\n"
                "Complete the wizard and click 'Save Preset' to create one.",
                parent=self.dialog,
            )
            return

        picker = _PresetPickerDialog(self.dialog, presets)
        chosen = picker.show()
        if chosen is None:
            return

        self._apply_preset_to_wizard(chosen)

    def _save_preset(self):
        """Prompt for a name and save current wizard config as a smart preset."""
        name = simpledialog.askstring(
            "Save Smart Format Preset",
            "Enter a name for this Smart Format preset:",
            parent=self.dialog,
        )
        if not name or not name.strip():
            return

        name = name.strip()
        col_map, derivation_plan, first_col, last_col = self._collect_mapping()
        ops_plan = self._collect_ops_plan()

        mc = {
            "column_map":     col_map,
            "derivation_plan": derivation_plan,
            "first_col":      first_col,
            "last_col":       last_col,
        }
        # Persist CSZ sub-sources for Post Office schema
        if "City, State, Zip" in self._schema:
            def _cb_val(cb: Optional[AutocompleteCombobox]) -> Optional[str]:
                if cb is None:
                    return None
                v = cb.get()
                return None if v in ("(blank)", "") else v
            mc["csz_city"]  = _cb_val(self._csz_city_cb)
            mc["csz_state"] = _cb_val(self._csz_state_cb)
            mc["csz_zip"]   = _cb_val(self._csz_zip_cb)

        config_to_save = {
            "template_id":    self._template_id,
            "mapping_config": mc,
            "operations_plan": ops_plan,
        }

        ok = self._preset_manager.save_preset(name, config_to_save)
        if ok:
            self._loaded_preset_name = name
            messagebox.showinfo(
                "Preset Saved",
                f"Smart Format preset '{name}' saved successfully.",
                parent=self.dialog,
            )
        else:
            messagebox.showerror(
                "Save Failed",
                "Could not save the preset. Check write permissions.",
                parent=self.dialog,
            )

    def _apply_preset_to_wizard(self, preset: Dict):
        """Populate step 2 and step 4 widgets from a loaded preset."""
        self._loaded_preset_name = preset.get("name")

        mapping_config = preset.get("mapping_config", {})
        col_map        = mapping_config.get("column_map", {})
        derivation_plan = mapping_config.get("derivation_plan", "blank")
        first_col      = mapping_config.get("first_col")
        last_col       = mapping_config.get("last_col")
        ops_plan       = preset.get("operations_plan", {})

        # ---- Populate step 2 dropdowns ----
        for target, source in col_map.items():
            if target == "Contact" and "Contact" in self._schema:
                continue
            cb = self._target_vars.get(target)
            if cb is None:
                continue
            if source and source != "__derived__" and source in self.raw_columns:
                cb.set(source)
            else:
                cb.set("(blank)")

        # Contact mode (Mail Standard only)
        if "Contact" in self._schema:
            if derivation_plan == "use_contact":
                self._contact_mode_var.set("Use existing Contact column")
            elif derivation_plan == "build_first_last":
                self._contact_mode_var.set("Build from First + Last Name")
            else:
                self._contact_mode_var.set("(blank)")

        # CSZ sub-sources (Post Office schema)
        if "City, State, Zip" in self._schema:
            def _set_csz(cb: Optional[AutocompleteCombobox], key: str):
                if cb is None:
                    return
                v = mapping_config.get(key)
                cb.set(v if v and v in self.raw_columns else "(blank)")
            _set_csz(self._csz_city_cb,  "csz_city")
            _set_csz(self._csz_state_cb, "csz_state")
            _set_csz(self._csz_zip_cb,   "csz_zip")

        # ---- Populate step 4 operations ----
        self._apply_ops_plan_to_widgets(ops_plan)

        messagebox.showinfo(
            "Preset Loaded",
            f"Preset '{self._loaded_preset_name}' loaded.\n\n"
            "Review mappings in Step 2 and operations in Step 4.\n"
            "Source columns not found in this file are marked (blank).",
            parent=self.dialog,
        )

    def _apply_ops_plan_to_widgets(self, ops_plan: Dict):
        """Set step 4 widget states from an ops_plan dict."""
        # Dedupe
        dedupe = ops_plan.get("dedupe", {})
        self._dedupe_enabled.set(dedupe.get("enabled", False))
        if self._dedupe_keys_lb and dedupe.get("enabled"):
            keys = set(dedupe.get("keys", []))
            for i, col in enumerate(self._schema):
                if col in keys:
                    self._dedupe_keys_lb.selection_set(i)
                else:
                    self._dedupe_keys_lb.selection_clear(i)

        # Remove rows containing
        rrc = ops_plan.get("remove_rows_containing", {})
        self._remove_rows_enabled.set(rrc.get("enabled", False))
        if self._remove_rows_cols_lb:
            cols = set(rrc.get("columns", []))
            for i, col in enumerate(self._schema):
                if col in cols:
                    self._remove_rows_cols_lb.selection_set(i)
                else:
                    self._remove_rows_cols_lb.selection_clear(i)
        self._remove_rows_text.set(rrc.get("patterns", ""))
        self._remove_rows_match.set(rrc.get("match_type", "contains"))

        # Remove blank rows
        rbr = ops_plan.get("remove_blank_rows", {})
        self._remove_blank_enabled.set(rbr.get("enabled", False))
        if self._remove_blank_cols_lb:
            cols = set(rbr.get("columns", []))
            for i, col in enumerate(self._schema):
                if col in cols:
                    self._remove_blank_cols_lb.selection_set(i)
                else:
                    self._remove_blank_cols_lb.selection_clear(i)

    # ------------------------------------------------------------------
    # Edit mode: pre-populate from existing SheetState.smart_format
    # ------------------------------------------------------------------

    def _populate_from_config(self, config: Dict):
        """Pre-populate wizard from a previously saved smart_format config."""
        mapping_config = config.get("mapping_config", {})
        ops_plan       = config.get("operations_plan", {})
        self._loaded_preset_name = config.get("preset_name")

        col_map        = mapping_config.get("column_map", {})
        derivation_plan = mapping_config.get("derivation_plan", "blank")

        # Step 2 dropdowns
        for target, source in col_map.items():
            if target == "Contact" and "Contact" in self._schema:
                continue
            cb = self._target_vars.get(target)
            if cb is None:
                continue
            if source and source != "__derived__" and source in self.raw_columns:
                cb.set(source)
            else:
                cb.set("(blank)")

        # Contact mode (Mail Standard only)
        if "Contact" in self._schema:
            if derivation_plan == "use_contact":
                self._contact_mode_var.set("Use existing Contact column")
            elif derivation_plan == "build_first_last":
                self._contact_mode_var.set("Build from First + Last Name")
            else:
                self._contact_mode_var.set("(blank)")

        # CSZ sub-sources (Post Office schema)
        if "City, State, Zip" in self._schema:
            def _set_csz(cb: Optional[AutocompleteCombobox], key: str):
                if cb is None:
                    return
                v = mapping_config.get(key)
                cb.set(v if v and v in self.raw_columns else "(blank)")
            _set_csz(self._csz_city_cb,  "csz_city")
            _set_csz(self._csz_state_cb, "csz_state")
            _set_csz(self._csz_zip_cb,   "csz_zip")

        # Step 4 ops
        self._apply_ops_plan_to_widgets(ops_plan)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> Optional[Dict]:
        """
        Show the wizard and block until closed.

        Returns the config dict on Apply, or None on Cancel.
        """
        self.parent.wait_window(self.dialog)
        return self._result


# ---------------------------------------------------------------------------
# Simple preset picker dialog
# ---------------------------------------------------------------------------

class _PresetPickerDialog:
    """
    Small modal dialog to select a smart format preset from a list.
    Returns the chosen preset dict or None.
    """

    def __init__(self, parent: tk.Widget, presets: List[Dict]):
        self.parent = parent
        self.presets = presets
        self._chosen: Optional[Dict] = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Load Smart Format Preset")
        self.dialog.geometry("400x320")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, True)

        tk.Label(self.dialog, text="Select a Smart Format Preset:",
                 font=("Segoe UI", 10, "bold")).pack(padx=16, pady=(16, 6), anchor=tk.W)

        frame = tk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=16)

        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        self._lb = tk.Listbox(frame, font=("Segoe UI", 9),
                              yscrollcommand=sb.set, selectmode=tk.SINGLE)
        sb.config(command=self._lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for p in presets:
            name = p.get("name", "Unnamed")
            suffix = " [system]" if p.get("_is_system") else ""
            self._lb.insert(tk.END, f"{name}{suffix}")

        self._lb.bind("<Double-Button-1>", lambda _: self._confirm())

        btn_bar = tk.Frame(self.dialog)
        btn_bar.pack(fill=tk.X, padx=16, pady=10)
        ttk.Button(btn_bar, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_bar, text="Load", command=self._confirm).pack(side=tk.RIGHT, padx=4)

    def _confirm(self):
        sel = self._lb.curselection()
        if sel:
            self._chosen = self.presets[sel[0]]
        self.dialog.destroy()

    def _cancel(self):
        self.dialog.destroy()

    def show(self) -> Optional[Dict]:
        self.parent.wait_window(self.dialog)
        return self._chosen
