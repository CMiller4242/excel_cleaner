"""
Workbook Session Management for Multi-Sheet Excel Files
Handles per-sheet state, workflows, validation, and lazy loading
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set, Any
import pandas as pd
from pathlib import Path
import copy


@dataclass
class Issue:
    """Validation issue for an operation on a specific sheet"""
    sheet_name: str
    op_index: int
    op_label: str
    code: str  # MISSING_COLUMNS, INVALID_MAPPING, etc.
    message: str
    details: Dict[str, Any] = field(default_factory=dict)  # missing_columns, etc.

    def __str__(self):
        return f"[{self.code}] {self.op_label} on '{self.sheet_name}': {self.message}"


@dataclass
class SheetState:
    """State for a single sheet in the workbook"""
    sheet_name_original: str
    sheet_name_display: str = field(default="")
    df_original: Optional[pd.DataFrame] = None
    df_result: Optional[pd.DataFrame] = None
    operations: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    removed_rows: Optional[pd.DataFrame] = None
    undo_stack: List[List[Dict[str, Any]]] = field(default_factory=list)
    redo_stack: List[List[Dict[str, Any]]] = field(default_factory=list)
    is_loaded: bool = False  # Track if df_original has been loaded
    is_dirty: bool = False  # Track if there are unsaved changes
    is_deleted: bool = False  # Soft delete flag

    def __post_init__(self):
        if not self.sheet_name_display:
            self.sheet_name_display = self.sheet_name_original

    def mark_dirty(self):
        """Mark this sheet as having unsaved changes"""
        self.is_dirty = True

    def mark_clean(self):
        """Mark this sheet as clean (changes saved)"""
        self.is_dirty = False

    def has_results(self) -> bool:
        """Check if this sheet has result data"""
        return self.df_result is not None and not self.df_result.empty

    def has_issues(self) -> bool:
        """Check if this sheet has validation issues"""
        return len(self.issues) > 0

    def clear_issues(self):
        """Clear all validation issues"""
        self.issues.clear()

    def add_issue(self, issue: Issue):
        """Add a validation issue"""
        self.issues.append(issue)

    def push_undo(self):
        """Save current operations state to undo stack"""
        self.undo_stack.append(copy.deepcopy(self.operations))
        self.redo_stack.clear()  # Clear redo when new change made
        # Limit undo stack size
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self) -> bool:
        """Undo last workflow change. Returns True if successful."""
        if not self.undo_stack:
            return False
        self.redo_stack.append(copy.deepcopy(self.operations))
        self.operations = self.undo_stack.pop()
        self.mark_dirty()
        return True

    def redo(self) -> bool:
        """Redo last undone change. Returns True if successful."""
        if not self.redo_stack:
            return False
        self.undo_stack.append(copy.deepcopy(self.operations))
        self.operations = self.redo_stack.pop()
        self.mark_dirty()
        return True


class WorkbookSession:
    """
    Manages state for a multi-sheet Excel workbook in single-file mode
    Handles per-sheet workflows, lazy loading, and validation
    """

    def __init__(self, file_path: str, is_excel: bool = True):
        self.file_path = file_path
        self.is_excel = is_excel
        self.sheet_names: List[str] = []
        self.active_sheet: Optional[str] = None
        self.sheets: Dict[str, SheetState] = {}
        self.deleted_sheets: Set[str] = set()
        self.file_name = Path(file_path).name
        self.extra_sheets: Dict[str, pd.DataFrame] = {}  # For tool-generated sheets like EMAIL_VALIDATION

    def initialize_from_excel(self, sheet_names: List[str]):
        """Initialize workbook session from Excel file sheet names (lazy load)"""
        self.sheet_names = sheet_names
        for sheet_name in sheet_names:
            self.sheets[sheet_name] = SheetState(sheet_name_original=sheet_name)
        if sheet_names:
            self.active_sheet = sheet_names[0]

    def initialize_from_csv(self, df: pd.DataFrame):
        """Initialize workbook session from CSV (single sheet)"""
        self.is_excel = False
        self.sheet_names = ["Sheet1"]
        self.active_sheet = "Sheet1"
        sheet_state = SheetState(
            sheet_name_original="Sheet1",
            df_original=df,
            is_loaded=True
        )
        self.sheets["Sheet1"] = sheet_state

    def get_active_sheet(self) -> Optional[SheetState]:
        """Get the currently active sheet state"""
        if self.active_sheet and self.active_sheet in self.sheets:
            return self.sheets[self.active_sheet]
        return None

    def get_sheet(self, sheet_name: str) -> Optional[SheetState]:
        """Get a specific sheet state by name"""
        return self.sheets.get(sheet_name)

    def switch_to_sheet(self, sheet_name: str) -> bool:
        """Switch active sheet. Returns True if successful."""
        if sheet_name in self.sheets and sheet_name not in self.deleted_sheets:
            self.active_sheet = sheet_name
            return True
        return False

    def load_sheet_data(self, sheet_name: str, df: pd.DataFrame):
        """Load dataframe for a specific sheet (lazy load callback)"""
        if sheet_name in self.sheets:
            self.sheets[sheet_name].df_original = df
            self.sheets[sheet_name].is_loaded = True

    def rename_sheet(self, old_name: str, new_name: str) -> bool:
        """Rename a sheet. Returns True if successful."""
        if old_name not in self.sheets or new_name in self.sheets:
            return False

        # Update sheet state
        sheet_state = self.sheets[old_name]
        sheet_state.sheet_name_display = new_name

        # Update sheet dict (keep original key but update display name)
        # We keep the original key to preserve lazy loading logic
        return True

    def soft_delete_sheet(self, sheet_name: str) -> bool:
        """Soft delete a sheet (hide but keep in session). Returns True if successful."""
        if sheet_name not in self.sheets or sheet_name in self.deleted_sheets:
            return False

        self.deleted_sheets.add(sheet_name)
        self.sheets[sheet_name].is_deleted = True

        # Switch to another sheet if this was active
        if self.active_sheet == sheet_name:
            active_sheets = [s for s in self.sheet_names if s not in self.deleted_sheets]
            self.active_sheet = active_sheets[0] if active_sheets else None

        return True

    def restore_sheet(self, sheet_name: str) -> bool:
        """Restore a soft-deleted sheet. Returns True if successful."""
        if sheet_name not in self.deleted_sheets:
            return False

        self.deleted_sheets.remove(sheet_name)
        self.sheets[sheet_name].is_deleted = False
        return True

    def get_visible_sheets(self) -> List[str]:
        """Get list of visible (non-deleted) sheet names"""
        return [s for s in self.sheet_names if s not in self.deleted_sheets]

    def get_all_issues(self) -> List[Issue]:
        """Get all validation issues across all sheets"""
        all_issues = []
        for sheet_state in self.sheets.values():
            all_issues.extend(sheet_state.issues)
        return all_issues

    def has_any_issues(self) -> bool:
        """Check if any sheet has validation issues"""
        return any(sheet.has_issues() for sheet in self.sheets.values())

    def apply_preset_to_sheets(self, preset_operations: List[Dict], sheet_names: List[str]):
        """Apply preset operations to selected sheets"""
        for sheet_name in sheet_names:
            if sheet_name in self.sheets:
                sheet_state = self.sheets[sheet_name]
                # Push current state to undo before applying preset
                sheet_state.push_undo()
                # Apply preset
                sheet_state.operations = copy.deepcopy(preset_operations)
                sheet_state.df_result = None  # Clear results
                sheet_state.clear_issues()  # Clear issues
                sheet_state.mark_dirty()

    def clear_all_results(self):
        """Clear all result data from all sheets"""
        for sheet_state in self.sheets.values():
            sheet_state.df_result = None
            sheet_state.removed_rows = None
            sheet_state.clear_issues()

    def get_export_data(self) -> Dict[str, pd.DataFrame]:
        """
        Get data ready for export
        Returns dict of {sheet_name: dataframe} including REMOVED_ROWS sheet
        """
        export_sheets = {}

        # Export all non-deleted sheets
        for sheet_name in self.sheet_names:
            if sheet_name in self.deleted_sheets:
                continue

            sheet_state = self.sheets[sheet_name]
            display_name = sheet_state.sheet_name_display

            # Use result if available and valid, otherwise original
            if sheet_state.has_results() and not sheet_state.has_issues():
                export_sheets[display_name] = sheet_state.df_result
            elif sheet_state.df_original is not None:
                export_sheets[display_name] = sheet_state.df_original

        # Build combined REMOVED_ROWS sheet
        removed_rows_list = []
        for sheet_name in self.sheet_names:
            if sheet_name in self.deleted_sheets:
                continue

            sheet_state = self.sheets[sheet_name]
            if sheet_state.removed_rows is not None and not sheet_state.removed_rows.empty:
                df_removed = sheet_state.removed_rows.copy()
                df_removed.insert(0, 'SourceSheet', sheet_state.sheet_name_display)
                if 'SourceRowIndex' not in df_removed.columns:
                    df_removed.insert(1, 'SourceRowIndex', range(len(df_removed)))
                if 'RemovedReason' not in df_removed.columns:
                    df_removed.insert(2, 'RemovedReason', '')
                removed_rows_list.append(df_removed)

        if removed_rows_list:
            combined_removed = pd.concat(removed_rows_list, ignore_index=True)
            export_sheets['REMOVED_ROWS'] = combined_removed

        # Add extra sheets (e.g., EMAIL_VALIDATION from tool actions)
        for sheet_name, df in self.extra_sheets.items():
            if df is not None and not df.empty:
                export_sheets[sheet_name] = df

        return export_sheets

    def __repr__(self):
        return f"WorkbookSession(file={self.file_name}, sheets={len(self.sheet_names)}, active={self.active_sheet})"
