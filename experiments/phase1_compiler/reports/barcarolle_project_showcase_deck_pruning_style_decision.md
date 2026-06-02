# Barcarolle Project Showcase Deck Pruning And Style Polish Decision

Stop label: `barcarolle_project_showcase_deck_pruning_style_complete`.

## Decision

The Chinese project-showcase deck pruning and style polish is complete.

The active Chinese project-showcase deck is now:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v2.zh.pptx
```

V1 remains reference material. The older Chinese approval-packet materials also
remain fact/reference artifacts, not the active deck structure.

## What Changed

The project-showcase deck was pruned at page level, not only redrawn.

- V1 had `15` slides.
- V2 has `14` slides.
- V1 Slide 5 `项目位置` was deleted after the page-responsibility audit.
- Useful Slide 5 positioning content was merged into V2 Slide 4 `相关工作`
  and V2 Slide 6 `方法`.
- Retained slide title labels were preserved.
- Reader-facing binary-reframe language was removed from the revised outline
  and extracted PPTX text.

## Artifact Locations

| Artifact | Path |
| --- | --- |
| Page responsibility matrix | `docs/research/barcarolle-project-showcase-deck-zh/page-responsibility-matrix-v2.zh.md` |
| Duplication audit | `docs/research/barcarolle-project-showcase-deck-zh/duplication-audit-v2.zh.md` |
| V2 outline | `docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md` |
| V2 PPTX | `docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v2.zh.pptx` |
| Text style audit | `docs/research/barcarolle-project-showcase-deck-zh/text-style-audit-v2.zh.md` |
| Visual QA report | `docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v2.zh.md` |
| Process report | `experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_pruning_style_process.md` |
| Machine-readable decision | `experiments/phase1_compiler/results/barcarolle_project_showcase_deck_pruning_style_decision.json` |

## Boundary Status

| Item | Status |
| --- | --- |
| V2 complete | `true` |
| V2 slide count | `14` |
| Deleted V1 slide | `Slide 5 项目位置` |
| Retained title labels preserved | `true` |
| Binary-reframe audit passed | `true` |
| Process-language audit passed | `true` |
| Visual repetition reduced | `true` |
| Predictive validity established | `false` |
| Tuning-loop improvement established | `false` |
| Paid ACUT calls used | `0` |
| Paid LLM calls used | `0` |
| External reviewer calls used | `0` |
| Public browsing used | `false` |
| Imagegen or generated raster assets used | `false` |
| Score tables changed | `false` |
| Selected task IDs or split labels changed | `false` |
| Source eligibility changed | `false` |
| Task statements or hidden-oracle material changed | `false` |

## QA Summary

Passed:

- V2 PPTX extraction reported `14` slides and the expected retained title
  labels.
- `unzip -t` passed for the target PPTX.
- Artifact-tool rendered all slides and generated a contact sheet.
- `check_layout_quality.mjs --warn-only` reported `0` errors.
- Contact sheet and selected full-size previews were inspected.
- Required binary-reframe, process-language, overclaim, and local-path checks
  passed on the V2 outline and extracted V2 PPTX text.
- README handoff checks passed.
- `git diff --check` passed.

Accepted:

- `11` tight-text layout warnings remain for compact labels; rendered previews
  were inspected and did not show clipping or incoherent overlap.
- `audit-ai-tropes` scanner flagged the technical term `harness`; it remains
  because the ACUT boundary needs that term.

## Why It Matters

The deck now reads as a more deliberate project-showcase sequence. Each page
has a distinct reader-facing role, the repeated release/freeze/validation
process strips have been separated by purpose, and the visible text no longer
uses the most obvious binary-reframe patterns.

## Remaining Work

Review V2 for audience-specific emphasis before circulation. Do not restore
deleted duplicate pages or binary-reframe phrasing. Predictive validity and
tuning-loop improvement remain future validation work.
