# Phase 1 Proposal Report Argument Rewrite Process

Status: in progress, 2026-05-30.

Runbook:
`docs/experiments/phase-1-proposal-report-argument-rewrite-runbook.md`.

## Step 0 Preflight And Diagnosis

Recorded at: `2026-05-30T16:01:58+08:00`.

Branch: `codex/restart-benchmark-compiler`.

HEAD: `c4b24f07475e86914fff1e9e82d691b50f1082f4`.

Worktree status at preflight:

```text
## codex/restart-benchmark-compiler...origin/codex/restart-benchmark-compiler [ahead 6]
 M PROCESS.md
?? docs/experiments/phase-1-proposal-report-argument-rewrite-runbook.md
?? docs/experiments/phase-1-proposal-report-skeleton-runbook.md
?? docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? experiments/phase1_compiler/external_review/phase1_candidate_policy_validation_protocol_gpt55_bundle_20260530/
?? experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/
```

Inputs read for diagnosis:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `docs/research/phase-1-proposal-argument-map.md`
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `docs/research/phase-1-proposal-claim-boundary.md`
- `docs/research/phase-1-proposal-report-v0.md`
- `docs/architecture/system-design.md`
- Phase 1 canonical decision reports named by the runbook
- local research notes under `/Users/chenmohan/Downloads/` as needed

No paid ACUT cells, paid LLM calls, or external reviewer calls were made.

### Current Report Failure Mode

The current `docs/research/phase-1-proposal-report-v0.md` contains the right
raw proposal material, but it still reads like an internal skeleton in several
places:

- Sections 1-7 already contain useful problem framing, north-star framing,
  system-boundary evidence, Phase 1 evidence, and validation-path caveats.
- Section 8 turns the reader-facing proposal into a milestone-management
  note, including M2-M6 sequencing.
- Section 10 is an explicit internal milestone list. That belongs in
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`, not in the
  proposal report body.
- Many `[NEEDS ...]` placeholders are useful, but some currently track internal
  decisions rather than proposal-critical evidence. The rewrite should keep
  only placeholders that block the argument a reader is asked to accept.
- The report already states the key boundary that Phase 1 does not prove
  predictive validity. The rewrite should make that boundary part of the
  argument, not a late risk note.

### Document Role Distinction

After this run:

- Proposal report:
  `docs/research/phase-1-proposal-report-v0.md` should be a reader-facing
  argument for why Barcarolle should continue toward repo-specific predictive
  validity.
- Roadmap owner:
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md` remains the
  internal roadmap and milestone-planning document.
- Evidence tracker:
  `docs/research/phase-1-proposal-evidence-todo-matrix.md` remains the matrix
  for missing proposal evidence and follow-up work.
- Claim guardrail:
  `docs/research/phase-1-proposal-claim-boundary.md` remains the allowed,
  draft, and prohibited claim boundary.

No new roadmap file was created.

Step 0 acceptance:

- no paid calls made: yes;
- report/roadmap role distinction written down: yes;
- no new roadmap file created: yes.
