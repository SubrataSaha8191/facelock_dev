"""SDK tests against a fake FaceLock daemon on a temporary UNIX socket."""

import json
import os
import socket
import tempfile
import threading

import pytest

import facelock
from facelock import (
    FaceLockConnectionError,
    UserNotEnrolledError,
    authenticate,
    authenticate_detailed,
    is_available,
    is_enrolled,
)


class FakeDaemon:
    def __init__(self, handler):
        self.path = os.path.join(tempfile.mkdtemp(), "fl.sock")
        self.handler = handler
        self.requests = []
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.path)
        self.sock.listen(5)
        self.sock.settimeout(0.2)
        self.running = True
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while self.running:
            try:
                conn, _ = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            with conn:
                data = conn.recv(65536).decode()
                if not data:  # availability probe: connect and hang up
                    continue
                req = json.loads(data)
                self.requests.append(req)
                conn.sendall(json.dumps(self.handler(req)).encode())

    def close(self):
        self.running = False
        self.sock.close()
        self.thread.join(timeout=1)


@pytest.fixture
def daemon():
    made = []

    def make(handler):
        d = FakeDaemon(handler)
        made.append(d)
        return d

    yield make
    for d in made:
        d.close()


def test_version_and_public_api():
    assert facelock.__version__ == "1.1.0"
    for name in ("authenticate", "is_enrolled", "is_available", "FaceLockConnectionError"):
        assert hasattr(facelock, name)


def test_authenticate_success_and_request_shape(daemon):
    d = daemon(lambda r: {"result": True, "similarity": 0.81, "reason": "match", "message": "ok"})
    assert authenticate("alice", socket_path=d.path) is True
    assert d.requests == [{"action": "authenticate_face", "user_id": "alice"}]


def test_detailed_result_carries_reason_and_score(daemon):
    d = daemon(lambda r: {"result": False, "similarity": 0.21, "reason": "mismatch", "message": "Face didn't match"})
    res = authenticate_detailed("alice", socket_path=d.path)
    assert not res and res.reason == "mismatch" and res.score == pytest.approx(0.21)


def test_no_face_is_a_plain_false_not_an_error(daemon):
    d = daemon(lambda r: {"result": False, "reason": "no_face", "message": "No face found"})
    assert authenticate("alice", socket_path=d.path) is False


@pytest.mark.parametrize("reason", ["not_enrolled", "re_enroll_required"])
def test_unusable_profile_raises_user_not_enrolled(daemon, reason):
    d = daemon(lambda r: {"result": False, "reason": reason, "message": "x"})
    with pytest.raises(UserNotEnrolledError):
        authenticate("alice", socket_path=d.path)


def test_old_daemon_without_reason_falls_back_to_enrollment_check(daemon):
    def handler(req):
        if req["action"] == "check_enrolled":
            return {"result": False}
        return {"result": False, "message": "Face auth failed"}

    d = daemon(handler)
    with pytest.raises(UserNotEnrolledError):
        authenticate("alice", socket_path=d.path)


def test_old_daemon_failed_match_for_enrolled_user_is_false(daemon):
    d = daemon(lambda r: {"result": True} if r["action"] == "check_enrolled" else {"result": False})
    assert authenticate("alice", socket_path=d.path) is False


def test_is_enrolled_and_availability(daemon):
    d = daemon(lambda r: {"result": r["user_id"] == "alice"})
    assert is_enrolled("alice", socket_path=d.path) is True
    assert is_enrolled("bob", socket_path=d.path) is False
    assert is_available(d.path) is True


def test_unreachable_service():
    missing = os.path.join(tempfile.mkdtemp(), "nope.sock")
    assert is_available(missing) is False
    assert is_enrolled("alice", socket_path=missing) is False
    with pytest.raises(FaceLockConnectionError):
        authenticate("alice", socket_path=missing)


def test_exceptions_stay_compatible_with_sdk_1_0():
    assert issubclass(FaceLockConnectionError, ConnectionError)
    assert issubclass(UserNotEnrolledError, ValueError)
