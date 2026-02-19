"""
Smart Format Wizard – Mail File Standard

Three-step modal wizard:
  Step 1 – Confirm target schema + detected column summary
  Step 2 – Mapping review table (user can adjust each target → source)
  Step 3 – Summary + Apply
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, List, Optional

from utils.smart_mapping import (
    REQUIRED_SCHEMA,
    TYPICALLY_BLANK,
    MappingResult,
    infer_mapping,
)
from ui.widgets.searchable_combobox import SearchableCombobox


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


class SmartFormatWizard:
    """
    Modal wizard that guides the user through mapping a raw DataFrame
    to the 24-column mail-file standard.

    Usage::

        wizard = SmartFormatWizard(parent, raw_columns=df.columns.tolist())
        config = wizard.show()   # blocks; returns mapping_config dict or None
    """

    STEPS = ["1. Schema Overview", "2. Column Mapping", "3. Review & Apply"]

    def __init__(self, parent: tk.Widget, raw_columns: List[str]):
        self.parent = parent
        self.raw_columns = raw_columns
        self._result: Optional[Dict] = None
        self.current_step = 0

        # Run inference once
        self.mapping_result: MappingResult = infer_mapping(raw_columns)

        # Source option list for dropdowns: "(blank)" + sorted raw columns
        self._source_options = ["(blank)"] + list(raw_columns)

        # Per-target StringVars for the mapping dropdowns (Step 2)
        self._target_vars: Dict[str, tk.StringVar] = {}
        # Contact mode StringVar
        self._contact_mode_var: tk.StringVar = tk.StringVar()
        # First/Last col display StringVars
        self._first_var: tk.StringVar = tk.StringVar()
        self._last_var:  tk.StringVar = tk.StringVar()

        self._build_dialog()

    # ------------------------------------------------------------------
    # Dialog construction
    # ------------------------------------------------------------------

    def _build_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("✨ Smart Format — Mail File Standard")
        self.dialog.geometry("820x640")
        self.dialog.minsize(700, 520)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)

        # ---- Header ----
        header = tk.Frame(self.dialog, bg="#0078D4", height=56)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="✨  Smart Format — Mail File Standard",
            font=("Segoe UI", 14, "bold"),
            bg="#0078D4", fg="white",
        ).pack(side=tk.LEFT, padx=16, pady=12)

        # Step indicator (right side of header)
        self._step_label = tk.Label(
            header,
            text="Step 1 of 3",
            font=("Segoe UI", 10),
            bg="#0078D4", fg="#BDD7F5",
        )
        self._step_label.pack(side=tk.RIGHT, padx=16)

        # ---- Button bar (packed BOTTOM so content fills middle) ----
        btn_bar = tk.Frame(self.dialog, bg="#F3F2F1", bd=0)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Frame(btn_bar, bg="#EDEBE9", height=1).pack(fill=tk.X)  # separator

        inner_btns = tk.Frame(btn_bar, bg="#F3F2F1")
        inner_btns.pack(pady=10, padx=16, anchor=tk.E)

        self._cancel_btn = ttk.Button(inner_btns, text="Cancel", width=10,
                                      command=self._on_cancel)
        self._cancel_btn.pack(side=tk.LEFT, padx=4)

        self._back_btn = ttk.Button(inner_btns, text="◀  Back", width=10,
                                    command=self._go_back, state=tk.DISABLED)
        self._back_btn.pack(side=tk.LEFT, padx=4)

        self._next_btn = ttk.Button(inner_btns, text="Next  ▶", width=12,
                                    command=self._go_next)
        self._next_btn.pack(side=tk.LEFT, padx=4)

        # ---- Content area (middle) ----
        self._content = tk.Frame(self.dialog, bg="white")
        self._content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Build all three step frames (hidden initially)
        self._step_frames = [
            self._build_step1(),
            self._build_step2(),
            self._build_step3(),
        ]

        self._show_step(0)

    # ------------------------------------------------------------------
    # Step builders
    # ------------------------------------------------------------------

    def _build_step1(self) -> tk.Frame:
        """Overview: target schema list + raw column summary."""
        frame = tk.Frame(self._content, bg="white")

        # Title
        tk.Label(
            frame,
            text="Target Schema: 24-Column Mail File Standard",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#323130",
        ).pack(anchor=tk.W, padx=20, pady=(20, 4))

        # Summary line
        n_raw = len(self.raw_columns)
        n_found = sum(
            1 for v in self.mapping_result.suggested_map.values() if v
        )
        n_blank = len(REQUIRED_SCHEMA) - n_found

        tk.Label(
            frame,
            text=(f"Raw file: {n_raw} columns detected  •  "
                  f"{n_found}/{len(REQUIRED_SCHEMA)} target columns auto-matched  •  "
                  f"{n_blank} will be created blank"),
            font=("Segoe UI", 10),
            bg="white", fg="#605E5C",
            wraplength=750, justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=20, pady=(0, 12))

        # Schema list in scrollable canvas
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

        # Header row
        hdr = tk.Frame(inner, bg="#F3F2F1")
        hdr.pack(fill=tk.X, pady=(0, 2))
        tk.Label(hdr, text="#",           width=4,  bg="#F3F2F1", font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=4)
        tk.Label(hdr, text="Target Column", width=22, bg="#F3F2F1", font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=4)
        tk.Label(hdr, text="Best Match",   width=28, bg="#F3F2F1", font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=4)
        tk.Label(hdr, text="Confidence",   width=10, bg="#F3F2F1", font=("Segoe UI", 9, "bold"), anchor=tk.W).pack(side=tk.LEFT, padx=4)

        for idx, target in enumerate(REQUIRED_SCHEMA):
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

        # Conflicts note
        if self.mapping_result.conflicts:
            note = tk.Frame(frame, bg="#FFF4CE", bd=1, relief=tk.FLAT)
            note.pack(fill=tk.X, padx=20, pady=(4, 0))
            tk.Label(
                note,
                text=(f"⚠  {len(self.mapping_result.conflicts)} mapping conflict(s) detected — "
                      f"review in Step 2."),
                font=("Segoe UI", 9),
                bg="#FFF4CE", fg="#7A5C00",
                anchor=tk.W,
            ).pack(anchor=tk.W, padx=8, pady=4)

        return frame

    def _build_step2(self) -> tk.Frame:
        """Mapping review: one row per target column with editable dropdown."""
        frame = tk.Frame(self._content, bg="white")

        tk.Label(
            frame,
            text="Review and Adjust Column Mapping",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#323130",
        ).pack(anchor=tk.W, padx=20, pady=(20, 2))

        tk.Label(
            frame,
            text="For each target column, choose the source column from your file (or '(blank)'). Type to search.",
            font=("Segoe UI", 9),
            bg="white", fg="#605E5C",
        ).pack(anchor=tk.W, padx=20, pady=(0, 10))

        # Scrollable mapping table
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

        for idx, target in enumerate(REQUIRED_SCHEMA):
            source = mr.suggested_map.get(target)
            conf   = mr.confidences.get(target, "low")
            row_bg = "white" if idx % 2 == 0 else "#FAFAFA"

            row = tk.Frame(table, bg=row_bg)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=target, width=20, bg=row_bg,
                     font=("Segoe UI", 9), anchor=tk.W).pack(side=tk.LEFT, padx=6)

            # ---- Contact gets special treatment ----
            if target == "Contact":
                self._build_contact_row(row, row_bg)
                continue

            # Searchable dropdown – options list excludes "(blank)"; widget adds it
            raw_only = [o for o in self._source_options if o != "(blank)"]
            cb = SearchableCombobox(row, options=raw_only, width=32)

            if source == "__derived__" or not source or source not in self.raw_columns:
                cb.set("(blank)")
            else:
                cb.set(source)

            cb.pack(side=tk.LEFT, padx=6)

            # Store widget directly so _collect_mapping can call cb.get()
            self._target_vars[target] = cb

            conf_color = _CONF_COLOR.get(conf, "#A19F9D") if source else "#A19F9D"
            conf_txt   = _CONF_LABEL.get(conf, "") if source else "—"
            tk.Label(row, text=conf_txt, width=8, bg=row_bg,
                     font=("Segoe UI", 9), fg=conf_color, anchor=tk.W).pack(side=tk.LEFT, padx=6)

            # Conflict note
            conflict_for = [c for c in mr.conflicts if c["target_col"] == target]
            note_txt = ""
            if conflict_for:
                other = [x for x in conflict_for[0]["candidates"] if x != source]
                note_txt = f"⚠ conflict with: {', '.join(other[:2])}"
            elif target in TYPICALLY_BLANK and not source:
                note_txt = "Optional – will be blank"

            if note_txt:
                tk.Label(row, text=note_txt, width=28, bg=row_bg,
                         font=("Segoe UI", 8), fg="#7A5C00" if "conflict" in note_txt else "#A19F9D",
                         anchor=tk.W).pack(side=tk.LEFT, padx=6)

        return frame

    def _build_contact_row(self, row: tk.Frame, row_bg: str):
        """Contact row with mode selector."""
        mr = self.mapping_result

        # Set initial mode
        if mr.derivation_plan == "use_contact":
            initial_mode = "Use existing Contact column"
        elif mr.derivation_plan == "build_first_last":
            initial_mode = "Build from First + Last Name"
        else:
            initial_mode = "(blank)"

        self._contact_mode_var.set(initial_mode)

        modes = ["Use existing Contact column",
                 "Build from First + Last Name",
                 "(blank)"]

        cb = ttk.Combobox(row, textvariable=self._contact_mode_var,
                          values=modes, width=30, state="readonly",
                          font=("Segoe UI", 9))
        cb.pack(side=tk.LEFT, padx=6)

        # Show first/last columns detected
        first_txt = mr.first_col or "(not found)"
        last_txt  = mr.last_col  or "(not found)"

        self._first_var.set(first_txt)
        self._last_var.set(last_txt)

        detail_lbl = tk.Label(
            row,
            text=f"First='{first_txt}'  Last='{last_txt}'",
            font=("Segoe UI", 8), bg=row_bg, fg="#605E5C",
        )
        detail_lbl.pack(side=tk.LEFT, padx=6)

    def _build_step3(self) -> tk.Frame:
        """Summary / confirmation screen."""
        frame = tk.Frame(self._content, bg="white")
        self._step3_frame = frame   # keep ref for refresh
        return frame

    def _populate_step3(self):
        """Rebuild step 3 content based on current Step 2 selections."""
        frame = self._step3_frame
        for w in frame.winfo_children():
            w.destroy()

        tk.Label(
            frame,
            text="Review & Apply",
            font=("Segoe UI", 12, "bold"),
            bg="white", fg="#323130",
        ).pack(anchor=tk.W, padx=20, pady=(20, 4))

        col_map, derivation_plan, first_col, last_col = self._collect_mapping()

        # Compute stats
        blank_targets = [t for t, s in col_map.items() if not s]
        mapped_targets = [t for t, s in col_map.items() if s]
        conflicts = self.mapping_result.conflicts
        dropped = self.mapping_result.dropped_columns

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
            tk.Label(frame, text="Blank columns: " + ", ".join(blank_targets),
                     font=("Segoe UI", 9), bg="white", fg="#605E5C",
                     wraplength=740, justify=tk.LEFT,
                     anchor=tk.W).pack(anchor=tk.W, padx=32, pady=(0, 4))

        if dropped:
            tk.Label(frame, text="Dropped: " + ", ".join(dropped[:10]) +
                     (f"  …+{len(dropped)-10} more" if len(dropped) > 10 else ""),
                     font=("Segoe UI", 9), bg="white", fg="#A19F9D",
                     wraplength=740, justify=tk.LEFT,
                     anchor=tk.W).pack(anchor=tk.W, padx=32, pady=(0, 8))

        tk.Label(
            frame,
            text="Click 'Apply' to transform the active sheet. This is reversible via Undo.",
            font=("Segoe UI", 9, "italic"),
            bg="white", fg="#605E5C",
        ).pack(anchor=tk.W, padx=20, pady=(8, 0))

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _show_step(self, step: int):
        for f in self._step_frames:
            f.pack_forget()
        self._step_frames[step].pack(fill=tk.BOTH, expand=True)
        self._step_label.config(text=f"Step {step + 1} of {len(self.STEPS)}")

        # Update buttons
        self._back_btn.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
        if step == len(self.STEPS) - 1:
            self._next_btn.config(text="✔  Apply")
        else:
            self._next_btn.config(text="Next  ▶")

    def _go_next(self):
        if self.current_step == len(self.STEPS) - 1:
            self._apply()
            return

        # Validate step 2 before proceeding
        if self.current_step == 1:
            self._populate_step3()

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

        for target in REQUIRED_SCHEMA:
            if target == "Contact":
                continue   # handled separately
            var = self._target_vars.get(target)
            if var is None:
                col_map[target] = None
                continue
            val = var.get()
            col_map[target] = None if val == "(blank)" else val

        # Contact
        mode = self._contact_mode_var.get()
        mr = self.mapping_result
        if mode == "Use existing Contact column":
            derivation_plan = "use_contact"
            # Find which raw col is the contact source
            contact_src = mr.suggested_map.get("Contact")
            if contact_src == "__derived__" or not contact_src:
                # fall back to greedy scan
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

        return col_map, derivation_plan, first_col, last_col

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def _apply(self):
        col_map, derivation_plan, first_col, last_col = self._collect_mapping()

        self._result = {
            "column_map": col_map,
            "derivation_plan": derivation_plan,
            "first_col": first_col,
            "last_col":  last_col,
        }
        self.dialog.destroy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> Optional[Dict]:
        """
        Show the wizard and block until closed.

        Returns the mapping_config dict on Apply, or None on Cancel.
        """
        self.parent.wait_window(self.dialog)
        return self._result
