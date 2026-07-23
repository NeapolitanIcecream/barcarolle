from __future__ import annotations

from pathlib import Path
from contextlib import suppress
import hashlib
import os
import signal
import sys
import time

import pytest

from barcarolle import _subprocess as subprocess_module
from barcarolle._subprocess import _terminate_direct_process, run_bounded_process


@pytest.mark.parametrize(
    ("command", "timeout_seconds", "max_capture_bytes", "grace_seconds", "message"),
    (
        ((), 1.0, 1024, 1.0, "command must not be empty"),
        (("command",), 0.0, 1024, 1.0, "timeout_seconds must be positive"),
        (("command",), float("nan"), 1024, 1.0, "timeout_seconds must be positive"),
        (("command",), 1.0, 0, 1.0, "max_capture_bytes must be positive"),
        (("command",), 1.0, 1.5, 1.0, "max_capture_bytes must be positive"),
        (
            ("command",),
            1.0,
            1024,
            -1.0,
            "termination_grace_seconds must be nonnegative",
        ),
        (
            ("command",),
            1.0,
            1024,
            float("nan"),
            "termination_grace_seconds must be nonnegative",
        ),
    ),
)
def test_run_bounded_process_validates_request_before_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: tuple[str, ...],
    timeout_seconds: float,
    max_capture_bytes: int | float,
    grace_seconds: float,
    message: str,
) -> None:
    def fail_if_started(*args: object, **kwargs: object) -> None:
        raise AssertionError("invalid requests must fail before process start")

    monkeypatch.setattr(subprocess_module, "_start_process", fail_if_started)

    with pytest.raises(ValueError, match=message):
        run_bounded_process(
            command,
            cwd=tmp_path,
            timeout_seconds=timeout_seconds,
            max_capture_bytes=max_capture_bytes,  # type: ignore[arg-type]
            termination_grace_seconds=grace_seconds,
        )


def test_run_bounded_process_preserves_small_output_and_exit_code(
    tmp_path: Path,
) -> None:
    result = run_bounded_process(
        (
            sys.executable,
            "-c",
            "import sys; print('stdout'); print('stderr', file=sys.stderr); raise SystemExit(7)",
        ),
        cwd=tmp_path,
        timeout_seconds=5,
    )

    assert result.returncode == 7
    assert not result.timed_out
    assert result.containment_error is None
    assert result.stdout.text == "stdout\n"
    assert result.stderr.text == "stderr\n"
    assert not result.stdout.truncated
    assert not result.stderr.truncated


def test_run_bounded_process_bounds_both_streams_without_losing_digests(
    tmp_path: Path,
) -> None:
    stdout = b"A" * 4096 + b"stdout-tail"
    stderr = b"B" * 3072 + b"stderr-tail"
    result = run_bounded_process(
        (
            sys.executable,
            "-c",
            "import sys; "
            f"sys.stdout.buffer.write({stdout!r}); sys.stdout.flush(); "
            f"sys.stderr.buffer.write({stderr!r}); sys.stderr.flush()",
        ),
        cwd=tmp_path,
        timeout_seconds=5,
        max_capture_bytes=1024,
    )

    assert result.returncode == 0
    assert result.stdout.total_bytes == len(stdout)
    assert result.stderr.total_bytes == len(stderr)
    assert result.stdout.sha256 == hashlib.sha256(stdout).hexdigest()
    assert result.stderr.sha256 == hashlib.sha256(stderr).hexdigest()
    assert result.stdout.truncated
    assert result.stderr.truncated
    assert "total_bytes=4107" in result.stdout.text
    assert result.stdout.text.endswith("stdout-tail")
    assert result.stderr.text.endswith("stderr-tail")


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_run_bounded_process_kills_grandchild_that_ignores_term(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "grandchild-finished.txt"
    child_code = (
        "from pathlib import Path; import signal,time; "
        "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        "time.sleep(0.8); "
        f"Path({str(marker)!r}).write_text('escaped', encoding='utf-8')"
    )
    result = run_bounded_process(
        (
            sys.executable,
            "-c",
            "import subprocess, sys, time; "
            f"child = subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
            "print(child.pid, flush=True); time.sleep(60)",
        ),
        cwd=tmp_path,
        timeout_seconds=0.2,
        termination_grace_seconds=0.2,
    )
    child_pid = int(result.stdout.text.strip())
    try:
        assert result.timed_out
        assert result.containment_error is None
        time.sleep(0.9)
        assert not marker.exists()
    finally:
        with suppress(ProcessLookupError):
            os.kill(child_pid, signal.SIGKILL)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_run_bounded_process_cleans_background_child_after_leader_exit(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "background-finished.txt"
    child_code = (
        "from pathlib import Path; import signal,time; "
        "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        "time.sleep(0.8); "
        f"Path({str(marker)!r}).write_text('escaped', encoding='utf-8')"
    )
    result = run_bounded_process(
        (
            sys.executable,
            "-c",
            "import subprocess, sys; "
            f"child = subprocess.Popen([sys.executable, '-c', {child_code!r}], "
            "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
            "print(child.pid, flush=True)",
        ),
        cwd=tmp_path,
        timeout_seconds=5,
        termination_grace_seconds=0.2,
    )
    child_pid = int(result.stdout.text.strip())
    try:
        assert result.returncode == 0
        assert not result.timed_out
        assert result.containment_error is None
        time.sleep(0.9)
        assert not marker.exists()
    finally:
        with suppress(ProcessLookupError):
            os.kill(child_pid, signal.SIGKILL)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_run_bounded_process_allows_term_handler_grace(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "terminated.txt"
    result = run_bounded_process(
        (
            sys.executable,
            "-c",
            "from pathlib import Path; import signal,sys,time; "
            f"marker=Path({str(marker)!r}); "
            "signal.signal(signal.SIGTERM, lambda *_: (marker.write_text('term'), sys.exit(0))[1]); "
            "time.sleep(60)",
        ),
        cwd=tmp_path,
        timeout_seconds=0.2,
        termination_grace_seconds=1.0,
    )

    assert result.timed_out
    assert result.containment_error is None
    assert marker.read_text(encoding="utf-8") == "term"


@pytest.mark.skipif(os.name != "posix", reason="POSIX escaped-session counterexample")
def test_run_bounded_process_returns_boundedly_when_escaped_child_holds_pipes(
    tmp_path: Path,
) -> None:
    child_code = "import time; time.sleep(60)"
    start = time.monotonic()
    result = run_bounded_process(
        (
            sys.executable,
            "-c",
            "import subprocess, sys, time; "
            f"child = subprocess.Popen([sys.executable, '-c', {child_code!r}], start_new_session=True); "
            "print(child.pid, flush=True); time.sleep(60)",
        ),
        cwd=tmp_path,
        timeout_seconds=0.2,
        termination_grace_seconds=0.1,
    )
    elapsed = time.monotonic() - start
    child_pid = int(result.stdout.text.strip())
    try:
        assert elapsed < 2.0
        assert result.timed_out
        assert result.containment_error is not None
        assert "output pipes did not close" in result.containment_error
    finally:
        with suppress(ProcessLookupError):
            os.kill(child_pid, signal.SIGKILL)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group cleanup")
@pytest.mark.parametrize("failure", [RuntimeError("start failed"), KeyboardInterrupt()])
def test_run_bounded_process_cleans_up_when_reader_start_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    marker = tmp_path / "leaked-process.txt"
    real_start = subprocess_module.Thread.start
    starts = 0

    def fail_second_start(thread) -> None:
        nonlocal starts
        starts += 1
        if starts == 2:
            raise failure
        real_start(thread)

    monkeypatch.setattr(subprocess_module.Thread, "start", fail_second_start)
    start = time.monotonic()
    with pytest.raises(type(failure), match=str(failure) or None):
        run_bounded_process(
            (
                sys.executable,
                "-c",
                "from pathlib import Path; import time; time.sleep(0.8); "
                f"Path({str(marker)!r}).write_text('leaked', encoding='utf-8')",
            ),
            cwd=tmp_path,
            timeout_seconds=5,
            termination_grace_seconds=0.1,
        )

    assert time.monotonic() - start < 2.0
    time.sleep(0.9)
    assert not marker.exists()


def test_run_bounded_process_keeps_partial_output_digest_on_timeout(
    tmp_path: Path,
) -> None:
    payload = b"partial-before-timeout\n"
    result = run_bounded_process(
        (
            sys.executable,
            "-c",
            f"import sys,time; sys.stdout.buffer.write({payload!r}); sys.stdout.flush(); time.sleep(60)",
        ),
        cwd=tmp_path,
        timeout_seconds=0.2,
        termination_grace_seconds=0.1,
    )

    assert result.timed_out
    assert result.stdout.text == payload.decode("ascii")
    assert result.stdout.total_bytes == len(payload)
    assert result.stdout.sha256 == hashlib.sha256(payload).hexdigest()


class _FakeDirectProcess:
    def __init__(
        self, *, terminate_error: bool = False, kill_error: bool = False
    ) -> None:
        self.alive = True
        self.terminate_error = terminate_error
        self.kill_error = kill_error
        self.terminated = False
        self.killed = False
        self.wait_timeouts: list[float | None] = []

    def poll(self) -> int | None:
        return None if self.alive else -9

    def terminate(self) -> None:
        self.terminated = True
        if self.terminate_error:
            raise OSError("terminate failed")

    def kill(self) -> None:
        self.killed = True
        if self.kill_error:
            raise OSError("kill failed")
        self.alive = False

    def wait(self, timeout: float | None = None) -> int:
        self.wait_timeouts.append(timeout)
        if self.alive:
            raise subprocess_module.subprocess.TimeoutExpired(("fake",), timeout)
        return -9


def test_direct_process_fallback_uses_only_bounded_waits() -> None:
    process = _FakeDirectProcess()

    error = _terminate_direct_process(process, 0.1)  # type: ignore[arg-type]

    assert error == "process-tree containment is unavailable on this platform"
    assert process.terminated
    assert process.killed
    assert process.wait_timeouts == [0.1, 0.2]
    assert all(timeout is not None for timeout in process.wait_timeouts)


def test_direct_process_fallback_reports_cleanup_errors_without_raising() -> None:
    process = _FakeDirectProcess(terminate_error=True, kill_error=True)

    error = _terminate_direct_process(process, 0.1)  # type: ignore[arg-type]

    assert "process-tree containment is unavailable" in error
    assert "terminate failed: OSError" in error
    assert "kill failed: OSError" in error
