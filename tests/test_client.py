"""SDK tests against a fake FaceLock daemon, over both transports (UNIX socket and loopback TCP)."""

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

TOKEN = "s3cret-token"


class FakeDaemon:
    """A daemon on a UNIX socket (POSIX) or a token-checked loopback TCP port."""

    def __init__(self, handler, transport, data_dir):
        self.handler, self.requests = handler, []
        if transport == "unix":
            self.address = os.path.join(tempfile.mkdtemp(), "fl.sock")
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.bind(self.address)
            self.token = None
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(("127.0.0.1", 0))
            port = self.sock.getsockname()[1]
            self.address, self.token = f"tcp://127.0.0.1:{port}", TOKEN
            (data_dir / "endpoint.json").write_text(json.dumps({"host": "127.0.0.1", "port": port, "token": TOKEN}))
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
                if self.token is not None and req.pop("token", None) != self.token:
                    conn.sendall(json.dumps({"result": False, "reason": "unauthorized"}).encode())
                    continue
                self.requests.append(req)
                conn.sendall(json.dumps(self.handler(req)).encode())

    def close(self):
        self.running = False
        self.sock.close()
        self.thread.join(timeout=1)


@pytest.fixture(params=["unix", "tcp"])
def daemon(request, tmp_path, monkeypatch):
    if request.param == "unix" and not hasattr(socket, "AF_UNIX"):
        pytest.skip("no AF_UNIX on this platform")
    monkeypatch.setenv("FACELOCK_DATA_DIR", str(tmp_path))
    made = []

    def make(handler):
        d = FakeDaemon(handler, request.param, tmp_path)
        made.append(d)
        return d

    yield make
    for d in made:
        d.close()


UNREACHABLE = os.path.join(tempfile.gettempdir(), "nope.sock") if hasattr(socket, "AF_UNIX") else "tcp://127.0.0.1:1"


def test_version_and_public_api():
    assert facelock.__version__ == "1.2.0"
    for name in ("authenticate", "is_enrolled", "is_available", "FaceLockConnectionError"):
        assert hasattr(facelock, name)


def test_authenticate_success_and_request_shape(daemon):
    d = daemon(lambda r: {"result": True, "similarity": 0.81, "reason": "match", "message": "ok"})
    assert authenticate("alice", socket_path=d.address) is True
    assert d.requests == [{"action": "authenticate_face", "user_id": "alice"}]  # token never reaches the handler


def test_detailed_result_carries_reason_and_score(daemon):
    d = daemon(lambda r: {"result": False, "similarity": 0.21, "reason": "mismatch", "message": "Face didn't match"})
    res = authenticate_detailed("alice", socket_path=d.address)
    assert not res and res.reason == "mismatch" and res.score == pytest.approx(0.21)


def test_no_face_is_a_plain_false_not_an_error(daemon):
    d = daemon(lambda r: {"result": False, "reason": "no_face", "message": "No face found"})
    assert authenticate("alice", socket_path=d.address) is False


@pytest.mark.parametrize("reason", ["not_enrolled", "re_enroll_required"])
def test_unusable_profile_raises_user_not_enrolled(daemon, reason):
    d = daemon(lambda r: {"result": False, "reason": reason, "message": "x"})
    with pytest.raises(UserNotEnrolledError):
        authenticate("alice", socket_path=d.address)


def test_old_daemon_without_reason_falls_back_to_enrollment_check(daemon):
    def handler(req):
        if req["action"] == "check_enrolled":
            return {"result": False}
        return {"result": False, "message": "Face auth failed"}

    d = daemon(handler)
    with pytest.raises(UserNotEnrolledError):
        authenticate("alice", socket_path=d.address)


def test_old_daemon_failed_match_for_enrolled_user_is_false(daemon):
    d = daemon(lambda r: {"result": True} if r["action"] == "check_enrolled" else {"result": False})
    assert authenticate("alice", socket_path=d.address) is False


def test_is_enrolled_and_availability(daemon):
    d = daemon(lambda r: {"result": r["user_id"] == "alice"})
    assert is_enrolled("alice", socket_path=d.address) is True
    assert is_enrolled("bob", socket_path=d.address) is False
    assert is_available(d.address) is True


def test_unreachable_service():
    assert is_available(UNREACHABLE) is False
    assert is_enrolled("alice", socket_path=UNREACHABLE) is False
    with pytest.raises(FaceLockConnectionError):
        authenticate("alice", socket_path=UNREACHABLE)


def test_exceptions_stay_compatible_with_sdk_1_0():
    assert issubclass(FaceLockConnectionError, ConnectionError)
    assert issubclass(UserNotEnrolledError, ValueError)


# ---- Windows-style transport: loopback TCP with a secret token ----

def test_tcp_token_is_read_from_endpoint_file_and_sent(tmp_path, monkeypatch):
    monkeypatch.setenv("FACELOCK_DATA_DIR", str(tmp_path))
    d = FakeDaemon(lambda r: {"result": True, "reason": "match"}, "tcp", tmp_path)
    try:
        assert authenticate("alice", socket_path=d.address) is True
        # 'auto' resolves the port and token purely from endpoint.json
        assert authenticate("alice", socket_path="auto") is True
        assert is_available("auto") is True
    finally:
        d.close()


def test_wrong_token_is_not_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv("FACELOCK_DATA_DIR", str(tmp_path))
    d = FakeDaemon(lambda r: {"result": True, "reason": "match"}, "tcp", tmp_path)
    try:
        monkeypatch.setenv("FACELOCK_TOKEN", "not-the-token")
        (tmp_path / "endpoint.json").unlink()  # force the env token to be used
        assert authenticate_detailed("alice", socket_path=d.address).ok is False
    finally:
        d.close()


def test_auto_without_endpoint_is_a_clean_error(tmp_path, monkeypatch):
    monkeypatch.setenv("FACELOCK_DATA_DIR", str(tmp_path))
    assert is_available("auto") is False
    with pytest.raises(FaceLockConnectionError):
        authenticate("alice", socket_path="auto")
