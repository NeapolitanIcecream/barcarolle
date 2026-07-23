from __future__ import annotations

from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.experiment_ledger import (  # noqa: E402
    append_ledger_event,
    ledger_events_path,
    load_ledger_events,
    load_resource_ledger,
    rebuild_ledger_snapshot,
    write_json,
)


def test_resource_ledger_rebuilds_reservation_completion_and_cost(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "resource-ledger.json"
    initial = {
        "authorization": {"budget_usd": 5.0},
        "calls": [],
        "spent_usd": 0.0,
        "remaining_usd": 5.0,
        "updated_at": "before",
    }
    write_json(snapshot, initial)
    events = ledger_events_path(snapshot)
    append_ledger_event(
        events,
        {
            "event_type": "reservation",
            "call_id": "cell-01",
            "state": "started",
        },
    )
    append_ledger_event(
        events,
        {
            "event_type": "completion",
            "call_id": "cell-01",
            "state": "completed",
            "estimated_cost_usd": 1.25,
        },
    )

    ledger = load_resource_ledger(snapshot, updated_at="after")

    assert ledger["calls"] == [
        {
            "call_id": "cell-01",
            "state": "completed",
            "estimated_cost_usd": 1.25,
        }
    ]
    assert ledger["spent_usd"] == 1.25
    assert ledger["remaining_usd"] == 3.75
    assert ledger["updated_at"] == "after"


def test_resource_ledger_allows_completion_without_known_cost(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "resource-ledger.json"

    ledger = rebuild_ledger_snapshot(
        snapshot,
        {"authorization": {"budget_usd": 5.0}, "calls": []},
        (
            {
                "event_type": "reservation",
                "call_id": "cell-01",
                "state": "started",
            },
            {
                "event_type": "completion",
                "call_id": "cell-01",
                "state": "stopped",
            },
        ),
        updated_at="after",
    )

    assert ledger["spent_usd"] == 0.0
    assert ledger["remaining_usd"] == 5.0


@pytest.mark.parametrize(
    "ledger, events, updated_at, message",
    (
        (
            {"authorization": {"budget_usd": float("nan")}, "calls": []},
            (),
            "after",
            "budget_usd must be finite and nonnegative",
        ),
        (
            {"authorization": {"budget_usd": float("inf")}, "calls": []},
            (),
            "after",
            "budget_usd must be finite and nonnegative",
        ),
        (
            {"authorization": {"budget_usd": 5.0}, "calls": []},
            (
                {"event_type": "reservation", "call_id": "cell-01"},
                {
                    "event_type": "completion",
                    "call_id": "cell-01",
                    "estimated_cost_usd": -0.01,
                },
            ),
            "after",
            "estimated_cost_usd must be finite and nonnegative",
        ),
        (
            {"authorization": {"budget_usd": 5.0}, "calls": []},
            (
                {"event_type": "reservation", "call_id": "cell-01"},
                {
                    "event_type": "completion",
                    "call_id": "cell-01",
                    "estimated_cost_usd": float("nan"),
                },
            ),
            "after",
            "estimated_cost_usd must be finite and nonnegative",
        ),
        (
            {"authorization": {"budget_usd": 5.0}, "calls": []},
            (
                {"event_type": "reservation", "call_id": "cell-01"},
                {
                    "event_type": "completion",
                    "call_id": "cell-01",
                    "estimated_cost_usd": float("inf"),
                },
            ),
            "after",
            "estimated_cost_usd must be finite and nonnegative",
        ),
        (
            {"authorization": {"budget_usd": 5.0}, "calls": []},
            (
                {"event_type": "reservation", "call_id": "cell-01"},
                {
                    "event_type": "completion",
                    "call_id": "cell-01",
                    "estimated_cost_usd": "1.0",
                },
            ),
            "after",
            "estimated_cost_usd must be finite and nonnegative",
        ),
        (
            {"authorization": {"budget_usd": 5.0}, "calls": []},
            (
                {"event_type": "reservation", "call_id": "cell-01"},
                {
                    "event_type": "completion",
                    "call_id": "cell-01",
                    "estimated_cost_usd": True,
                },
            ),
            "after",
            "estimated_cost_usd must be finite and nonnegative",
        ),
        (
            {"authorization": {"budget_usd": 5.0}, "calls": []},
            (),
            7,
            "updated_at must be a nonempty string",
        ),
        (
            {"authorization": {"budget_usd": 5.0}, "calls": []},
            (),
            " ",
            "updated_at must be a nonempty string",
        ),
    ),
)
def test_resource_ledger_rejects_invalid_accounting_inputs_before_write(
    tmp_path: Path,
    ledger: dict[str, object],
    events: tuple[dict[str, object], ...],
    updated_at: object,
    message: str,
) -> None:
    snapshot = tmp_path / "resource-ledger.json"

    with pytest.raises(RuntimeError, match=message):
        rebuild_ledger_snapshot(
            snapshot,
            ledger,
            events,
            updated_at=updated_at,  # type: ignore[arg-type]
        )

    assert not snapshot.exists()
    assert not snapshot.with_suffix(".json.tmp").exists()


def test_resource_ledger_rejects_snapshot_calls_without_events(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "resource-ledger.json"
    write_json(
        snapshot,
        {
            "authorization": {"budget_usd": 5.0},
            "calls": [{"call_id": "unproven"}],
        },
    )

    with pytest.raises(RuntimeError, match="calls without an event log"):
        load_resource_ledger(snapshot, updated_at="after")


@pytest.mark.parametrize(
    "updates, message",
    (
        (
            {"remaining_usd": 100.0},
            "empty snapshot totals do not match its event log",
        ),
        (
            {"spent_usd": 1.0, "remaining_usd": 4.0},
            "empty snapshot totals do not match its event log",
        ),
        (
            {"spent_usd": "0.0"},
            "spent_usd must be finite and nonnegative",
        ),
        (
            {"updated_at": 7},
            "updated_at must be a nonempty string",
        ),
    ),
)
def test_resource_ledger_rejects_unproven_empty_snapshot_authority(
    tmp_path: Path,
    updates: dict[str, object],
    message: str,
) -> None:
    snapshot = tmp_path / "resource-ledger.json"
    write_json(
        snapshot,
        {
            "authorization": {"budget_usd": 5.0},
            "calls": [],
            "spent_usd": 0.0,
            "remaining_usd": 5.0,
            "updated_at": "before",
            **updates,
        },
    )

    with pytest.raises(RuntimeError, match=message):
        load_resource_ledger(snapshot, updated_at="after")


def test_resource_ledger_event_log_rejects_unterminated_tail(
    tmp_path: Path,
) -> None:
    path = tmp_path / "resource-ledger-events.jsonl"
    path.write_text('{"event_type":"reservation"}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="unterminated final line"):
        load_ledger_events(path)


@pytest.mark.parametrize(
    "events, message",
    (
        (
            (
                {"event_type": "reservation", "call_id": "cell"},
                {"event_type": "reservation", "call_id": "cell"},
            ),
            "duplicate reservation",
        ),
        (
            ({"event_type": "completion", "call_id": "cell"},),
            "completion has no reservation",
        ),
        (
            ({"event_type": "unknown", "call_id": "cell"},),
            "event_type is invalid",
        ),
    ),
)
def test_resource_ledger_rejects_invalid_event_sequences(
    tmp_path: Path,
    events: tuple[dict[str, object], ...],
    message: str,
) -> None:
    with pytest.raises(RuntimeError, match=message):
        rebuild_ledger_snapshot(
            tmp_path / "resource-ledger.json",
            {"authorization": {"budget_usd": 5.0}, "calls": []},
            events,
            updated_at="after",
        )
