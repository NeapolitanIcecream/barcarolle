# Proposal Approval Packet M6 Process

Status: in progress, 2026-06-01.

## Step 0: Preflight And Packet Setup

Execution context:

| Item | Value |
| --- | --- |
| Branch | `codex/restart-benchmark-compiler` |
| HEAD | `6030d118f918c042e484e3bc3e0ad83043a6bea1` |
| Recorded date | `2026-06-01 18:19:38 CST` |
| Initial worktree status | clean |

Required inputs were available:

| Input | Status |
| --- | --- |
| `AGENTS.md` | present |
| `PROCESS.md` | present |
| `docs/research/barcarolle-proposal-report-v5.md` | present |
| `docs/research/phase-1-proposal-roadmap-and-claim-planning.md` | present |
| `docs/research/phase-1-proposal-report-reviewer-ready-checklist.md` | present |
| `experiments/phase1_compiler/reports/proposal_report_v5_phase_label_cleanup_decision.md` | present |
| `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md` | present |

Accepted proposal source:

```text
docs/research/barcarolle-proposal-report-v5.md
```

Packet contract recorded:

- combined approval packet;
- editable PPTX as the primary artifact;
- one-page executive summary as the fast-read artifact;
- concise evidence appendix as the audit trail;
- V5 remains the source-of-truth long-form report;
- no imagegen or generated raster assets by default;
- no new experiments, paid ACUT calls, paid LLM calls, external reviewer
  calls, or public browsing;
- no changes to score tables, task IDs, split labels, source eligibility, task
  statements, hidden-oracle material, or completed experiment decisions;
- current evidence may support project approval, but it does not establish
  predictive validity or tuning-loop improvement.

Output directories created locally:

```text
docs/research/m6-approval-packet/
docs/research/m6-approval-packet/assets/
```

Acceptance evidence:

- no paid or external calls were made;
- required inputs were present;
- the packet contract is recorded above;
- the output directory exists;
- no reader-facing approval-packet artifact had been drafted at Step 0 close.

## Step 1: Extract The Claim Spine

Created:

```text
docs/research/m6-approval-packet/approval-deck-outline-v1.md
```

Outline choices:

- kept the 12-slide default spine because V5's approval story maps cleanly to
  decision ask, problem, boundary, tuning path, current evidence, non-claims,
  validation path, work packages, gates, risks, deliverables, and decision;
- gave every slide a one-sentence claim, proof object, source evidence, claim
  limit, and placeholder note;
- used V5 as the source of truth and earlier inputs only for traceability and
  handoff context;
- left staffing, duration, budget-ceiling, approval-owner, and owner-category
  values as placeholders.

Acceptance evidence:

- the outline covers the full deck;
- every slide has a claim and proof object;
- predictive validity remains unproven;
- tuning-loop improvement remains unproven;
- no paid or external calls were made.

## Step 2: Draft Summary And Evidence Appendix

Created:

```text
docs/research/m6-approval-packet/executive-summary-v1.md
docs/research/m6-approval-packet/appendix-evidence-index-v1.md
```

Drafting choices:

- executive summary follows the requested decision-facing shape: decision
  requested, why this matters, what Barcarolle is, current evidence, remaining
  non-claims, approved-project work, budget and validation gates, and expected
  decision outcome;
- evidence appendix maps readable evidence labels to key numbers, canonical
  sources, and claim limits;
- V5 remains the long-form source of truth;
- path-level traceability points to the V5 evidence manifest instead of making
  raw internal paths the main reader experience;
- staffing, duration, budget ceiling, and approval path remain visible
  placeholders.

Acceptance evidence:

- the executive summary is independent and decision-facing;
- the evidence appendix is concise and traceable;
- neither artifact claims predictive validity or tuning-loop improvement;
- no paid or external calls were made.

## Step 3: Build The PPTX

Created:

```text
docs/research/m6-approval-packet/barcarolle-approval-deck-v1.pptx
```

Presentation workflow:

- used the Codex Presentations artifact-tool workflow in create mode;
- selected the `engineering-platform` profile because the packet is a
  technical benchmark/evaluation-platform approval story;
- created a thread-scoped presentation workspace under:

```text
outputs/manual-20260601-181938-m6/presentations/barcarolle-approval-packet/
```

- built 12 editable slides from artifact-tool slide modules;
- used only editable text, shapes, tables, and diagram lanes;
- used no imagegen, generated raster assets, logos, or identity assets;
- rendered per-slide PNG previews, layout JSON, and a contact sheet before
  copying only the final PPTX into the packet directory.

Build evidence:

- exported PPTX size: `62669` bytes;
- package contains 12 slide XML parts;
- artifact-tool render produced 12 preview slides and a contact sheet;
- layout QA passed with `0` errors after iteration;
- remaining layout warnings are tight-title/table-label warnings accepted after
  full-size rendered review because no visible clipping or collision remains.

Manual review notes:

- the first contact sheet exposed a real slide 4 workflow-label collision and
  slide 12 decision-box clipping;
- both were repaired in the slide source and rerendered;
- full-size spot checks reviewed slides 3, 4, 7, 9, and 12 after repair.

Acceptance evidence:

- PPTX exists at the expected path;
- the deck is editable and uses native text/shapes where practical;
- each slide has a clear claim and proof object;
- no slide depends on decorative generated imagery;
- the deck can be understood without V5 open beside it;
- the deck preserves the predictive-validity and tuning-loop non-claims;
- no paid or external calls were made.
