# FaceLock SDK

The **FaceLock SDK** is the official Python client library for the FaceLock Authentication Service.

It enables Python applications to authenticate users using FaceLock without directly interacting with cameras, machine learning models, or biometric processing.

The SDK communicates locally with the FaceLock Authentication Service, providing a simple and secure interface for biometric authentication.

---

## Features

- Lightweight Python SDK
- Local biometric authentication
- No machine learning dependencies
- No OpenCV dependency
- No direct camera access
- Local UNIX Domain Socket communication
- Simple and intuitive API
- Works with the service's multi-angle face recognition (any enrolled head angle)
- Cross-platform architecture

---

## Installation

```bash
pip install git+https://github.com/SubrataSaha8191/facelock_dev.git
```

> **Requirement**
>
> The FaceLock Authentication Service must already be installed and running on the target system.
>
> Repository:
>
> https://github.com/SubrataSaha8191/FaceLock

---

## Quick Start

```python
import facelock

try:
    if facelock.authenticate():
        print("Authentication successful.")
    else:
        print("Authentication failed.")

except facelock.UserNotEnrolledError:
    print("User is not enrolled (or needs to enroll again).")

except facelock.FaceLockConnectionError:
    print("FaceLock Authentication Service is unavailable.")
```

One call is normally enough. The service watches the camera for a few seconds and
accepts any head angle the user enrolled, so don't wrap `authenticate()` in a retry loop.

---

## API

### authenticate(user_id=None, timeout=None)

Authenticate a user with their face. `user_id` defaults to the current OS user.

Returns `bool`

Raises

- `FaceLockConnectionError`
- `UserNotEnrolledError`

---

### authenticate_detailed(user_id=None, timeout=None)

Same as `authenticate()`, but returns an `AuthResult` so you can tell the user *why*
it failed. An `AuthResult` is truthy when authentication succeeded.

```python
result = facelock.authenticate_detailed()
if not result:
    print(result.reason, result.message, result.score)
```

`reason` is one of `match`, `mismatch`, `no_face`, `low_quality`, `liveness_failed`,
`locked`, `camera_unavailable`.

---

### is_enrolled(user_id=None)

Check whether the user has a usable face profile. Returns `bool`
(`False` if the service is unreachable; use `is_available()` to tell the cases apart).

---

### is_available()

Check whether the FaceLock Authentication Service is reachable. Returns `bool`.

---

### Exceptions

| Exception | Meaning |
|---|---|
| `FaceLockError` | Base class |
| `FaceLockConnectionError` | Service unreachable (also a `ConnectionError`) |
| `UserNotEnrolledError` | No usable face profile (also a `ValueError`) |
| `AuthenticationFailedError` | For callers that prefer failure as an exception |

The socket path can be overridden with the `FACELOCK_SOCKET` environment variable
or the `socket_path=` argument.

---

## Architecture

```text
Application
      │
      ▼
 FaceLock SDK
      │
 UNIX Domain Socket
      │
      ▼
FaceLock Authentication Service
      │
      ▼
Face Recognition Engine
```

---

## Design Goals

The SDK intentionally contains no:

- Machine learning models
- OpenCV
- Camera handling
- Face recognition logic
- Authentication logic

All biometric operations are delegated to the FaceLock Authentication Service.

---

## Roadmap

Planned SDK features include:

- version()
- enroll()
- remove_user()
- list_users()
- get_status()
- @require_face decorator
- Async API
- Windows Named Pipe support
- Cross-platform communication layer

---

## License

MIT License

---

## FaceLock Ecosystem

```text
FaceLock/
│
├── Core (detection, recognition, liveness, storage)
├── Authentication Service
├── Dashboard
├── Linux / Windows integration
│
└── exposes
        │
        ▼
FaceLock SDK
        │
        ▼
Developer Applications
```

## Changelog

**1.1.0**: `is_available()`, `authenticate_detailed()` / `AuthResult`, custom exceptions
(compatible with the 1.0 `ValueError` / `ConnectionError`), configurable socket path,
reads long responses correctly, and a 30 s default timeout to cover the service's
multi-frame unlock window.
