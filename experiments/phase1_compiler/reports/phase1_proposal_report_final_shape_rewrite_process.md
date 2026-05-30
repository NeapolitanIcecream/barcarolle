# Phase 1 Proposal Report Final-Shape Rewrite Process

Status: in progress.
Runbook: `docs/experiments/phase-1-proposal-report-final-shape-rewrite-runbook.md`.
Started: 2026-05-30T19:11:01+08:00.

## Step 0: Preflight And Failure Diagnosis

Branch: `codex/restart-benchmark-compiler`.
HEAD: `bb46db6bb2a7e3dc668914f1bb73df946caad1ae`.

Starting worktree status:

```text
 M PROCESS.md
?? docs/experiments/phase-1-proposal-report-argument-rewrite-runbook.md
?? docs/experiments/phase-1-proposal-report-final-shape-rewrite-runbook.md
?? docs/experiments/phase-1-proposal-report-skeleton-runbook.md
?? docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? experiments/phase1_compiler/external_review/phase1_candidate_policy_validation_protocol_gpt55_bundle_20260530/
?? experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/
```

Required input availability:

| Input | Status |
| --- | --- |
| `AGENTS.md` | available and read |
| `PROCESS.md` | available and read |
| `docs/research/phase-1-proposal-report-v0.md` | available and read |
| `docs/research/phase-1-proposal-roadmap-and-claim-planning.md` | available and read |
| `docs/research/phase-1-proposal-argument-map.md` | available and read |
| `docs/research/phase-1-proposal-evidence-todo-matrix.md` | available and read |
| `docs/research/phase-1-proposal-claim-boundary.md` | available and read |
| `docs/architecture/system-design.md` | available and read |
| `/Users/chenmohan/Downloads/barcarolle-research-0519.md` | available; read for background positioning as needed |
| `/Users/chenmohan/Downloads/barcarolle-research-0526.md` | available; read for weighted-design diagnosis as needed |
| `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md` | available; not needed beyond existing evidence tracker references |
| `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | available; read for current adversarial-review findings |

Canonical evidence reports named by the runbook were available under
`experiments/phase1_compiler/reports/`; the core decision, retrospective,
candidate-policy, source-repair, adapter, and task-supply reports were read or
spot-checked for the values used in the draft.

No paid ACUT cells, paid LLM calls, GPT-5.5-Pro calls, or external reviewer
calls were made.

### V0 Failure Diagnosis

`docs/research/phase-1-proposal-report-v0.md` contains useful proposal
material, but it is not the final-shape approval report the runbook asks for.
Its main failure modes are:

- It still reads from the current research state. The central structure moves
  from thesis to research problem to existing systems, but then turns into a
  numbered Phase 1 evidence report with subsections for weighted failure,
  exploratory paid runs, adapter/source boundaries, retrospective signal, and
  the frozen candidate.
- It exposes process details that an approval reader does not need in the main
  body: exact completed-cell counts, scoreability rates, decision labels,
  runbook-derived next-step sequencing, and artifact-governance details that
  belong in appendices or evidence links.
- Its Phase 1 evidence is often chronological or ledger-like. The evidence is
  valid source material, but the main body does not consistently route each
  paragraph to one of the reader-facing questions: whether the problem is real,
  whether the work is tractable, and whether the next phase is justified.
- Its final sections still behave like a near-term internal agenda. They name
  no-paid hardening categories and future work, but do not yet present a
  final proposal-level ask, deliverable set, decision gates, and risks in the
  shape reviewers can approve once placeholders are filled.

### V1 Target Contract

The target is `docs/research/phase-1-proposal-report-v1.md`: a final-shape
proposal-approval report that would be close to reviewer-ready once explicit
`[NEEDS ...]` placeholders are filled. It must:

- keep predictive validity as the north star without claiming it is
  established;
- present Barcarolle as a target-repository benchmark compiler, not an ACUT
  harness, general SWE task generator, public leaderboard, or agent-license
  product;
- use Phase 1 evidence only to show the problem is real, measurable, and
  technically tractable;
- describe the proposed compiler and validation design at proposal level, with
  placeholders for missing figures, pseudocode, numbers, citations, and
  result-dependent paragraphs;
- preserve paid-validation non-authorization and avoid inventing future
  results;
- keep roadmap ownership in
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`;
- avoid creating a new roadmap or later milestone runbooks.

Acceptance evidence:

- No paid calls made.
- V0 failure mode recorded.
- V1 target contract recorded.
- No new roadmap file created.
