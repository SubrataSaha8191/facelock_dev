"""
FaceLock SDK
Add biometric face authentication to Python applications through the local
FaceLock Authentication Service. The SDK does no camera or ML work itself.
"""

from .client import AuthResult, authenticate, authenticate_detailed, is_available, is_enrolled
from .exceptions import (
    AuthenticationFailedError,
    FaceLockConnectionError,
    FaceLockError,
    UserNotEnrolledError,
)
from .version import __version__

__all__ = [
    "authenticate",
    "authenticate_detailed",
    "is_enrolled",
    "is_available",
    "AuthResult",
    "FaceLockError",
    "FaceLockConnectionError",
    "UserNotEnrolledError",
    "AuthenticationFailedError",
    "__version__",
]
