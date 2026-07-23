"""Small single-writer resource-ledger persistence for paid examples."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence
import json
import math
import os

from barcarolle.records import canonical_json


def ledger_events_path(snapshot_path: Path) -> Path:
    return snapshot_path.with_name(f"{snapshot_path.stem}-events.jsonl")


def load_resource_ledger(
    path: Path,
    *,
    updated_at: str,
) -> dict[str, object]:
    if not path.exists():
        raise RuntimeError(f"resource ledger is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("calls"), list):
        raise RuntimeError("resource ledger must contain a calls list")
    events = load_ledger_events(ledger_events_path(path))
    if events:
        return rebuild_ledger_snapshot(
            path,
            value,
            events,
            updated_at=updated_at,
        )
    if value["calls"]:
        raise RuntimeError("resource ledger snapshot has calls without an event log")
    _validate_empty_ledger_snapshot(value)
    return value


def load_ledger_events(path: Path) -> tuple[dict[str, object], ...]:
    if not path.exists():
        return ()
    text = path.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        raise RuntimeError("resource ledger event log has an unterminated final line")
    events: list[dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"resource ledger event line {line_number} is invalid"
            ) from exc
        if not isinstance(value, dict):
            raise RuntimeError("resource ledger events must be JSON objects")
        events.append(value)
    return tuple(events)


def append_ledger_event(path: Path, event: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(event))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_directory(path.parent)


def rebuild_ledger_snapshot(
    path: Path,
    ledger: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    *,
    updated_at: str,
) -> dict[str, object]:
    _require_updated_at(updated_at)
    calls = _fold_ledger_events(events)
    budget = _ledger_budget(ledger)
    spent = _ledger_spent(calls)
    snapshot = dict(ledger)
    snapshot["calls"] = calls
    snapshot["spent_usd"] = spent
    snapshot["remaining_usd"] = budget - spent
    snapshot["updated_at"] = updated_at
    write_json(path, snapshot)
    return snapshot


def _fold_ledger_events(
    events: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    by_id: dict[str, dict[str, object]] = {}
    completed: set[str] = set()
    for event in events:
        event_type = event.get("event_type")
        call_id = event.get("call_id")
        if not isinstance(call_id, str) or not call_id:
            raise RuntimeError("resource ledger event call_id is required")
        if event_type == "reservation":
            if call_id in by_id:
                raise RuntimeError("resource ledger has a duplicate reservation")
            call = {key: value for key, value in event.items() if key != "event_type"}
            calls.append(call)
            by_id[call_id] = call
        elif event_type == "completion":
            call = by_id.get(call_id)
            if call is None or call_id in completed:
                raise RuntimeError("resource ledger completion has no reservation")
            call.update(
                {
                    key: value
                    for key, value in event.items()
                    if key not in {"event_type", "call_id"}
                }
            )
            completed.add(call_id)
        else:
            raise RuntimeError("resource ledger event_type is invalid")
    return calls


def _ledger_budget(ledger: Mapping[str, object]) -> float:
    authorization = ledger.get("authorization")
    if not isinstance(authorization, Mapping):
        raise RuntimeError("resource ledger authorization is missing")
    return _finite_nonnegative_number(
        authorization.get("budget_usd"),
        field_name="budget_usd",
    )


def _validate_empty_ledger_snapshot(ledger: Mapping[str, object]) -> None:
    _require_updated_at(ledger.get("updated_at"))
    budget = _ledger_budget(ledger)
    spent = _finite_nonnegative_number(
        ledger.get("spent_usd"),
        field_name="spent_usd",
    )
    remaining = _finite_nonnegative_number(
        ledger.get("remaining_usd"),
        field_name="remaining_usd",
    )
    if spent != 0.0 or remaining != budget:
        raise RuntimeError(
            "resource ledger empty snapshot totals do not match its event log"
        )


def _ledger_spent(calls: Sequence[Mapping[str, object]]) -> float:
    spent = 0.0
    for call in calls:
        estimated_cost = call.get("estimated_cost_usd")
        if estimated_cost is None:
            continue
        spent += _finite_nonnegative_number(
            estimated_cost,
            field_name="estimated_cost_usd",
        )
        if not math.isfinite(spent):
            raise RuntimeError("resource ledger spent_usd must remain finite")
    return spent


def _finite_nonnegative_number(value: object, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise RuntimeError(
            f"resource ledger {field_name} must be finite and nonnegative"
        )
    try:
        number = float(value)
    except OverflowError as exc:
        raise RuntimeError(
            f"resource ledger {field_name} must be finite and nonnegative"
        ) from exc
    if not math.isfinite(number) or number < 0:
        raise RuntimeError(
            f"resource ledger {field_name} must be finite and nonnegative"
        )
    return number


def _require_updated_at(value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("resource ledger updated_at must be a nonempty string")


def write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(canonical_json(value))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
