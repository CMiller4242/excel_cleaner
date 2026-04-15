"""
Clean Sheet — Streamlit Web App
=================================
Browser-accessible parallel entrypoint.  The Tkinter desktop app
(main_gui_v2_office365.py) is completely unaffected by this file.

This file is Tkinter-free.  It imports only from:
  operations/   — registry + all operations (no Tkinter at module level)
  engine/executor.py
  presets/preset_manager.py

Run desktop: py main_gui_v2_office365.py
Run web:     streamlit run streamlit_app.py
"""

import sys
import uuid
import logging
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

# ── path setup (must come before local imports) ────────────────────────────
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── backend imports (Tkinter-free) ─────────────────────────────────────────
from operations import registry          # triggers all operation registrations
from engine.executor import OperationExecutor
from presets.preset_manager import PresetManager
from ui_web.operation_forms import render_param_form, normalize_params, param_widget_key

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────
ACCEPTED_TYPES  = ["csv", "xlsx", "xls"]
PREVIEW_ROWS    = 200   # rows shown in data preview
RESULT_ROWS     = 500   # rows shown in result preview


# ══════════════════════════════════════════════════════════════════════════
# Session-state helpers
# ══════════════════════════════════════════════════════════════════════════

def _init_state() -> None:
    defaults = {
        # File
        "df_original":   None,
        "filename":      None,
        # Workflow queue  ← NEW
        # Each item: {operation_id, parameters, enabled, _label, _category}
        "queue":         [],
        # Execution results
        "df_result":     None,
        "df_removed":    None,
        "run_complete":  False,
        "run_error":     None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset_results() -> None:
    """Clear execution results.  Does NOT wipe the queue."""
    st.session_state.df_result    = None
    st.session_state.df_removed   = None
    st.session_state.run_complete = False
    st.session_state.run_error    = None


# ══════════════════════════════════════════════════════════════════════════
# File loading
# ══════════════════════════════════════════════════════════════════════════

def _load_uploaded_file(uploaded_file):
    """Parse an uploaded file → (df, error_msg).  error_msg is None on success."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding="latin-1")
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file, sheet_name=0, engine="openpyxl")
        else:
            return None, f"Unsupported type: '{uploaded_file.name}'"
    except Exception as exc:
        return None, f"Could not parse '{uploaded_file.name}': {exc}"

    if df is None or df.empty:
        return None, f"'{uploaded_file.name}' loaded but contains no data."
    return df, None


# ══════════════════════════════════════════════════════════════════════════
# Preset helpers
# ══════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def _get_preset_manager() -> PresetManager:
    return PresetManager()


def _list_presets():
    try:
        return sorted(_get_preset_manager().list_presets(), key=lambda p: p.name.lower())
    except Exception as exc:
        logger.error("Failed to list presets: %s", exc)
        return []


def _preset_to_queue(preset) -> list:
    """Convert a Preset's operations into the unified queue-item format."""
    items = []
    for op in preset.operations:
        op_id   = op.operation_id if hasattr(op, "operation_id") else op.get("operation_id", "")
        params  = dict(op.parameters if hasattr(op, "parameters") else op.get("parameters", {}))
        enabled = op.enabled if hasattr(op, "enabled") else op.get("enabled", True)
        reg_op  = registry.get_by_id(op_id)
        label   = reg_op.metadata.name     if reg_op else op_id
        cat     = reg_op.metadata.category if reg_op else ""
        items.append({
            "operation_id": op_id,
            "parameters":   params,
            "enabled":      enabled,
            "_label":       label,
            "_category":    cat,
            "_uid":         str(uuid.uuid4()),
        })
    return items


# ══════════════════════════════════════════════════════════════════════════
# Queue helpers
# ══════════════════════════════════════════════════════════════════════════

def _op_default_params(operation) -> dict:
    """Build a parameter dict pre-filled with metadata defaults."""
    params = {}
    for p in operation.metadata.parameters:
        if p.default is not None:
            params[p.name] = p.default
        elif p.type == "column_list":
            params[p.name] = []
        elif p.type == "boolean":
            params[p.name] = False
        elif p.type == "number":
            params[p.name] = 0
        else:
            params[p.name] = ""
    return params


def _queue_item_from_registry(op_id: str) -> dict:
    """Create a new queue item for an operation ID."""
    op = registry.get_by_id(op_id)
    if op is None:
        return {"operation_id": op_id, "parameters": {}, "enabled": True,
                "_label": op_id, "_category": "", "_uid": str(uuid.uuid4())}
    return {
        "operation_id": op_id,
        "parameters":   _op_default_params(op),
        "enabled":      True,
        "_label":       op.metadata.name,
        "_category":    op.metadata.category,
        "_uid":         str(uuid.uuid4()),
    }


def _ensure_uids(queue: list) -> None:
    """Back-fill _uid on any queue items missing one (e.g. loaded from older sessions)."""
    for item in queue:
        if "_uid" not in item:
            item["_uid"] = str(uuid.uuid4())


def _normalize_queue_for_execution(queue: list) -> list:
    """Build an executor-ready copy of the queue with normalized parameters."""
    result = []
    for item in queue:
        op_id      = item.get("operation_id", "")
        op         = registry.get_by_id(op_id)
        raw_params = item.get("parameters", {})
        norm_params = normalize_params(op, raw_params) if op is not None else raw_params
        result.append({
            "operation_id": op_id,
            "parameters":   norm_params,
            "enabled":      item.get("enabled", True),
        })
    return result


# ══════════════════════════════════════════════════════════════════════════
# Export helper
# ══════════════════════════════════════════════════════════════════════════

def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cleaned Data")
    return buf.getvalue()


def _output_filename(original_name: str) -> str:
    return f"{Path(original_name).stem}_cleaned.xlsx"


# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR — preset loader + operation browser
# ══════════════════════════════════════════════════════════════════════════

def _render_sidebar() -> None:
    """Sidebar: preset loader and operation browser (Add to Queue)."""
    with st.sidebar:
        # ── Preset Loader ─────────────────────────────────────────────────
        st.header("Presets")
        presets = _list_presets()
        if not presets:
            st.caption("No preset files found.")
        else:
            preset_map = {f"{p.name}  [{p.category}]": p for p in presets}
            chosen_label = st.selectbox(
                "Select preset",
                list(preset_map.keys()),
                key="sidebar_preset_select",
            )
            chosen_preset = preset_map[chosen_label]
            n_ops = len(chosen_preset.operations)
            st.caption(
                f"{n_ops} operation{'s' if n_ops != 1 else ''}"
                + (f" · {chosen_preset.description[:60]}" if chosen_preset.description else "")
            )

            col_load, col_replace = st.columns(2)
            with col_load:
                if st.button("➕ Append", use_container_width=True,
                             help="Add preset operations to the end of the current queue"):
                    new_items = _preset_to_queue(chosen_preset)
                    st.session_state.queue.extend(new_items)
                    _reset_results()
                    st.success(f"Added {len(new_items)} ops from '{chosen_preset.name}'")
            with col_replace:
                if st.button("↺ Replace", use_container_width=True,
                             help="Replace the current queue with this preset"):
                    st.session_state.queue = _preset_to_queue(chosen_preset)
                    _reset_results()
                    st.success(f"Queue replaced with '{chosen_preset.name}'")

        st.divider()

        # ── Operation Browser ─────────────────────────────────────────────
        st.header("Add Operation")

        all_ops  = sorted(registry.list_all(),
                          key=lambda o: (o.metadata.category, o.metadata.name))
        all_cats = ["All Categories"] + sorted(set(o.metadata.category for o in all_ops))

        cat_choice = st.selectbox("Category", all_cats, key="sidebar_cat")

        filtered = (
            all_ops if cat_choice == "All Categories"
            else [o for o in all_ops if o.metadata.category == cat_choice]
        )

        if not filtered:
            st.caption("No operations in this category.")
            return

        op_map = {f"{o.metadata.name}": o for o in filtered}
        chosen_op_name = st.selectbox(
            "Operation",
            list(op_map.keys()),
            key="sidebar_op",
        )
        chosen_op = op_map[chosen_op_name]

        # Brief description
        st.caption(
            f"**Category:** {chosen_op.metadata.category}  \n"
            f"{chosen_op.metadata.description[:120]}"
            + ("…" if len(chosen_op.metadata.description) > 120 else "")
        )
        if chosen_op.metadata.parameters:
            n_req = sum(1 for p in chosen_op.metadata.parameters if p.required)
            n_tot = len(chosen_op.metadata.parameters)
            st.caption(f"{n_tot} parameter{'s' if n_tot != 1 else ''} "
                       f"({n_req} required)")
        else:
            st.caption("No parameters required.")

        if st.button("➕ Add to Queue", type="primary", use_container_width=True):
            item = _queue_item_from_registry(chosen_op.metadata.id)
            st.session_state.queue.append(item)
            _reset_results()
            st.success(f"Added: {chosen_op.metadata.name}")


# ══════════════════════════════════════════════════════════════════════════
# MAIN SECTIONS
# ══════════════════════════════════════════════════════════════════════════

def _section_upload() -> bool:
    """Upload widget.  Returns True when a valid DataFrame is in session state."""
    st.subheader("Upload File")

    uploaded = st.file_uploader(
        "Choose a CSV or Excel file",
        type=ACCEPTED_TYPES,
        label_visibility="collapsed",
    )

    if uploaded is None:
        return False

    if st.session_state.filename != uploaded.name:
        df, err = _load_uploaded_file(uploaded)
        if err:
            st.error(err)
            st.session_state.df_original = None
            st.session_state.filename    = None
            _reset_results()
            return False
        st.session_state.df_original = df
        st.session_state.filename    = uploaded.name
        _reset_results()
        # Note: we intentionally keep the queue when a new file is loaded.
        # Users can keep building their workflow even while testing different files.

    return st.session_state.df_original is not None


def _section_data_info(df: pd.DataFrame) -> None:
    """Show dataset summary metrics, column list, and preview table."""
    st.subheader("Dataset")

    # ── metrics row ───────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("File",    st.session_state.filename)
    m2.metric("Rows",    f"{len(df):,}")
    m3.metric("Columns", len(df.columns))

    # ── column list ───────────────────────────────────────────────────────
    with st.expander(f"Column names ({len(df.columns)})", expanded=True):
        # Render as a tight two-column grid of pills / badges
        col_names = list(df.columns)
        cols_per_row = 3
        rows = [col_names[i:i+cols_per_row] for i in range(0, len(col_names), cols_per_row)]
        for row in rows:
            grid = st.columns(cols_per_row)
            for ci, col_name in enumerate(row):
                grid[ci].code(col_name, language=None)

    # ── data preview ──────────────────────────────────────────────────────
    total = len(df)
    preview_label = (
        f"Data preview — first {PREVIEW_ROWS:,} of {total:,} rows"
        if total > PREVIEW_ROWS
        else f"Data preview — all {total:,} rows"
    )
    with st.expander(preview_label, expanded=False):
        st.dataframe(df.head(PREVIEW_ROWS), use_container_width=True)


def _section_queue() -> None:
    """Show the current workflow queue with parameter forms and reorder controls."""
    queue = st.session_state.queue
    st.subheader(f"Workflow Queue  ({len(queue)} step{'s' if len(queue) != 1 else ''})")

    if not queue:
        st.info(
            "No operations yet.  "
            "Use **Add Operation** in the sidebar to build your workflow, "
            "or load a **Preset**."
        )
        return

    # Ensure every item has a stable _uid (needed for widget-key stability)
    _ensure_uids(queue)

    # Available columns for column/column_list widgets
    df_cols = (
        list(st.session_state.df_original.columns)
        if st.session_state.df_original is not None
        else []
    )

    # ── Pre-render sync ───────────────────────────────────────────────────────
    # Streamlit auto-stores widget values in session_state by key.
    # Mirror those back into queue[i]["parameters"] BEFORE rendering so that:
    #   • the param-summary reflects current user edits
    #   • the executor sees current values even before an explicit Save
    for item in queue:
        uid   = item["_uid"]
        op_id = item.get("operation_id", "")
        op    = registry.get_by_id(op_id)
        if op is None or not op.metadata.parameters:
            continue
        for param in op.metadata.parameters:
            key = param_widget_key(uid, param.name)
            if key in st.session_state:
                item["parameters"][param.name] = st.session_state[key]

    # Controls: clear all
    if st.button("🗑 Clear Queue", help="Remove all operations from the queue"):
        st.session_state.queue = []
        _reset_results()
        st.rerun()

    st.divider()

    to_remove    = None   # deferred mutations — avoids modifying list mid-loop
    to_move_up   = None
    to_move_down = None

    for i, item in enumerate(queue):
        uid      = item["_uid"]
        op_id    = item.get("operation_id", "?")
        label    = item.get("_label", op_id)
        category = item.get("_category", "")
        enabled  = item.get("enabled", True)
        params   = item.get("parameters", {})
        op       = registry.get_by_id(op_id)

        # Build a one-line parameter summary for the expander header
        param_parts = []
        for k, v in params.items():
            if v is None or v == "" or v == [] or v == {}:
                continue
            if isinstance(v, list):
                disp = ", ".join(str(x) for x in v[:3])
                if len(v) > 3:
                    disp += f" +{len(v)-3}"
            else:
                disp = str(v)[:40]
            param_parts.append(f"{k}: {disp}")
        param_summary = " | ".join(param_parts) if param_parts else "defaults"

        # ── Row: step# · name+category · enable · ▲ · ▼ · ✕ ─────────────────
        c_num, c_body, c_toggle, c_up, c_dn, c_del = st.columns([0.5, 5, 1, 0.7, 0.7, 0.7])
        with c_num:
            st.markdown(f"**{i+1}**")
        with c_body:
            strike = "~~" if not enabled else ""
            st.markdown(
                f"{strike}**{label}**{strike}  "
                f"<span style='color:#888;font-size:0.82em'>{category}</span>",
                unsafe_allow_html=True,
            )
        with c_toggle:
            new_enabled = st.checkbox(
                "On",
                value=enabled,
                key=f"q_enabled_{uid}",
                label_visibility="collapsed",
                help="Enable / disable this step",
            )
            if new_enabled != enabled:
                st.session_state.queue[i]["enabled"] = new_enabled
                _reset_results()
        with c_up:
            if st.button("▲", key=f"q_up_{uid}", disabled=(i == 0),
                         help="Move up"):
                to_move_up = i
        with c_dn:
            if st.button("▼", key=f"q_dn_{uid}", disabled=(i == len(queue) - 1),
                         help="Move down"):
                to_move_down = i
        with c_del:
            if st.button("✕", key=f"q_del_{uid}", help="Remove this step"):
                to_remove = i

        # ── Parameter form (collapsible expander) ─────────────────────────────
        if op is not None and op.metadata.parameters:
            with st.expander(f"Parameters  ·  {param_summary}", expanded=False):
                render_param_form(
                    operation=op,
                    available_columns=df_cols,
                    existing_params=params,
                    uid=uid,
                )
        else:
            st.caption(f"_No parameters · {param_summary}_")

        st.divider()

    # ── Deferred mutations (only one can fire per rerun) ─────────────────────
    if to_remove is not None:
        st.session_state.queue.pop(to_remove)
        _reset_results()
        st.rerun()
    elif to_move_up is not None:
        q = st.session_state.queue
        q[to_move_up - 1], q[to_move_up] = q[to_move_up], q[to_move_up - 1]
        _reset_results()
        st.rerun()
    elif to_move_down is not None:
        q = st.session_state.queue
        q[to_move_down], q[to_move_down + 1] = q[to_move_down + 1], q[to_move_down]
        _reset_results()
        st.rerun()


def _section_run() -> None:
    """Run the workflow queue against the uploaded file."""
    queue = [item for item in st.session_state.queue if item.get("enabled", True)]

    if not queue:
        st.button("▶  Run Workflow", disabled=True,
                  help="Add operations to the queue first")
        return

    if st.button("▶  Run Workflow", type="primary"):
        df_in      = st.session_state.df_original.copy()
        executor   = OperationExecutor()
        norm_queue = _normalize_queue_for_execution(st.session_state.queue)
        with st.spinner(f"Running {len(queue)} operation(s)…"):
            try:
                result_df, removed_df = executor.execute_queue_with_tracking(
                    df_in, norm_queue
                )
                st.session_state.df_result    = result_df
                st.session_state.df_removed   = removed_df
                st.session_state.run_complete = True
                st.session_state.run_error    = None
            except Exception as exc:
                st.session_state.run_complete = False
                st.session_state.run_error    = str(exc)
                logger.exception("Workflow execution failed")

    if st.session_state.run_error:
        st.error(f"Execution failed: {st.session_state.run_error}")


def _section_results() -> None:
    """Show result metrics, preview, and download button."""
    if not st.session_state.run_complete or st.session_state.df_result is None:
        return

    result_df:   pd.DataFrame = st.session_state.df_result
    original_df: pd.DataFrame = st.session_state.df_original
    removed_df                = st.session_state.df_removed

    st.divider()
    st.subheader("Results")

    rows_orig    = len(original_df)
    rows_result  = len(result_df)
    rows_removed = len(removed_df) if (removed_df is not None and not removed_df.empty) else 0
    cols_orig    = len(original_df.columns)
    cols_result  = len(result_df.columns)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Original Rows", f"{rows_orig:,}")
    m2.metric("Result Rows",   f"{rows_result:,}",
              delta=rows_result - rows_orig)
    m3.metric("Removed Rows",  f"{rows_removed:,}")
    m4.metric("Columns",       str(cols_result),
              delta=cols_result - cols_orig if cols_result != cols_orig else None)

    # Side-by-side tabs: Original preview | Result preview
    tab_result, tab_original, tab_removed = st.tabs(
        ["Result", "Original", "Removed Rows"]
    )
    with tab_result:
        total = len(result_df)
        if total > RESULT_ROWS:
            st.caption(f"Showing first {RESULT_ROWS:,} of {total:,} rows.")
        st.dataframe(result_df.head(RESULT_ROWS), use_container_width=True)
    with tab_original:
        st.dataframe(original_df.head(PREVIEW_ROWS), use_container_width=True)
    with tab_removed:
        if rows_removed:
            st.dataframe(removed_df.head(PREVIEW_ROWS), use_container_width=True)
        else:
            st.caption("No rows were removed.")

    st.divider()
    st.subheader("Download")

    out_name = _output_filename(st.session_state.filename)
    try:
        excel_bytes = _df_to_excel_bytes(result_df)
        st.download_button(
            label="⬇  Download Cleaned File (.xlsx)",
            data=excel_bytes,
            file_name=out_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
    except Exception as exc:
        st.warning(f"Excel export failed ({exc}). Falling back to CSV.")
        csv_bytes = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇  Download as CSV (fallback)",
            data=csv_bytes,
            file_name=Path(out_name).with_suffix(".csv").name,
            mime="text/csv",
        )


# ══════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════

def main() -> None:
    st.set_page_config(
        page_title="Clean Sheet",
        page_icon="🔷",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_state()
    _render_sidebar()

    # ── header ────────────────────────────────────────────────────────────
    st.title("🔷 Clean Sheet")
    st.caption("Professional Data Cleaning Made Simple  ·  Web Edition")
    st.divider()

    # ── step 1: upload ────────────────────────────────────────────────────
    file_ready = _section_upload()

    if not file_ready:
        st.info(
            "Upload a file to get started.  "
            "You can also build your workflow queue using the sidebar "
            "before uploading."
        )
        # Still show queue even without a file, so users can pre-build workflows
        if st.session_state.queue:
            st.divider()
            _section_queue()
        return

    df = st.session_state.df_original
    st.divider()

    # ── step 2: data inspection ───────────────────────────────────────────
    _section_data_info(df)
    st.divider()

    # ── step 3: workflow queue ────────────────────────────────────────────
    _section_queue()
    st.divider()

    # ── step 4: run ───────────────────────────────────────────────────────
    _section_run()

    # ── step 5: results + download ────────────────────────────────────────
    _section_results()


if __name__ == "__main__":
    main()
