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

## Step 1: Define The Final-Shape Report Contract

### Reader Brief

Target readers:

- project or proposal reviewers deciding whether Barcarolle should continue;
- coding-agent evaluation researchers who will reject benchmark overclaiming;
- agent developers and repo owners who need repo-specific evaluation evidence,
  not only public benchmark scores.

What readers already know:

- repository-level SWE evaluation exists and executable tasks can be generated
  or mined from multiple sources;
- public/general benchmark scores are useful but can be weak evidence for a
  specific repository's future work;
- small benchmark packages are vulnerable to sampling, source-quality, adapter,
  and validation-design errors.

What readers doubt:

- whether Barcarolle is a distinct benchmark-compiler project rather than a
  task generator, ACUT harness, or leaderboard variant;
- whether a failed weighted design undermines the whole project;
- whether weak retrospective signal and a simple coverage candidate justify
  another research phase;
- whether source repair, adapter handling, and artifact hygiene are research
  evidence or mere process cleanup;
- whether the proposal is quietly asking for paid validation before the
  protocol is ready.

What would justify approval:

- a clear research question centered on repo-specific predictive validity;
- a credible system object: versioned benchmark releases compiled from
  candidate supply, not raw task piles;
- honest preliminary evidence showing the problem is real and tractable,
  including negative evidence;
- a validation strategy that separates traction evidence from predictive
  validity and freezes baselines, adapters, invalid-cell rules, and support
  thresholds before future outcomes are joined;
- explicit placeholders for missing numbers, figures, citations, and gates so
  the remaining pre-proposal work is pulled by report blanks.

What the report must not overclaim:

- it must not say predictive validity is established;
- it must not authorize paid ACUT validation;
- it must not treat pseudo-future replay as formal predictive-validity
  evidence;
- it must not report Codex/Kilo differences as model-only superiority;
- it must not make Task Supply v2 or an external generator the central
  Barcarolle contribution.

### Section Contract

| V1 section | Reader-facing job |
| --- | --- |
| Executive Summary | State the decision problem, Barcarolle's contribution, current readiness, remaining blanks, and approval ask without ledger detail. |
| Problem And Stakes | Explain the cost of target-repository shift for teams choosing or tuning ACUTs. |
| Research Question And North Star | Define predictive validity, estimand, and allowed current claim. |
| Barcarolle Thesis And Boundary | Separate benchmark compilation from ACUT harnessing, task generation, leaderboards, and product licensing. |
| Proposed Benchmark-Compiler Design | Describe the final proposed system object: inputs, layers, release outputs, candidate policy family, and needed diagrams/pseudocode. |
| Validation Strategy For Predictive Validity | Specify study modes, estimand, baselines, metrics, adapter reporting, fallback handling, support requirements, invalid-cell rules, and success gates. |
| Preliminary Evidence And Feasibility | Compress Phase 1 into evidence that the problem is real, work is tractable, and the next phase is justified. |
| Project Plan, Decision Gates, And Resource Ask | Present proposal-level work packages and stop/go gates, not internal runbook sequencing. |
| Risks, Objections, And Mitigations | Put the strongest objections up front and answer them with bounded claims and concrete mitigations. |
| Expected Deliverables | Name the artifacts the approved project should produce. |
| Appendices And Evidence Index | Route detailed evidence, report links, claim boundaries, and technical details away from the main argument. |

### Main Body Versus Appendix Routing

Main-body material:

- the problem of predicting future target-repo ACUT performance;
- Barcarolle's benchmark-compiler boundary and proposed release object;
- the validation logic needed to establish predictive validity later;
- a compact preliminary-evidence synthesis tied to reader questions;
- decision gates, risks, mitigations, and deliverables.

Appendix or supporting-document material:

- exact Phase 1 report links and decision labels;
- full weighted-pilot, three-repo pilot, retrospective, adapter, and
  source-repair evidence tables;
- selected task IDs, detailed coverage gaps, fallback manifests, and
  outcome-blindness audit details;
- internal roadmap ownership, milestone labels, and later runbook candidates;
- detailed external-review triage once that work exists.

Acceptance evidence:

- Each planned v1 section has a reader-facing job.
- Phase 1 evidence has a limited argumentative role.
- Internal roadmap details are excluded from the v1 main-body contract.

## Step 2: Write Proposal Report V1 From The Contract

Created `docs/research/phase-1-proposal-report-v1.md`.

Draft structure:

1. Executive Summary
2. Problem And Stakes
3. Research Question And North Star
4. Barcarolle Thesis And Boundary
5. Proposed Benchmark-Compiler Design
6. Validation Strategy For Predictive Validity
7. Preliminary Evidence And Feasibility
8. Project Plan, Decision Gates, And Resource Ask
9. Risks, Objections, And Mitigations
10. Expected Deliverables
11. Appendices And Evidence Index

The draft was written from the Step 1 reader contract rather than by preserving
v0's organization. The main body uses Phase 1 evidence only for the three
reader questions named by the runbook: problem reality, technical tractability,
and enough traction to justify the next phase. Detailed report links and
placeholder registers are routed to the appendices.

Initial diagnostic checks:

```text
rg -n "M[0-9]|runbook|roadmap|current state|completed cells|score table" docs/research/phase-1-proposal-report-v1.md
  no matches

rg -n "proves predictive validity|established predictive validity|authorizes paid" docs/research/phase-1-proposal-report-v1.md
  no matches
```

Acceptance evidence:

- V1 reads as a proposal-approval report with explicit placeholders.
- V1 keeps predictive validity as the north star without claiming it is
  established.
- V1 does not authorize paid ACUT validation.
- V1 does not include an experiment-by-experiment Phase 1 ledger in the main
  body.
- Missing figures, tables, pseudocode, citations, result-dependent numbers,
  decisions, and analysis are marked with precise `[NEEDS ...]` placeholders.

## Step 3: Align Supporting Documents

Supporting-document changes:

- Added a supersession note to
  `docs/research/phase-1-proposal-report-v0.md` stating that v1 supersedes v0
  as the final-shape proposal report while v0 remains source material.
- Updated `docs/research/phase-1-proposal-argument-map.md` to identify v1 as
  the supported proposal report.
- Updated `docs/research/phase-1-proposal-evidence-todo-matrix.md` to state
  that v1 should pull from the matrix without reproducing it as a main-body
  evidence ledger.
- Updated `docs/research/phase-1-proposal-claim-boundary.md` to identify v1
  as the final-shape report draft while preserving the guardrail role.

No change was made to the untracked
`docs/research/phase-1-proposal-roadmap-and-claim-planning.md` input. Roadmap
ownership remains there, and no new roadmap file or later milestone runbook was
created. `PROCESS.md` handoff text will be updated during closeout so it can
point to the final decision artifacts after they exist.

Acceptance evidence:

- V0 is clearly superseded by v1.
- Argument, evidence, and claim-boundary support files point to v1 and keep
  their internal scaffolding roles.
- Roadmap ownership remains in the existing planning document.
- No duplicate roadmap file was created.
- No later runbook was drafted or created.

## Step 4: Self-Review Against The Final-Shape Standard

Review questions:

| Question | Result |
| --- | --- |
| If placeholders were filled, would v1 be close to the final proposal-approval report? | Yes. The draft has the required approval-report sections, explicit ask, validation strategy, risks, deliverables, and appendices. |
| Can a proposal reader understand the project without reading internal runbooks? | Yes. The main text defines the problem, contribution, boundary, system object, validation design, and evidence limits without relying on runbook chronology. |
| Does every Phase 1 evidence paragraph support a reader-facing claim? | Yes. Evidence is grouped under problem reality, technical tractability, and traction without a chronological ledger. |
| Are algorithm, validation, and risk sections shaped as proposal content rather than process notes? | Yes. Internal milestone and runbook details are excluded from the main body. |
| Are unsupported or result-dependent claims explicitly marked? | Yes. Missing citations, figures, pseudocode, numbers, results, decisions, and analyses are marked with precise `[NEEDS ...]` placeholders. |

Text diagnostics:

```text
rg -n "M[0-9]|runbook|roadmap|current state|completed cells|score table" docs/research/phase-1-proposal-report-v1.md
  no matches

rg -n "proves predictive validity|established predictive validity|authorizes paid" docs/research/phase-1-proposal-report-v1.md
  no matches

rg -n "predictive validity is established|paid validation is authorized|validated predictive benchmark compiler|model-only superiority" docs/research/phase-1-proposal-report-v1.md
  no matches

git diff --check
  passed
```

Acceptance evidence:

- V1 passes the final-shape review.
- No prohibited predictive-validity or paid-authorization phrasing was found.
- `git diff --check` passed.
- No paid calls were made.
