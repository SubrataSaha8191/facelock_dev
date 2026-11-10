"""FaceLock SDK exceptions.

``FaceLockConnectionError`` and ``UserNotEnrolledError`` also derive from the
built-in ``ConnectionError`` / ``ValueError`` so code written against SDK 1.0
(which raised those) keeps working.
"""


class FaceLockError(Exception):
    """Base class for all FaceLock SDK errors."""


class FaceLockConnectionError(FaceLockError, ConnectionError):
    """The FaceLock Authentication Service could not be reached."""


class UserNotEnrolledError(FaceLockError, ValueError):
    """The user has no usable face profile (never enrolled, or must enroll again)."""


class AuthenticationFailedError(FaceLockError):
    """Raised by callers that want a failed authentication as an exception."""

    def __init__(self, message: str = "Face authentication failed", reason: str = ""):
        super().__init__(message)
        self.reason = reason
