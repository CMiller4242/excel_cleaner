"""
Preset Loader Module
Loads preset JSON files and instantiates operations with proper parameter validation
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from operations.registry import get_registry

# Set up logging
logger = logging.getLogger("PresetLoader")
logger.setLevel(logging.DEBUG)


class PresetLoader:
    """
    Loads preset JSON files and converts them to instantiated operations
    with proper parameter validation.
    """

    def __init__(self):
        """Initialize preset loader"""
        self.registry = get_registry()
        logger.info("PresetLoader initialized")

    def load_preset_file(self, preset_path: str) -> Optional[Dict]:
        """
        Load a preset JSON file

        Args:
            preset_path: Path to preset JSON file

        Returns:
            Preset data dict or None if loading fails
        """
        try:
            preset_file = Path(preset_path)

            if not preset_file.exists():
                logger.error(f"Preset file not found: {preset_path}")
                return None

            with open(preset_file, 'r') as f:
                preset_data = json.load(f)

            logger.info(f"Loaded preset: {preset_data.get('name', 'Unknown')}")
            return preset_data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in preset file {preset_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading preset file {preset_path}: {e}")
            return None

    def load_preset_operations(self, preset_data: Dict) -> Tuple[List[Dict], List[str]]:
        """
        Load operations from a preset and validate parameters

        Args:
            preset_data: Preset configuration dict

        Returns:
            Tuple of (valid_operations, error_messages)
            - valid_operations: List of operation dicts ready to execute
            - error_messages: List of error messages for failed operations
        """
        operations = preset_data.get('operations', [])
        valid_operations = []
        errors = []

        logger.info(f"Loading {len(operations)} operations from preset '{preset_data.get('name', 'Unknown')}'")

        for idx, operation_config in enumerate(operations):
            # Skip disabled operations
            if not operation_config.get('enabled', True):
                logger.debug(f"Skipping disabled operation {idx + 1}: {operation_config.get('operation_id')}")
                continue

            operation_id = operation_config.get('operation_id')
            parameters = operation_config.get('parameters', {})

            logger.debug(f"Processing operation {idx + 1}: {operation_id}")

            # Validate and instantiate operation
            is_valid, error_msg = self.validate_operation_parameters(operation_id, parameters)

            if not is_valid:
                error_text = f"Operation {idx + 1} ({operation_id}): {error_msg}"
                logger.error(error_text)
                errors.append(error_text)
                continue

            # Add to valid operations list
            operation_dict = {
                'operation_id': operation_id,
                'parameters': parameters,
                'description': operation_config.get('description', ''),
                'order': operation_config.get('order', idx),
                'editable': operation_config.get('editable', False),
                'required': operation_config.get('required', True)
            }

            valid_operations.append(operation_dict)
            logger.debug(f"Added operation {idx + 1}: {operation_id}")

        logger.info(f"Successfully validated {len(valid_operations)} of {len(operations)} operations")

        if errors:
            logger.warning(f"Failed to validate {len(errors)} operations")

        return valid_operations, errors

    def validate_operation_parameters(self, operation_id: str, parameters: Dict) -> Tuple[bool, str]:
        """
        Validate that all required parameters for an operation are present
        and have correct types.

        Args:
            operation_id: Operation identifier (e.g., "zoominfo_split_address")
            parameters: Parameters dict

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if valid, False if invalid
            - error_message: Error description (empty string if valid)
        """
        # Get operation from registry
        operation = self.registry.get(operation_id)

        if not operation:
            return False, f"Operation '{operation_id}' not found in registry"

        # Get operation metadata
        try:
            metadata = operation.get_metadata()
        except Exception as e:
            return False, f"Failed to get metadata for '{operation_id}': {str(e)}"

        # Check required parameters
        required_params = [
            param for param in metadata.parameters
            if param.required is not False
        ]

        missing_params = []
        for param in required_params:
            if param.name not in parameters:
                missing_params.append(param.name)

        if missing_params:
            return False, f"Missing required parameter(s): {', '.join(missing_params)}"

        # All validations passed
        return True, ""

    def get_operation_summary(self, operations: List[Dict]) -> str:
        """
        Get human-readable summary of operations

        Args:
            operations: List of operation dicts

        Returns:
            Summary string
        """
        if not operations:
            return "No operations"

        summary_parts = []
        for idx, op in enumerate(operations, 1):
            op_id = op.get('operation_id', 'unknown')
            desc = op.get('description', '')
            summary_parts.append(f"{idx}. {op_id}")
            if desc:
                summary_parts.append(f"   {desc}")

        return '\n'.join(summary_parts)


def load_preset(preset_path: str) -> Tuple[Optional[Dict], List[Dict], List[str]]:
    """
    Convenience function to load a preset and its operations

    Args:
        preset_path: Path to preset JSON file

    Returns:
        Tuple of (preset_data, operations, errors)
        - preset_data: Preset configuration dict (None if failed)
        - operations: List of valid operation dicts
        - errors: List of error messages
    """
    loader = PresetLoader()

    # Load preset file
    preset_data = loader.load_preset_file(preset_path)
    if not preset_data:
        return None, [], ["Failed to load preset file"]

    # Load and validate operations
    operations, errors = loader.load_preset_operations(preset_data)

    return preset_data, operations, errors
