from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.pylint_swe_bench_verified import check  # noqa: E402


INSTANCE_ID = "pylint-dev__pylint-4551"
PATCH_DIGEST = "a" * 64


def test_summarize_report_exposes_only_sanitized_counts_and_digests() -> None:
    report = {
        INSTANCE_ID: {
            "resolved": True,
            "tests_status": {
                check.FAIL_TO_PASS: {
                    "success": ["hidden::fixed_b", "hidden::fixed_a"],
                    "failure": ["hidden::still_failing"],
                },
                check.PASS_TO_PASS: {
                    "success": ["hidden::regression_safe"],
                    "failure": [],
                },
            },
            "hidden_oracle": "must-not-be-emitted",
        }
    }

    summary = check.summarize_report(report, INSTANCE_ID, PATCH_DIGEST)

    expected_digest_payload = {
        check.FAIL_TO_PASS: {
            "success": ("hidden::fixed_a", "hidden::fixed_b"),
            "failure": ("hidden::still_failing",),
        },
        check.PASS_TO_PASS: {
            "success": ("hidden::regression_safe",),
            "failure": (),
        },
    }
    expected_digest = hashlib.sha256(
        json.dumps(
            expected_digest_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    assert summary == {
        "instance_id": INSTANCE_ID,
        "patch_digest": PATCH_DIGEST,
        "resolved": True,
        "state": "scored",
        "status_digest": expected_digest,
        "tests": {
            check.FAIL_TO_PASS: {"success_count": 2, "failure_count": 1},
            check.PASS_TO_PASS: {"success_count": 1, "failure_count": 0},
        },
    }
    serialized = json.dumps(summary, sort_keys=True)
    for secret in (
        "hidden::fixed_a",
        "hidden::fixed_b",
        "hidden::still_failing",
        "hidden::regression_safe",
        "must-not-be-emitted",
    ):
        assert secret not in serialized


def test_summarize_report_digest_is_independent_of_test_order() -> None:
    statuses = {
        check.FAIL_TO_PASS: {
            "success": ["hidden::first", "hidden::second"],
            "failure": ["hidden::third", "hidden::fourth"],
        },
        check.PASS_TO_PASS: {
            "success": ["hidden::fifth", "hidden::sixth"],
            "failure": [],
        },
    }
    reversed_statuses = {
        group_name: {
            "success": list(reversed(group["success"])),
            "failure": list(reversed(group["failure"])),
        }
        for group_name, group in statuses.items()
    }

    first = check.summarize_report(
        {INSTANCE_ID: {"resolved": False, "tests_status": statuses}},
        INSTANCE_ID,
        PATCH_DIGEST,
    )
    second = check.summarize_report(
        {INSTANCE_ID: {"resolved": False, "tests_status": reversed_statuses}},
        INSTANCE_ID,
        PATCH_DIGEST,
    )

    assert first == second


@pytest.mark.parametrize(
    "report",
    (
        {},
        {INSTANCE_ID: {}},
        {
            INSTANCE_ID: {
                "tests_status": {
                    check.FAIL_TO_PASS: {"success": [], "failure": []}
                }
            }
        },
    ),
)
def test_summarize_report_rejects_incomplete_reports(report: object) -> None:
    with pytest.raises(RuntimeError, match="SWE-bench report is missing"):
        check.summarize_report(report, INSTANCE_ID, PATCH_DIGEST)  # type: ignore[arg-type]


def test_main_redacts_infrastructure_exception_details(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    secret = "hidden::oracle_name"
    monkeypatch.setattr(
        check,
        "_parse_args",
        lambda: SimpleNamespace(
            bundle=None,
            image_ref="unused",
            raw_output_dir=None,
            timeout_seconds=1,
        ),
    )

    def fail_check(**_: object) -> dict[str, object]:
        raise RuntimeError(f"oracle failed at {secret}")

    monkeypatch.setattr(check, "run_check", fail_check)

    assert check.main() == 2
    output = capsys.readouterr().out
    assert json.loads(output) == {
        "state": "infrastructure_error",
        "error": "RuntimeError",
    }
    assert secret not in output
