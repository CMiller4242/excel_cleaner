"""
Base Operation Class
All Excel operations inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pandas as pd


@dataclass
class Parameter:
    """Parameter definition for an operation"""
    name: str
    type: str  # 'column', 'column_list', 'text', 'number', 'boolean', 'file', 'choice'
    description: str
    required: bool = True
    default: Any = None
    choices: Optional[List[str]] = None  # For 'choice' type
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'required': self.required,
            'default': self.default,
            'choices': self.choices
        }


@dataclass
class OperationMetadata:
    """Metadata about an operation"""
    id: str
    name: str
    category: str
    description: str
    parameters: List[Parameter]
    excel_equivalent: str
    examples: List[str]
    tags: List[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'parameters': [p.to_dict() for p in self.parameters],
            'excel_equivalent': self.excel_equivalent,
            'examples': self.examples,
            'tags': self.tags or []
        }


class BaseOperation(ABC):
    """
    Base class for all Excel operations
    Each operation must implement the required abstract methods
    """
    
    def __init__(self):
        self.metadata = self.get_metadata()
    
    @abstractmethod
    def get_metadata(self) -> OperationMetadata:
        """
        Return metadata about this operation
        This defines what the operation is, what parameters it needs, etc.
        """
        pass
    
    @abstractmethod
    def execute(self, df: pd.DataFrame, params: Dict) -> pd.DataFrame:
        """
        Execute the operation on the DataFrame
        
        Args:
            df: Input DataFrame
            params: Dictionary of parameter values
            
        Returns:
            Modified DataFrame
        """
        pass
    
    def validate_params(self, df: pd.DataFrame, params: Dict) -> tuple[bool, str]:
        """
        Validate parameters before execution
        
        Args:
            df: Input DataFrame (to check column names, etc.)
            params: Dictionary of parameter values
            
        Returns:
            (is_valid, error_message)
        """
        # Check all required parameters are present
        for param in self.metadata.parameters:
            if param.required and param.name not in params:
                return False, f"Missing required parameter: {param.name}"
            
            # Validate column parameters
            if param.type == 'column' and param.name in params:
                if params[param.name] not in df.columns:
                    return False, f"Column '{params[param.name]}' not found in data"
            
            # Validate column_list parameters
            if param.type == 'column_list' and param.name in params:
                for col in params[param.name]:
                    if col not in df.columns:
                        return False, f"Column '{col}' not found in data"
            
            # Validate choice parameters
            if param.type == 'choice' and param.name in params:
                if params[param.name] not in param.choices:
                    return False, f"Invalid choice for {param.name}: {params[param.name]}"
        
        return True, ""
    
    def preview(self, df: pd.DataFrame, params: Dict, max_rows: int = 100) -> pd.DataFrame:
        """
        Generate preview of what the operation will do
        By default, executes on first N rows
        
        Args:
            df: Input DataFrame
            params: Dictionary of parameter values
            max_rows: Number of rows to preview
            
        Returns:
            Preview DataFrame
        """
        preview_df = df.head(max_rows).copy()
        return self.execute(preview_df, params)
    
    def get_param_value(self, params: Dict, param_name: str, default: Any = None) -> Any:
        """
        Helper to get parameter value with fallback to metadata default
        
        Args:
            params: Dictionary of parameter values
            param_name: Name of parameter to retrieve
            default: Override default if provided
            
        Returns:
            Parameter value
        """
        if param_name in params:
            return params[param_name]
        
        # Look for default in metadata
        for param in self.metadata.parameters:
            if param.name == param_name:
                return param.default if default is None else default
        
        return default
    
    def __str__(self) -> str:
        return f"{self.metadata.name} ({self.metadata.id})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.metadata.id}>"


class OperationResult:
    """Result of an operation execution"""
    
    def __init__(self, 
                 success: bool, 
                 df: Optional[pd.DataFrame] = None,
                 message: str = "",
                 rows_affected: int = 0,
                 columns_affected: List[str] = None):
        self.success = success
        self.df = df
        self.message = message
        self.rows_affected = rows_affected
        self.columns_affected = columns_affected or []
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'message': self.message,
            'rows_affected': self.rows_affected,
            'columns_affected': self.columns_affected
        }
