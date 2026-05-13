"""
Smart Format Preset Manager

Manages save/load of Smart Format presets (mapping + operations plan).
These are SEPARATE from normal workflow presets (presets/preset_manager.py).

Storage locations:
  System presets : <repo>/presets/smart_format/   (read-only)
  User presets   : ~/.config/CleanSheet/smart_presets/  (read-write)

Preset JSON schema (example at bottom of file).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Directory resolution
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent          # excel_cleaner/
_SYSTEM_DIR = _REPO_ROOT / "presets" / "smart_format"
_USER_DIR = Path.home() / ".config" / "CleanSheet" / "smart_presets"

# Schema version for forward-compat checks
SCHEMA_VERSION = "1"
TEMPLATE_ID_MAIL_STANDARD = "MAIL_STANDARD_V1"
TEMPLATE_ID_BCC_MAIL = "BCC_MAIL_V1"


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class SmartPresetManager:
    """Load and save Smart Format presets independently of workflow presets."""

    def __init__(
        self,
        system_dir: Optional[Path] = None,
        user_dir: Optional[Path] = None,
    ):
        self.system_dir: Path = system_dir or _SYSTEM_DIR
        self.user_dir: Path = user_dir or _USER_DIR

        # Create directories on first use
        self.system_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_presets(self) -> List[Dict]:
        """
        Return all available smart presets as a list of dicts.

        Each dict has at minimum:
          name, template_id, schema_version, _is_system, _file_path
        """
        presets: List[Dict] = []
        for directory, is_system in [
            (self.system_dir, True),
            (self.user_dir, False),
        ]:
            for filepath in sorted(directory.glob("*.json")):
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    data["_is_system"] = is_system
                    data["_file_path"] = str(filepath)
                    presets.append(data)
                except Exception as exc:
                    logger.warning("Failed to read smart preset %s: %s", filepath, exc)
        return presets

    def list_preset_names(self) -> List[str]:
        """Convenience: return preset display names in order (system first)."""
        return [p.get("name", p.get("_file_path", "?")) for p in self.list_presets()]

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load_preset_by_name(self, name: str) -> Optional[Dict]:
        """Load a preset by its display name. User presets shadow system ones."""
        # Search user dir first, then system
        for directory in (self.user_dir, self.system_dir):
            for filepath in directory.glob("*.json"):
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    if data.get("name") == name:
                        return data
                except Exception:
                    pass
        return None

    def load_preset_by_filename(self, filename: str) -> Optional[Dict]:
        """Load a preset by its filename (without .json)."""
        for directory in (self.user_dir, self.system_dir):
            filepath = directory / f"{filename}.json"
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        return json.load(fh)
                except Exception as exc:
                    logger.warning("Failed to read %s: %s", filepath, exc)
        return None

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_preset(self, name: str, smart_format_config: Dict) -> bool:
        """
        Persist a Smart Format config as a named preset.

        Parameters
        ----------
        name : str
            Human-readable preset name (used as JSON ``name`` field and
            derived for filename).
        smart_format_config : dict
            The config dict stored in SheetState.smart_format.
            Must include ``mapping_config`` and ``operations_plan``.

        Returns
        -------
        bool
            True on success.
        """
        try:
            filename = self._name_to_filename(name)
            preset = {
                "name": name,
                "template_id": smart_format_config.get("template_id", TEMPLATE_ID_MAIL_STANDARD),
                "schema_version": SCHEMA_VERSION,
                "mapping_config": smart_format_config.get("mapping_config", {}),
                "operations_plan": smart_format_config.get("operations_plan", {}),
                "created_at": datetime.now().isoformat(),
                "notes": smart_format_config.get("notes", ""),
            }
            filepath = self.user_dir / f"{filename}.json"
            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(preset, fh, indent=2, default=str)
            logger.info("Saved smart preset '%s' → %s", name, filepath)
            return True
        except Exception as exc:
            logger.error("Failed to save smart preset '%s': %s", name, exc)
            return False

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_preset(self, name: str) -> bool:
        """Delete a user smart preset by name. System presets cannot be deleted."""
        filename = self._name_to_filename(name)
        filepath = self.user_dir / f"{filename}.json"
        if filepath.exists():
            try:
                filepath.unlink()
                logger.info("Deleted smart preset '%s'", name)
                return True
            except Exception as exc:
                logger.warning("Could not delete smart preset '%s': %s", name, exc)
        return False

    # ------------------------------------------------------------------
    # Compatibility check
    # ------------------------------------------------------------------

    @staticmethod
    def validate_preset_against_columns(
        preset: Dict,
        available_columns: List[str],
    ) -> Dict[str, List[str]]:
        """
        Check which mapped source columns in the preset are present or missing
        in ``available_columns``.

        Returns
        -------
        dict with keys:
          "resolved"   – list of target cols whose source is present
          "unresolved" – list of target cols whose source is absent
          "blank"      – list of target cols mapped to blank/None
        """
        mapping_config = preset.get("mapping_config", {})
        col_map: Dict = mapping_config.get("column_map", {})
        available = set(available_columns)

        resolved, unresolved, blank = [], [], []
        for target, source in col_map.items():
            if not source or source == "(blank)":
                blank.append(target)
            elif source == "__derived__":
                resolved.append(target)
            elif source in available:
                resolved.append(target)
            else:
                unresolved.append(target)

        return {"resolved": resolved, "unresolved": unresolved, "blank": blank}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _name_to_filename(name: str) -> str:
        """Convert a preset name to a safe filename (no extension)."""
        safe = re.sub(r"[^\w\s\-]", "", name).strip()
        safe = re.sub(r"\s+", "_", safe).lower()
        return safe or "unnamed_preset"


# ---------------------------------------------------------------------------
# Example preset JSON schema (for documentation)
# ---------------------------------------------------------------------------
#
# {
#   "name": "My Mail Standard Preset",
#   "template_id": "MAIL_STANDARD_V1",
#   "schema_version": "1",
#   "mapping_config": {
#     "column_map": {
#       "KeyCode":          null,
#       "Cust":             "Customer Number",
#       "Company":          "Company Name",
#       "Address1":         "Address",
#       "City":             "City",
#       "State":            "State",
#       "Zip":              "Zip Code",
#       "Contact":          "__derived__",
#       "Email Address":    "Email",
#       ...
#     },
#     "derivation_plan": "build_first_last",
#     "first_col":         "First Name",
#     "last_col":          "Last Name"
#   },
#   "operations_plan": {
#     "dedupe": {
#       "enabled": true,
#       "keys": ["Email Address", "Company", "Zip"]
#     },
#     "remove_rows_containing": {
#       "enabled": true,
#       "columns": ["Address1"],
#       "patterns": "PO BOX, P.O. BOX",
#       "match_type": "contains"
#     },
#     "remove_blank_rows": {
#       "enabled": false,
#       "columns": []
#     }
#   },
#   "created_at": "2026-02-19T10:00:00",
#   "notes": ""
# }
