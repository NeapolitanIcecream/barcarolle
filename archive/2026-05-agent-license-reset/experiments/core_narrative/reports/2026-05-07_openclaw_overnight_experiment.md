# 2026-05-07 OpenClaw Overnight Core-Narrative Experiment

status: `openclaw_runner_scoreable_data_obtained`
updated: 2026-05-07T18:40:00+08:00
repo: `/Users/chenmohan/gits/barcarolle`
branch: `codex/core-narrative-experiment`
start_head: `84409b6` (`Record env-restored single paid probe`)

## Operator decision

The old Codex work/review-loop runner is no longer treated as an experiment constraint. I kept the experimental core intact:

- task manifests and ACUT manifests;
- public task statement + declared ACUT policy/context;
- prepared base-tree workspace;
- git patch artifact;
- hidden verifier and normalized result schema;
- cost/usage ledger discipline.

I replaced the brittle launch/output plumbing with an OpenClaw-native direct runner:

- tool: `experiments/core_narrative/tools/openclaw_direct_runner.py`
- runner id: `openclaw-direct-search-replace-v1`
- output contract: JSON search/replace bundle, then a normal git diff artifact
- cost reconciliation: `experiments/core_narrative/tools/reconcile_cost_accounting.py`

The pre-existing dirty file `docs/experiments/core-narrative-experiment-plan.md` was not staged or overwritten.

## Short diagnosis

Previous paid probe `pilot_011` proved transport was no longer the primary blocker: the model responded in 67.3s, but the direct command had no verifier-ready patch because the response could not be parsed under the strict structured-files contract.

Root cause for the repeated dead-end was not a research issue; it was runner/output-contract engineering:

1. the one-shot direct prompt provided too little source context for a model to make a reliable patch;
2. full-file JSON output is expensive/brittle for repository edits;
3. the old runner path kept preserving Codex-loop assumptions instead of producing scoreable artifacts.

## New runner behavior

`openclaw_direct_runner.py` builds a prompt from:

- public task statement;
- sanitized ACUT policy summary;
- selected workspace source files (`click/core.py`, `tests/test_options.py` here);
- task-agnostic Click specialist context only when the ACUT allows it.

The model must return:

```json
{"edits":[{"path":"relative/file.py","old":"exact existing text","new":"replacement text"}]}
```

The runner validates paths and exact old-string uniqueness, applies edits, writes `submission.patch`, records prompt/config/raw-response artifacts, and appends usage/cost records. Verification then runs through the existing `apply_and_verify.py` normalized result path.

## No-model and verifier checks

- `noop_verify_check__click__rbench__001__20260507`: no-op verifier check failed as expected, proving the hidden verifier catches the baseline bug.
- `openclaw_direct_mock__cheap-generic-swe__click__rbench__001__attempt1`: no-model search/replace patch passed the hidden verifier, proving the new runner + patch + verifier path can produce a scoreable/passing artifact without old Codex plumbing.

## Live OpenClaw runs

| run_id | ACUT | status | verifier | model usage | observed provider usage cost | ledger estimate | note |
|---|---:|---:|---:|---:|---:|---:|---|
| `openclaw_001__cheap-generic-swe__click__rbench__001__search-replace__attempt1` | cheap generic | patch generated | failed | 15,786 in / 2,339 out | USD 0.022365 | USD 1.00 | fixed crash but rendered tuple repr, not expected comma-separated default text |
| `openclaw_002__cheap-click-specialist__click__rbench__001__search-replace__attempt1` | cheap Click specialist | infra_failed | not run | 17,131 in / 4,462 out | USD 0.03292725 | USD 1.00 | generated `src/click/core.py` for a historical workspace whose path is `click/core.py`; ledgered after response |
| `openclaw_003__frontier-generic-swe__click__rbench__001__search-replace__attempt1` | frontier generic | patch generated | failed | 15,819 in / 1,434 out | USD 0.122115 | USD 3.00 | same semantic miss as cheap generic: tuple repr avoids crash but fails repo behavior |

Scoreable summary (`experiments/core_narrative/results/normalized/openclaw_search_replace_summary.json`):

- total live OpenClaw runs: 3
- scoreable verifier results: 2
- passed: 0
- failed: 2
- infra_failed: 1

This is not a success-rate claim yet; it is the first real data after the runner stopped blocking the experiment.

## Cost accounting reconciliation

Artifact: `experiments/core_narrative/results/cost_reconciliation_2026-05-07.json`.

Current distinction:

- `latest_cumulative_estimated_cost_usd`: USD 66.0008 — local ledger/budget estimate, not actual spend.
- `observed_provider_usage_cost_sum_usd`: USD 0.177407 — provider response `usage.cost` sum for the three OpenClaw live runs; this is provider-reported usage cost, not invoice proof.
- `actual_provider_billed_cost_observed_usd`: `null` — no invoice/billing export was available in repo artifacts.
- `actual_provider_billed_cost_status`: `unknown_no_invoice_or_billed_cost_records`.

So the earlier “USD 61” should be described only as cumulative local estimated/ledger cost. It is not evidence of real billing. The available provider-reported usage/cost evidence is much closer to the user’s suspicion than to the old ledger estimate, but true billed cost remains unknown without provider billing data.

## NFL / Barcarolle narrative signal

The useful story is no longer “the agent cannot run.” We now have plays on tape:

1. Both generic ACUTs made the same partial fix: they addressed the crash (`% tuple` formatting) but missed the repository/user-facing output semantics expected by the verifier.
2. The specialist ACUT exposed a different repository-context hazard: task-agnostic modern Click context pushed it toward `src/click/core.py`, which is wrong for this historical RBench workspace.
3. This is exactly the kind of “box score hides film” evidence Barcarolle needs: a general patch can look plausible while failing the repo-specific behavioral contract.

## Main artifacts

- Runner: `experiments/core_narrative/tools/openclaw_direct_runner.py`
- Cost reconciliation: `experiments/core_narrative/tools/reconcile_cost_accounting.py`
- Live raw artifacts:
  - `experiments/core_narrative/results/raw/openclaw_001__cheap-generic-swe__click__rbench__001__search-replace__attempt1/`
  - `experiments/core_narrative/results/raw/openclaw_002__cheap-click-specialist__click__rbench__001__search-replace__attempt1/`
  - `experiments/core_narrative/results/raw/openclaw_003__frontier-generic-swe__click__rbench__001__search-replace__attempt1/`
- Live normalized artifacts:
  - `experiments/core_narrative/results/normalized/openclaw_001__cheap-generic-swe__click__rbench__001__search-replace__attempt1.json`
  - `experiments/core_narrative/results/normalized/openclaw_002__cheap-click-specialist__click__rbench__001__search-replace__attempt1.json`
  - `experiments/core_narrative/results/normalized/openclaw_003__frontier-generic-swe__click__rbench__001__search-replace__attempt1.json`
- Aggregates:
  - `experiments/core_narrative/results/normalized/openclaw_search_replace_summary.json`
  - `experiments/core_narrative/results/cost_reconciliation_2026-05-07.json`
  - `experiments/core_narrative/results/overnight_2026-05-07_summary.json`

## Validation run

Focused commands run during this stage:

```bash
python3 -m py_compile experiments/core_narrative/tools/openclaw_direct_runner.py experiments/core_narrative/tools/reconcile_cost_accounting.py experiments/core_narrative/tools/test_openclaw_direct_runner.py experiments/core_narrative/tools/test_reconcile_cost_accounting.py
cd experiments/core_narrative/tools && python3 -m unittest test_openclaw_direct_runner.py test_reconcile_cost_accounting.py
python3 experiments/core_narrative/tools/prepare_workspace.py ... click__rbench__001 ...
python3 experiments/core_narrative/tools/openclaw_direct_runner.py ...
python3 -m venv .venv && .venv/bin/python -m pip install -q -e . pytest
python3 experiments/core_narrative/tools/apply_and_verify.py ... --skip-apply
python3 experiments/core_narrative/tools/reconcile_cost_accounting.py --ledger experiments/core_narrative/results/cost_ledger.jsonl --output experiments/core_narrative/results/cost_reconciliation_2026-05-07.json
python3 experiments/core_narrative/tools/summarize_results.py ... --output experiments/core_narrative/results/normalized/openclaw_search_replace_summary.json
```

## Next steps

1. Keep the OpenClaw runner; do not return to `.codex-workflows` as the primary path.
2. Fix the specialist-context path guard: when a task base commit predates the `src/` layout, specialist context must not bias edits toward modern paths.
3. Add allowed PR text/context packaging for `click__rbench__001` if the experiment wants ACUTs to see the declared “expected help text shape” rather than only source files.
4. Expand to one or two additional RBench tasks only after the path guard is fixed; current data is enough to support a first qualitative NFL-style memo, not a quantitative claim.
