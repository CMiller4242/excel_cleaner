"""
Preset-Queue Integration Module
Provides integration between preset system and operation queue
"""

import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from utils.preset_manager import PresetManager, detect_and_suggest_preset
from utils.preset_loader import PresetLoader, load_preset

# Set up logging
logger = logging.getLogger("PresetQueueIntegration")
logger.setLevel(logging.DEBUG)


class PresetQueueIntegration:
    """
    Integration layer between preset system and operation queue

    This class provides methods for:
    - Loading presets and adding operations to queue
    - Validating operations before queueing
    - Providing user feedback during the process
    """

    def __init__(self, operation_queue=None):
        """
        Initialize integration

        Args:
            operation_queue: Reference to the operation queue object
        """
        self.operation_queue = operation_queue
        self.preset_manager = PresetManager()
        self.preset_loader = PresetLoader()

        logger.info("PresetQueueIntegration initialized")

    def load_preset_to_queue(self, preset_id: str) -> Tuple[bool, str, List[Dict]]:
        """
        Load a preset and add all its operations to the queue

        Args:
            preset_id: Preset identifier

        Returns:
            Tuple of (success, message, operations)
            - success: True if successful, False if failed
            - message: Success/error message for user
            - operations: List of operation dicts that were added
        """
        logger.info(f"Loading preset '{preset_id}' to queue")

        # Load preset file
        preset_file = self.preset_manager.preset_directory / f"{preset_id}.json"

        if not preset_file.exists():
            error_msg = f"Preset file not found: {preset_id}"
            logger.error(error_msg)
            return False, error_msg, []

        # Load and validate preset operations
        preset_data, operations, errors = load_preset(str(preset_file))

        if not preset_data:
            error_msg = f"Failed to load preset: {preset_id}"
            logger.error(error_msg)
            return False, error_msg, []

        if errors:
            error_msg = f"Preset has {len(errors)} invalid operations:\n" + "\n".join(errors)
            logger.warning(error_msg)
            # Continue with valid operations

        if not operations:
            error_msg = "No valid operations found in preset"
            logger.error(error_msg)
            return False, error_msg, []

        logger.info(f"Loaded {len(operations)} valid operations from preset")

        # Add operations to queue (if queue exists)
        if self.operation_queue:
            try:
                added_count = self._add_operations_to_queue(operations)
                success_msg = f"Successfully added {added_count} operations to queue"
                logger.info(success_msg)
                return True, success_msg, operations
            except Exception as e:
                error_msg = f"Error adding operations to queue: {str(e)}"
                logger.error(error_msg)
                return False, error_msg, []
        else:
            # No queue - just return the operations
            success_msg = f"Loaded {len(operations)} operations (no queue attached)"
            logger.warning(success_msg)
            return True, success_msg, operations

    def _add_operations_to_queue(self, operations: List[Dict]) -> int:
        """
        Add operations to the operation queue

        Args:
            operations: List of operation dicts

        Returns:
            Number of operations added
        """
        added_count = 0

        for operation in operations:
            try:
                # Check if operation_queue has an add method
                if hasattr(self.operation_queue, 'add_operation'):
                    self.operation_queue.add_operation(
                        operation['operation_id'],
                        operation['parameters']
                    )
                    added_count += 1
                    logger.debug(f"Added operation: {operation['operation_id']}")
                elif hasattr(self.operation_queue, 'append'):
                    # Alternative: queue is a list
                    self.operation_queue.append(operation)
                    added_count += 1
                    logger.debug(f"Appended operation: {operation['operation_id']}")
                else:
                    logger.error("Operation queue has no add_operation or append method")
                    break

            except Exception as e:
                logger.error(f"Failed to add operation {operation['operation_id']}: {e}")
                continue

        return added_count

    def detect_and_load_preset(self, df, file_path: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Detect file type and automatically load appropriate preset

        Args:
            df: DataFrame to analyze
            file_path: Optional file path

        Returns:
            Tuple of (detected, message, detection_result)
            - detected: True if preset was detected and loaded
            - message: Message for user
            - detection_result: Detection dict with preset info
        """
        logger.info("Detecting file type and suggesting preset")

        # Detect file type
        detection = detect_and_suggest_preset(df, file_path)

        if not detection:
            logger.info("No preset detected for this file")
            return False, "No preset detected for this file type", None

        # Found a preset
        preset_name = detection['preset_name']
        confidence = detection['confidence']

        logger.info(f"Detected: {preset_name} with {confidence:.0%} confidence")

        return True, f"Detected {preset_name} ({confidence:.0%} confidence)", detection

    def get_preset_operations_summary(self, preset_id: str) -> str:
        """
        Get a summary of operations in a preset

        Args:
            preset_id: Preset identifier

        Returns:
            Human-readable summary string
        """
        preset = self.preset_manager.load_preset(preset_id)

        if not preset:
            return f"Preset '{preset_id}' not found"

        operations = preset.get('operations', [])
        enabled_ops = [op for op in operations if op.get('enabled', True)]

        summary_parts = [
            f"Preset: {preset.get('name', 'Unknown')}",
            f"Total operations: {len(operations)}",
            f"Enabled operations: {len(enabled_ops)}",
            "",
            "Operations:"
        ]

        for idx, op in enumerate(enabled_ops, 1):
            op_id = op.get('operation_id', 'unknown')
            desc = op.get('description', '')
            summary_parts.append(f"  {idx}. {op_id}")
            if desc:
                summary_parts.append(f"     {desc}")

        return '\n'.join(summary_parts)


def add_preset_operations_to_queue(preset_id: str, operation_queue) -> Tuple[bool, str]:
    """
    Convenience function to add preset operations to queue

    Args:
        preset_id: Preset identifier
        operation_queue: Operation queue object

    Returns:
        Tuple of (success, message)

    Example usage:
        success, message = add_preset_operations_to_queue(
            'zoominfo_healthcare_evs',
            self.operation_queue
        )
        if success:
            print(message)  # "Successfully added 9 operations to queue"
        else:
            print(f"Error: {message}")
    """
    integration = PresetQueueIntegration(operation_queue)
    success, message, operations = integration.load_preset_to_queue(preset_id)
    return success, message


def get_operations_from_preset(preset_id: str) -> Tuple[List[Dict], List[str]]:
    """
    Get operations from a preset without adding to queue

    Args:
        preset_id: Preset identifier

    Returns:
        Tuple of (operations, errors)
        - operations: List of valid operation dicts
        - errors: List of error messages

    Example usage:
        operations, errors = get_operations_from_preset('zoominfo_healthcare_evs')
        if operations:
            for op in operations:
                print(f"{op['operation_id']}: {op['description']}")
        if errors:
            print(f"Errors: {errors}")
    """
    manager = PresetManager()
    preset_file = manager.preset_directory / f"{preset_id}.json"

    if not preset_file.exists():
        return [], [f"Preset file not found: {preset_id}"]

    preset_data, operations, errors = load_preset(str(preset_file))

    return operations, errors
