# Agent Tuning Demo Phase 2 report

生成日期：2026-06-15T02:42:50+00:00

## What this demo tried to prove

This Phase 2 demo tested whether Barcarolle can turn target-repo Agent feedback into one deployable repo-local Agent artifact, then validate before/after behavior under a frozen protocol.

## Result

- Terminal state: `phase2_success_no_holdout_regression`
- Paid cells: `20`
- Estimated cost: `$1.3267749`
- Action-level preflight passed: `True`
- Optimizer/proposer: `gepa_optimize_anything_custom_local_proposer`
- Target: `kilo_gpt_5_4_mini` via `repo_AGENTS_md`
- Chosen artifact hash: `sha256:59f72edee9f4ff321c190c4f80443132b12f6c295486e315308697643d9ded3a`

Phase 1 only proved request-context visibility. Phase 2 therefore started with an action gate: the Kilo CLI had to execute a command, write a public-test marker, change file behavior, or otherwise differ at the action level because of the injected artifact. The gate passed with no paid calls: Variant B executed `python -m pytest tests/test_public_smoke.py -q` through Kilo's `bash` tool and wrote `.barcarolle_public_test_marker`; Variant A did not.

## Feedback and artifact

Selection-train export used 16 optimizer-visible rows for `kilo_gpt_5_4_mini` and excluded Selection-dev and Holdout. Labels were `verified_pass: 13`, `timeout_or_context_exhaustion: 2`, and `wrong_api_semantics: 1`.

GEPA standalone `optimize_anything` ran with a custom local proposer and no reflection LM, so proposer cost was zero and no provider-specific fallback auth was used. It produced 2 candidate `AGENTS.md` appendix artifacts. Candidate 1 was frozen after Selection-dev non-regression.

## Selection-dev matrix

| Task | Baseline | Baseline pass | Tuned | Tuned pass |
| --- | --- | --- | --- | --- |
| boltons__supply_expansion_20260526__001 | verified_fail | False | verified_fail | False |
| boltons__supply_expansion_20260526__004 | verified_fail | False | verified_fail | False |
| boltons__supply_expansion_20260526__006 | verified_pass | True | verified_pass | True |
| boltons__supply_expansion_20260526__107 | verified_fail | False | verified_fail | False |

Selection-dev baseline and tuned both passed `1/4`; paired net wins were `0`, invalid/unscoreable cells were `0` for both conditions. This opened the Holdout gate as a non-regression, not as an improvement signal.

## Holdout matrix

| Task | Baseline | Baseline pass | Tuned | Tuned pass |
| --- | --- | --- | --- | --- |
| boltons__clean_ext__017 | verified_pass | True | verified_pass | True |
| boltons__hist__019 | verified_fail | False | verified_fail | False |
| boltons__hist__020 | verified_pass | True | verified_pass | True |
| boltons__hist__022 | verified_pass | True | verified_pass | True |
| boltons__hist__023 | verified_pass | True | verified_pass | True |
| boltons__hist__024 | verified_pass | True | verified_pass | True |

Holdout baseline and tuned both passed `5/6`; paired net wins were `0`, invalid/unscoreable cells were `0` for both conditions. Tuned estimated cost was lower on this small Holdout slice (`$0.2917602` versus `$0.3224709`) but median latency was slightly higher (`34.701s` versus `32.081s`).

## Case studies

- Improved task: none observed on Selection-dev or Holdout.
- Unchanged task: `boltons__hist__020` passed in both Holdout baseline and tuned runs.
- Remaining failure: `boltons__hist__019` failed in both Holdout baseline and tuned runs.

## Validation and hygiene

- `uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q`: `11 passed`.
- `uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py -q`: `30 passed`.
- `git diff --check`: pass.
- `git ls-files experiments/agent_tuning_demo | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|secret|prompt|completion)' || true`: no hits.

## Supported claims

- A repo-local Kilo AGENTS.md appendix can change real Kilo CLI action behavior in the controlled preflight.
- Barcarolle can export Selection-train feedback without Holdout task IDs or raw transcripts.
- Barcarolle can generate and freeze a deployable repo-local text artifact before Holdout validation.

## Unsupported claims

- full predictive validity
- cross-repo generalization
- model fine-tuning
- full opaque Codex/Kilo Agent tuning
- GEPA/Phoenix superiority
- statistical significance
- production-ready Agent tuning system

## Recommended next work

- Repeat with a larger preregistered Selection-dev/Holdout sample only after cost and variance are acceptable.
- Try one alternate surface, such as Kilo project rules, only in a separate single-surface run.
- Keep predictive-validity and cross-repo claims separate from this artifact-tuning demo.
