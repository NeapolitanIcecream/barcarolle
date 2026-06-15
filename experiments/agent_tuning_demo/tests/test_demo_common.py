from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.demo_common import costs
from experiments.demo_common import files
from experiments.demo_common import workspace_inputs


def test_estimate_cost_uses_observed_cached_tokens() -> None:
    config = {
        "pricing_per_1m_tokens_usd": {
            "demo-model": {
                "input": 2.0,
                "cached_input": 0.5,
                "output": 8.0,
            }
        },
        "run_policy": {"conservative_cell_estimate_usd": 0.25},
    }

    observed, cost, tokens = costs.estimate_cost(
        {"input_tokens": 1000, "cached_input_tokens": 400, "output_tokens": 250},
        "demo-model",
        config,
    )

    assert observed is True
    assert cost == 0.0034
    assert tokens == {"input_tokens": 1000, "cached_input_tokens": 400, "output_tokens": 250}


def test_extract_usage_from_kilo_step_finish_events() -> None:
    text = "\n".join(
        [
            "noise",
            json.dumps({"type": "step_finish", "part": {"tokens": {"input": 10, "output": 3, "reasoning": 2, "cache": {"read": 4}}}}),
            json.dumps({"type": "step_finish", "part": {"tokens": {"input": 7, "output": 5, "cache": {"read": 1}}}}),
        ]
    )

    assert costs.extract_usage_from_text(text) == {
        "input_tokens": 22,
        "cached_input_tokens": 5,
        "output_tokens": 10,
        "usage_source_schema": "kilo_step_finish_tokens",
    }


def test_failure_category_matches_workspace_terminal_statuses() -> None:
    assert costs.failure_category({"status": "verified_pass"}, {}) == "verified pass"
    assert costs.failure_category({"status": "verified_fail"}, {}) == "hidden verifier failure"
    assert costs.failure_category({"status": "policy_violation", "harness_error": "edited_tests"}, {}) == "edited tests when prohibited"
    assert costs.failure_category({}, {"status": "invalid_output"}) == "no meaningful change"


def test_markdown_table_escapes_cell_pipes() -> None:
    assert files.markdown_table([{"name": "a|b"}], [("Name", "name")]) == [
        "| Name |",
        "| --- |",
        "| a\\|b |",
    ]


def test_adapter_config_for_adds_kilo_completion_mode() -> None:
    config = {"run_policy": {"adapter_cleanup_grace_seconds": 30}}
    candidate = {
        "agent_id": "kilo_demo",
        "harness": "kilo",
        "model": "gpt-demo",
        "adapter_script": "experiments/phase0_headroom/tools/kilo_workspace_adapter.py",
        "timeout_seconds": 100,
        "completion_mode": "strict-final",
    }

    adapter = workspace_inputs.adapter_config_for(config, candidate, command_template_source="unit")

    assert adapter.adapter_id == "kilo_demo"
    assert adapter.command_template_source == "unit"
    assert adapter.timeout_seconds == 130
    assert "--completion-mode strict-final" in adapter.command_template
