from __future__ import annotations

from pathlib import Path

import measured_endpoint_run as measured


def test_parse_usage_reads_cached_and_reasoning_tokens() -> None:
    payload = {
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "prompt_tokens_details": {"cached_tokens": 30},
            "completion_tokens_details": {"reasoning_tokens": 5},
        }
    }

    usage = measured.parse_usage(payload)

    assert usage["input_tokens"] == 100
    assert usage["cached_input_tokens"] == 30
    assert usage["output_tokens"] == 20
    assert usage["reasoning_output_tokens"] == 5
    assert usage["usage_observed"] is True


def test_estimate_cost_accounts_for_cached_input_tokens() -> None:
    cost = measured.estimate_cost_usd(
        100,
        40,
        10,
        input_rate=3.0,
        cached_rate=0.3,
        output_rate=15.0,
    )

    assert cost == 0.000342


def test_extract_unified_diff_from_fenced_response() -> None:
    text = "Here is the patch:\n```diff\ndiff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-a\n+b\n```"

    diff = measured.extract_unified_diff(text)

    assert diff.startswith("diff --git")
    assert "+b" in diff


def test_summarize_cost_reports_usage_observed_rate() -> None:
    rows = [
        {"usage_observed": True, "input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 5, "reasoning_output_tokens": 0, "estimated_cost_usd": 0.1, "latency_seconds": 1.0},
        {"usage_observed": False, "input_tokens": None, "cached_input_tokens": None, "output_tokens": None, "reasoning_output_tokens": None, "estimated_cost_usd": None, "latency_seconds": 3.0},
    ]

    summary = measured.summarize_cost(rows)

    assert summary["call_count"] == 2
    assert summary["usage_observed_rate"] == 0.5
    assert summary["input_tokens"] == 10
    assert summary["estimated_cost_usd"] == 0.1


def test_discover_models_skips_non_json_model_path(monkeypatch) -> None:
    endpoint = measured.Endpoint("https://example.invalid", "secret")
    calls = []

    def fake_request_json(endpoint, path, payload=None, timeout=120):
        calls.append(path)
        if path == "/models":
            return 200, {"error": "non_json_response"}, 0.1
        return 200, {"data": [{"id": "gpt-5.4-mini"}]}, 0.2

    monkeypatch.setattr(measured, "request_json", fake_request_json)

    path, payload = measured.discover_models(endpoint)

    assert path == "/v1/models"
    assert payload["data"][0]["id"] == "gpt-5.4-mini"
    assert calls == ["/models", "/v1/models"]


def test_apply_submission_patch_falls_back_to_patch_tool(monkeypatch, tmp_path: Path) -> None:
    calls = []
    patch = tmp_path / "bad-offset.patch"
    patch.write_text("diff --git a/a.py b/a.py\n", encoding="utf-8")

    def fake_run_command(command, cwd, timeout=120):
        calls.append(command)
        if command[:3] == ["git", "apply", "--check"]:
            return measured.CommandResult(command, str(cwd), 1, "", "strict apply failed", 0.1)
        if command[0] == "patch":
            return measured.CommandResult(command, str(cwd), 0, "", "", 0.1)
        raise AssertionError(command)

    monkeypatch.setattr(measured, "run_command", fake_run_command)

    applied, method, error = measured.apply_submission_patch(tmp_path, patch)

    assert applied is True
    assert method == "patch_p1_fuzzy"
    assert error == ""
    assert calls[0][:3] == ["git", "apply", "--check"]
    assert calls[1][0] == "patch"
