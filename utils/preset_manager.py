"""
Preset Manager Module
Handles loading, saving, and managing operation presets
Includes ZoomInfo file detection
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd

# Set up logging
logger = logging.getLogger("PresetManager")
logger.setLevel(logging.DEBUG)


class PresetManager:
    """Manages operation presets and file type detection"""

    def __init__(self, preset_directory: str = None):
        """
        Initialize preset manager

        Args:
            preset_directory: Path to directory containing presets.
                            Defaults to ~/.universal_excel_tool/presets
        """
        if preset_directory is None:
            # Default to user home directory
            preset_directory = Path.home() / ".universal_excel_tool" / "presets"

        self.preset_directory = Path(preset_directory)

        # Create directory if it doesn't exist
        try:
            self.preset_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Preset directory ready: {self.preset_directory}")
        except Exception as e:
            logger.error(f"Failed to create preset directory: {e}")
            raise

        # Initialize preset registry (in-memory cache)
        self._presets_cache = {}

        # Load all presets on startup
        self._load_all_presets_to_cache()

        logger.info(f"PresetManager initialized with {len(self._presets_cache)} presets")

    def _load_all_presets_to_cache(self):
        """
        Load all preset JSON files from the presets directory into memory cache.
        Called on startup to populate preset registry.
        """
        try:
            # Find all .json files in preset directory
            preset_files = list(self.preset_directory.glob("*.json"))

            if not preset_files:
                logger.warning(f"No preset files found in {self.preset_directory}")
                logger.info("Preset directory is empty - presets can be added later")
                return

            for preset_file in preset_files:
                try:
                    with open(preset_file, 'r') as f:
                        preset_data = json.load(f)

                    # Store in cache using preset ID as key
                    preset_id = preset_data.get('id', preset_file.stem)
                    self._presets_cache[preset_id] = preset_data
                    logger.debug(f"Cached preset: {preset_data.get('name', preset_id)} (ID: {preset_id})")

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in {preset_file.name}: {e}")
                except Exception as e:
                    logger.error(f"Error loading {preset_file.name}: {e}")

            logger.info(f"Loaded {len(self._presets_cache)} presets into cache")

        except Exception as e:
            logger.error(f"Error scanning preset directory: {e}")

    def list_presets(self, category: str = None) -> List[Dict]:
        """
        List all available presets from cache

        Args:
            category: Optional category filter (e.g., "ZoomInfo", "Standard Format")

        Returns:
            List of preset metadata dicts
        """
        presets = []

        for preset_id, preset_data in self._presets_cache.items():
            # Apply category filter if specified
            if category and preset_data.get('category') != category:
                continue

            preset_info = {
                'id': preset_data.get('id', preset_id),
                'name': preset_data.get('name'),
                'description': preset_data.get('description'),
                'category': preset_data.get('category'),
                'file_path': str(self.preset_directory / f"{preset_id}.json"),
                'operation_count': len(preset_data.get('operations', []))
            }
            presets.append(preset_info)

        logger.debug(f"Returning {len(presets)} presets" + (f" (category: {category})" if category else ""))
        return presets

    def load_preset(self, preset_id: str) -> Optional[Dict]:
        """
        Load a specific preset by ID from cache

        Args:
            preset_id: Preset identifier

        Returns:
            Preset data dict or None if not found
        """
        if preset_id not in self._presets_cache:
            logger.error(f"Preset not found in cache: {preset_id}")
            logger.debug(f"Available presets: {list(self._presets_cache.keys())}")
            return None

        preset_data = self._presets_cache[preset_id]
        logger.info(f"Loaded preset from cache: {preset_data.get('name', preset_id)}")
        return preset_data

    def save_preset(self, preset_data: Dict, preset_id: str = None) -> bool:
        """
        Save a preset to disk and update cache

        Args:
            preset_data: Preset configuration dict
            preset_id: Optional preset ID (uses preset_data['id'] if not provided)

        Returns:
            True if successful, False otherwise
        """
        if preset_id is None:
            preset_id = preset_data.get('id')

        if not preset_id:
            logger.error("Preset must have an 'id' field")
            return False

        preset_file = self.preset_directory / f"{preset_id}.json"

        try:
            # Create directory if it doesn't exist
            self.preset_directory.mkdir(parents=True, exist_ok=True)

            # Save to disk
            with open(preset_file, 'w') as f:
                json.dump(preset_data, f, indent=2)

            # Update cache
            self._presets_cache[preset_id] = preset_data

            logger.info(f"Saved preset: {preset_data.get('name', preset_id)} (ID: {preset_id})")
            logger.debug(f"Preset file: {preset_file}")

            return True
        except Exception as e:
            logger.error(f"Error saving preset {preset_id}: {e}")
            return False

    def detect_file_type(self, df: pd.DataFrame, file_path: str = None) -> Tuple[str, str, float]:
        """
        Detect file type and suggest appropriate preset

        Args:
            df: DataFrame to analyze
            file_path: Optional file path for additional context

        Returns:
            Tuple of (file_type, suggested_preset_id, confidence)
            e.g., ("ZoomInfo", "zoominfo_healthcare_evs", 0.95)
        """
        # Check for ZoomInfo files
        zoominfo_type, confidence = self._detect_zoominfo(df)
        if zoominfo_type:
            return "ZoomInfo", zoominfo_type, confidence

        # Check for other file types
        # (Add more detection logic here for LinkedIn, SugarCRM, etc.)

        return "Unknown", None, 0.0

    def _detect_zoominfo(self, df: pd.DataFrame) -> Tuple[Optional[str], float]:
        """
        Detect ZoomInfo file type

        Returns:
            Tuple of (preset_id, confidence) or (None, 0.0)
        """
        columns = set(df.columns)

        # ZoomInfo indicator columns
        zoominfo_indicators = {
            'ZoomInfo Contact ID',
            'ZoomInfo Company ID',
            'ZoomInfo Contact Profile URL',
            'ZoomInfo Company Profile URL'
        }

        indicator_matches = len(columns.intersection(zoominfo_indicators))

        if indicator_matches < 2:
            # Not a ZoomInfo file
            return None, 0.0

        # It's a ZoomInfo file - determine which variant

        # Healthcare/EVS format indicators
        healthcare_columns = {
            'Person Street',
            'Person City',
            'Person State',
            'Person Zip Code',
            'First Name',
            'Last Name',
            'Company Name',
            'Job Title',
            'Direct Phone Number',
            'Email Address'
        }

        healthcare_matches = len(columns.intersection(healthcare_columns))

        if healthcare_matches >= 8:
            # High confidence Healthcare/EVS format
            confidence = min(0.9 + (healthcare_matches - 8) * 0.01, 0.99)
            return "zoominfo_healthcare_evs", confidence

        # Could add other ZoomInfo format detection here
        # For now, default to healthcare format with lower confidence
        return "zoominfo_healthcare_evs", 0.7

    def get_preset_operations(self, preset_id: str) -> List[Dict]:
        """
        Get list of operations from a preset

        Args:
            preset_id: Preset identifier

        Returns:
            List of operation dicts
        """
        preset = self.load_preset(preset_id)
        if not preset:
            return []

        return preset.get('operations', [])

    def validate_preset_columns(self, preset_id: str, df: pd.DataFrame) -> Dict:
        """
        Validate that a dataframe has the expected columns for a preset

        Args:
            preset_id: Preset identifier
            df: DataFrame to validate

        Returns:
            Dict with validation results:
            {
                'valid': bool,
                'missing_columns': list,
                'extra_columns': list,
                'confidence': float
            }
        """
        preset = self.load_preset(preset_id)
        if not preset:
            return {
                'valid': False,
                'missing_columns': [],
                'extra_columns': [],
                'confidence': 0.0,
                'error': 'Preset not found'
            }

        expected_columns = set(preset.get('expected_columns', []))
        actual_columns = set(df.columns)

        missing = list(expected_columns - actual_columns)
        extra = list(actual_columns - expected_columns)

        # Calculate confidence based on matches
        if len(expected_columns) == 0:
            confidence = 1.0
        else:
            matches = len(expected_columns.intersection(actual_columns))
            confidence = matches / len(expected_columns)

        return {
            'valid': len(missing) == 0,
            'missing_columns': missing,
            'extra_columns': extra,
            'confidence': confidence
        }


class PresetEditor:
    """Handles editing operations within a preset"""

    def __init__(self, preset_data: Dict):
        """
        Initialize with preset data

        Args:
            preset_data: Preset configuration dict
        """
        self.preset_data = preset_data.copy()
        self.operations = self.preset_data.get('operations', [])

    def get_operations(self) -> List[Dict]:
        """Get list of operations"""
        return self.operations

    def update_operation(self, index: int, parameters: Dict):
        """
        Update operation parameters

        Args:
            index: Operation index
            parameters: New parameters dict
        """
        if 0 <= index < len(self.operations):
            self.operations[index]['parameters'] = parameters

    def enable_operation(self, index: int, enabled: bool = True):
        """
        Enable or disable an operation

        Args:
            index: Operation index
            enabled: True to enable, False to disable
        """
        if 0 <= index < len(self.operations):
            self.operations[index]['enabled'] = enabled

    def remove_operation(self, index: int):
        """
        Remove an operation

        Args:
            index: Operation index
        """
        if 0 <= index < len(self.operations):
            self.operations.pop(index)
            # Re-order remaining operations
            for i, op in enumerate(self.operations):
                op['order'] = i

    def add_operation(self, operation_data: Dict, index: int = None):
        """
        Add a new operation

        Args:
            operation_data: Operation configuration dict
            index: Optional position to insert (appends to end if None)
        """
        if index is None:
            index = len(self.operations)

        operation_data['order'] = index
        self.operations.insert(index, operation_data)

        # Re-order subsequent operations
        for i in range(index + 1, len(self.operations)):
            self.operations[i]['order'] = i

    def get_preset_data(self) -> Dict:
        """Get updated preset data"""
        self.preset_data['operations'] = self.operations
        return self.preset_data


def detect_and_suggest_preset(df: pd.DataFrame, file_path: str = None) -> Optional[Dict]:
    """
    Convenience function to detect file type and suggest preset

    Args:
        df: DataFrame to analyze
        file_path: Optional file path

    Returns:
        Dict with detection results or None
        {
            'file_type': str,
            'preset_id': str,
            'preset_name': str,
            'confidence': float,
            'validation': dict
        }
    """
    logger.debug(f"Detecting file type for dataframe with {len(df)} rows, {len(df.columns)} columns")

    manager = PresetManager()

    file_type, preset_id, confidence = manager.detect_file_type(df, file_path)

    if not preset_id:
        logger.debug("No preset detected")
        return None

    logger.info(f"Detected file type: {file_type}, suggested preset: {preset_id} (confidence: {confidence:.0%})")

    preset = manager.load_preset(preset_id)
    if not preset:
        logger.error(f"Failed to load detected preset: {preset_id}")
        return None

    validation = manager.validate_preset_columns(preset_id, df)

    logger.info(f"Preset validation: {validation['confidence']:.0%} match, valid={validation['valid']}")

    return {
        'file_type': file_type,
        'preset_id': preset_id,
        'preset_name': preset.get('name'),
        'confidence': confidence,
        'validation': validation,
        'preset_data': preset
    }
