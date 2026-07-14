from pathlib import Path
import hashlib

import pytest

from barcarolle.records import CheckRecord, RuntimeConfig, canonical_digest
from barcarolle.verification import (
    CheckOutcome,
    CheckNormalizationConfig,
    WorkspaceRef,
    normalize_outcome,
    prepare_verifier,
    summarize_evidence,
    verify_diff,
)


def test_prepare_verifier_copies_hidden_material_only_inside_verifier_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    check = _check()

    prepared = prepare_verifier(
        check,
        _workspace_ref(
            path=workspace,
            check_command=("python", "-c", "print('ok')"),
            hidden_material_source=hidden,
            hidden_material_destination=Path(".barcarolle/check_bundle.txt"),
        ),
    )

    assert prepared.prepared
    assert (workspace / ".barcarolle/check_bundle.txt").read_text(encoding="utf-8") == "private oracle"


def test_prepare_verifier_rejects_hidden_material_destination_outside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    check = _check()

    with pytest.raises(ValueError, match="inside verifier workspace"):
        prepare_verifier(
            check,
            _workspace_ref(
                path=workspace,
                check_command=("python", "-c", "print('ok')"),
                hidden_material_source=hidden,
                hidden_material_destination=tmp_path / "outside.txt",
            ),
        )


def test_prepare_verifier_rejects_mismatch_before_copying_hidden_material(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    destination = workspace / ".barcarolle/check_bundle.txt"
    check = _check()

    with pytest.raises(ValueError, match="identity does not match"):
        prepare_verifier(
            check,
            _workspace_ref(
                path=workspace,
                check_command=("python", "-c", "print('ok')"),
                check_id="other-check",
                hidden_material_source=hidden,
                hidden_material_destination=Path(".barcarolle/check_bundle.txt"),
            ),
        )

    assert not destination.exists()


def test_prepare_verifier_requires_hidden_material_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(ValueError, match="hidden_material_source is required"):
        prepare_verifier(
            _check(),
            _workspace_ref(path=workspace, check_command=("python", "-c", "print('ok')")),
        )


def test_prepare_verifier_rejects_hidden_bundle_digest_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("wrong private material", encoding="utf-8")

    with pytest.raises(ValueError, match="hidden material digest"):
        prepare_verifier(
            _check(),
            _workspace_ref(
                path=workspace,
                check_command=("python", "-c", "print('ok')"),
                hidden_material_source=hidden,
                hidden_material_destination=Path(".barcarolle/check_bundle.txt"),
            ),
        )


def test_prepare_verifier_rejects_check_command_digest_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")

    with pytest.raises(ValueError, match="check command digest"):
        prepare_verifier(
            _check(),
            _workspace_ref(
                path=workspace,
                check_command=("python", "-c", "print('different check')"),
                check_manifest_digest=_check().check_manifest_digest,
                hidden_material_source=hidden,
                hidden_material_destination=Path(".barcarolle/check_bundle.txt"),
            ),
        )


def test_verify_diff_executes_prepared_check_and_normalizes_pass(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    check = _check()
    prepared = prepare_verifier(
        check,
        _workspace_ref(
            path=workspace,
            check_command=("python", "-c", "print('ok')"),
            hidden_material_source=hidden,
            hidden_material_destination=Path(".barcarolle/check_bundle.txt"),
        ),
    )

    outcome = verify_diff(check, prepared, _runtime(timeout_seconds=5))

    assert outcome.outcome == "pass"
    assert outcome.failure_label is None
    assert outcome.evidence_excerpt == "[verifier output omitted]"


def test_verify_diff_returns_invalid_for_check_workspace_mismatch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    prepared = _workspace_ref(
        path=workspace,
        check_command=("python", "-c", "print('wrong oracle passed')"),
        check_id="other-check",
        prepared=True,
    )

    outcome = verify_diff(_check(), prepared, _runtime(timeout_seconds=5))

    assert outcome.outcome == "invalid"
    assert outcome.failure_label == "check_workspace_mismatch"


def test_verify_diff_rechecks_command_digest_before_execution(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    marker = workspace / "should-not-exist.txt"
    check = _check()
    prepared = _workspace_ref(
        path=workspace,
        check_command=("python", "-c", "from pathlib import Path; Path('should-not-exist.txt').write_text('ran')"),
        check_manifest_digest=check.check_manifest_digest,
        hidden_material_source=None,
        hidden_material_destination=None,
        prepared=True,
    )

    outcome = verify_diff(check, prepared, _runtime(timeout_seconds=5))

    assert outcome.outcome == "invalid"
    assert outcome.failure_label == "check_command_mismatch"
    assert not marker.exists()


def test_verify_diff_normalizes_missing_check_executable(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("private oracle", encoding="utf-8")
    check = _check(command=("missing-check-executable",))
    prepared = prepare_verifier(
        check,
        _workspace_ref(
            path=workspace,
            check_command=("missing-check-executable",),
            hidden_material_source=hidden,
            hidden_material_destination=Path(".barcarolle/check_bundle.txt"),
        ),
    )

    outcome = verify_diff(check, prepared, _runtime(timeout_seconds=5))

    assert outcome.outcome == "invalid"
    assert outcome.failure_label == "check_launch_error"
    assert outcome.evidence_excerpt == "[verifier output omitted]"


def test_verify_diff_requires_prepared_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(ValueError, match="must be prepared"):
        verify_diff(_check(), _workspace_ref(path=workspace, check_command=("python", "-c", "print('ok')")), _runtime())


def test_normalize_outcome_maps_fail_invalid_and_timeout() -> None:
    config = CheckNormalizationConfig(invalid_exit_codes=(2,))

    failed = normalize_outcome({"exit_code": 1, "stdout": "", "stderr": "bad"}, config)
    invalid = normalize_outcome({"exit_code": 2, "stdout": "", "stderr": "bad"}, config)
    timeout = normalize_outcome({"timed_out": True, "stdout": "", "stderr": ""}, config)

    assert failed.outcome == "fail"
    assert failed.failure_label == "check_failed"
    assert invalid.outcome == "invalid"
    assert invalid.failure_label == "check_invalid"
    assert timeout.outcome == "invalid"
    assert timeout.failure_label == "timeout"


def test_summarize_evidence_omits_raw_verifier_text_by_default() -> None:
    outcome = normalize_outcome(
        {"exit_code": 1, "stdout": "AssertionError: assert 3 == 4", "stderr": ""},
        CheckNormalizationConfig(),
    )

    summary = summarize_evidence(outcome)

    assert summary.evidence_excerpt == "[verifier output omitted]"
    assert "3 == 4" not in summary.evidence_excerpt


def test_summarize_evidence_redacts_hidden_oracle_text_when_text_is_explicitly_allowed() -> None:
    outcome = normalize_outcome(
        {"exit_code": 1, "stdout": "the hidden oracle expected output is 42", "stderr": ""},
        CheckNormalizationConfig(allow_verifier_text=True),
    )

    summary = summarize_evidence(outcome)

    assert summary.evidence_excerpt == "[redacted unsafe verifier evidence]"
    assert "42" not in summary.evidence_excerpt


def test_summarize_evidence_omits_prepopulated_raw_excerpt() -> None:
    summary = summarize_evidence(
        CheckOutcome(
            outcome="fail",
            failure_label="check_failed",
            exit_code=1,
            timed_out=False,
            duration_seconds=0.1,
            evidence_excerpt="AssertionError: assert 3 == 4",
        )
    )

    assert summary.evidence_excerpt == "[verifier output omitted]"
    assert "3 == 4" not in summary.evidence_excerpt


def test_summarize_evidence_omits_explicit_text_normalization_path_when_not_known_safe() -> None:
    outcome = normalize_outcome(
        {"exit_code": 1, "stdout": "AssertionError: assert 3 == 4", "stderr": ""},
        CheckNormalizationConfig(allow_verifier_text=True),
    )

    summary = summarize_evidence(outcome)

    assert outcome.evidence_excerpt == "AssertionError: assert 3 == 4\n"
    assert summary.evidence_excerpt == "[verifier output omitted]"


def _check(command: tuple[str, ...] = ("python", "-c", "print('ok')")) -> CheckRecord:
    return CheckRecord(
        check_id="check",
        task_id="task",
        check_type="pytest",
        check_manifest_digest=_command_digest(command),
        hidden_check_bundle_digest=_hidden_digest(),
        resource_limits={"timeout_seconds": 5},
        oracle_source="private_tests",
        check_material_available_at="2026-01-01T00:00:00Z",
    )


def _runtime(timeout_seconds: int = 5) -> RuntimeConfig:
    return RuntimeConfig(
        runtime_config_id="runtime",
        budget_digest="budget",
        retry_policy_digest="retry",
        stochastic_settings_digest="stochastic",
        timeout_seconds=timeout_seconds,
        hardware_profile_digest=None,
    )


def _workspace_ref(
    path: Path,
    check_command: tuple[str, ...],
    *,
    check_id: str = "check",
    check_manifest_digest: str | None = None,
    hidden_check_bundle_digest: str | None = None,
    hidden_material_source: Path | None = None,
    hidden_material_destination: Path | None = None,
    prepared: bool = False,
) -> WorkspaceRef:
    return WorkspaceRef(
        path=path,
        check_command=check_command,
        check_id=check_id,
        check_manifest_digest=check_manifest_digest or _command_digest(check_command),
        hidden_check_bundle_digest=hidden_check_bundle_digest or _hidden_digest(),
        hidden_material_source=hidden_material_source,
        hidden_material_destination=hidden_material_destination,
        prepared=prepared,
    )


def _command_digest(command: tuple[str, ...]) -> str:
    return canonical_digest({"check_command": command})


def _hidden_digest() -> str:
    return hashlib.sha256(b"private oracle").hexdigest()
