# Proposal Approval Packet M6 Runbook

Status: approval-packet production runbook, 2026-06-01.

## Goal

Convert the accepted V5 proposal report into an approval packet for project
decision makers.

The primary output is an editable PowerPoint deck. Markdown artifacts are the
source, summary, and evidence handoff material.

Plain-language target:

```text
Give reviewers a concise decision package: what problem Barcarolle solves, why
the current evidence is enough to approve the project, what remains unproven,
what the approved project will build, and how budgeted validation will be
gated.
```

## Format Decision

The M6 format is a combined approval packet:

1. PPTX as the primary presentation artifact.
2. One-page executive summary as the fast-read artifact.
3. Evidence appendix as the audit trail.
4. V5 proposal report as the source-of-truth long-form report.

Do not use `imagegen` by default. This packet is an evidence and decision
artifact, not a marketing visual. Diagrams should be editable, auditable, and
reproducible through presentation-native shapes, Mermaid/SVG, tables, or
simple charts. Use generated raster images only if the user explicitly asks
for a more public/roadshow-style visual.

## Reader Contract

The approval packet should be understandable without knowing Barcarolle's
internal runbook or phase history.

Reader-facing artifacts must not use internal labels such as `Phase 1`,
`Phase 2`, `Phase 3`, `M1`, `M2`, `M3`, `M4`, `M5`, or `M6`. Use plain
language:

| Internal meaning | Reader-facing wording |
| --- | --- |
| completed internal pre-proposal work | preliminary evidence, completed pilot work, current evidence |
| later scientific extension | stronger multi-configuration validation |
| later product application path | tuning and regression-feedback workflows |
| paid/no-paid internal boundary | budgeted validation gates, evaluation budget, approval path |
| runbook/process evidence | evidence appendix, supporting reports, audit trail |

The packet must preserve the V5 claim boundary:

```text
Current evidence supplies traction and a credible validation path. It does not
establish formal predictive validity.
```

## Boundary

Allowed:

- create a new approval packet directory under `docs/research/`;
- create a one-page executive summary;
- create a deck outline and final editable PPTX;
- create or reuse simple, auditable diagrams/tables for the deck;
- create an evidence appendix pointing to committed reports and V5;
- lightly copyedit V5 only if a blocking factual inconsistency is found;
- update the roadmap, checklist, and `PROCESS.md` after the packet passes;
- add process and decision closeout artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- public browsing unless a V5 public citation is discovered to be broken or
  materially ambiguous;
- changing score tables, selected task IDs, split labels, source eligibility,
  task statements, hidden-oracle material, or completed experiment decisions;
- claiming predictive validity has been established;
- claiming agent tuning or tuning-loop improvement has been empirically proven;
- turning the deck into a protocol packet, lab notebook, or evidence dump;
- reintroducing internal phase/milestone vocabulary into reader-facing
  artifacts;
- using decorative generated images or abstract AI art by default;
- setting final staffing, duration, or budget numbers beyond placeholders
  unless the user provides them.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/research/barcarolle-proposal-report-v5.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_decision.md
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
```

Use V5 as the source of truth. Use earlier reports only to resolve traceability
or exact evidence references, not to reopen the proposal argument.

If working in a Codex desktop environment with the Presentations skill
available, use that workflow for the final PPTX. It requires editable
artifact-tool presentation JSX and rendered QA previews before export. Do not
use `python-pptx`, direct OOXML edits, or LibreOffice round trips for the
final deck when the Presentations workflow is available.

## Expected Outputs

Create:

```text
docs/research/m6-approval-packet/executive-summary-v1.md
docs/research/m6-approval-packet/approval-deck-outline-v1.md
docs/research/m6-approval-packet/appendix-evidence-index-v1.md
docs/research/m6-approval-packet/barcarolle-approval-deck-v1.pptx
docs/research/m6-approval-packet/approval-packet-checklist-v1.md
```

Create `assets/` only for committed, final, auditable deck assets:

```text
docs/research/m6-approval-packet/assets/
```

Do not commit temporary presentation workspaces, preview images, contact
sheets, generated slide source, scratch scripts, or layout JSON unless they are
explicitly promoted as final audit artifacts. The Presentations workflow may
use `outputs/.../presentations/...` for scratch work; keep only the final PPTX
and final committed assets under `docs/research/m6-approval-packet/`.

Create closeout artifacts:

```text
experiments/phase1_compiler/reports/proposal_approval_packet_m6_process.md
experiments/phase1_compiler/reports/proposal_approval_packet_m6_decision.md
experiments/phase1_compiler/results/proposal_approval_packet_m6_decision.json
```

Update if the packet succeeds:

```text
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
docs/research/phase-1-proposal-report-reviewer-ready-checklist.md
PROCESS.md
```

## Approval Packet Contract

The packet must answer five questions:

1. What decision is being requested?
2. What problem makes the decision worth considering?
3. What has already been shown, and what has not been shown?
4. What will the approved project build and validate?
5. What gates prevent overclaiming or uncontrolled evaluation spending?

The packet should not try to reproduce the full report. V5 remains the
long-form source of truth.

### Executive Summary Contract

The executive summary should fit on roughly one printed page and use this
shape:

```text
Decision requested
Why this matters
What Barcarolle is
Current evidence
What remains unproven
Approved-project work
Budget and validation gates
Expected decision outcome
```

Use placeholders instead of inventing user-owned values:

```text
[NEEDS USER DECISION: project staffing]
[NEEDS USER DECISION: project duration]
[NEEDS USER DECISION: gated ACUT evaluation budget ceiling]
[NEEDS USER DECISION: approval path or approving owner]
```

### Deck Contract

Create a 10-12 slide deck. Default slide spine:

| Slide | Working title | Main claim | Proof object |
| --- | --- | --- | --- |
| 1 | Approval Ask | Approve Barcarolle as a repo-specific benchmark-compiler project. | One-sentence ask and north star. |
| 2 | The Evaluation Gap | Teams need evidence about future work in their own repository. | Public-benchmark-vs-target-repo contrast. |
| 3 | What Barcarolle Builds | Barcarolle compiles benchmark releases; it does not replace the ACUT harness. | Boundary diagram. |
| 4 | Why It Matters For Tuning | Predictive benchmarks become useful through configuration comparison, tuning, and regression feedback. | Tuning workflow diagram. |
| 5 | What We Already Learned | Current evidence shows the problem is real, measurable, and technically tractable. | Four-row evidence table from V5. |
| 6 | What We Are Not Claiming | Predictive validity and tuning-loop improvement remain unproven. | Claim-boundary callout. |
| 7 | Validation Path | Stronger claims require frozen releases and future or rolling-origin validation. | Validation roadmap. |
| 8 | Project Work Packages | The approved project builds release machinery, selection algorithms, certification, validation, and tuning interfaces. | Work-package map. |
| 9 | Gates And Budget Discipline | Paid evaluation is budgeted and gated, not open-ended. | Gate table with placeholders. |
| 10 | Risks And Mitigations | Main risks are overclaiming, overfitting, source quality, support gaps, and adapter interpretation. | Risk matrix. |
| 11 | Deliverables | Reviewers can expect concrete releases, protocols, reports, and tuning-facing interfaces. | Deliverable list. |
| 12 | Decision | Approve the project under the stated claim boundary and gates. | Final ask and next actions. |

If the deck works better at 10 or 11 slides, merge slides. Do not exceed 12
slides unless the user provided an audience requirement that makes it necessary.

Deck style:

- restrained engineering/research presentation;
- dense enough for technical reviewers, not a marketing landing page;
- each slide must have one claim and one proof object;
- no generic decorative cards, abstract blobs, generated mascots, or hero art;
- use editable diagrams, tables, callouts, and simple charts;
- keep text short enough to read in presentation mode;
- include source notes only where they help trace claims without crowding the
  slide.

### Evidence Appendix Contract

The appendix should be short and readable. It should map claims to committed
evidence without forcing readers through internal process history.

Default columns:

```text
Evidence label
Reader-facing role
Key numbers or conclusion
Canonical source
Claim limit
```

Use readable labels, for example:

```text
Weighted design pilot
Three-repo workspace execution pilot
Click source-context repair
Random-baseline comparison
Baseline-envelope comparison
Fallback-share accounting
Validation-protocol hardening
V5 proposal report
```

Raw path-level traceability can point to the internal V5 evidence manifest.

## Worker Prompt

Use this prompt to start the execution worker:

```text
You are executing docs/experiments/proposal-approval-packet-m6-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read the runbook and follow it with step-level acceptance and scoped
commits.

Main goal: create a combined approval packet from
docs/research/barcarolle-proposal-report-v5.md. The primary deliverable is an
editable PowerPoint deck, supported by a one-page executive summary and an
evidence appendix.

Do not run paid ACUT cells, paid LLM calls, or external reviewer calls. Do not
change score tables, task IDs, split labels, source eligibility, task
statements, hidden-oracle material, or completed experiment decisions. Do not
claim predictive validity, tuning-loop improvement, or multi-configuration
residual predictive validity has been established. Do not use imagegen or
decorative generated images by default. Do not put internal phase or milestone
labels into reader-facing artifacts.
```

## Step 0: Preflight And Packet Setup

Actions:

1. Record branch, HEAD, date, worktree status, and input availability in the
   process report.
2. Confirm V5 is the accepted proposal source:

```text
docs/research/barcarolle-proposal-report-v5.md
```

3. Create:

```text
docs/research/m6-approval-packet/
docs/research/m6-approval-packet/assets/
```

4. Record the packet contract:
   - combined packet;
   - PPTX primary;
   - executive summary fast read;
   - evidence appendix audit trail;
   - no imagegen by default;
   - no new experiments or paid calls.

Acceptance:

- no paid/external calls made;
- process report records source inputs and packet contract;
- output directory exists;
- no reader-facing artifact has been drafted yet.

Suggested commit:

```text
Record approval packet preflight
```

## Step 1: Extract The Claim Spine

Actions:

1. Read V5 and extract the approval story into:

```text
docs/research/m6-approval-packet/approval-deck-outline-v1.md
```

2. The outline must include, for every slide:
   - slide title;
   - one-sentence claim;
   - proof object;
   - source evidence;
   - claim limit;
   - notes on any needed placeholder.
3. Keep the default 10-12 slide spine unless there is a clear reader-facing
   reason to merge or reorder slides.
4. Verify the outline does not introduce new evidence or stronger claims than
   V5.

Acceptance:

- outline exists and covers the full deck;
- every slide has a claim and proof object;
- predictive validity remains unproven;
- tuning-loop improvement remains unproven;
- staffing, duration, and budget values are placeholders unless user supplied.

Suggested commit:

```text
Draft approval packet claim spine
```

## Step 2: Draft Summary And Evidence Appendix

Actions:

1. Write the one-page summary:

```text
docs/research/m6-approval-packet/executive-summary-v1.md
```

2. Write the evidence appendix:

```text
docs/research/m6-approval-packet/appendix-evidence-index-v1.md
```

3. The summary should be decision-facing, not process-facing.
4. The appendix should map claim labels to canonical sources and limits.
5. Do not copy long sections from V5. Summarize for decision use.

Acceptance:

- executive summary can be read independently in a few minutes;
- evidence appendix is concise and traceable;
- neither artifact exposes internal phase/milestone vocabulary;
- no local `/Users/chenmohan/Downloads` source paths appear;
- no claim exceeds V5.

Suggested commit:

```text
Draft approval packet summary and evidence index
```

## Step 3: Build The PPTX

Actions:

1. Use the outline, summary, and V5 to build:

```text
docs/research/m6-approval-packet/barcarolle-approval-deck-v1.pptx
```

2. Use editable presentation-native diagrams and tables. Recommended proof
   objects:
   - target-repo prediction gap contrast;
   - Barcarolle/ACUT boundary diagram;
   - benchmark release workflow;
   - tuning and regression feedback loop;
   - preliminary evidence table;
   - future-validation roadmap;
   - budget and decision-gate table.
3. If using the Presentations skill, follow its artifact-tool JSX workflow:
   - create a thread-scoped presentation workspace under `outputs/...`;
   - write editable slides;
   - render previews and layout JSON;
   - inspect the deck at contact-sheet and slide level;
   - export only after the QA gate passes;
   - copy only the final PPTX into `docs/research/m6-approval-packet/`.
4. If the presentation toolchain is unavailable, stop with
   `blocked_pptx_generation_tool_unavailable` after completing the Markdown
   artifacts. Do not silently substitute a markdown-only deck for the expected
   PPTX.

Acceptance:

- PPTX exists at the expected path;
- deck is editable and uses native text/shapes/tables where practical;
- each slide has a clear claim and proof object;
- no slide depends on a decorative generated image;
- deck can be understood without V5 open beside it;
- deck does not overclaim predictive validity or tuning impact.

Suggested commit:

```text
Build approval presentation deck
```

## Step 4: Review And Audit The Packet

Actions:

1. Create:

```text
docs/research/m6-approval-packet/approval-packet-checklist-v1.md
```

2. Checklist items must cover:
   - decision ask clarity;
   - reader-facing vocabulary;
   - V5 claim-boundary preservation;
   - preliminary evidence accuracy;
   - predictive-validity non-claim;
   - tuning-loop non-claim;
   - paid evaluation framed as budgeted and gated;
   - evidence traceability;
   - placeholder visibility for user-owned values;
   - deck readability.
3. Extract PPTX text for audit. A simple local helper is acceptable if it only
   reads the PPTX zip and writes a temporary text file under an ignored scratch
   path.
4. Run text checks on Markdown artifacts and extracted PPTX text:

```bash
rg -n "Phase 1|Phase 2|Phase 3|phase 1|phase 2|phase 3|M[0-9]|No Paid|no-paid|runbook|closeout" docs/research/m6-approval-packet/*.md
rg -n "validated predictive benchmark compiler|established predictive validity|tuning validation established|improves agent tuning|multi-ACUT residual validity established" docs/research/m6-approval-packet/*.md
rg -n "/Users/chenmohan/Downloads" docs/research/m6-approval-packet/*.md
git diff --check
```

5. Run the same prohibited-term checks against extracted PPTX text.
6. Review the deck manually:
   - thumbnail/contact-sheet view has a coherent story;
   - slide text is readable;
   - diagrams are not crowded;
   - source notes do not overwhelm the main claims.

Acceptance:

- checklist exists and passes;
- Markdown checks pass or every intentional internal match is explained;
- PPTX text checks pass or every intentional internal match is explained;
- `git diff --check` passes;
- deck has been visually reviewed through rendered previews or an equivalent
  PowerPoint preview.

Suggested commit:

```text
Audit approval packet
```

## Step 5: Update Handoff State

Actions:

1. Update the roadmap to mark M6 complete if the packet passes.
2. Update the reviewer-ready checklist to include approval-packet status.
3. Update `PROCESS.md` with a short current-state entry:
   - approval packet produced;
   - V5 remains long-form source of truth;
   - predictive validity and tuning-loop improvement remain unproven;
   - remaining user-owned values, if any.

Acceptance:

- handoff docs point to the M6 packet;
- `PROCESS.md` remains concise;
- no stale "M6 waiting" language remains in the roadmap if packet completed;
- user-owned placeholders are listed rather than invented.

Suggested commit:

```text
Align approval packet handoff docs
```

## Step 6: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/proposal_approval_packet_m6_process.md
experiments/phase1_compiler/reports/proposal_approval_packet_m6_decision.md
experiments/phase1_compiler/results/proposal_approval_packet_m6_decision.json
```

2. Stop with one label:

```text
proposal_approval_packet_m6_complete
blocked_pptx_generation_tool_unavailable
blocked_claim_boundary_unclear
blocked_reader_facing_packet_overclaims
blocked_missing_core_inputs
blocked_user_owned_resource_values_needed
```

Decision report must state:

- whether the approval packet is complete;
- where the PPTX, executive summary, outline, appendix, and checklist are;
- whether V5 remains the source of truth;
- whether the packet preserves the claim boundary;
- whether imagegen or generated raster assets were used;
- whether any user-owned staffing/duration/budget placeholders remain;
- whether any paid/external calls were made;
- what should happen next.

Suggested commit:

```text
Close approval packet production
```

## Final Report Expectations

The closeout should say:

```text
What changed:
  The accepted V5 proposal report was converted into a concise approval packet
  with a PPTX deck, one-page summary, and evidence appendix.

Why it matters:
  Reviewers now have a decision-facing artifact instead of a long technical
  report as the main entry point.

What remains:
  Fill or confirm any user-owned staffing, duration, budget-ceiling, or
  approval-path placeholders before sending the packet to reviewers.
```

Do not draft a follow-up runbook unless the user explicitly asks after
reviewing the M6 result.
