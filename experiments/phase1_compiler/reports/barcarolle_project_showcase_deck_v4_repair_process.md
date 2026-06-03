# Barcarolle Project Showcase Deck V4 Repair Process

Status: completed targeted repair, 2026-06-03.

## Scope

Executed:

```text
docs/experiments/barcarolle-project-showcase-deck-v4-argument-visual-terminology-repair-runbook.md
```

No paid ACUT solver calls, paid LLM calls, external reviewer calls, imagegen, or generated raster assets were used.

## Step-Level Execution

| Step | Evidence | Commit |
| --- | --- | --- |
| Lock V4 argument, terminology, evidence, and architecture | Created `argument-repair-v4.zh.md`, `terminology-reduction-v4.zh.md`, `evidence-accuracy-audit-v4.zh.md`, and `deck-architecture-v4.zh.md`. | `aafa17a1` |
| Draft V4 outline | Created `showcase-deck-outline-v4.zh.md`; residue and overclaim checks passed before PPTX work. | `e4a744e0` |
| Build V4 PPTX and QA reports | Exported `barcarolle-project-showcase-deck-v4.zh.pptx`; rendered all `11` slides; created reader-review, text-style, and visual QA reports. | `d3fc5305` |
| Commit V4 runbook artifact | Added the executed V4 repair runbook so PROCESS canonical links are not dangling. | `ad4e0795` |
| Closeout package | Updated README and PROCESS; created process, decision, and JSON closeout artifacts. | current closeout commit |

## Verification

| Check | Result |
| --- | --- |
| artifact-tool PPTX export | passed |
| slide PNG render | passed for all `11` slides |
| layout JSON extraction | passed for all `11` slides |
| contact sheet | `outputs/manual-20260603-showcase-v4-repair/presentations/barcarolle-project-showcase-deck-v4/preview/contact-sheet.png` |
| layout quality | `0` errors, `5` accepted warnings |
| full-size visual QA | passed for Slides `1`, `2`, `5`, `7`, `8`, `9`, `10`, `11` |
| forbidden residue check | `0` matches for V4 outline and extracted PPTX text |
| overclaim check | `0` matches for V4 outline and extracted PPTX text |
| local Downloads path check | `0` matches in project-showcase Markdown files |
| audit-ai-tropes scan | findings accepted as outline/diagram/technical-term false positives |
| PPTX zip integrity | passed |

## Evidence Boundary

The committed evidence supports:

- `120/120` planned cells;
- scoreability `1.0`;
- click source repair `30/30`;
- candidate MAE `0.209`;
- best simple aggregate baseline MAE `0.2149`;
- edge `0.0059`;
- `1000` random-control seeds;
- random beats/ties share `93.4%`.

The future random-control gate is `95.0%`, so V4 uses `93.4%` and states that this is below the future gate.

## Residual Risks

- V4 remains a presentation artifact and does not change experiment results or validation protocol status.
- Necessary mixed terminology remains in the deck for ACUT, release, harness, MAE, future holdout, rolling-origin, and dev/eval/canary.
- The current evidence remains traction only. Predictive validity and tuning-loop improvement remain future validation work.

## Recommended Next Action

Use V4 for reader review or circulation. Treat any next edit as a targeted presentation polish unless new committed evidence changes the claim boundary.
