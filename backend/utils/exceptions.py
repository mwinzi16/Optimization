"""
Custom exceptions for Portfolio Optimizer.
Provides structured error handling with error codes.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Enumeration of error codes for API responses."""
    
    # Data errors (1xxx)
    DATA_NOT_LOADED = "ERR_1001"
    INVALID_FILE_FORMAT = "ERR_1002"
    FILE_EMPTY = "ERR_1003"
    INSUFFICIENT_ASSETS = "ERR_1004"
    INSUFFICIENT_SCENARIOS = "ERR_1005"
    DATA_PARSE_ERROR = "ERR_1006"
    
    # Optimization errors (2xxx)
    OPTIMIZATION_FAILED = "ERR_2001"
    INVALID_METHOD = "ERR_2002"
    INFEASIBLE_CONSTRAINTS = "ERR_2003"
    NUMERICAL_ERROR = "ERR_2004"
    
    # Validation errors (3xxx)
    INVALID_WEIGHT_RANGE = "ERR_3001"
    INVALID_ALPHA = "ERR_3002"
    INVALID_RISK_AVERSION = "ERR_3003"
    INVALID_CONSTRAINT = "ERR_3004"
    
    # Server errors (5xxx)
    INTERNAL_ERROR = "ERR_5001"
    SOLVER_ERROR = "ERR_5002"


class OptimizerError(Exception):
    """Base exception for optimizer errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to API response format."""
        return {
            "error": True,
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }


class DataError(OptimizerError):
    """Exception for data-related errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DATA_NOT_LOADED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details, status_code=400)


class ValidationError(OptimizerError):
    """Exception for input validation errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_WEIGHT_RANGE,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details, status_code=422)


class OptimizationError(OptimizerError):
    """Exception for optimization algorithm errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.OPTIMIZATION_FAILED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details, status_code=500)
