# Barcarolle Project Showcase Deck Pruning And Style Polish Process

Status: in progress, 2026-06-02.

Runbook:

```text
docs/experiments/barcarolle-project-showcase-deck-pruning-style-polish-runbook.md
```

## Step 0 - Preflight And Text Extraction

Branch and revision:

```text
branch: codex/restart-benchmark-compiler
head: fa7325bc33c7adbe0f2118cd15afef22f2327fc4
date: 2026-06-02 11:40:06 CST
```

Initial worktree status:

```text
## codex/restart-benchmark-compiler...origin/codex/restart-benchmark-compiler [ahead 45]
 M PROCESS.md
 M docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? docs/experiments/barcarolle-project-showcase-deck-pruning-style-polish-runbook.md
?? docs/experiments/barcarolle-project-showcase-deck-rewrite-runbook.md
```

The existing modified `PROCESS.md` and roadmap entries already point to this
runbook as the next action. They are treated as pre-existing worktree changes;
later commits should stage only runbook-execution hunks.

Input availability:

| Input | Status |
| --- | --- |
| `AGENTS.md` | present and read |
| `PROCESS.md` | present and read |
| `docs/research/barcarolle-proposal-report-v5.md` | present and read for claim boundaries |
| `docs/research/barcarolle-project-showcase-deck-zh/README.md` | present and read |
| `docs/research/barcarolle-project-showcase-deck-zh/project-argument-map-v1.zh.md` | present and read |
| `docs/research/barcarolle-project-showcase-deck-zh/related-work-positioning-v1.zh.md` | present and read |
| `docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v1.zh.md` | present and read |
| `docs/research/barcarolle-project-showcase-deck-zh/text-and-claim-audit-v1.zh.md` | present and read |
| `docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v1.zh.md` | present and read |
| `docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v1.zh.pptx` | present and extracted |
| `experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_rewrite_decision.md` | present and read |

Additional evidence-boundary inputs were checked for the current metric,
fallback, adapter, and claim-limit values:

```text
docs/research/phase-1-proposal-evidence-package.md
docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_decision.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md
```

V1 PPTX extraction:

```text
scratch workspace: outputs/manual-20260602-114006-showcase-pruning/presentations/barcarolle-project-showcase-deck-pruning-style/
extracted text: outputs/manual-20260602-114006-showcase-pruning/presentations/barcarolle-project-showcase-deck-pruning-style/qa/v1-pptx-text.txt
slide inventory: outputs/manual-20260602-114006-showcase-pruning/presentations/barcarolle-project-showcase-deck-pruning-style/qa/v1-slide-inventory.json
slide count: 15
```

V1 visible title labels:

| Slide | Title label |
| --- | --- |
| 1 | 项目定位 |
| 2 | 问题 |
| 3 | 代价 |
| 4 | 相关工作 |
| 5 | 项目位置 |
| 6 | 研究目标 |
| 7 | 方法 |
| 8 | 执行边界 |
| 9 | 算法问题 |
| 10 | 算法环境 |
| 11 | 当前效果 |
| 12 | 限制 |
| 13 | 研究路线 |
| 14 | 产品化方向 |
| 15 | 产品化方向 |

Initial style scan:

| Source | Binary-reframe matches |
| --- | ---: |
| V1 PPTX extracted text | 8 |
| V1 outline | 3 |

Representative V1 PPTX matches include direct reader-facing sentences such as
`Barcarolle 是 benchmark 编译器，不是 ACUT harness。`, `问题不是通用 benchmark
无用，而是它们不直接给出仓库级未来估计。`, `Barcarolle 的输出不是原始任务列表，
而是带有 source、oracle、split、fallback、ACUT 边界和验证规则的 release。`,
and `这些是 traction evidence，不是 predictive-validity result。`

Initial repetition scan:

- Release/freeze/validation vocabulary appears heavily on slides 1, 5, 6, 7,
  and 13.
- Slides 5, 7, and 13 all show a multi-stage process from supply or freeze to
  validation/result.
- Slides 10 and 13 both cover baselines, selector variants, and future
  validation vocabulary.
- Slides 11 and 12 both use MAE/fallback/support facts; slide 11 frames current
  traction while slide 12 frames weaknesses and repairs.
- Slides 14 and 15 share the same top-level title label and both describe
  productization interfaces, but their product roles are governance evidence
  and tuning feedback.

No paid ACUT calls, paid LLM calls, external reviewer calls, public browsing,
image generation, test edits, score-table edits, task edits, split-label edits,
or hidden-oracle changes were made in Step 0.

## Step 1 - Page Responsibility Matrix

Created:

```text
docs/research/barcarolle-project-showcase-deck-zh/page-responsibility-matrix-v2.zh.md
```

Acceptance evidence:

- The matrix covers all `15` V1 slides.
- Target V2 length is set before deck editing: `14` slides.
- V1 Slide 5 `项目位置` is marked `delete / merge` because its positioning role
  overlaps with Slide 1, Slide 4, and Slide 7.
- The useful Slide 5 layer-positioning content is assigned to Slide 4
  `相关工作` and Slide 7 `方法`.
- Retained slide title labels are listed and preserved.
- The matrix explicitly evaluates the required overlap suspects:
  - Slide 1 vs Slide 5;
  - Slides 5/6/7/13 around release/freeze/validation workflow;
  - Slide 10 vs Slide 13 around baselines and future validation;
  - Slide 11 vs Slide 12 around MAE edge, fallback, and support;
  - Slide 14 vs Slide 15 around productization direction.
- Retained slides have distinct roles:
  - Slide 6 defines the estimand and MAE;
  - Slide 7 is the only complete compiler workflow;
  - Slide 10 is the current algorithm-evaluation environment;
  - Slide 13 is the future validation protocol;
  - Slide 14 is deployment-governance evidence;
  - Slide 15 is protected tuning feedback.

No paid ACUT calls, paid LLM calls, external reviewer calls, public browsing,
image generation, test edits, score-table edits, task edits, split-label edits,
or hidden-oracle changes were made in Step 1.
