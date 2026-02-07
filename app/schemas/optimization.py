"""
Input validation and sanitization for API requests.
"""

from __future__ import annotations

from typing import Optional, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator
from ..utils.exceptions import ValidationError, ErrorCode


class ValidatedOptimizationRequest(BaseModel):
    """Validated optimization request with proper constraints."""
    
    method: str = Field(..., description="Optimization method")
    min_weight: float = Field(0.0, ge=0.0, le=1.0, description="Minimum weight per asset")
    max_weight: float = Field(1.0, ge=0.0, le=1.0, description="Maximum weight per asset")
    risk_free_rate: float = Field(0.0, ge=-0.1, le=0.3, description="Risk-free rate")
    cvar_alpha: float = Field(0.05, ge=0.01, le=0.2, description="CVaR confidence level")
    risk_aversion: float = Field(1.0, ge=0.01, le=10.0, description="Risk aversion parameter")
    exp_risk_aversion: float = Field(0.5, ge=0.0, le=1.0, description="Exponential utility risk aversion")
    max_volatility: Optional[float] = Field(None, ge=0.01, le=0.8, description="Max volatility constraint")
    max_cvar: Optional[float] = Field(None, ge=0.01, le=1.0, description="Max CVaR constraint")
    constraint_type: str = Field("volatility", description="Constraint type: volatility or cvar")
    cvar_constraint_alpha: float = Field(0.05, ge=0.01, le=0.2, description="CVaR constraint alpha")
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate optimization method."""
        valid_methods = [
            'Maximum Sharpe Ratio',
            'Minimum Variance', 
            'Minimum CVaR',
            'Mean-CVaR Trade-off',
            'Maximum Return (Constrained)',
            'Exponential Utility (CARA)',
        ]
        # Also accept normalized versions
        normalized = v.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
        valid_normalized = [m.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_') for m in valid_methods]
        
        if v not in valid_methods and normalized not in valid_normalized:
            raise ValueError(f"Invalid method. Valid options: {valid_methods}")
        return v
    
    @field_validator('constraint_type')
    @classmethod
    def validate_constraint_type(cls, v: str) -> str:
        """Validate constraint type."""
        if v not in ['volatility', 'cvar']:
            raise ValueError("constraint_type must be 'volatility' or 'cvar'")
        return v
    
    @model_validator(mode='after')
    def validate_weights(self) -> 'ValidatedOptimizationRequest':
        """Validate weight constraints are consistent."""
        if self.min_weight > self.max_weight:
            raise ValueError(
                f"min_weight ({self.min_weight}) cannot be greater than max_weight ({self.max_weight})"
            )
        
        # Check if constraints allow for a valid portfolio
        if self.min_weight > 1.0 / 2:  # Can't have all weights >= min if min > 0.5 (for 2+ assets)
            # This is a soft check - depends on number of assets
            pass
        
        return self


def validate_file_extension(filename: str) -> Tuple[bool, str]:
    """
    Validate that file has an allowed extension.
    
    Returns:
        Tuple of (is_valid, file_type or error_message)
    """
    if not filename:
        return False, "No filename provided"
    
    lower_name = filename.lower()
    if lower_name.endswith('.csv'):
        return True, 'csv'
    elif lower_name.endswith('.xlsx'):
        return True, 'xlsx'
    elif lower_name.endswith('.xls'):
        return True, 'xls'
    else:
        return False, f"Unsupported file format: {filename}. Supported: .csv, .xlsx, .xls"


def sanitize_column_names(columns: list) -> list:
    """
    Sanitize column names by removing problematic characters.
    
    Args:
        columns: List of column names
        
    Returns:
        List of sanitized column names
    """
    sanitized = []
    for col in columns:
        # Convert to string if not already
        col_str = str(col).strip()
        # Replace problematic characters
        col_str = col_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Remove excessive whitespace
        col_str = ' '.join(col_str.split())
        # Truncate if too long
        if len(col_str) > 100:
            col_str = col_str[:97] + '...'
        sanitized.append(col_str if col_str else f"Asset_{len(sanitized) + 1}")
    return sanitized
