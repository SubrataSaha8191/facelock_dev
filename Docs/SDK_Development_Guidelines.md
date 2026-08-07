# FaceLock SDK Development Guidelines

## Objective

Develop the official FaceLock Python SDK that enables developers to integrate biometric authentication into their Python applications through the FaceLock Authentication Service.

The SDK must remain lightweight and must never perform any computer vision or machine learning tasks locally.

---

# Design Philosophy

The SDK is a client library.

It communicates with the FaceLock Authentication Service over a local UNIX Domain Socket.

The SDK is **not** responsible for:

- Camera access
- Face recognition
- Face detection
- Liveness detection
- Model loading
- Authentication logic

These responsibilities belong exclusively to the FaceLock Authentication Service.

---

# Responsibilities

The SDK is responsible for:

- Sending requests to the daemon
- Receiving responses
- Parsing JSON
- Raising meaningful Python exceptions
- Providing a clean Python API
- Hiding socket implementation details

---

# Project Structure

SDK/

    facelock/

        __init__.py

        client.py

        constants.py

        exceptions.py

        version.py

---

# __init__.py

Purpose:

Expose the public SDK API.

Example:

from .client import authenticate
from .client import is_enrolled
from .client import is_available

from .version import __version__

---

# client.py

Contains:

- socket communication
- request handling
- authenticate()
- is_enrolled()
- is_available()

No business logic.

---

# constants.py

Contains:

DEFAULT_SOCKET_PATH

SOCKET_TIMEOUT

ACTION_AUTHENTICATE

ACTION_CHECK_ENROLLED

Future protocol constants.

---

# exceptions.py

Contains custom exceptions.

FaceLockError

FaceLockConnectionError

UserNotEnrolledError

AuthenticationFailedError

---

# version.py

Contains

__version__ = "0.1.0"

---

# Public API

Current

authenticate()

is_enrolled()

is_available()

Future

version()

enroll()

list_users()

remove_user()

get_status()

---

# Socket Protocol

The SDK communicates only through JSON messages.

Example Request

{
    "action": "authenticate_face",
    "user_id": "subrata"
}

Example Response

{
    "result": true
}

---

# Coding Rules

- Use type hints.
- Use descriptive docstrings.
- Never expose socket internals.
- Never expose daemon internals.
- Never expose ML implementation.
- Raise custom exceptions.
- Keep functions small.
- Use constants instead of hardcoded strings.
- Keep __init__.py minimal.

---

# Testing

Every public SDK function must have unit tests.

Authentication tests must mock the daemon.

No test should require an actual webcam.

---

# Future Compatibility

The SDK must remain backward compatible.

New features should never break existing applications.

Deprecations should follow semantic versioning.
