"""
Core verification module for credentials and delegations.
"""

from .verifier import verify_cvc
from .constants import ErrorCode

__all__ = ['verify_cvc', 'ErrorCode']
