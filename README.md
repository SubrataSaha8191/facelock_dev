# FaceLock SDK

The official Python client for the [FaceLock](https://github.com/SubrataSaha8191/FaceLock) authentication service.

Ask "is the owner in front of the camera?" from your own Python app in one line. The SDK has no camera, OpenCV or machine-learning code: it talks to the locally running FaceLock service over a UNIX socket, and the service does all the biometric work.

```python
import facelock

if facelock.authenticate():
    print("Welcome back.")
```

---

## Features

- One-call face authentication that accepts any head angle the user enrolled
- Detailed results (reason and score) so you can tell users *why* it failed
- Clear exceptions for "service not running" and "not enrolled"
- Standard library only, Python 3.8+
- Works on Linux and Windows
- Local UNIX Domain Socket communication; nothing leaves the machine

---

## Requirements

The FaceLock service **2.0 or newer** must be installed and running, and the user must have enrolled a face (see the [FaceLock README](https://github.com/SubrataSaha8191/FaceLock)).

| Check | How |
|---|---|
| Service running | `facelock.is_available()` |
| User enrolled | `facelock.is_enrolled()` |

Older services still work with `authenticate()` and `is_enrolled()`, but do not report failure reasons.

---

## Installation

```bash
pip install git+https://github.com/SubrataSaha8191/facelock_dev.git
```

---

## Quick start

```python
import facelock

try:
    if facelock.authenticate():
        print("Authentication successful.")
    else:
        print("Authentication failed.")

except facelock.UserNotEnrolledError:
    print("No usable face profile. Enroll (or re-scan) in the FaceLock dashboard.")

except facelock.FaceLockConnectionError:
    print("The FaceLock service is not running.")
```

### Notes

- **Don't retry in a loop.** One call watches the camera for several seconds (6 s by default) and returns as soon as it is sure, so a single call is normally enough.
- `authenticate()` blocks while the camera is in use. Call it from a worker thread in GUI apps.
- `user_id` defaults to the **current OS user**. FaceLock maps that to the face profile linked to the account, so you rarely need to pass it.
- Only one unlock runs at a time; a second concurrent call waits for the first.

---

## API

### `authenticate(user_id=None, timeout=None, socket_path=None) -> bool`

Authenticate a user with their face.

Raises `FaceLockConnectionError`, `UserNotEnrolledError`.

### `authenticate_detailed(user_id=None, timeout=None, socket_path=None) -> AuthResult`

Same as `authenticate()` but returns an `AuthResult`, which is truthy when authentication succeeded.

```python
result = facelock.authenticate_detailed()
if not result:
    print(result.reason, "-", result.message, f"(score {result.score:.2f})")
```

| Field | Meaning |
|---|---|
| `ok` | `True` on success |
| `score` | Best similarity seen (0 to 1) |
| `reason` | `match`, `mismatch`, `no_face`, `low_quality`, `liveness_failed`, `locked`, `camera_unavailable` (empty with older services) |
| `message` | Human-readable explanation |

Handy mapping for UIs:

| Reason | Suggest to the user |
|---|---|
| `no_face` | "Look at the camera" |
| `low_quality` | "Check your lighting and distance" |
| `mismatch` | "That didn't look like you" |
| `locked` | "Too many attempts, try again later or use your password" |
| `camera_unavailable` | "Close other apps using the camera" |

### `is_enrolled(user_id=None, socket_path=None) -> bool`

Whether the user has a **usable** face profile. Returns `False` if the service is unreachable; use `is_available()` to tell those cases apart. Profiles made with the pre-2.0 matcher count as not enrolled until the user re-scans.

### `is_available(socket_path=None) -> bool`

Whether the service is reachable.

### Exceptions

| Exception | Meaning |
|---|---|
| `FaceLockError` | Base class |
| `FaceLockConnectionError` | Service unreachable (also a `ConnectionError`) |
| `UserNotEnrolledError` | No usable face profile (also a `ValueError`) |
| `AuthenticationFailedError` | For callers that prefer failure as an exception; carries `.reason` |

### Configuration

| Option | Default |
|---|---|
| Socket path | Linux: `/tmp/facelock.sock`. Windows: `auto` (read from `%LOCALAPPDATA%\FaceLock\endpoint.json`). Override with the `FACELOCK_SOCKET` environment variable or `socket_path=` |
| Data folder | `FACELOCK_DATA_DIR` (where `endpoint.json` is looked up on Windows) |
| Token | Read from `endpoint.json`; `FACELOCK_TOKEN` overrides it for `tcp://` addresses |
| Timeout | 30 s (covers the service's multi-frame unlock window), override with `timeout=` |

---

## Recipes

**Guard a sensitive action**

```python
def require_owner():
    result = facelock.authenticate_detailed()
    if not result:
        raise facelock.AuthenticationFailedError(result.message, reason=result.reason)

def export_secrets():
    require_owner()
    ...
```

**Friendly pre-checks**

```python
if not facelock.is_available():
    print("Start the service: sudo systemctl start facelock")
elif not facelock.is_enrolled():
    print("Enroll your face in the FaceLock dashboard first.")
```

---

## Architecture

```text
Your application
      │
      ▼
 FaceLock SDK
      │
 local socket: UNIX socket (Linux) or
 loopback TCP + secret token (Windows)
      │
      ▼
FaceLock service ──► camera ► detection ► recognition ► liveness ► decision
```

The SDK intentionally contains no machine-learning models, OpenCV, camera handling, recognition or authentication logic.

### Project structure

```text
facelock/
  __init__.py    public API
  client.py      socket client, authenticate(), is_enrolled(), is_available()
  constants.py   socket path, timeouts, actions, reasons
  exceptions.py  FaceLockError and subclasses
  version.py     __version__
tests/           pytest suite (runs against a fake daemon, no camera needed)
```

---

## Development

```bash
pip install -e .
python -m pytest -q
```

The tests start a fake daemon on a temporary UNIX socket, so they need neither the FaceLock service nor a camera.

---

## Roadmap

- `version()`, `get_status()`
- `enroll()`, `remove_user()`, `list_users()`
- `@require_face` decorator
- Async API
- Windows named-pipe transport

---

## Changelog

**1.2.0**
- Windows support: the SDK connects over loopback TCP with the per-user token from `endpoint.json` when there is no UNIX socket
- `is_available()` and the other calls report an unreachable service as `False` / `FaceLockConnectionError` on every platform

**1.1.0**
- Added `is_available()` and `authenticate_detailed()` / `AuthResult`
- Added `FaceLockError`, `FaceLockConnectionError`, `UserNotEnrolledError`, `AuthenticationFailedError` (the first two remain compatible with 1.0's `ConnectionError` / `ValueError`)
- Configurable socket path; long responses are read correctly
- 30 s default timeout for the service's multi-frame unlock window
- Split into `client` / `constants` / `exceptions` / `version` modules; added tests

**1.0.0**
- Initial release: `authenticate()` and `is_enrolled()`

---

## License

MIT
