# Phase 1 Proposal Report V3 Genre Repair Process

Status: in progress, 2026-06-01.

This process report records execution evidence for
`docs/experiments/phase-1-proposal-report-v3-genre-repair-runbook.md`.

## Step 0: Preflight And Regression Diagnosis

Branch: `codex/restart-benchmark-compiler`.

HEAD at preflight:
`ac8531297b3fc59477deb8ea483f1bf6631373b7`.

Date: `2026-06-01`.

Starting worktree status:

```text
## codex/restart-benchmark-compiler...origin/codex/restart-benchmark-compiler
 M PROCESS.md
 M docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? docs/experiments/phase-1-proposal-report-v3-genre-repair-runbook.md
```

The preexisting `PROCESS.md` and roadmap edits already describe the user review
that found V2 evidence-safe but proposal-genre regressed. The untracked runbook
is the execution input for this run. These starting changes are treated as
user/coordinator context and are not reverted.

Input availability: all required repository inputs, support artifacts, and
local planning/review files named by the runbook were present at preflight.
Local planning files were checked for availability only; they should not be
cited as public literature support in V3.

Paid/external-call boundary:

- Paid ACUT solver cells run in this step: `0`.
- Paid LLM calls run in this step: `0`.
- External reviewer calls run in this step: `0`.
- Public browsing used in this step: `false`.
- Score tables, selected task IDs, split labels, source eligibility, task
  statements, and completed experiment decisions changed: `false`.

V2 genre regression diagnosis:

- Internal milestone/process vocabulary appears in reader-facing argument
  positions. Examples include `M3`, `M4`, `M5`, `M6`, `P0`, `no-paid`,
  `user-owned`, and report/process artifact references in the executive
  summary, validation section, risks, proposed next phase, deliverables, and
  appendix.
- The opening frames the requested decision as approval of a "no-paid research
  phase" and repeatedly says paid validation is not authorized. That is a
  correct execution guardrail for the writing work, but it makes the proposal
  sound as if the approved project itself is defined by not spending evaluation
  budget.
- The phrase "next phase" points to remaining pre-proposal/M6 packaging work in
  several places rather than to the project work that would begin after
  approval.
- Technical due-diligence detail dominates the back half. Study-mode tables,
  adapter-estimand wording, fallback caps, release-schema fields, support
  thresholds, and user decision tables should be translated into a readable
  validation plan, resource plan, risks, and appendices.
- Terminology is introduced before a proposal reader has a reason to care about
  it. V3 should name detailed policy objects only where they clarify evidence
  or traceability.

V3 execution decision:

- Use `docs/research/phase-1-proposal-report-v1.md` as the structural
  reference and preserve its eleven-section proposal shape.
- Use `docs/research/phase-1-proposal-report-v2.md` as the evidence, citation,
  figure, and conservative claim-boundary source.
- Reframe paid ACUT evaluation as a normal budgeted project activity that may
  occur only after candidate policies, validation protocols, baselines, and
  success criteria are frozen.
- Preserve the central claim boundary: predictive validity is the north star;
  Phase 1 does not establish it; Phase 1 supplies traction evidence and a
  concrete path for testing it.

Acceptance evidence: Step 0 complete. No proposal report text changed. No paid
or external calls made.

## Step 1: V1-To-V3 Section Map

V3 will preserve the V1 eleven-section structure. The repair changes emphasis
and placement, not the basic proposal shape.

| V3 section | Reader question answered | V2 material to keep | Material to remove, translate, or move | Evidence or citation source |
| --- | --- | --- | --- | --- |
| 1. Executive Summary | What decision is requested and why now? | V2's bounded claim, north-star question, four approval-relevant results, citation to benchmark-validity concerns. | Replace "no-paid research phase", repeated non-authorization wording, and M6 packaging language with a positive approval ask for the project and budgeted evaluation after freezes. | V2 sections 1 and 5; `Validity-Challenges-2022`; M3/M4 summary docs. |
| 2. Problem And Stakes | Why does repo-specific prediction matter to reviewers? | V2's target-repo shift framing and related-work comparison table. | Remove paid/no-paid boundary language from stakes; keep public benchmark systems as context, not a chronology. | V2 section 2; citation matrix. |
| 3. Research Question And North Star | What is the precise research question and claim standard? | V2's estimand and "traction, not validity" boundary. | Restore V1's separate research-question section; avoid dropping directly from related work into design. | V1 section 3; V2 section 3; claim-boundary doc. |
| 4. Barcarolle Thesis And Boundary | What is Barcarolle and what is outside scope? | V2's ACUT boundary, source-as-input framing, and non-leaderboard/task-factory distinctions. | Move implementation or protocol detail that belongs in design or appendix; keep boundary reader-facing. | V1 section 4; V2 sections 1 and 3; `AGENTS.md`. |
| 5. Proposed Benchmark-Compiler Design | What will the project build? | V2 architecture figure, compiler layers, release object, and policy sketch. | Translate "candidate policy object" into an example current selector; keep detailed pseudocode and fallback thresholds for appendix. | V1 section 5; V2 section 4; candidate-policy hardening report. |
| 6. Validation Strategy For Predictive Validity | How will the project test the north star? | V2 validation figure, evidence-mode distinction, mandatory baselines, named-ACUT reporting, and joint-gate principle. | Remove the protocol-table dump from the main body; move detailed thresholds, fallback caps, release schema fields, and support values to appendices. | V2 section 6; validation hardening summary and reports. |
| 7. Preliminary Evidence And Feasibility | Is there enough evidence to approve project work? | V2 problem/feasibility/signal evidence, MAE explanation, random percentile, adapter/fallback caveats. | Stop using M3/M4 labels as section logic; present evidence as proposal traction rather than experiment chronology. | V2 section 5; evidence package; baseline envelope; random baseline distribution; fallback share. |
| 8. Project Plan, Decision Gates, And Resource Ask | What work happens after approval and what resources may be needed? | V2 workstreams and power/budget scenario context. | Replace "next no-paid phase" and user-owned decision table with approved-project work packages, bracketed resource decisions, and budgeted evaluation after freezes. | V1 section 8; V2 sections 8-9; power/budget note. |
| 9. Risks, Objections, And Mitigations | What could make the project fail, and how will it be controlled? | V2 risk register content: failed weighting, small edge, fallback, adapter-specific support, source quality, post-hoc risk, budget risk. | Rewrite from internal readiness failures into mature proposal risks and mitigations. | V2 section 7; M5 risk register. |
| 10. Expected Deliverables | What should reviewers expect to receive? | V2 technical deliverables: compiler spec, validation protocol, release schema, risk register, evidence index. | Remove "current v2 report", M6 artifact, user-owner tables, and runbook/process artifacts as deliverables. | V1 section 10; V2 section 9. |
| 11. Appendices And Evidence Index | Where can reviewers audit the details? | V2 appendices, evidence index, citation bibliography, release-schema and protocol pointers. | Put internal artifact names here when needed for traceability; keep main body free of milestone/process vocabulary. | V2 section 10; citation matrix; support artifacts. |

Back-half remapping from V2:

- V2 section 6 becomes V3 section 6 plus Appendix B. The main body keeps the
  validation logic: freeze before outcomes, compare against baselines, report by
  named ACUT configuration, handle invalid cells with predefined rules, and
  require meaningful improvement. Threshold tables, fallback caps, support
  thresholds, and schema fields move to appendices.
- V2 section 7 becomes V3 section 9. Risk rows are rewritten as proposal risks,
  not as internal readiness failures.
- V2 section 8 becomes V3 section 8. "Next phase" now means approved project
  work: compiler optimization, source certification, release freezing,
  validation execution, and publication of results.
- V2 section 9 splits across V3 sections 8, 10, and 11. Resource decisions
  become bracketed project inputs; technical deliverables become approved
  project outputs; artifact pointers move to the evidence index.

Paid evaluation mapping:

- Main body: budgeted ACUT evaluation is a project resource that should be
  spent only after benchmark releases, task-selection rules, baselines, success
  criteria, and score-join procedures are frozen.
- Appendices: execution guardrails and historical no-paid labels may appear
  only as artifact context where needed for traceability.

Acceptance evidence: every V3 section has a reader-facing job, the V1 structure
is preserved, and paid evaluation is mapped to resource planning rather than to
a repeated prohibition.
