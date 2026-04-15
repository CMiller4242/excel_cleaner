"""
ui_web/operation_forms.py
==========================
Generic parameter form renderer and effective-schema helper for the
CleanSheet Streamlit web edition.

Everything here is Tkinter-free.  It reads operation metadata from the
existing registry and renders the appropriate Streamlit widget for each
parameter type.

Supported parameter types (from operations/base.py + actual usage scan):
  column            → st.selectbox (effective columns)
  column_list       → st.multiselect (effective columns)
  text              → st.text_input
  number            → st.number_input (int or float depending on default)
  boolean           → st.checkbox
  choice            → st.selectbox (param.choices)
  list              → st.text_input (comma-separated, operations accept str)
  file              → st.file_uploader + temp-file write
  column_rename_list → st.text_area ("OldName=NewName" per line)
  add_columns_list  → st.text_area ("ColName" or "ColName=Default" per line)
  <unknown>         → st.text_input fallback
"""

import logging
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Effective schema
# ---------------------------------------------------------------------------

def get_effective_columns(df: pd.DataFrame, queue: list, up_to_index: int) -> list:
    """
    Return the list of column names that would exist in the DataFrame
    after running the first `up_to_index` operations in `queue`.

    Uses preview_execute_queue on a 5-row sample so it is fast and
    silently skips any operation with invalid / incomplete parameters.

    Falls back to the original DataFrame columns on any error.
    """
    if df is None or df.empty:
        return []
    if up_to_index <= 0 or not queue:
        return list(df.columns)

    # Import here to avoid circular paths at module load time
    from engine.executor import OperationExecutor

    sample = df.head(5).copy()
    ops_to_run = queue[:up_to_index]
    try:
        executor = OperationExecutor()
        result = executor.preview_execute_queue(sample, ops_to_run)
        if result is not None and not result.empty:
            return list(result.columns)
        if result is not None:
            return list(result.columns)  # may have 0 rows but still columns
    except Exception as exc:
        logger.debug("Effective schema compute failed at index %d: %s", up_to_index, exc)

    return list(df.columns)


# ---------------------------------------------------------------------------
# Form renderer
# ---------------------------------------------------------------------------

def render_param_form(
    operation,
    available_columns: list,
    existing_params: dict = None,
    key_prefix: str = "",
) -> dict:
    """
    Render Streamlit widgets for every parameter of `operation`.

    Args:
        operation:         A BaseOperation instance from the registry.
        available_columns: Column names visible at this point in the queue.
        existing_params:   Current saved parameter values (for editing).
        key_prefix:        Unique string prepended to every widget key.

    Returns:
        dict mapping param_name → raw widget value.
        Call normalize_params() before passing to executor.
    """
    saved = existing_params.copy() if existing_params else {}
    result = {}

    if not operation.metadata.parameters:
        st.caption("_This operation has no configurable parameters._")
        return result

    for param in operation.metadata.parameters:
        current_val = saved.get(param.name, param.default)
        # Build a unique, stable key for this widget
        safe_prefix = key_prefix.replace(" ", "_").replace("/", "_")
        safe_param = param.name.replace(" ", "_")
        key = f"{safe_prefix}__{safe_param}"

        label = param.description
        if param.required:
            label = f"**{label}** _(required)_"
        else:
            label = f"{label} _(optional)_"

        try:
            val = _render_single_param(param, current_val, available_columns, key, label)
        except Exception as exc:
            st.warning(f"Could not render '{param.name}': {exc}")
            val = current_val

        result[param.name] = val

    return result


def _render_single_param(param, current_val, available_columns, key, label):
    """Dispatch to the right widget for a single parameter."""
    ptype = param.type

    # ---- column ----
    if ptype == "column":
        opts = available_columns if available_columns else ["(no columns available)"]
        idx = 0
        if current_val and current_val in opts:
            idx = opts.index(current_val)
        return st.selectbox(label, options=opts, index=idx, key=key)

    # ---- column_list ----
    if ptype == "column_list":
        opts = available_columns if available_columns else []
        if isinstance(current_val, list):
            default = [c for c in current_val if c in opts]
        else:
            default = []
        return st.multiselect(label, options=opts, default=default, key=key)

    # ---- boolean ----
    if ptype == "boolean":
        default_bool = bool(current_val) if current_val is not None else False
        return st.checkbox(label, value=default_bool, key=key)

    # ---- choice ----
    if ptype == "choice":
        choices = param.choices or []
        if not choices:
            return st.text_input(label + " (no choices defined)", value=str(current_val or ""), key=key)
        idx = 0
        if current_val and current_val in choices:
            idx = choices.index(current_val)
        return st.selectbox(label, options=choices, index=idx, key=key)

    # ---- number ----
    if ptype == "number":
        # Infer int vs float from default; fall back to float
        if isinstance(param.default, int) or (
            isinstance(param.default, float) and param.default == int(param.default)
        ):
            raw = int(current_val) if current_val is not None else int(param.default or 0)
            return st.number_input(label, value=raw, step=1, key=key)
        else:
            raw = float(current_val) if current_val is not None else float(param.default or 0.0)
            return st.number_input(label, value=raw, step=0.1, key=key)

    # ---- file ----
    if ptype == "file":
        st.caption(label)
        uploaded = st.file_uploader(
            "Upload lookup file (CSV / XLSX / XLS)",
            type=["csv", "xlsx", "xls"],
            key=key,
        )
        if uploaded is not None:
            st.session_state[f"_fbytes_{key}"] = uploaded.getvalue()
            st.session_state[f"_fname_{key}"] = uploaded.name
            st.success(f"Ready: {uploaded.name}")
            return f"__FUPLOAD__{key}"
        existing = current_val or ""
        if existing and not str(existing).startswith("__FUPLOAD__"):
            st.caption(f"Current file: {existing}")
        return existing

    # ---- list (comma-separated; operations accept str or list) ----
    if ptype == "list":
        if isinstance(current_val, list):
            default_str = ",".join(str(v) for v in current_val)
        elif current_val is not None:
            default_str = str(current_val)
        else:
            default_str = str(param.default or "")
        return st.text_input(label + " (comma-separated)", value=default_str, key=key)

    # ---- column_rename_list (text_rename_batch) ----
    if ptype == "column_rename_list":
        if isinstance(current_val, list):
            lines = []
            for m in current_val:
                if isinstance(m, dict):
                    lines.append(f"{m.get('old', '')}={m.get('new', '')}")
                else:
                    lines.append(str(m))
            default_str = "\n".join(lines)
        elif current_val is not None:
            default_str = str(current_val)
        else:
            default_str = ""
        return st.text_area(
            label + " — one mapping per line: OldName=NewName",
            value=default_str,
            height=120,
            key=key,
            help="Example:\nFirst Name=FirstName\nLast Name=LastName",
        )

    # ---- add_columns_list (data_add_multiple_columns) ----
    if ptype == "add_columns_list":
        if isinstance(current_val, list):
            lines = []
            for c in current_val:
                if isinstance(c, dict):
                    name = c.get("name", "")
                    dv = c.get("default_value", "")
                    lines.append(f"{name}={dv}" if dv else name)
                else:
                    lines.append(str(c))
            default_str = "\n".join(lines)
        elif current_val is not None:
            default_str = str(current_val)
        else:
            default_str = ""
        return st.text_area(
            label + " — one column per line: ColumnName or ColumnName=DefaultValue",
            value=default_str,
            height=120,
            key=key,
            help="Example:\nStatus\nCountry=USA\nNotes",
        )

    # ---- text (and unknown types) ----
    default_str = str(current_val) if current_val is not None else str(param.default or "")
    return st.text_input(label, value=default_str, key=key)


# ---------------------------------------------------------------------------
# Param normalizer
# ---------------------------------------------------------------------------

def normalize_params(operation, raw_params: dict) -> dict:
    """
    Convert raw Streamlit widget values to the types that operation.execute()
    expects.  Handles:
      - column_rename_list: text-area string  →  list[{"old":…,"new":…}]
      - add_columns_list:   text-area string  →  list[{"name":…, …}]
      - file:               sentinel string   →  temp file path
      - number:             float from widget →  int when appropriate
    All other types are passed through unchanged.
    """
    out = {}
    for param in operation.metadata.parameters:
        val = raw_params.get(param.name)

        try:
            if param.type == "column_rename_list":
                if isinstance(val, str):
                    mappings = []
                    for line in val.strip().splitlines():
                        line = line.strip()
                        if "=" in line:
                            old, new = line.split("=", 1)
                            if old.strip():
                                mappings.append({"old": old.strip(), "new": new.strip()})
                    out[param.name] = mappings
                else:
                    out[param.name] = val or []

            elif param.type == "add_columns_list":
                if isinstance(val, str):
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
                    out[param.name] = specs
                else:
                    out[param.name] = val or []

            elif param.type == "file":
                sentinel = str(val or "")
                if sentinel.startswith("__FUPLOAD__"):
                    fkey = sentinel[len("__FUPLOAD__"):]
                    b_key = f"_fbytes_{fkey}"
                    n_key = f"_fname_{fkey}"
                    if b_key in st.session_state:
                        file_bytes = st.session_state[b_key]
                        file_name = st.session_state.get(n_key, "lookup.xlsx")
                        suffix = Path(file_name).suffix or ".xlsx"
                        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                        tmp.write(file_bytes)
                        tmp.flush()
                        out[param.name] = tmp.name
                    else:
                        out[param.name] = ""
                else:
                    out[param.name] = sentinel

            elif param.type == "number":
                # st.number_input returns int when step=1, float otherwise
                # Operations using row-index math need int; pass through as-is
                out[param.name] = val

            else:
                out[param.name] = val

        except Exception as exc:
            logger.warning("normalize_params failed for '%s': %s", param.name, exc)
            out[param.name] = val

    return out
