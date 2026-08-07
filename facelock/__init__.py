"""
FaceLock API Library
Integrate FaceLock biometric authentication seamlessly into your Python projects.
"""

import socket
import json
import getpass
import os

SOCKET_PATH = "/tmp/facelock.sock"

def _send_request(action: str, **kwargs) -> dict:
    try:
        req = {"action": action}
        req.update(kwargs)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(15.0)
            s.connect(SOCKET_PATH)
            s.sendall(json.dumps(req).encode('utf-8'))
            response_data = s.recv(8192).decode('utf-8')
            return json.loads(response_data)
    except FileNotFoundError:
        raise ConnectionError("FaceLock daemon is not running (socket not found). Install FaceLock OS first.")
    except Exception as e:
        raise ConnectionError(f"Failed to communicate with FaceLock daemon: {e}")


def is_enrolled(user_id: str = None) -> bool:
    """
    Check if a specific user is enrolled in FaceLock.
    
    Args:
        user_id (str): The system username or FaceLock user ID. If None, uses current OS user.
        
    Returns:
        bool: True if enrolled, False otherwise.
    """
    if user_id is None:
        user_id = getpass.getuser()
    try:
        res = _send_request("check_enrolled", user_id=user_id)
        return res.get("result", False)
    except Exception:
        return False


def authenticate(user_id: str = None) -> bool:
    """
    Authenticate a user using FaceLock biometric verification.
    
    Args:
        user_id (str): The system username or FaceLock user ID. If None, uses current OS user.
        
    Returns:
        bool: True if authentication successful.
        
    Raises:
        ValueError: If user is not enrolled.
        ConnectionError: If daemon is unreachable.
    """
    if user_id is None:
        user_id = getpass.getuser()
        
    if not is_enrolled(user_id):
        raise ValueError(f"User '{user_id}' is not enrolled in FaceLock. Please enroll via the FaceLock Dashboard.")
        
    res = _send_request("authenticate_face", user_id=user_id)
    return res.get("result", False)
