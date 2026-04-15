"""
Clean Sheet - Streamlit Web App
================================
Browser-accessible MVP entrypoint.

Flow:
  1. Upload file (CSV / XLSX / XLS)
  2. Select a preset
  3. Run the preset against the uploaded data
  4. Preview results
  5. Download cleaned output as .xlsx

This file is completely independent of Tkinter.
It imports only from the clean backend modules:
  - operations/   (registry + all operations)
  - engine/executor.py
  - presets/preset_manager.py

Desktop app (main_gui_v2_office365.py) is unaffected.
Run desktop app:  py main_gui_v2_office365.py
Run this app:     streamlit run streamlit_app.py
"""

import sys
import logging
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — must happen before any local imports
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ---------------------------------------------------------------------------
# Backend imports — Tkinter-free
# ---------------------------------------------------------------------------
from operations import registry          # noqa: E402  (triggers all op registrations)
from engine.executor import OperationExecutor   # noqa: E402
from presets.preset_manager import PresetManager  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PREVIEW_ROWS = 500          # max rows shown in the result preview
ACCEPTED_TYPES = ["csv", "xlsx", "xls"]


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------

def _init_state() -> None:
    """Initialise all session-state keys on first run."""
    defaults = {
        "df_original": None,
        "df_result": None,
        "df_removed": None,
        "filename": None,
        "run_complete": False,
        "run_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_results() -> None:
    """Clear execution results (called when a new file is loaded)."""
    st.session_state.df_result = None
    st.session_state.df_removed = None
    st.session_state.run_complete = False
    st.session_state.run_error = None


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def _load_uploaded_file(uploaded_file) -> tuple:
    """
    Parse an uploaded file into a DataFrame.

    Returns:
        (df, error_message)  — error_message is None on success.
    """
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            # Try UTF-8 first; fall back to latin-1 for Windows-origin files
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding="latin-1")
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file, sheet_name=0, engine="openpyxl")
        else:
            return None, f"Unsupported file type: '{uploaded_file.name}'. Please upload CSV, XLSX, or XLS."
    except Exception as exc:
        return None, f"Could not parse '{uploaded_file.name}': {exc}"

    if df is None or df.empty:
        return None, f"'{uploaded_file.name}' loaded but contains no data."

    return df, None


# ---------------------------------------------------------------------------
# Preset loading
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _get_preset_manager() -> PresetManager:
    """Single shared PresetManager instance (cached for the server lifetime)."""
    return PresetManager()


def _list_presets():
    """Load all available presets, sorted alphabetically by name."""
    try:
        pm = _get_preset_manager()
        presets = pm.list_presets()
        return sorted(presets, key=lambda p: p.name.lower())
    except Exception as exc:
        logger.error("Failed to list presets: %s", exc)
        return []


def _ops_for_executor(preset):
    """
    Convert a Preset's operations list into the List[Dict] format
    that OperationExecutor.execute_queue_with_tracking() expects.

    Each dict needs at minimum: operation_id, parameters, enabled.
    OperationConfig.to_dict() provides all of these.
    """
    result = []
    for op in preset.operations:
        if hasattr(op, "to_dict"):
            result.append(op.to_dict())
        elif isinstance(op, dict):
            result.append(op)
        else:
            logger.warning("Unexpected operation type %s — skipping", type(op))
    return result


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to an in-memory .xlsx and return raw bytes."""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cleaned Data")
    return buf.getvalue()


def _output_filename(original_name: str) -> str:
    """Build the download filename from the original upload name."""
    stem = Path(original_name).stem
    return f"{stem}_cleaned.xlsx"


# ---------------------------------------------------------------------------
# UI sections
# ---------------------------------------------------------------------------

def _section_upload() -> bool:
    """
    Render the file-upload section.

    Returns True if a valid DataFrame is loaded in session state.
    """
    st.subheader("1  Upload File")

    uploaded = st.file_uploader(
        "Choose a CSV or Excel file",
        type=ACCEPTED_TYPES,
        help="Supported formats: .csv  .xlsx  .xls",
        label_visibility="collapsed",
    )

    if uploaded is None:
        st.caption("No file uploaded yet.")
        return False

    # Detect a fresh upload (different filename or first load)
    if st.session_state.filename != uploaded.name:
        df, err = _load_uploaded_file(uploaded)
        if err:
            st.error(err)
            st.session_state.df_original = None
            st.session_state.filename = None
            _reset_results()
            return False
        st.session_state.df_original = df
        st.session_state.filename = uploaded.name
        _reset_results()

    if st.session_state.df_original is None:
        return False

    df = st.session_state.df_original
    st.success(
        f"**{st.session_state.filename}** — "
        f"{len(df):,} rows × {len(df.columns)} columns"
    )

    with st.expander("Preview original data (first 100 rows)", expanded=False):
        st.dataframe(df.head(100), use_container_width=True)

    return True


def _section_preset() -> object:
    """
    Render the preset-selection section.

    Returns the selected Preset object, or None if none available / selected.
    """
    st.subheader("2  Select Preset")

    presets = _list_presets()

    if not presets:
        st.warning(
            "No presets found. "
            "Check that `presets/system/` or `presets/user/` contain .json files."
        )
        return None

    # Build label → preset mapping
    labels = []
    by_label = {}
    for p in presets:
        label = f"{p.name}  [{p.category}]"
        labels.append(label)
        by_label[label] = p

    selected_label = st.selectbox(
        "Choose a workflow preset",
        options=labels,
        help="Each preset is a saved sequence of cleaning operations.",
        label_visibility="visible",
    )
    selected = by_label[selected_label]

    # Info row
    enabled_ops = [
        op for op in selected.operations
        if (op.enabled if hasattr(op, "enabled") else op.get("enabled", True))
    ]
    n_total = len(selected.operations)
    n_enabled = len(enabled_ops)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        if selected.description:
            st.caption(selected.description)
    with col_b:
        st.caption(f"{n_enabled} / {n_total} operations enabled")

    with st.expander("View operations in this preset", expanded=False):
        if not selected.operations:
            st.write("_No operations defined._")
        else:
            for i, op in enumerate(selected.operations, start=1):
                op_id = (
                    op.operation_id
                    if hasattr(op, "operation_id")
                    else op.get("operation_id", "unknown")
                )
                enabled = (
                    op.enabled
                    if hasattr(op, "enabled")
                    else op.get("enabled", True)
                )
                icon = "✓" if enabled else "⏸"
                # Try to get a human-readable name from the registry
                reg_op = registry.get_by_id(op_id)
                display = reg_op.metadata.name if reg_op else op_id
                st.text(f"  {i}. {icon}  {display}")

    return selected


def _section_run(preset) -> None:
    """Render the Run button and execute the preset."""
    st.subheader("3  Run Preset")

    if st.button("▶  Run Preset", type="primary"):
        df_in = st.session_state.df_original.copy()
        op_dicts = _ops_for_executor(preset)

        if not op_dicts:
            st.warning("This preset has no operations. Nothing to run.")
            return

        executor = OperationExecutor()
        with st.spinner("Running operations…"):
            try:
                result_df, removed_df = executor.execute_queue_with_tracking(
                    df_in, op_dicts
                )
                st.session_state.df_result = result_df
                st.session_state.df_removed = removed_df
                st.session_state.run_complete = True
                st.session_state.run_error = None
            except Exception as exc:
                st.session_state.run_complete = False
                st.session_state.run_error = str(exc)
                logger.exception("Preset execution failed")

    if st.session_state.run_error:
        st.error(f"Preset execution failed: {st.session_state.run_error}")


def _section_results() -> None:
    """Render the result summary, preview table, and download button."""
    if not st.session_state.run_complete:
        return
    if st.session_state.df_result is None:
        return

    result_df: pd.DataFrame = st.session_state.df_result
    original_df: pd.DataFrame = st.session_state.df_original
    removed_df = st.session_state.df_removed

    st.divider()
    st.subheader("4  Results")

    # --- Metrics ---
    rows_orig = len(original_df)
    rows_result = len(result_df)
    rows_removed = (
        len(removed_df)
        if removed_df is not None and not removed_df.empty
        else 0
    )
    cols_orig = len(original_df.columns)
    cols_result = len(result_df.columns)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Original Rows", f"{rows_orig:,}")
    m2.metric("Result Rows", f"{rows_result:,}", delta=rows_result - rows_orig)
    m3.metric("Removed Rows", f"{rows_removed:,}")
    m4.metric(
        "Columns",
        f"{cols_result}",
        delta=cols_result - cols_orig if cols_result != cols_orig else None,
    )

    # --- Preview table ---
    total_rows = len(result_df)
    caption_suffix = (
        f"Showing first {PREVIEW_ROWS:,} of {total_rows:,} rows."
        if total_rows > PREVIEW_ROWS
        else f"All {total_rows:,} rows shown."
    )
    st.caption(caption_suffix)
    st.dataframe(result_df.head(PREVIEW_ROWS), use_container_width=True)

    # --- Download ---
    st.divider()
    st.subheader("5  Download")

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
        csv_name = Path(out_name).with_suffix(".csv").name
        st.download_button(
            label="⬇  Download as CSV (fallback)",
            data=csv_bytes,
            file_name=csv_name,
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Clean Sheet",
        page_icon="🔷",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    _init_state()

    # Header
    st.title("🔷 Clean Sheet")
    st.caption("Professional Data Cleaning Made Simple  ·  Web Edition")
    st.divider()

    # Step 1 — upload
    file_ready = _section_upload()
    if not file_ready:
        st.info("Upload a file above to get started.")
        return

    st.divider()

    # Step 2 — preset
    selected_preset = _section_preset()
    if selected_preset is None:
        return

    st.divider()

    # Step 3 — run
    _section_run(selected_preset)

    # Step 4 + 5 — results + download
    _section_results()


if __name__ == "__main__":
    main()
