"""Socket client for the FaceLock Authentication Service."""

import getpass
import json
import socket
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .constants import (
    ACTION_AUTHENTICATE,
    ACTION_CHECK_ENROLLED,
    AVAILABILITY_TIMEOUT,
    DEFAULT_SOCKET_PATH,
    REASON_NOT_ENROLLED,
    REASON_REENROLL,
    SOCKET_TIMEOUT,
)
from .exceptions import FaceLockConnectionError, UserNotEnrolledError


@dataclass(frozen=True)
class AuthResult:
    """Detailed outcome of an authentication attempt.

    ``reason`` is one of: ``match``, ``mismatch``, ``no_face``, ``low_quality``,
    ``liveness_failed``, ``locked``, ``camera_unavailable`` (or an empty string when
    talking to an older service that doesn't report reasons).
    """

    ok: bool
    score: float = 0.0
    reason: str = ""
    message: str = ""

    def __bool__(self) -> bool:
        return self.ok


def _send_request(
    action: str,
    socket_path: Optional[str] = None,
    timeout: float = SOCKET_TIMEOUT,
    **fields: Any,
) -> Dict[str, Any]:
    path = socket_path or DEFAULT_SOCKET_PATH
    request = {"action": action, **fields}
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(path)
            sock.sendall(json.dumps(request).encode("utf-8"))
            buf = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
                try:
                    return json.loads(buf.decode("utf-8"))
                except ValueError:
                    continue  # partial JSON, keep reading
            return json.loads(buf.decode("utf-8"))
    except (FileNotFoundError, ConnectionRefusedError) as exc:
        raise FaceLockConnectionError(
            f"FaceLock service is not running (no socket at {path}). "
            "Install and start the FaceLock Authentication Service first."
        ) from exc
    except (OSError, ValueError) as exc:
        raise FaceLockConnectionError(f"Could not talk to the FaceLock service: {exc}") from exc


def _resolve(user_id: Optional[str]) -> str:
    return getpass.getuser() if user_id is None else user_id


def is_available(socket_path: Optional[str] = None) -> bool:
    """Return True if the FaceLock Authentication Service is reachable."""
    path = socket_path or DEFAULT_SOCKET_PATH
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(AVAILABILITY_TIMEOUT)
            sock.connect(path)
        return True
    except OSError:
        return False


def is_enrolled(user_id: Optional[str] = None, socket_path: Optional[str] = None) -> bool:
    """Return True if the user has a usable face profile.

    Returns False (rather than raising) when the service is unreachable; use
    :func:`is_available` to tell those cases apart.
    """
    try:
        return bool(_check_enrolled(_resolve(user_id), socket_path))
    except FaceLockConnectionError:
        return False


def _check_enrolled(user_id: str, socket_path: Optional[str]) -> bool:
    resp = _send_request(
        ACTION_CHECK_ENROLLED, socket_path, AVAILABILITY_TIMEOUT * 5, user_id=user_id
    )
    return bool(resp.get("result", False))


def authenticate_detailed(
    user_id: Optional[str] = None,
    timeout: Optional[float] = None,
    socket_path: Optional[str] = None,
) -> AuthResult:
    """Authenticate and return the full :class:`AuthResult`.

    The service watches the camera for several seconds and accepts any angle the
    user enrolled, so a single call is normally enough; don't wrap it in a retry loop.

    Raises:
        UserNotEnrolledError: no usable face profile for ``user_id``.
        FaceLockConnectionError: the service is unreachable.
    """
    user = _resolve(user_id)
    resp = _send_request(
        ACTION_AUTHENTICATE, socket_path, SOCKET_TIMEOUT if timeout is None else timeout, user_id=user
    )
    reason = str(resp.get("reason", ""))
    if reason in (REASON_NOT_ENROLLED, REASON_REENROLL):
        raise UserNotEnrolledError(
            f"User '{user}' has no usable face profile: {resp.get('message', reason)}. "
            "Enroll in the FaceLock dashboard."
        )
    if not resp.get("reason") and not resp.get("result", False) and not _check_enrolled(user, socket_path):
        # Older services report no reason; fall back to an explicit enrollment check.
        raise UserNotEnrolledError(
            f"User '{user}' is not enrolled in FaceLock. Enroll in the FaceLock dashboard."
        )
    return AuthResult(
        ok=bool(resp.get("result", False)),
        score=float(resp.get("similarity", 0.0) or 0.0),
        reason=reason,
        message=str(resp.get("message", "")),
    )


def authenticate(
    user_id: Optional[str] = None,
    timeout: Optional[float] = None,
    socket_path: Optional[str] = None,
) -> bool:
    """Authenticate a user with their face. Returns True on success.

    ``user_id`` defaults to the current OS user. See :func:`authenticate_detailed`
    for the reason behind a failure.
    """
    return authenticate_detailed(user_id, timeout, socket_path).ok
