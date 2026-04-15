"""
ui_web/operation_forms.py
==========================
Generic parameter-form renderer for the CleanSheet Streamlit web edition.
Tkinter-free.  Reads BaseOperation metadata and renders Streamlit widgets.

Public API
----------
param_widget_key(uid, param_name)       → stable, unique widget key
render_param_form(op, cols, params, uid)→ renders all widgets; returns raw dict
normalize_params(op, raw_params)        → convert raw widget values → executor format

Supported parameter types
--------------------------
column            → st.selectbox  (from available_columns)
column_list       → st.multiselect (from available_columns)
text              → st.text_input
number            → st.number_input (int step=1 when default is int, else float)
boolean           → st.checkbox
choice            → st.selectbox  (from param.choices)
list              → st.text_input  (comma-separated; operations accept str OR list)
file              → st.file_uploader + session-state byte cache
column_rename_list→ st.text_area  (OldName=NewName per line)
add_columns_list  → st.text_area  (ColName or ColName=DefaultValue per line)
<unknown>         → st.text_input  (fallback)
"""

import logging
import tempfile
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)


# ── key helper ────────────────────────────────────────────────────────────────

def param_widget_key(uid: str, param_name: str) -> str:
    """
    Build a unique, stable Streamlit widget key for one parameter on one
    queue item.

    uid        — the queue item's immutable _uid string
    param_name — operation parameter name (e.g. 'columns', 'fill_value')

    The key format is:  qparam_<uid>__<safe_param_name>
    Both `render_param_form` and the sync loop in streamlit_app.py must use
    this function so the keys always match.
    """
    safe_uid   = uid.replace(" ", "_").replace("/", "_")
    safe_param = param_name.replace(" ", "_").replace("/", "_")
    return f"qparam_{safe_uid}__{safe_param}"


# ── form renderer ─────────────────────────────────────────────────────────────

def render_param_form(
    operation,
    available_columns: list,
    existing_params: dict = None,
    uid: str = "",
) -> dict:
    """
    Render Streamlit widgets for every parameter of *operation*.

    Args:
        operation:         BaseOperation instance from the registry.
        available_columns: Column names currently visible in the DataFrame.
        existing_params:   Saved parameter values to pre-fill the form with.
        uid:               The queue item's stable _uid (used for widget keys).

    Returns:
        dict {param_name: raw_widget_value}.
        Pass through normalize_params() before handing to the executor.

    Widget keys are built with param_widget_key(uid, param_name) so they
    match the sync loop in streamlit_app.py exactly.
    """
    saved  = existing_params.copy() if existing_params else {}
    result = {}

    if not operation.metadata.parameters:
        st.caption("_No configurable parameters — this operation runs as-is._")
        return result

    for param in operation.metadata.parameters:
        current_val = saved.get(param.name, param.default)
        key         = param_widget_key(uid, param.name)
        label       = param.description
        req_marker  = " \\*" if param.required else ""

        try:
            val = _render_single(param, current_val, available_columns, key,
                                 label + req_marker)
        except Exception as exc:
            st.warning(f"Cannot render '{param.name}': {exc}")
            val = current_val

        result[param.name] = val

    return result


def _render_single(param, current_val, available_columns, key, label):
    """Dispatch a single parameter to the right widget type."""
    ptype = param.type

    # ── column ──────────────────────────────────────────────────────────────
    if ptype == "column":
        opts = list(available_columns) if available_columns else []
        if not opts:
            return st.text_input(label + " (no columns — upload a file first)",
                                 value=str(current_val or ""), key=key)
        idx = opts.index(current_val) if (current_val and current_val in opts) else 0
        return st.selectbox(label, options=opts, index=idx, key=key)

    # ── column_list ──────────────────────────────────────────────────────────
    if ptype == "column_list":
        opts = list(available_columns) if available_columns else []
        if isinstance(current_val, list):
            default = [c for c in current_val if c in opts]
        else:
            default = []
        return st.multiselect(label, options=opts, default=default, key=key)

    # ── boolean ──────────────────────────────────────────────────────────────
    if ptype == "boolean":
        val_bool = bool(current_val) if current_val is not None else False
        return st.checkbox(label, value=val_bool, key=key)

    # ── choice ───────────────────────────────────────────────────────────────
    if ptype == "choice":
        choices = param.choices or []
        if not choices:
            return st.text_input(label + " (no choices defined)",
                                 value=str(current_val or ""), key=key)
        idx = choices.index(current_val) if (current_val and current_val in choices) else 0
        return st.selectbox(label, options=choices, index=idx, key=key)

    # ── number ───────────────────────────────────────────────────────────────
    if ptype == "number":
        # Use integer step when the metadata default is an int (or whole float)
        use_int = isinstance(param.default, int) or (
            isinstance(param.default, float) and param.default == int(param.default or 0)
        )
        if use_int:
            try:
                raw = int(float(current_val)) if current_val is not None else int(param.default or 0)
            except (TypeError, ValueError):
                raw = int(param.default or 0)
            return st.number_input(label, value=raw, step=1, key=key)
        else:
            try:
                raw = float(current_val) if current_val is not None else float(param.default or 0.0)
            except (TypeError, ValueError):
                raw = float(param.default or 0.0)
            return st.number_input(label, value=raw, step=0.1, key=key)

    # ── file ─────────────────────────────────────────────────────────────────
    if ptype == "file":
        st.caption(f"**{label}**")
        uploaded = st.file_uploader(
            "Upload lookup file",
            type=["csv", "xlsx", "xls"],
            key=key,
        )
        if uploaded is not None:
            st.session_state[f"_fbytes_{key}"] = uploaded.getvalue()
            st.session_state[f"_fname_{key}"]  = uploaded.name
            st.success(f"File ready: {uploaded.name}")
            return f"__FUPLOAD__{key}"
        existing = str(current_val or "")
        if existing and not existing.startswith("__FUPLOAD__"):
            st.caption(f"Current: {existing}")
        return existing

    # ── list (comma-separated; operations accept str OR list) ────────────────
    if ptype == "list":
        if isinstance(current_val, list):
            default_str = ",".join(str(v) for v in current_val)
        elif current_val is not None:
            default_str = str(current_val)
        else:
            default_str = str(param.default or "")
        return st.text_input(label + " (comma-separated)", value=default_str, key=key)

    # ── column_rename_list — "OldName=NewName" per line ──────────────────────
    if ptype == "column_rename_list":
        default_str = _column_rename_list_to_str(current_val)
        return st.text_area(
            label + "  (OldName=NewName, one mapping per line)",
            value=default_str,
            height=120,
            key=key,
            help="Example:\nFirst Name=FirstName\nLast Name=LastName",
        )

    # ── add_columns_list — "ColName" or "ColName=Default" per line ───────────
    if ptype == "add_columns_list":
        default_str = _add_columns_list_to_str(current_val)
        return st.text_area(
            label + "  (ColumnName or ColumnName=DefaultValue, one per line)",
            value=default_str,
            height=120,
            key=key,
            help="Example:\nStatus\nCountry=USA\nNotes",
        )

    # ── text / fallback ──────────────────────────────────────────────────────
    default_str = str(current_val) if current_val is not None else str(param.default or "")
    return st.text_input(label, value=default_str, key=key)


# ── display-form converters ───────────────────────────────────────────────────

def _column_rename_list_to_str(val) -> str:
    """Convert stored column_rename_list value → text-area string."""
    if isinstance(val, list):
        lines = []
        for m in val:
            if isinstance(m, dict):
                lines.append(f"{m.get('old', '')}={m.get('new', '')}")
            else:
                lines.append(str(m))
        return "\n".join(lines)
    return str(val) if val is not None else ""


def _add_columns_list_to_str(val) -> str:
    """Convert stored add_columns_list value → text-area string."""
    if isinstance(val, list):
        lines = []
        for c in val:
            if isinstance(c, dict):
                name = c.get("name", "")
                dv   = c.get("default_value", "")
                lines.append(f"{name}={dv}" if dv else name)
            else:
                lines.append(str(c))
        return "\n".join(lines)
    return str(val) if val is not None else ""


# ── normalizer (raw widget values → executor-ready params) ───────────────────

def normalize_params(operation, raw_params: dict) -> dict:
    """
    Convert raw Streamlit widget values to the types operation.execute() expects.

    Most types pass through unchanged.  Special conversions:
      column_rename_list  text-area string  →  list[{"old":…, "new":…}]
      add_columns_list    text-area string  →  list[{"name":…, …}]
      file                sentinel string   →  temp file path on disk
    """
    out = {}
    for param in operation.metadata.parameters:
        val = raw_params.get(param.name)
        try:
            if param.type == "column_rename_list":
                out[param.name] = _parse_column_rename_list(val)

            elif param.type == "add_columns_list":
                out[param.name] = _parse_add_columns_list(val)

            elif param.type == "file":
                out[param.name] = _resolve_file_param(val)

            else:
                out[param.name] = val

        except Exception as exc:
            logger.warning("normalize_params failed for '%s': %s", param.name, exc)
            out[param.name] = val

    return out


def _parse_column_rename_list(val) -> list:
    if isinstance(val, list):
        return val   # already normalized (e.g. loaded from preset JSON)
    if not isinstance(val, str) or not val.strip():
        return []
    mappings = []
    for line in val.strip().splitlines():
        line = line.strip()
        if "=" in line:
            old, new = line.split("=", 1)
            if old.strip():
                mappings.append({"old": old.strip(), "new": new.strip()})
    return mappings


def _parse_add_columns_list(val) -> list:
    if isinstance(val, list):
        return val   # already normalized
    if not isinstance(val, str) or not val.strip():
        return []
    specs = []
    for line in val.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if "=" in line:
            name, dv = line.split("=", 1)
            specs.append({
                "name": name.strip(),
                "default_type": "value",
                "default_value": dv.strip(),
                "on_exists": "skip",
            })
        else:
            specs.append({
                "name": line,
                "default_type": "blank",
                "default_value": "",
                "on_exists": "skip",
            })
    return specs


def _resolve_file_param(val) -> str:
    sentinel = str(val or "")
    if not sentinel.startswith("__FUPLOAD__"):
        return sentinel
    fkey  = sentinel[len("__FUPLOAD__"):]
    b_key = f"_fbytes_{fkey}"
    n_key = f"_fname_{fkey}"
    if b_key not in st.session_state:
        return ""
    file_bytes = st.session_state[b_key]
    file_name  = st.session_state.get(n_key, "lookup.xlsx")
    suffix     = Path(file_name).suffix or ".xlsx"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(file_bytes)
    tmp.flush()
    return tmp.name
