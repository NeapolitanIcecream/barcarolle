# GitHub Access Guide For External Review

If the reviewer can browse GitHub, use this repository reference:

```text
Repository: https://github.com/NeapolitanIcecream/barcarolle
Branch: codex/restart-benchmark-compiler
Commit: da8d9977f823952932efb67ecab5c068f1bc5531
```

Preferred stable URL:

```text
https://github.com/NeapolitanIcecream/barcarolle/tree/da8d9977f823952932efb67ecab5c068f1bc5531
```

Branch URL:

```text
https://github.com/NeapolitanIcecream/barcarolle/tree/codex/restart-benchmark-compiler
```

Use the commit URL when possible, because it is stable. Use the branch URL only
if the commit is unavailable or if the reviewer needs the latest pushed branch
state.

## Useful GitHub Paths

Core process and boundaries:

```text
AGENTS.md
PROCESS.md
docs/architecture/system-design.md
```

Current candidate policy and protocol:

```text
docs/experiments/phase-1-candidate-policy-validation-protocol-pre-adversarial-review-runbook.md
experiments/phase1_compiler/tools/phase1_candidate_policy_validation_protocol.py
experiments/phase1_compiler/tests/test_phase1_candidate_policy_validation_protocol.py
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_policy_spec.json
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_selection_manifest.json
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_validation_protocol.json
experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_success_criteria.json
experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md
```

Retrospective signal evidence:

```text
docs/experiments/phase-1-retrospective-predictive-signal-analysis-runbook.md
experiments/phase1_compiler/tools/phase1_retrospective_predictive_signal.py
experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md
```

Relevant earlier evidence:

```text
experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md
experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md
experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md
experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md
experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_adapter_fairness_audit.md
```

Do not ask the reviewer to inspect raw ACUT transcripts, raw prompts, raw
completions, raw diffs, raw tests, workspaces, verifier workspaces, target repo
clones, caches, or secrets. Those are intentionally excluded from committed
artifacts and from this bundle.
