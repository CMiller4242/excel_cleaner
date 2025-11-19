"""Operations Package V2"""
from .base import BaseOperation, OperationMetadata, Parameter, OperationResult
from .registry import registry, get_registry

# Import all v1 operations
from . import text_ops
from . import data_ops
from . import cleaning_ops
from . import math_ops
from . import date_ops
from . import validation_ops
from . import conditional_ops
from . import zoominfo_ops

# Import standardization operations (phone, ZIP, state, etc.)
from . import standardization_ops

# Import v2 advanced operations
try:
    from .advanced import math_advanced
except ImportError:
    pass

__all__ = ['BaseOperation', 'OperationMetadata', 'Parameter', 'OperationResult', 'registry', 'get_registry']