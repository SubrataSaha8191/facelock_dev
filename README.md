# FaceLock API Library

This is the lightweight developer API package for **FaceLock**, a system-wide biometric facial authentication platform for Linux.

This package allows developers to easily embed highly secure facial authentication into their custom Python applications without worrying about heavy machine learning dependencies, camera resources, or OS permissions.

## Installation

```bash
pip install git+https://github.com/SubrataSaha8191/facelock_dev.git
```

*(**Note**: The main [FaceLock OS Daemon](https://github.com/SubrataSaha8191/FaceLock) must be installed and running on the target machine for this library to work.)*

## Usage Example (FaceLock Captcha)

```python
import facelock

def enter_admin_vault():
    print("Welcome! Please look at the camera to verify your identity.")
    
    try:
        # Automatically triggers camera via background socket
        if facelock.authenticate():
            print("✅ Access Granted: You are now in the admin vault!")
        else:
            print("❌ Access Denied: Biometric verification failed.")
            
    except ValueError as e:
        print(f"Error: {e}")
    except ConnectionError:
        print("FaceLock daemon is not running. Please start the service.")

if __name__ == "__main__":
    enter_admin_vault()
```

## How it Works
This library contains **zero ML or OpenCV dependencies**. It communicates over a lightweight UNIX Domain Socket (`/tmp/facelock.sock`) directly to the system-level `facelock.service` daemon. This means your Python applications stay blazingly fast and avoid "Device Busy" webcam errors.
# facelock_dev
