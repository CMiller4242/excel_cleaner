"""
Operation Registry
Central registry for all available operations
"""

from typing import Dict, List, Optional
from .base import BaseOperation


class OperationRegistry:
    """
    Central registry of all Excel operations
    Provides discovery, search, and retrieval of operations
    """
    
    def __init__(self):
        self.operations: Dict[str, BaseOperation] = {}
        self._categories: Dict[str, List[str]] = {}
        self._tags: Dict[str, List[str]] = {}
        
    def register(self, operation: BaseOperation):
        """
        Register an operation
        
        Args:
            operation: Instance of an operation to register
        """
        op_id = operation.metadata.id
        
        if op_id in self.operations:
            raise ValueError(f"Operation {op_id} is already registered")
        
        self.operations[op_id] = operation
        
        # Index by category
        category = operation.metadata.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(op_id)
        
        # Index by tags
        for tag in (operation.metadata.tags or []):
            if tag not in self._tags:
                self._tags[tag] = []
            self._tags[tag].append(op_id)
    
    def get_by_id(self, op_id: str) -> Optional[BaseOperation]:
        """
        Get an operation by its ID
        
        Args:
            op_id: Operation ID
            
        Returns:
            Operation instance or None if not found
        """
        return self.operations.get(op_id)
    
    def get_by_category(self, category: str) -> List[BaseOperation]:
        """
        Get all operations in a category
        
        Args:
            category: Category name
            
        Returns:
            List of operations in that category
        """
        op_ids = self._categories.get(category, [])
        return [self.operations[op_id] for op_id in op_ids]
    
    def get_by_tag(self, tag: str) -> List[BaseOperation]:
        """
        Get all operations with a specific tag
        
        Args:
            tag: Tag name
            
        Returns:
            List of operations with that tag
        """
        op_ids = self._tags.get(tag, [])
        return [self.operations[op_id] for op_id in op_ids]
    
    def get_all_categories(self) -> List[str]:
        """
        Get list of all categories
        
        Returns:
            List of category names
        """
        return sorted(self._categories.keys())
    
    def get_all_tags(self) -> List[str]:
        """
        Get list of all tags
        
        Returns:
            List of tag names
        """
        return sorted(self._tags.keys())
    
    def search(self, query: str) -> List[BaseOperation]:
        """
        Search operations by name, description, or tags
        
        Args:
            query: Search query
            
        Returns:
            List of matching operations
        """
        query_lower = query.lower()
        results = []
        
        for operation in self.operations.values():
            # Search in name
            if query_lower in operation.metadata.name.lower():
                results.append(operation)
                continue
            
            # Search in description
            if query_lower in operation.metadata.description.lower():
                results.append(operation)
                continue
            
            # Search in tags
            if operation.metadata.tags:
                for tag in operation.metadata.tags:
                    if query_lower in tag.lower():
                        results.append(operation)
                        break
        
        return results
    
    def list_all(self) -> List[BaseOperation]:
        """
        Get all registered operations
        
        Returns:
            List of all operations
        """
        return list(self.operations.values())
    
    def get_count(self) -> int:
        """
        Get total number of registered operations
        
        Returns:
            Number of operations
        """
        return len(self.operations)
    
    def to_dict(self) -> Dict:
        """
        Export registry as dictionary (for UI display)

        Returns:
            Dictionary representation of registry
        """
        return {
            'operations': {
                op_id: op.metadata.to_dict()
                for op_id, op in self.operations.items()
            },
            'categories': self._categories,
            'tags': self._tags,
            'count': self.get_count()
        }

    def normalize_operation(self, op_dict: Dict) -> Dict:
        """
        Convert old-format preset operations into full operation format.

        Handles multiple formats:
        - Old format: {"operation_id": "...", "parameters": {}, "enabled": true}
        - Legacy format: {"name": "...", "parameters": {}}
        - New format: {"class": "...", "type": "...", "name": "...", "parameters": {}, "enabled": true}

        Args:
            op_dict: Operation dictionary from preset

        Returns:
            Normalized operation dictionary with class, name, type, parameters, enabled
        """
        print(f"[DEBUG] Normalizing operation: {op_dict}")

        # If already in new format (has 'class' field), return as-is
        if 'class' in op_dict:
            print(f"[DEBUG] Already in new format")
            return op_dict

        # Extract operation ID from various possible keys
        op_id = op_dict.get('operation_id') or op_dict.get('class') or op_dict.get('id')

        if not op_id:
            # If no ID found, check if there's a 'name' field (legacy format)
            legacy_name = op_dict.get('name')
            if legacy_name:
                print(f"[DEBUG] Legacy format with name: {legacy_name}")
                # Try to find operation by name
                for operation in self.operations.values():
                    if operation.metadata.name.lower() == legacy_name.lower():
                        op_id = operation.metadata.id
                        break

        if not op_id:
            print(f"[WARN] Could not determine operation ID, using UnknownOperation")
            # Fallback to unknown operation
            return {
                'class': 'unknown_operation',
                'name': op_dict.get('name', 'Unknown Operation'),
                'type': 'Unknown',
                'parameters': op_dict.get('parameters', op_dict.get('params', {})),
                'enabled': op_dict.get('enabled', True),
                'notes': op_dict.get('notes', ''),
                '_original': op_dict  # Store original for debugging
            }

        # Look up operation in registry
        operation = self.get_by_id(op_id)

        if not operation:
            print(f"[WARN] Operation '{op_id}' not found in registry")
            # Operation not found - use fallback
            return {
                'class': op_id,
                'name': op_dict.get('name', op_id.replace('_', ' ').title()),
                'type': 'Unknown',
                'parameters': op_dict.get('parameters', op_dict.get('params', {})),
                'enabled': op_dict.get('enabled', True),
                'notes': op_dict.get('notes', ''),
                '_missing_from_registry': True
            }

        # Operation found - create normalized dict
        normalized = {
            'class': operation.metadata.id,
            'name': operation.metadata.name,
            'type': operation.metadata.category,
            'parameters': op_dict.get('parameters', op_dict.get('params', {})),
            'enabled': op_dict.get('enabled', True),
            'notes': op_dict.get('notes', ''),
            'description': operation.metadata.description
        }

        print(f"[DEBUG] Normalized to: {normalized['name']} ({normalized['class']})")
        return normalized

    def get_display_name(self, op_dict: Dict) -> str:
        """
        Get the display name for an operation, handling multiple formats.

        Args:
            op_dict: Operation dictionary

        Returns:
            Human-readable operation name
        """
        # Try direct name field first
        if 'name' in op_dict and op_dict['name'] != 'Unknown Operation':
            return op_dict['name']

        # Try to get from class/operation_id
        op_id = op_dict.get('class') or op_dict.get('operation_id') or op_dict.get('id')

        if op_id:
            operation = self.get_by_id(op_id)
            if operation:
                return operation.metadata.name

            # Fallback: convert ID to readable name
            return op_id.replace('_', ' ').title()

        return 'Unknown Operation'

    def get_operation_metadata(self, op_dict: Dict) -> Optional[Dict]:
        """
        Get full metadata for an operation from the registry.

        Args:
            op_dict: Operation dictionary

        Returns:
            Metadata dict or None if not found
        """
        op_id = op_dict.get('class') or op_dict.get('operation_id') or op_dict.get('id')

        if not op_id:
            return None

        operation = self.get_by_id(op_id)

        if not operation:
            return None

        return operation.metadata.to_dict()


# Global registry instance
registry = OperationRegistry()


def get_registry() -> OperationRegistry:
    """Get the global operation registry"""
    return registry
