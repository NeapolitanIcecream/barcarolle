# Barcarolle 项目展示 Deck V4 文本风格审计

状态：V4 text and claim audit，2026-06-03。

## Scope

审计对象：

- `docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v4.zh.md`
- `docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v4.zh.pptx` 的抽取文本

PPTX 文本抽取位置：

```text
outputs/manual-20260603-showcase-v4-repair/presentations/barcarolle-project-showcase-deck-v4/qa/v4-pptx-text.txt
```

## Required Checks

| Check | Target | Result |
| --- | --- | --- |
| forbidden residue pattern | V4 outline | `0` matches |
| forbidden residue pattern | extracted V4 PPTX text | `0` matches |
| overclaim pattern | V4 outline and extracted PPTX text | `0` matches |
| local Downloads path | project-showcase Markdown files | `0` matches |
| PPTX zip integrity | V4 PPTX | passed |

The evidence audit rejected a future-gate pass claim for the random-control result. V4 uses `93.4%` and states that this is below the future `95.0%` gate.

## Scanner Findings

`audit-ai-tropes` scanner findings:

| Source | Finding | Disposition |
| --- | --- | --- |
| V4 outline | `short punchy fragment run` | Accepted false positive from slide-outline metadata, headings, and table-like page structure. |
| V4 outline | stock diction: `harness` | Accepted technical term required by ACUT boundary explanation. |
| V4 PPTX text | Unicode decoration: `→` | Accepted intentional diagram connector in editable slides. |
| V4 PPTX text | stock diction: `harness` | Accepted technical term required by ACUT boundary explanation. |

## Accepted Technical Terms

| Term | Reason |
| --- | --- |
| ACUT | Defined on Slide 1 as Agent Configuration Under Test; central boundary object. |
| benchmark | Standard evaluation term; used sparingly with Chinese explanation. |
| release | Refers to a frozen/versioned benchmark package; Chinese alternatives are longer and less precise. |
| harness | ACUT-owned execution wrapper; important boundary term. |
| prompt / tools / model / budget | User-facing configuration dimensions for ACUT ownership. |
| solver workspace / verifier workspace | Boundary terms for execution isolation. |
| hidden oracle | Verifier-side validation material; retained for precision. |
| source / oracle | Source-quality and verifier terms used in existing Barcarolle reports. |
| MAE | Defined on Slide 4 as average absolute error. |
| W_r(a) | Formal estimand notation from the proposal report. |
| selector | Retained where it names the task-selection algorithm object; paired with `任务选择器`. |
| fallback | Retained where it names support-limited fallback behavior; paired with `兜底来源`. |
| future holdout / rolling-origin | Validation route names; Slide 9 explains their role. |
| dev / eval / canary | Tuning split names; Slide 11 pairs them with Chinese explanations. |
| Agent License / Agent Tuning | Product/use-case names. |

## Claim Boundary

V4 preserves these boundaries:

- predictive validity remains unproven;
- tuning-loop improvement remains unproven;
- adapter differences are reported as named ACUT configuration evidence;
- random-control evidence is `93.4%` beats/ties across `1000` seeds and remains below the future `95.0%` gate;
- no paid ACUT calls, paid LLM calls, external reviewer calls, imagegen, or generated raster assets were used for the revision.
