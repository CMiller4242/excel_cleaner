"""
Preset Initializer Module
Initializes user's preset directory with system presets on first run
"""

import json
import logging
import shutil
from pathlib import Path
from typing import List, Tuple

# Set up logging
logger = logging.getLogger("PresetInitializer")
logger.setLevel(logging.DEBUG)


def get_user_preset_directory() -> Path:
    """
    Get the user's preset directory path

    Returns:
        Path to user preset directory
    """
    return Path.home() / ".universal_excel_tool" / "presets"


def get_system_preset_directory() -> Path:
    """
    Get the system preset directory path (in project)

    Returns:
        Path to system preset directory
    """
    # Get project root (go up from utils/)
    project_root = Path(__file__).parent.parent
    return project_root / "presets" / "system"


def initialize_preset_directory(force_overwrite: bool = False) -> Tuple[bool, str, List[str]]:
    """
    Initialize user's preset directory with system presets

    Args:
        force_overwrite: If True, overwrites existing preset files

    Returns:
        Tuple of (success, message, copied_files)
        - success: True if initialization successful
        - message: Status message
        - copied_files: List of preset files that were copied
    """
    user_dir = get_user_preset_directory()
    system_dir = get_system_preset_directory()

    logger.info(f"Initializing preset directory: {user_dir}")
    logger.debug(f"System preset directory: {system_dir}")

    # Create user preset directory if it doesn't exist
    try:
        user_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"User preset directory ready: {user_dir}")
    except Exception as e:
        error_msg = f"Failed to create preset directory: {e}"
        logger.error(error_msg)
        return False, error_msg, []

    # Check if system preset directory exists
    if not system_dir.exists():
        error_msg = f"System preset directory not found: {system_dir}"
        logger.error(error_msg)
        return False, error_msg, []

    # Find all JSON files in system preset directory
    system_presets = list(system_dir.glob("*.json"))

    if not system_presets:
        warning_msg = f"No system presets found in {system_dir}"
        logger.warning(warning_msg)
        return True, warning_msg, []

    logger.info(f"Found {len(system_presets)} system presets to copy")

    # Copy each preset file
    copied_files = []
    skipped_files = []

    for system_preset in system_presets:
        user_preset = user_dir / system_preset.name

        # Skip if file exists and not forcing overwrite
        if user_preset.exists() and not force_overwrite:
            logger.debug(f"Skipping existing preset: {system_preset.name}")
            skipped_files.append(system_preset.name)
            continue

        try:
            # Copy preset file
            shutil.copy2(system_preset, user_preset)
            logger.info(f"Copied preset: {system_preset.name}")
            copied_files.append(system_preset.name)

        except Exception as e:
            logger.error(f"Failed to copy {system_preset.name}: {e}")
            continue

    # Build success message
    if copied_files:
        message = f"Initialized {len(copied_files)} preset(s): {', '.join(copied_files)}"
    elif skipped_files:
        message = f"Preset directory already initialized ({len(skipped_files)} preset(s) exist)"
    else:
        message = "No presets copied"

    logger.info(message)
    return True, message, copied_files


def ensure_zoominfo_healthcare_preset() -> bool:
    """
    Ensure ZoomInfo Healthcare preset exists in user directory

    Returns:
        True if preset exists or was created successfully
    """
    user_dir = get_user_preset_directory()
    preset_file = user_dir / "zoominfo_healthcare_evs.json"

    # Check if preset already exists
    if preset_file.exists():
        logger.debug(f"ZoomInfo Healthcare preset already exists: {preset_file}")
        return True

    # Create user directory if it doesn't exist
    try:
        user_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create preset directory: {e}")
        return False

    # Try to copy from system directory
    system_dir = get_system_preset_directory()
    system_preset = system_dir / "zoominfo_healthcare_evs.json"

    if system_preset.exists():
        try:
            shutil.copy2(system_preset, preset_file)
            logger.info(f"Copied ZoomInfo Healthcare preset to: {preset_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy preset: {e}")
            return False
    else:
        logger.error(f"System preset not found: {system_preset}")
        return False


def list_available_system_presets() -> List[str]:
    """
    List all available system presets

    Returns:
        List of system preset filenames
    """
    system_dir = get_system_preset_directory()

    if not system_dir.exists():
        logger.warning(f"System preset directory not found: {system_dir}")
        return []

    preset_files = list(system_dir.glob("*.json"))
    preset_names = [p.name for p in preset_files]

    logger.debug(f"Found {len(preset_names)} system presets: {preset_names}")
    return preset_names


def validate_preset_file(preset_path: Path) -> Tuple[bool, str]:
    """
    Validate a preset JSON file

    Args:
        preset_path: Path to preset file

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not preset_path.exists():
        return False, f"File not found: {preset_path}"

    try:
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)

        # Check required fields
        required_fields = ['id', 'name', 'operations']
        missing_fields = [field for field in required_fields if field not in preset_data]

        if missing_fields:
            return False, f"Missing required field(s): {', '.join(missing_fields)}"

        # Check operations is a list
        if not isinstance(preset_data['operations'], list):
            return False, "'operations' must be a list"

        # Validate each operation
        for idx, op in enumerate(preset_data['operations']):
            if 'operation_id' not in op:
                return False, f"Operation {idx} missing 'operation_id'"

        return True, "Valid"

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"


# Convenience function for GUI initialization
def initialize_presets_on_startup() -> bool:
    """
    Initialize preset system on application startup
    Call this from your main application __init__

    Returns:
        True if initialization successful
    """
    try:
        success, message, copied_files = initialize_preset_directory(force_overwrite=False)

        if success:
            logger.info(f"Preset initialization complete: {message}")
            return True
        else:
            logger.error(f"Preset initialization failed: {message}")
            return False

    except Exception as e:
        logger.error(f"Error during preset initialization: {e}")
        return False
