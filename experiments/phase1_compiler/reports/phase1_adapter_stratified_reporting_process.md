# Adapter-Stratified Reporting Process

Current step: `Step 3 three-repo reporting supplement complete`.

Completed artifacts:
- Step 0 preflight.
- Step 1 reporting policy and schema.
- Step 2 adapter summary tooling.
- Step 3 three-repo reporting supplement.

Boundary:
- No-paid adapter-stratified reporting run.
- New paid LLM or ACUT calls allowed: `false`.
- New paid LLM or ACUT calls made: `false`.
- Completed paid pilot decision changed by this run: `false`.
- Follow-up runbook drafted by this worker: `false`.

Step evidence:
- Step 0 read `AGENTS.md`, the runbook, and the diagnostics decision.
- Step 0 recorded branch, HEAD, date, Python version, and uv version.
- Step 0 recorded `git status --short --branch` and `git diff --check`.
- Step 0 confirmed the diagnostics decision requires adapter stratification.
- Step 0 classified the unrelated untracked external-review package and left it uncommitted.
- Step 1 added `phase1_adapter_stratified_reporting.yaml`.
- Step 1 added policy loading and validation tooling.
- Step 1 generated policy JSON and markdown outputs.
- Step 1 tests passed: `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_adapter_stratified_reporting.py -q`.
- Step 2 extended the tool to compute adapter-level pass rates, repo/split breakouts, B_eval/H_future gaps, paired disagreements, and cost/latency summaries.
- Step 2 generated `phase1_adapter_stratified_reporting_three_repo_summary.json`.
- Step 2 generated `phase1_adapter_stratified_reporting_three_repo_summary.csv`.
- Step 2 generated `phase1_adapter_stratified_reporting_pairwise_summary.json`.
- Step 2 generated `phase1_adapter_stratified_reporting_cost_latency_summary.json`.
- Step 2 reproduced Codex `22/60`, Kilo `32/60`, both fail `22`, both pass `16`, Codex-only pass `6`, Kilo-only pass `16`, Codex token-estimated USD `32.22309`, and Kilo token-estimated USD `19.044243`.
- Step 2 tests passed: `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_adapter_stratified_reporting.py -q`.
- Step 3 wrote the human-readable adapter-stratified three-repo supplement.
- Step 3 wrote the human-readable adapter-stratified cost and latency supplement.
- Step 3 states that the completed paid pilot decision is unchanged and predictive validity is not established.

Commits made during this run:
- Step 0: `Record adapter stratified reporting preflight`.
- Step 1: `Define adapter stratified reporting policy`.
- Step 2: `Add adapter stratified reporting summaries`.
- Step 3: `Report adapter stratified three-repo pilot summary`.

Notes:
- The run will use committed sanitized results only.
