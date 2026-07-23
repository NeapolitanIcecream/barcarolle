"""Bounded subprocess capture and cooperative process-tree containment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock, Thread
from time import monotonic, sleep
from typing import BinaryIO, Sequence
import hashlib
import math
import os
import signal
import subprocess


_DEFAULT_CAPTURE_BYTES = 1024 * 1024
_READ_CHUNK_BYTES = 64 * 1024
_PIPE_DRAIN_SECONDS = 0.1
_POSIX_PROCESS_GROUPS = os.name == "posix"


@dataclass(frozen=True)
class CapturedStream:
    text: str
    total_bytes: int
    sha256: str
    truncated: bool


@dataclass(frozen=True)
class BoundedProcessResult:
    returncode: int | None
    stdout: CapturedStream
    stderr: CapturedStream
    timed_out: bool
    containment_error: str | None

    @property
    def output_digest(self) -> str:
        payload = (
            f"stdout:{self.stdout.total_bytes}:{self.stdout.sha256}\n"
            f"stderr:{self.stderr.total_bytes}:{self.stderr.sha256}"
        )
        return hashlib.sha256(payload.encode("ascii")).hexdigest()


class _StreamAccumulator:
    def __init__(self, max_capture_bytes: int) -> None:
        self._max_capture_bytes = max_capture_bytes
        self._tail = bytearray()
        self._digest = hashlib.sha256()
        self._total_bytes = 0
        self._lock = Lock()

    def add(self, chunk: bytes) -> None:
        with self._lock:
            self._digest.update(chunk)
            self._total_bytes += len(chunk)
            self._tail.extend(chunk)
            excess = len(self._tail) - self._max_capture_bytes
            if excess > 0:
                del self._tail[:excess]

    def finish(self) -> CapturedStream:
        with self._lock:
            digest = self._digest.hexdigest()
            total_bytes = self._total_bytes
            tail = bytes(self._tail)
        truncated = total_bytes > self._max_capture_bytes
        tail_text = tail.decode("utf-8", errors="replace")
        if not truncated:
            text = tail_text
        else:
            text = (
                "[barcarolle output truncated: "
                f"total_bytes={total_bytes} sha256={digest}; "
                f"showing_last_bytes={len(tail)}]\n"
                f"{tail_text}"
            )
        return CapturedStream(
            text=text,
            total_bytes=total_bytes,
            sha256=digest,
            truncated=truncated,
        )


def run_bounded_process(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: float,
    max_capture_bytes: int = _DEFAULT_CAPTURE_BYTES,
    termination_grace_seconds: float = 1.0,
) -> BoundedProcessResult:
    normalized_command = _validated_process_request(
        command,
        timeout_seconds,
        max_capture_bytes,
        termination_grace_seconds,
    )
    process = _start_process(normalized_command, cwd)
    reader_errors: list[str] = []
    stdout_accumulator, stderr_accumulator, readers = _process_stream_readers(
        process,
        max_capture_bytes,
        reader_errors,
    )
    started_readers: list[Thread] = []
    try:
        _start_readers(readers, started_readers)
        timed_out = _wait_for_process(process, timeout_seconds)
        containment_errors = _contain_and_drain_process(
            process,
            started_readers,
            reader_errors,
            timed_out=timed_out,
            termination_grace_seconds=termination_grace_seconds,
        )
    except BaseException:
        _cleanup_failed_process(
            process,
            started_readers,
            termination_grace_seconds,
        )
        raise

    return BoundedProcessResult(
        returncode=process.returncode,
        stdout=stdout_accumulator.finish(),
        stderr=stderr_accumulator.finish(),
        timed_out=timed_out,
        containment_error="; ".join(containment_errors) or None,
    )


def _validated_process_request(
    command: Sequence[str],
    timeout_seconds: float,
    max_capture_bytes: int,
    termination_grace_seconds: float,
) -> tuple[str, ...]:
    normalized_command = tuple(command)
    if not normalized_command:
        raise ValueError("command must not be empty")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, int | float)
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise ValueError("timeout_seconds must be positive")
    if type(max_capture_bytes) is not int or max_capture_bytes < 1:
        raise ValueError("max_capture_bytes must be positive")
    if (
        isinstance(termination_grace_seconds, bool)
        or not isinstance(termination_grace_seconds, int | float)
        or not math.isfinite(float(termination_grace_seconds))
        or termination_grace_seconds < 0
    ):
        raise ValueError("termination_grace_seconds must be nonnegative")
    return normalized_command


def _process_stream_readers(
    process: subprocess.Popen[bytes],
    max_capture_bytes: int,
    reader_errors: list[str],
) -> tuple[_StreamAccumulator, _StreamAccumulator, tuple[Thread, Thread]]:
    assert process.stdout is not None
    assert process.stderr is not None
    stdout_accumulator = _StreamAccumulator(max_capture_bytes)
    stderr_accumulator = _StreamAccumulator(max_capture_bytes)
    readers = (
        Thread(
            target=_drain_stream,
            args=(process.stdout, stdout_accumulator, reader_errors),
            name="barcarolle-stdout-reader",
            daemon=True,
        ),
        Thread(
            target=_drain_stream,
            args=(process.stderr, stderr_accumulator, reader_errors),
            name="barcarolle-stderr-reader",
            daemon=True,
        ),
    )
    return stdout_accumulator, stderr_accumulator, readers


def _start_readers(readers: Sequence[Thread], started_readers: list[Thread]) -> None:
    for reader in readers:
        reader.start()
        started_readers.append(reader)


def _wait_for_process(
    process: subprocess.Popen[bytes],
    timeout_seconds: float,
) -> bool:
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return True
    return False


def _contain_and_drain_process(
    process: subprocess.Popen[bytes],
    readers: Sequence[Thread],
    reader_errors: Sequence[str],
    *,
    timed_out: bool,
    termination_grace_seconds: float,
) -> tuple[str, ...]:
    containment_errors: list[str] = []
    if timed_out or _POSIX_PROCESS_GROUPS:
        if error := _terminate_process_tree(process, termination_grace_seconds):
            containment_errors.append(error)
    _join_readers(readers, _PIPE_DRAIN_SECONDS)
    if any(reader.is_alive() for reader in readers):
        if error := _terminate_process_tree(process, termination_grace_seconds):
            containment_errors.append(error)
        _join_readers(readers, termination_grace_seconds + 0.5)
    if any(reader.is_alive() for reader in readers):
        containment_errors.append("process output pipes did not close")
    if reader_errors:
        containment_errors.append("; ".join(sorted(set(reader_errors))))
    return tuple(containment_errors)


def _cleanup_failed_process(
    process: subprocess.Popen[bytes],
    readers: Sequence[Thread],
    termination_grace_seconds: float,
) -> None:
    _terminate_process_tree(process, termination_grace_seconds)
    _join_readers(readers, termination_grace_seconds + 0.5)
    if not any(reader.is_alive() for reader in readers):
        _close_process_pipes(process)


def _start_process(
    command: tuple[str, ...],
    cwd: Path,
) -> subprocess.Popen[bytes]:
    if _POSIX_PROCESS_GROUPS:
        return subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            start_new_session=True,
        )
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        creationflags=creation_flags,
    )


def _drain_stream(
    pipe: BinaryIO,
    accumulator: _StreamAccumulator,
    errors: list[str],
) -> None:
    try:
        while chunk := pipe.read(_READ_CHUNK_BYTES):
            accumulator.add(chunk)
    except (OSError, ValueError) as exc:
        errors.append(f"output capture failed: {type(exc).__name__}")
    finally:
        try:
            pipe.close()
        except OSError:
            pass


def _join_readers(readers: Sequence[Thread], timeout_seconds: float) -> None:
    deadline = monotonic() + timeout_seconds
    for reader in readers:
        reader.join(max(0.0, deadline - monotonic()))


def _terminate_process_tree(
    process: subprocess.Popen[bytes],
    grace_seconds: float,
) -> str | None:
    if not _POSIX_PROCESS_GROUPS:
        return _terminate_direct_process(process, grace_seconds)

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        _wait_for_leader(process, grace_seconds)
        return None
    except OSError as exc:
        return f"process-group TERM failed: {type(exc).__name__}"
    if _wait_for_process_group_exit(process, grace_seconds):
        return None
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        _wait_for_leader(process, grace_seconds)
        return None
    except OSError as exc:
        return f"process-group KILL failed: {type(exc).__name__}"
    _wait_for_leader(process, max(grace_seconds, 0.2))
    if process.poll() is None:
        return "process leader remained alive after SIGKILL"
    return None


def _terminate_direct_process(
    process: subprocess.Popen[bytes],
    grace_seconds: float,
) -> str:
    errors = ["process-tree containment is unavailable on this platform"]
    if process.poll() is not None:
        return errors[0]

    needs_kill = False
    try:
        process.terminate()
    except OSError as exc:
        errors.append(f"direct-process terminate failed: {type(exc).__name__}")
        needs_kill = True
    if not needs_kill:
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            needs_kill = True
        except OSError as exc:
            errors.append(f"direct-process wait failed: {type(exc).__name__}")
            needs_kill = True
    if needs_kill:
        try:
            process.kill()
        except OSError as exc:
            errors.append(f"direct-process kill failed: {type(exc).__name__}")
        else:
            try:
                process.wait(timeout=max(grace_seconds, 0.2))
            except subprocess.TimeoutExpired:
                errors.append("direct process remained alive after kill")
            except OSError as exc:
                errors.append(f"direct-process wait failed: {type(exc).__name__}")
    return "; ".join(errors)


def _wait_for_process_group_exit(
    process: subprocess.Popen[bytes],
    timeout_seconds: float,
) -> bool:
    deadline = monotonic() + timeout_seconds
    while True:
        _wait_for_leader(process, 0.0)
        if not _process_group_exists(process.pid):
            return True
        if monotonic() >= deadline:
            return False
        sleep(min(0.02, max(0.0, deadline - monotonic())))


def _wait_for_leader(
    process: subprocess.Popen[bytes],
    timeout_seconds: float,
) -> None:
    if process.poll() is not None:
        return
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        pass


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _close_process_pipes(process: subprocess.Popen[bytes]) -> None:
    for pipe in (process.stdout, process.stderr):
        if pipe is None:
            continue
        try:
            pipe.close()
        except OSError:
            pass
