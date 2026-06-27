from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "experiments" / "agent_tuning_demo" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import agent_injection_smoke as smoke  # noqa: E402
import tuning_artifacts as artifacts  # noqa: E402


def test_injection_cases_have_valid_artifacts() -> None:
    cases = smoke.injection_cases()

    assert {case.agent_id for case in cases} == {"codex_workspace", "kilo_workspace"}
    assert any(case.surface == "repo_AGENTS_md" for case in cases)
    assert any(case.surface == "kilo_rules" for case in cases)

    for case in cases:
        artifact = smoke.smoke_artifact(case)
        artifacts.validate_artifact(artifact)
        assert artifact["target_agent"] == case.agent_id


def test_behavior_cases_compare_same_agent_and_surface() -> None:
    cases = smoke.behavior_cases()

    assert len(cases) == 2
    assert {case.agent_id for case in cases} == {"codex_workspace"}
    assert {case.surface for case in cases} == {"repo_AGENTS_md"}
    assert cases[0].statement == cases[1].statement
