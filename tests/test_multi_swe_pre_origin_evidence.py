from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.multi_swe_research.pre_origin_evidence import (  # noqa: E402
    load_pre_origin_evidence_summary,
)


def test_pre_origin_evidence_summary_is_self_bound() -> None:
    summary = load_pre_origin_evidence_summary()

    assert summary["decision"] == {
        "current_opened_source_candidate_search": "closed",
        "empirical_nomination_replay_requires": [
            (
                "a source with native Task time and historical Result availability "
                "plus denser repository-local Origins"
            ),
            "an independent complete Agent panel or source family",
            "a strict prospective target-repository campaign",
        ],
        "pre_origin_target_future_increment_supported": False,
        "selector_nominated": False,
        "static_cross_agent_response_structure_supported": True,
        "static_raw_embedding_response_transfer_supported": False,
        "theory_design_may_resume_with": (
            "a new observable mechanism proposed independently of the "
            "opened outcomes, without replay on the opened panels"
        ),
    }
    assert summary["alg_014_prcs"]["cross_agent_response_signal"][
        "macro_repository_auc"
    ] == pytest.approx(0.9120810480543055)
    assert summary["alg_014_prcs"]["h5_future_increment"][
        "macro_repository_difference"
    ] == pytest.approx(0.000991985166277122)
    assert (
        summary["alg_013_rcp"]["history_precision_diagnostic"][
            "preserves_complete_task_response_vectors"
        ]
        is True
    )


def test_pre_origin_evidence_summary_rejects_tampering(
    tmp_path: Path,
) -> None:
    source = (
        REPOSITORY_ROOT
        / "examples"
        / "multi_swe_research"
        / "evidence"
        / "pre-origin-signal-summary.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["decision"]["selector_nominated"] = True
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest"):
        load_pre_origin_evidence_summary(path)
