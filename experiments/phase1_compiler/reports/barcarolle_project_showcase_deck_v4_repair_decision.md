# Barcarolle Project Showcase Deck V4 Repair Decision

Stop label: `barcarolle_project_showcase_deck_v4_repair_complete`.

## Decision

The V4 argument, visual, and terminology repair is complete.

The active Chinese project-showcase deck is now:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v4.zh.pptx
```

V3, V2, and V1 remain reference/input artifacts. V5 remains the long-form factual and claim-boundary source.

## Final Slide List

| Slide | Title label | Claim |
| --- | --- | --- |
| 1 | 项目定位 | Barcarolle compiles a target-repo evaluation release and defines ACUT on first use. |
| 2 | 问题与代价 | General scores do not directly estimate future work in this repository. |
| 3 | 相关工作与缺口 | Adjacent work provides task/quality/freshness/scale/environment inputs; Barcarolle studies release evidence. |
| 4 | 研究目标 | The north star is outcome-unseen predictive validity, with MAE explained plainly. |
| 5 | 方法 | Candidate tasks are compiled into an auditable release. |
| 6 | 执行边界 | Solver and verifier workspaces are separated; hidden oracle appears only on the verifier side. |
| 7 | 算法问题 | The task selector determines the finite-budget estimate. |
| 8 | 当前证据 | Current evidence supports continued selector optimization while keeping claims limited. |
| 9 | 研究路线 | Next work improves the selector and freezes validation routes. |
| 10 | 证据治理 | Agent License can consume repo-level evidence status for deployment governance. |
| 11 | 调优回路 | Agent Tuning can consume protected dev/eval/canary feedback while preserving validation material. |

## Repairs

| Slide | Repair |
| --- | --- |
| 1 | Redrew the right-side target repo / release / ACUT relationship and removed accidental-looking connector dots. |
| 2 | Replaced the floating gap badge with a bridge band connected to a shared consequence rail. |
| 5 | Removed unclear bottom shapes and process wording; added a readable certification checklist. |
| 7 | Rebuilt the argument around finite-budget estimation and selector rules. Old weighted failure appears only as a small historical diagnostic. |
| 8 | Rebuilt the evidence slide around protocol feasibility, source repair, selector traction, and claim boundary. |
| 9 | Aligned the algorithm-evolution loop on a grid and separated validation gates. |
| 10 | Removed the detached bottom output strip and kept positive governance use-case language. |
| 11 | Rebuilt the feedback loop as one path from configuration change to regression signal, with future-validation material isolated. |

## Slide 7/8 Argument Change

V4 no longer uses the old weighted design failure as the main proof that algorithm design matters. The new logic is:

1. A repo-specific release is a finite-budget estimator of future target-repo work.
2. The task selector decides which observations enter that estimator.
3. Sample support, fallback, source caps, slice stability, adapter reporting, and baseline comparison can change the estimate or its credibility.
4. Task selection is therefore the benchmark compiler's core algorithm problem.
5. Current evidence shows feasibility and traction, not predictive validity.

## Evidence Accuracy

The `>=95%` claim was rejected for V4. The committed reports support `93.4%` beats/ties across `1000` same-budget random selections. The future success gate is `95.0%`, so V4 states that the current random-control result is below the future gate.

Verified deck evidence:

- `120/120` planned cells;
- scoreability `1.0`;
- click `30/30` tasks repaired;
- MAE `0.209`;
- best simple aggregate baseline `0.2149`;
- edge `0.0059`;
- random-control seed count `1000`;
- random beats/ties share `93.4%`.

## Terminology Reduction

V4 translates or explains the highest-load terms across the deck:

- target-repo -> 目标仓库;
- selector -> 任务选择器 where space permits;
- support -> 样本支撑;
- fallback -> 兜底来源 where space permits;
- baseline -> 对照基线;
- prediction gap -> 预测缺口;
- regression signal -> 回归信号.

Accepted remaining terms are documented in `text-style-audit-v4.zh.md`.

## QA Status

Passed:

- artifact-tool PPTX export;
- slide PNG render for all `11` slides;
- layout JSON extraction for all `11` slides;
- contact-sheet review;
- full-size review of Slides `1`, `2`, `5`, `7`, `8`, `9`, `10`, and `11`;
- explicit diagram sanity checks for Slides `1`, `2`, `5`, `7`, `9`, `10`, and `11`;
- `check_layout_quality.mjs --warn-only`: `0` errors, `5` accepted warnings;
- final extracted PPTX text residue and overclaim checks;
- `audit-ai-tropes` heuristic scan with accepted false positives;
- `unzip -t` on final PPTX.

## Claim Boundary

V4 keeps these boundaries:

- predictive validity remains unproven;
- Agent Tuning effect remains unproven;
- adapter differences are named ACUT configuration evidence;
- current MAE evidence is traction with a small edge;
- current random-control evidence is below the future gate;
- no new performance claim was added from old exploratory data.

## Residual Risks

- This is a presentation artifact. It does not change experiment results, paid-run readiness, or validation protocol status.
- Necessary technical terms remain in mixed Chinese/English form.
- The `0.0059` MAE edge is still too small for a validity claim.
- The current candidate remains support- and fallback-limited for future primary claims.

## Recommended Next Action

Use V4 for reader review or circulation. If new feedback arrives, treat the next edit as targeted presentation polish unless the factual evidence package changes.
