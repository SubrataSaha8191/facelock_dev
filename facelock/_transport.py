"""Local transport to the FaceLock service (standard library only).

POSIX talks over a UNIX socket. Windows has no AF_UNIX in Python, so the service
listens on 127.0.0.1 and publishes ``endpoint.json`` (port + secret token) in the
user's FaceLock data folder; the token is sent with every request.

Addresses: a socket path, ``tcp://host:port``, or ``auto`` (use endpoint.json).
"""

import json
import os
import socket
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

IS_WINDOWS = os.name == "nt"
POSIX_DEFAULT_SOCKET = "/tmp/facelock.sock"
LOOPBACK = "127.0.0.1"


def default_address() -> str:
    return os.environ.get("FACELOCK_SOCKET") or ("auto" if IS_WINDOWS else POSIX_DEFAULT_SOCKET)


def data_dir() -> Path:
    override = os.environ.get("FACELOCK_DATA_DIR")
    if override:
        return Path(override)
    if IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA")
        return (Path(base) if base else Path.home() / "AppData" / "Local") / "FaceLock"
    return Path.home() / ".facelock"


def read_endpoint() -> Optional[Dict[str, Any]]:
    try:
        return json.loads((data_dir() / "endpoint.json").read_text("utf-8"))
    except (OSError, ValueError):
        return None


def uses_tcp(address: str) -> bool:
    return address == "auto" or address.startswith("tcp://")


def open_client(address: Optional[str], timeout: float) -> Tuple[socket.socket, Optional[str]]:
    """Connect; returns ``(socket, token_to_send_or_None)``."""
    addr = address or default_address()
    if uses_tcp(addr):
        ep = read_endpoint()
        if addr == "auto":
            if not ep:
                raise FileNotFoundError("FaceLock service endpoint not found")
            host, port, token = ep.get("host", LOOPBACK), int(ep["port"]), ep.get("token")
        else:
            host, _, port_s = addr[len("tcp://"):].rpartition(":")
            host, port = host or LOOPBACK, int(port_s)
            token = os.environ.get("FACELOCK_TOKEN") or (ep.get("token") if ep and int(ep.get("port", -1)) == port else None)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        host = port = token = None
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  # POSIX only
    sock.settimeout(timeout)
    try:
        sock.connect((host, port) if host else addr)
    except Exception:
        sock.close()
        raise
    return sock, token
