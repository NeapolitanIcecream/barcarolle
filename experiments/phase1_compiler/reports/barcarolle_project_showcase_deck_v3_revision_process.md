# Barcarolle Project Showcase Deck V3 Revision Process

Date: 2026-06-02 CST

Runbook:

```text
docs/experiments/barcarolle-project-showcase-deck-v3-reader-centered-revision-runbook.md
```

## Step 0 - Intake And Architecture

Commit:

```text
f3c49d5f Add showcase deck V3 revision plan
```

Created or committed:

```text
docs/experiments/barcarolle-project-showcase-deck-rewrite-runbook.md
docs/experiments/barcarolle-project-showcase-deck-pruning-style-polish-runbook.md
docs/experiments/barcarolle-project-showcase-deck-v3-reader-centered-revision-runbook.md
docs/research/barcarolle-project-showcase-deck-zh/slide-by-slide-reader-review-handoff-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/deck-architecture-v3.zh.md
```

Acceptance evidence:

- Read `AGENTS.md`, `PROCESS.md`, the V3 revision runbook, the V3 reader
  feedback handoff, V2 package audits, V5 proposal facts, and M3/M4 evidence
  support.
- Inspected V2 PPTX extracted text and contact sheet.
- Locked the V3 architecture at `11` slides.
- Recorded V2 merge/delete decisions: merge V2 Slides 2/3, merge V2 Slides
  8/9, absorb V2 Slide 11 into evidence/route, keep Agent License and Agent
  Tuning as separate use cases.

## Step 1 - Source Sanity And Outline

Commit:

```text
bb04fca2 Draft showcase deck V3 outline
```

Created:

```text
docs/research/barcarolle-project-showcase-deck-zh/related-work-source-sanity-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v3.zh.md
```

Acceptance evidence:

- Related-work sanity checked primary or near-primary sources for SWE-bench,
  SWE-bench Verified, SWE-bench quality follow-up, SWE-bench-Live,
  SWE-Bench++, SWE-smith, and R2E-Gym.
- The V3 outline wrote full related-work names and concrete unresolved issues.
- The outline passed required forbidden-language, overclaim, local-path, and
  whitespace checks.
- `audit-ai-tropes` scanner findings on the outline were limited to outline
  metadata/structure and accepted technical terms.

## Step 2 - PPTX Build And QA

Commit:

```text
fc4fcbfb Build showcase deck V3
```

Created:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx
docs/research/barcarolle-project-showcase-deck-zh/reader-review-audit-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/text-style-audit-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v3.zh.md
```

Presentation workspace:

```text
outputs/019e8755-8880-7371-835c-73415d32af4a/presentations/barcarolle-project-showcase-deck-v3/
```

Acceptance evidence:

- Used the Presentations artifact-tool workflow in create-from-existing-content
  mode with the `engineering-platform` profile.
- Built `11` editable slides with text, shapes, rules, tables, and diagram
  primitives; no generated raster images, imagegen, logos, or external assets.
- Exported final PPTX through artifact-tool.
- Rendered all slides to PNG, generated layout JSON, and generated a contact
  sheet.
- Full-size slide review inspected Slides 1 through 11.
- `check_layout_quality.mjs --warn-only` reported `0` errors and `15` tight
  text warnings; rendered warning areas were visually checked and accepted.
- Required diagram sanity checks passed for Slides 1, 5, 6, 10, and 11.
- Final extracted PPTX text passed forbidden-language and overclaim checks.
- `unzip -t` passed for the final PPTX.

## Step 3 - Handoff And Closeout

Updated:

```text
docs/research/barcarolle-project-showcase-deck-zh/README.md
PROCESS.md
```

Created:

```text
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_v3_revision_process.md
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_v3_revision_decision.md
experiments/phase1_compiler/results/barcarolle_project_showcase_deck_v3_revision_decision.json
```

Closeout checks:

- Final deck path: `docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx`.
- Final slide count: `11`.
- No paid ACUT calls, paid LLM calls, external reviewer calls, imagegen, or
  generated raster assets were used.
- No score tables, selected task IDs, split labels, source eligibility, task
  statements, hidden-oracle material, or completed experiment decisions were
  changed.
