from __future__ import annotations

from pathlib import Path
import json

import pytest

import workspace_usage_import as usage


def write_pricing(path: Path) -> Path:
    config = path / "model_pricing.yaml"
    config.write_text(
        "\n".join(
            [
                "schema_version: barcarolle.model_pricing.v1",
                "default_currency: USD",
                "prices:",
                '  - endpoint_host_hash: "host123"',
                "    model: gpt-5.4-mini",
                "    pricing_source: test",
                "    input_rate_per_1m_usd: 3.0",
                "    cached_input_rate_per_1m_usd: 0.3",
                "    output_rate_per_1m_usd: 15.0",
                "    reasoning_output_policy: included_in_output_tokens",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config


def test_price_lookup_by_endpoint_hash_and_model(tmp_path: Path) -> None:
    prices = usage.load_model_prices(write_pricing(tmp_path))

    price = usage.lookup_price(prices, "host123", "gpt-5.4-mini")

    assert price is not None
    assert price.pricing_source == "test"
    assert price.output_rate_per_1m_usd == 15.0


def test_missing_model_price_fails_closed(tmp_path: Path) -> None:
    prices = usage.load_model_prices(write_pricing(tmp_path))

    with pytest.raises(KeyError, match="missing price"):
        usage.lookup_price(prices, "host123", "unknown-model")


def test_missing_model_price_can_be_explicitly_allowed(tmp_path: Path) -> None:
    prices = usage.load_model_prices(write_pricing(tmp_path))

    assert usage.lookup_price(prices, "host123", "unknown-model", allow_missing_price_estimate=True) is None


def test_token_cost_uses_uncached_cached_and_output_rates(tmp_path: Path) -> None:
    price = usage.lookup_price(usage.load_model_prices(write_pricing(tmp_path)), "host123", "gpt-5.4-mini")

    cost = usage.estimate_token_cost_usd(
        price,
        input_tokens=1_000_000,
        cached_input_tokens=100_000,
        output_tokens=10_000,
        reasoning_output_tokens=500,
    )

    assert cost == 2.88


def test_parse_codex_turn_completed_fixture() -> None:
    aggregate = usage.parse_codex_usage(
        "\n".join(
            [
                "not json",
                json.dumps({"type": "thread.started"}),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 1000,
                            "cached_input_tokens": 300,
                            "output_tokens": 90,
                            "reasoning_output_tokens": 30,
                        },
                    }
                ),
                "",
            ]
        )
    )

    assert aggregate.usage_observed is True
    assert aggregate.usage_source == "codex_turn_completed"
    assert aggregate.input_tokens == 1000
    assert aggregate.cached_input_tokens == 300
    assert aggregate.uncached_input_tokens == 700
    assert aggregate.output_tokens == 90
    assert aggregate.reasoning_output_tokens == 30


def test_parse_kilo_step_finish_fixture() -> None:
    aggregate = usage.parse_kilo_usage(
        json.dumps(
            {
                "type": "step_finish",
                "part": {
                    "tokens": {
                        "input": 100,
                        "output": 20,
                        "reasoning": 5,
                        "cache": {"read": 10, "write": 3},
                    },
                    "cost": 0,
                },
            }
        )
    )

    assert aggregate.usage_observed is True
    assert aggregate.usage_source == "kilo_step_finish"
    assert aggregate.input_tokens == 113
    assert aggregate.cached_input_tokens == 10
    assert aggregate.uncached_input_tokens == 103
    assert aggregate.visible_output_tokens == 20
    assert aggregate.output_tokens == 25
    assert aggregate.reasoning_output_tokens == 5
    assert aggregate.cache_write_tokens == 3
    assert aggregate.reported_cost_usd == 0
    assert aggregate.reported_cost_trusted is False


def test_parse_kilo_sums_multiple_steps() -> None:
    aggregate = usage.parse_kilo_usage(
        "\n".join(
            [
                json.dumps({"type": "step_finish", "part": {"tokens": {"input": 10, "output": 2, "reasoning": 1, "cache": {"read": 5, "write": 0}}, "cost": 0}}),
                json.dumps({"type": "step_finish", "part": {"tokens": {"input": 20, "output": 3, "reasoning": 4, "cache": {"read": 6, "write": 0}}, "cost": 0.25}}),
            ]
        )
    )

    assert aggregate.usage_event_count == 2
    assert aggregate.input_tokens == 41
    assert aggregate.cached_input_tokens == 11
    assert aggregate.uncached_input_tokens == 30
    assert aggregate.output_tokens == 10
    assert aggregate.reasoning_output_tokens == 5
    assert aggregate.reported_cost_usd == 0.25
    assert aggregate.reported_cost_trusted is True


def test_usage_parsers_ignore_non_json_and_unrelated_rows() -> None:
    codex = usage.parse_codex_usage('hello\n{"type":"turn.started"}\n')
    kilo = usage.parse_kilo_usage('hello\n{"type":"step_start"}\n')

    assert codex.usage_observed is False
    assert codex.usage_source == "missing"
    assert kilo.usage_observed is False
    assert kilo.usage_source == "missing"


def test_usage_ledger_keeps_raw_stdout_content_out(tmp_path: Path) -> None:
    exp = tmp_path
    raw_dir = exp / "results" / "raw" / "example" / "run1"
    raw_dir.mkdir(parents=True)
    (raw_dir / "acut_stdout.txt").write_text(
        "\n".join(
            [
                "RAW_COMPLETION_SHOULD_NOT_APPEAR",
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 5, "reasoning_output_tokens": 1}}),
            ]
        ),
        encoding="utf-8",
    )
    submissions = [
        {
            "run_id": "run1",
            "result_prefix": "sample",
            "adapter_id": "codex_workspace",
            "harness_name": "codex",
            "model_or_agent_name": "gpt-5.4-mini",
            "task_id": "task1",
            "split": "B_real",
            "raw_artifacts": {"stdout": "results/raw/example/run1/acut_stdout.txt"},
        }
    ]
    usage.write_jsonl(exp / "results" / "sample_submissions.jsonl", submissions)
    rows = usage.import_prefix_usage(exp, "sample", usage.load_model_prices(write_pricing(tmp_path)), "host123")

    serialized = json.dumps(rows, sort_keys=True)
    assert "RAW_COMPLETION_SHOULD_NOT_APPEAR" not in serialized
    assert "results/raw/example/run1/acut_stdout.txt" in serialized
    assert rows[0]["estimated_cost_usd"] > 0
