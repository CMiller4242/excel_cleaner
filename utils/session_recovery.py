"""
Session Auto-Recovery for CleanSheet
Lightweight session persistence for workbook state (no dataframes stored)
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import platform
import os
from datetime import datetime


logger = logging.getLogger(__name__)


def get_session_directory() -> Path:
    """
    Get platform-specific session directory

    Returns:
        Path to session directory (creates if doesn't exist)
    """
    system = platform.system()

    if system == "Windows":
        # Windows: %APPDATA%/CleanSheet/session
        appdata = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        session_dir = appdata / 'CleanSheet' / 'session'
    else:
        # Linux/macOS: ~/.config/CleanSheet/session
        config_home = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
        session_dir = config_home / 'CleanSheet' / 'session'

    # Create directory if it doesn't exist
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


class SessionRecovery:
    """
    Handles saving and restoring workbook session state
    Does NOT store dataframes - only metadata and operations
    """

    def __init__(self):
        self.session_dir = get_session_directory()
        self.session_file = self.session_dir / 'last_session.json'
        self._save_pending = False
        self._save_timer_id = None

    def save_session(self, workbook_session, last_export_path: Optional[str] = None, debounce_ms: int = 500):
        """
        Save workbook session state (debounced to prevent disk thrashing)

        Args:
            workbook_session: WorkbookSession instance
            last_export_path: Optional path to last export location
            debounce_ms: Milliseconds to wait before actually saving
        """
        if workbook_session is None:
            logger.debug("No workbook session to save")
            return

        # Mark save as pending
        self._save_pending = True

        # Actual save will happen after debounce delay
        # This is handled by the caller using after() in tkinter
        try:
            self._perform_save(workbook_session, last_export_path)
        except Exception as e:
            logger.error(f"Failed to save session: {e}", exc_info=True)

    def _perform_save(self, workbook_session, last_export_path: Optional[str] = None):
        """
        Actually perform the session save (internal method)
        """
        session_data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'file_path': workbook_session.file_path,
            'is_excel': workbook_session.is_excel,
            'sheet_names': workbook_session.sheet_names,
            'active_sheet': workbook_session.active_sheet,
            'deleted_sheets': list(workbook_session.deleted_sheets),
            'last_export_path': last_export_path,
            'sheets': {}
        }

        # Save per-sheet metadata (NO dataframes)
        for sheet_name, sheet_state in workbook_session.sheets.items():
            session_data['sheets'][sheet_name] = {
                'sheet_name_display': sheet_state.sheet_name_display,
                'is_deleted': sheet_state.is_deleted,
                'is_loaded': sheet_state.is_loaded,
                'has_results': sheet_state.has_results(),
                'operations': sheet_state.operations,  # This is just metadata/config
                'issues': [
                    {
                        'sheet_name': issue.sheet_name,
                        'op_index': issue.op_index,
                        'op_label': issue.op_label,
                        'code': issue.code,
                        'message': issue.message,
                        'details': issue.details
                    }
                    for issue in sheet_state.issues
                ]
            }

        # Write to file
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)

        self._save_pending = False
        logger.info(f"Session saved: {workbook_session.file_name} ({len(workbook_session.sheets)} sheets)")

    def load_session(self) -> Optional[Dict[str, Any]]:
        """
        Load saved session if it exists and is valid

        Returns:
            Session data dict or None if no valid session
        """
        if not self.session_file.exists():
            logger.debug("No saved session found")
            return None

        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Validate required fields
            required_fields = ['file_path', 'is_excel', 'sheet_names', 'sheets']
            for field in required_fields:
                if field not in session_data:
                    logger.warning(f"Invalid session: missing field '{field}'")
                    return None

            # Check if file still exists
            file_path = Path(session_data['file_path'])
            if not file_path.exists():
                logger.info(f"Session file no longer exists: {file_path}")
                return None

            logger.info(f"Loaded session: {file_path.name} (saved: {session_data.get('timestamp', 'unknown')})")
            return session_data

        except Exception as e:
            logger.error(f"Failed to load session: {e}", exc_info=True)
            return None

    def clear_session(self):
        """
        Clear saved session (e.g., after successful restore or on discard)
        """
        if self.session_file.exists():
            try:
                self.session_file.unlink()
                logger.info("Session cleared")
            except Exception as e:
                logger.error(f"Failed to clear session: {e}")

    def restore_session_to_workbook(self, session_data: Dict[str, Any], workbook_session):
        """
        Restore session data into a WorkbookSession instance

        Args:
            session_data: Loaded session data
            workbook_session: WorkbookSession instance to restore into

        Note:
            Dataframes are NOT restored - they remain lazy-loaded
        """
        from workbook_session import SheetState, Issue

        # Restore basic session info
        workbook_session.file_path = session_data['file_path']
        workbook_session.is_excel = session_data['is_excel']
        workbook_session.sheet_names = session_data['sheet_names']
        workbook_session.active_sheet = session_data.get('active_sheet')
        workbook_session.deleted_sheets = set(session_data.get('deleted_sheets', []))

        # Restore per-sheet state
        for sheet_name, sheet_data in session_data['sheets'].items():
            sheet_state = SheetState(sheet_name_original=sheet_name)
            sheet_state.sheet_name_display = sheet_data.get('sheet_name_display', sheet_name)
            sheet_state.is_deleted = sheet_data.get('is_deleted', False)
            sheet_state.is_loaded = False  # Always start with lazy load
            sheet_state.operations = sheet_data.get('operations', [])

            # Restore issues
            for issue_data in sheet_data.get('issues', []):
                issue = Issue(
                    sheet_name=issue_data['sheet_name'],
                    op_index=issue_data['op_index'],
                    op_label=issue_data['op_label'],
                    code=issue_data['code'],
                    message=issue_data['message'],
                    details=issue_data.get('details', {})
                )
                sheet_state.issues.append(issue)

            workbook_session.sheets[sheet_name] = sheet_state

        logger.info(f"Session restored: {len(workbook_session.sheets)} sheets")

    def has_saved_session(self) -> bool:
        """
        Check if a saved session exists

        Returns:
            True if session file exists
        """
        return self.session_file.exists()
