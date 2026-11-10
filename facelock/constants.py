"""Protocol constants shared with the FaceLock Authentication Service."""

import os

DEFAULT_SOCKET_PATH = os.environ.get("FACELOCK_SOCKET", "/tmp/facelock.sock")

# An unlock attempt watches the camera for a few seconds (the service default is 6 s,
# configurable up to 20 s), plus camera start-up, so allow generous headroom.
SOCKET_TIMEOUT = 30.0
AVAILABILITY_TIMEOUT = 2.0

ACTION_AUTHENTICATE = "authenticate_face"
ACTION_CHECK_ENROLLED = "check_enrolled"

# Reasons the service reports for a failed attempt.
REASON_MATCH = "match"
REASON_NOT_ENROLLED = "not_enrolled"
REASON_REENROLL = "re_enroll_required"
REASON_LOCKED = "locked"
