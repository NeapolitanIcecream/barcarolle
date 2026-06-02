# Barcarolle Project Showcase Deck Rewrite Decision

Stop label: `barcarolle_project_showcase_deck_rewrite_complete`.

## Decision

The Chinese project-showcase deck rewrite is complete.

The new showcase deck supersedes the older Chinese approval-packet decks for
reader-facing presentation use. The older approval-packet materials remain
available as fact/reference artifacts, but the active Chinese presentation
package is now:

```text
docs/research/barcarolle-project-showcase-deck-zh/
```

## Artifact Locations

| Artifact | Path |
| --- | --- |
| PPTX deck | `docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v1.zh.pptx` |
| README | `docs/research/barcarolle-project-showcase-deck-zh/README.md` |
| Argument map | `docs/research/barcarolle-project-showcase-deck-zh/project-argument-map-v1.zh.md` |
| Related-work note | `docs/research/barcarolle-project-showcase-deck-zh/related-work-positioning-v1.zh.md` |
| Deck outline | `docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v1.zh.md` |
| Text and claim audit | `docs/research/barcarolle-project-showcase-deck-zh/text-and-claim-audit-v1.zh.md` |
| Visual review report | `docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v1.zh.md` |
| Process report | `experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_rewrite_process.md` |
| Machine-readable decision | `experiments/phase1_compiler/results/barcarolle_project_showcase_deck_rewrite_decision.json` |

## Boundary Status

| Item | Status |
| --- | --- |
| New showcase deck complete | `true` |
| Supersedes older Chinese approval-packet decks for presentation use | `true` |
| Presents problem, method, current effects, limits, and future work | `true` |
| Related work included in main narrative | `true` |
| Agent License included | `true` |
| Agent Tuning included | `true` |
| Predictive validity established | `false` |
| Tuning-loop improvement established | `false` |
| Process-language audit passed | `true` |
| Visual review passed | `true` |
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

- required Markdown forbidden-language, overclaim, and local-path checks;
- extracted PPTX text forbidden-language, overclaim, and local-path checks;
- `git diff --check`;
- PPTX zip integrity check;
- artifact-tool render of all 15 slides;
- contact sheet and selected full-size preview review;
- artifact-tool layout checker with `0` errors;
- engineering-platform presentation scorecard with `42/45`.

The final deck uses editable artifact-tool text and shapes. No decorative
generated images, public browsing, paid LLM calls, paid ACUT calls, or external
reviewer calls were used.

## Remaining Work

Before circulation, review the new deck for audience-specific emphasis. Do not
restore approval-request framing, internal process vocabulary, or unsupported
claims about predictive validity or tuning-loop improvement.

