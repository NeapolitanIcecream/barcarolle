# Phase 0 Headroom Experiments

This directory is for the Barcarolle restart experiments.

Run the experiment from the repository root:

```bash
uv run --project experiments/phase0_headroom python experiments/phase0_headroom/tools/phase0_driver.py --root .
uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools -q
```

The operating plan is `docs/experiments/phase-0-runbook.md`. If Phase 0 stops
at `repair_source_adapter`, continue from
`docs/experiments/phase-0-source-adapter-followup-runbook.md`. If that follow-up
reaches `ready_for_headroom_matrix`, continue from
`docs/experiments/phase-0-headroom-matrix-followup-runbook.md`. After the matrix
follow-up, use `docs/experiments/phase-0-closeout-followup-runbook.md` to return
to the original Phase 0 Step 8/9 decision memo and commit hygiene.

For future measured runs, use
`docs/experiments/phase-0-measured-endpoint-runbook.md`. That runbook requires
all LLM and ACUT calls to use `LLM_BASE_URL` plus `LLM_API_KEY`, records token
usage and measured cost, and uses those measurements to decide whether to scale
task count or ACUT count.

Phase 0 asks whether repo-specific benchmark signal exists before building a
larger benchmark compiler:

- distribution mismatch between general SWE benchmarks and target-repo work;
- same-repo predictive headroom from early tasks to later work;
- task-supply and certification funnel from candidate anchors to
  benchmark-grade tasks.

If existing task-generation pipelines cannot provide inputs for the selected
repositories, add a minimal repo-history generator under this experiment tree.
Treat it as candidate supply infrastructure: measure certified yield,
replayability, oracle quality, and manual effort.

The certification funnel should report gate-level rejection reasons, including
known-bad failure, ambiguity, solution leakage, scope clarity, cost boundedness,
and taxonomy labelability. Keep `near_certified` tasks separate from
benchmark-grade `certified` tasks.

Large raw artifacts should not be committed. Store them under ignored paths and
commit a small manifest with path, digest, producer, and reproduction command.
For the current run, see `results/raw_artifact_manifest.json`.

Expected layout:

```text
configs/
candidate_sources/
target_profiles/
certified_tasks/
releases/
results/
reports/
```
