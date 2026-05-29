# Phase 1 Blocked Split Redesign Process

## Step 0: Preflight

What happened: the run started on branch `codex/restart-benchmark-compiler` at
commit `6a691553` (`Add blocked split redesign runbook`). The working tree had
one unrelated untracked bundle:
`experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/`
with 106 untracked files. Nothing from that bundle was staged.

Why it matters: the runbook can proceed without mixing this split redesign with
the external-review material. Required committed inputs were present, including
10 paid score tables, 10 cost summaries, and the workspace usage ledger.

What action it suggests next: keep the untracked external-review bundle out of
this run and build the split only from committed source-hardening artifacts.

The source-hardening decision is `source_context_ready_with_minor_risk`, with
`ready_for_blocked_split_design=true`. This run is no-paid: it will not make new
paid LLM calls or paid ACUT solver calls. The completed three-repo paid pilot
remains frozen with `primary_design=repo_stratified`, 120 planned/completed/
scoreable cells, and primary pooled gap 0.1.

Click remains the visible caveat for the redesign. Its eligible tasks use
title-only source context and `minor_risk` source quality, so every split,
diagnostic, gate, and decision in this run must keep that claim boundary
explicit.
