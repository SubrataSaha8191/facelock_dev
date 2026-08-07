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

    print("User is not enrolled.")

except facelock.FaceLockConnectionError:

    print("FaceLock Authentication Service is unavailable.")
```

---

## API

### authenticate()

Authenticate the current user.

Returns

```python
bool
```

Raises

- FaceLockConnectionError
- UserNotEnrolledError

---

### is_enrolled()

Check whether the current user is enrolled.

Returns

```python
bool
```

---

### is_available()

Check whether the FaceLock Authentication Service is available.

Returns

```python
bool
```

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

Since you're building both FaceLock and the SDK, I recommend documenting a simple repository architecture so contributors immediately understand how everything fits together:

```text
FaceLock/
│
├── FaceLock Core
├── Authentication Service
├── Dashboard
├── Linux Integration
├── Windows Integration
│
└── exposes
        │
        ▼
FaceLock SDK
        │
        ▼
Developer Applications
```
