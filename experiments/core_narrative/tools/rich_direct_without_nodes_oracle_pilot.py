#!/usr/bin/env python3
"""Run one Rich W* Oracle pilot for direct tests without extractable nodes."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from rich_direct_smoke_pilot import (
    DEFAULT_REPO,
    admission_decision,
    patch_for_candidate,
    problem_statement,
    repo_relative,
    run_noop_smoke,
    run_reference_smoke,
    sha256_text,
    source_anchor_digest,
)
from rich_source_oracle_pilot import hidden_verifier_digest, materialize_task_pack
from rich_task_admission_readiness import changed_file_set_digest, discover_candidates


TOOL = "rich_direct_without_nodes_oracle_pilot"
SCHEMA_VERSION = "core-narrative.rich-direct-without-nodes-oracle-pilot.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/rich_direct_without_nodes_oracle_pilot_20260514"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_direct_without_nodes_oracle_pilot_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_rich_direct_without_nodes_oracle_pilot.md"


IMPORT_SIDE_EFFECT_TEST = '''\
from __future__ import annotations

import importlib
import sys


def assert_import_keeps_modules_lazy(module_name: str, forbidden_modules: set[str]) -> None:
    for loaded_module in [module_name, *forbidden_modules]:
        sys.modules.pop(loaded_module, None)

    importlib.import_module(module_name)

    loaded_forbidden = forbidden_modules.intersection(sys.modules)
    assert loaded_forbidden == set(), f"{module_name} eagerly loaded {sorted(loaded_forbidden)}"


def test_protocol_repr_and_syntax_imports_avoid_inspect_and_console_side_effects() -> None:
    """Import-only paths should not eagerly import inspect or Console."""
    assert_import_keeps_modules_lazy("rich.protocol", {"inspect"})
    assert_import_keeps_modules_lazy("rich.repr", {"inspect"})
    assert_import_keeps_modules_lazy("rich.syntax", {"inspect", "rich.console"})


if __name__ == "__main__":
    test_protocol_repr_and_syntax_imports_avoid_inspect_and_console_side_effects()
'''


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local Rich checkout.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Ignored private artifact root.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public redacted JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Public markdown report.")
    parser.add_argument("--candidate-index", type=int, default=0, help="Zero-based direct-without-node candidate index.")
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--venv-python", default="python3")
    parser.add_argument("--force", action="store_true", default=True)
    parser.add_argument("--no-force", dest="force", action="store_false")
    return parser.parse_args(list(argv) if argv is not None else None)


def direct_without_nodes_candidates(repo_path: Path) -> list[Mapping[str, Any]]:
    return [
        candidate
        for candidate in discover_candidates(repo_path)
        if candidate.get("window") == "W_star" and candidate.get("oracle_requirement") == "direct_tests_without_extractable_nodes"
    ]


def select_candidate(repo_path: Path, index: int) -> Mapping[str, Any]:
    candidates = direct_without_nodes_candidates(repo_path)
    if not candidates:
        raise ToolError("no Rich W* direct-without-node Oracle candidates found")
    if index < 0 or index >= len(candidates):
        raise ToolError("candidate index out of range", index=index, candidate_count=len(candidates))
    return candidates[index]


def hidden_verifier_for_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    subject = str(candidate.get("subject", "")).strip().lower()
    source_files = set(str(path) for path in candidate.get("source_files", []))
    required = {"rich/protocol.py", "rich/repr.py", "rich/syntax.py"}
    if subject == "perf: eliminate inspect imports from protocol.py, repr.py, and syntax.py" and required.issubset(source_files):
        return {
            "hidden_files": [
                {
                    "path": "tests/check_import_side_effects.py",
                    "content": IMPORT_SIDE_EFFECT_TEST,
                }
            ],
            "command": ".venv/bin/python tests/check_import_side_effects.py",
            "test_node_count": 1,
            "oracle_template": "import_side_effects_lazy_inspect_console",
        }
    raise ToolError(
        "no direct-without-node Oracle template is available for selected candidate",
        subject_digest=sha256_text(str(candidate.get("subject", ""))),
        source_file_set_digest=changed_file_set_digest([str(path) for path in candidate.get("source_files", [])]),
    )


def public_result(
    *,
    candidate: Mapping[str, Any],
    verifier: Mapping[str, Any],
    reference_patch_digest: str,
    reference_patch_bytes: int,
    noop: Mapping[str, Any],
    reference: Mapping[str, Any],
    private_root: str,
) -> dict[str, Any]:
    decision = admission_decision(str(noop.get("status")), str(reference.get("status")))
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "repo_slug": "rich",
        "split": "W_star",
        "pilot_scope": "one_direct_tests_without_extractable_nodes_candidate",
        "oracle_template": verifier.get("oracle_template"),
        "source_anchor_digest": source_anchor_digest(str(candidate["commit"])),
        "base_anchor_digest": source_anchor_digest(str(candidate["base_commit"])),
        "subject_digest": sha256_text(str(candidate["subject"])),
        "family": candidate["family"],
        "surface": candidate["surface"],
        "source_file_count": candidate["source_file_count"],
        "test_file_count": candidate["test_file_count"],
        "test_node_count": verifier.get("test_node_count"),
        "changed_file_set_digest": candidate.get("changed_file_set_digest")
        or changed_file_set_digest(list(candidate.get("source_files", [])) + list(candidate.get("test_files", []))),
        "statement_digest": sha256_text(problem_statement(str(candidate["subject"]))),
        "hidden_verifier_digest": hidden_verifier_digest(verifier),
        "reference_patch_digest": reference_patch_digest,
        "reference_patch_bytes": reference_patch_bytes,
        "no_op_result": {
            "status": noop.get("status"),
            "verifier_exit_code": noop.get("verifier_exit_code"),
            "public_artifact_redacted": True,
        },
        "reference_result": {
            "status": reference.get("status"),
            "verifier_exit_code": reference.get("verifier_exit_code"),
            "public_artifact_redacted": True,
        },
        "admission_decision": decision,
        "primary_runs_authorized": False,
        "private_artifact_root": private_root,
        "claim_boundary": [
            "This is a one-candidate direct-without-node Oracle smoke pilot, not a frozen Rich denominator.",
            "Raw source commits, raw subjects, reference patches, and hidden verifier files are retained only in ignored private artifacts.",
            "No ACUT primary attempt or model call was made.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Rich Direct-Without-Nodes Oracle Pilot",
            "",
            f"Status: `{payload.get('status')}`",
            f"Generated at: `{payload.get('generated_at')}`",
            "",
            "## Result",
            "",
            f"- Admission decision: `{payload.get('admission_decision')}`",
            f"- No-op status: `{payload.get('no_op_result', {}).get('status') if isinstance(payload.get('no_op_result'), Mapping) else None}`",
            f"- Reference status: `{payload.get('reference_result', {}).get('status') if isinstance(payload.get('reference_result'), Mapping) else None}`",
            f"- Oracle template: `{payload.get('oracle_template')}`",
            f"- Family: `{payload.get('family')}`",
            "",
            "Primary R/W* model attempts remain unauthorized. This pilot checks one Rich W* direct-tests-without-extractable-nodes candidate only.",
            "",
        ]
    )


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_path = Path(args.repo).resolve()
    private_root = Path(args.private_root).resolve()
    if args.force:
        shutil.rmtree(private_root, ignore_errors=True)
    private_root.mkdir(parents=True, exist_ok=True)
    candidate = select_candidate(repo_path, args.candidate_index)
    verifier = hidden_verifier_for_candidate(candidate)
    task_pack = materialize_task_pack(
        candidate,
        verifier,
        private_root / "candidate_task_pack",
        task_id="rich__wstar_direct_without_nodes_oracle__001",
    )
    task_path = Path(task_pack["task_path"])
    reference_patch = patch_for_candidate(repo_path, candidate)
    reference_digest = sha256_text(reference_patch)
    noop = run_noop_smoke(
        task_path,
        repo_path,
        private_root,
        args.install_timeout_seconds,
        args.verifier_timeout_seconds,
        args.venv_python,
    )
    reference = run_reference_smoke(
        task_path,
        repo_path,
        candidate,
        private_root,
        args.install_timeout_seconds,
        args.verifier_timeout_seconds,
        args.venv_python,
    )
    payload = public_result(
        candidate=candidate,
        verifier=verifier,
        reference_patch_digest=reference_digest,
        reference_patch_bytes=len(reference_patch.encode("utf-8")),
        noop=noop,
        reference=reference,
        private_root=repo_relative(private_root),
    )
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
