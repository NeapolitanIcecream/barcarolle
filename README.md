# Barcarolle

Barcarolle is a target-repository benchmark compiler for coding-agent
evaluation and tuning.

Given a repository, a cutoff, candidate task sources, an evaluation budget, and
an Agent family, Barcarolle compiles auditable benchmark releases and evidence
packages. An Agent means the complete tested configuration: model, harness,
prompt or skills, tools, retrieval, runtime policy, and budget.

The north-star research question is predictive validity: whether a
repo-specific benchmark can predict how Agents will perform on later real work
in the same repository. Barcarolle has not established that claim yet. The
current repository state preserves the proposal-stage evidence, the compiler
prototype, and the next validation path needed to keep working toward it.

## Current Source Of Truth

Start here:

- [Project state after proposal](docs/research/project-state-after-proposal.md)
- [System design](docs/architecture/system-design.md)
- [Proposal report v5](docs/research/barcarolle-proposal-report-v5.md)
- [Evidence manifest](experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md)

These documents define the active project boundary. Historical Agent License
and core-narrative materials are archived and are not active semantics.

## Active Work Areas

- `experiments/phase1_compiler/`: compiler prototype, schemas, tests, selected
  reports, and small evidence tables for task selection and validation.
- `experiments/phase0_headroom/`: historical task-supply, workspace-adapter, and
  score-table evidence used by the compiler prototype.
- `docs/research/`: final proposal materials and the canonical project state.
- `archive/2026-05-agent-license-reset/`: historical Agent License and
  core-narrative design notes retained for audit only.

## Research Asset Map

The experiment code assets are retained in the repository, but they are still
prototype assets rather than a packaged product library.

- Task supply and generation:
  `experiments/phase1_compiler/tools/phase1_task_supply_v2_generator_bakeoff.py`,
  `phase1_two_repo_certified_supply_expansion.py`,
  `phase1_third_repo_release_supply_screen.py`,
  `phase1_clean_outcome_unseen_supply_mining.py`.
- Task certification, statements, and oracle checks:
  `phase1_task_supply_v2_fresh_certification.py`,
  `phase1_source_certification_hardening.py`,
  `phase1_source_context_statement_hardening.py`,
  `phase1_reference_pass_failure_audit.py`.
- Task selection and predictive-signal analysis:
  `phase1_local_algorithm_bakeoff.py`,
  `phase1_future_holdout.py`,
  `phase1_retrospective_predictive_signal.py`,
  `phase1_three_repo_paid_validation.py`,
  `phase1_three_repo_paid_result_diagnostics.py`.
- Workspace and Agent execution support:
  `experiments/phase0_headroom/tools/workspace_acut_run.py`,
  `codex_workspace_adapter.py`,
  `kilo_workspace_adapter.py`,
  `measured_endpoint_run.py`,
  `workspace_usage_import.py`.
- Contracts and regression coverage:
  `experiments/phase1_compiler/schemas/`,
  `experiments/phase1_compiler/tests/`,
  `experiments/phase0_headroom/tools/test_*.py`.

## Useful Commands

Run the current compiler tests:

```bash
uv run --project experiments/phase1_compiler pytest -q
```

Run the retained headroom/workspace-adapter tests:

```bash
uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools -q
```

Check patch hygiene before committing:

```bash
git diff --check
```

Paid LLM or Agent calls must use `LLM_BASE_URL` plus `LLM_API_KEY`; see
`AGENTS.md` for the full rule.
