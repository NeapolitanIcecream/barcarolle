# Barcarolle Project Showcase Deck V3 Revision Decision

Stop label: `barcarolle_project_showcase_deck_v3_revision_complete`.

## Decision

The V3 reader-centered revision is complete.

The active Chinese project-showcase deck is now:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx
```

V1 and V2 remain reference/input artifacts. V5 remains the long-form factual and
claim-boundary source.

## Final Slide List

| Slide | Title label | Claim |
| --- | --- | --- |
| 1 | 项目定位 | Barcarolle compiles a target-repo benchmark release and defines ACUT on first use. |
| 2 | 问题与代价 | General scores do not directly estimate future work in this repository. |
| 3 | 相关工作与缺口 | Adjacent work provides task/quality/freshness/scale/environment inputs; Barcarolle studies release evidence. |
| 4 | 研究目标 | The north star is outcome-unseen predictive validity, with MAE explained plainly. |
| 5 | 方法 | Candidate tasks are compiled into an auditable release. |
| 6 | 执行边界 | Solver and verifier workspaces are separated; hidden oracle appears only on the verifier side. |
| 7 | 算法问题 | Task selection changes the target-repo estimate, so support/fallback/baselines are algorithm variables. |
| 8 | 当前证据 | Current evidence supports continued optimization while keeping claims limited. |
| 9 | 研究路线 | Next work centers task-selection algorithm evolution and outcome-unseen validation gates. |
| 10 | 产品化方向 | Agent License can consume repo-level evidence status for deployment governance. |
| 11 | 产品化方向 | Agent Tuning can consume protected dev/eval/canary feedback while preserving validation material. |

## V2 Merge And Delete Map

| V2 content | V3 treatment |
| --- | --- |
| Slides 2-3 | Merged into V3 Slide 2 `问题与代价`. |
| Slide 4 | Rewritten as V3 Slide 3 with full related-work names and concrete gaps. |
| Slide 5 | Rewritten as V3 Slide 4 with formula and MAE explanation. |
| Slide 6 | Rewritten as V3 Slide 5 with a single compiler workflow. |
| Slide 7 | Rewritten as V3 Slide 6 with Chinese boundary copy. |
| Slides 8-9 | Merged into V3 Slide 7 `算法问题`. |
| Slide 10 | Reorganized as V3 Slide 8 `当前证据`. |
| Slide 11 | Removed as standalone page; useful content absorbed into Slides 8-9. |
| Slide 12 | Recentered as V3 Slide 9 around task-selection algorithm evolution. |
| Slides 13-14 | Kept as distinct V3 Slides 10-11 with positive use-case language and redrawn diagrams. |

## User Feedback Resolution

| Feedback group | Resolution |
| --- | --- |
| ACUT explanation and awkward first-slide diagram | Slide 1 defines ACUT and redraws the target repo / release / ACUT relationship. |
| Problem pages too abstract and overlapping | Slide 2 merges the gap and cost pages into a single decision problem. |
| Related-work names and gaps too abstract | Slide 3 uses full names, adds SWE-Bench++, and grounds each gap in source sanity. |
| Research target and MAE unclear | Slide 4 uses a formula block plus plain MAE explanation and removes unclear cards. |
| Method and boundary too terminology-heavy | Slides 5-6 reduce process residue and translate boundary copy into Chinese. |
| Algorithm/evidence pages too process-heavy | Slides 7-8 organize algorithm and evidence by reader question. |
| Research route missed selector evolution | Slide 9 centers selector evolution and treats freeze/baseline/success criteria as validation gates. |
| Productization pages used negative boundary language and malformed visuals | Slides 10-11 use positive evidence-interface language and redraw governance/feedback flows. |

## Source Sanity Status

Related-work source sanity passed. Checked sources:

- SWE-bench paper;
- SWE-bench Verified introduction;
- SWE-bench Verified quality follow-up;
- SWE-bench-Live;
- SWE-Bench++;
- SWE-smith;
- R2E-Gym.

No unsupported related-work claim was found.

## Formula Rendering

PowerPoint native equation export was not used. Slide 4 uses an editable
typeset text math block with `Wᵣ(a) = E[success(a, future work in repo r)]`.
The rendered formula is visually clearer than the V2 raw plain-text formula and
was accepted in visual QA.

## QA Status

Passed:

- artifact-tool PPTX export;
- slide PNG render for all `11` slides;
- layout JSON extraction for all `11` slides;
- contact-sheet review;
- full-size review of Slides `1` through `11`;
- explicit diagram sanity checks for Slides `1`, `5`, `6`, `10`, and `11`;
- `check_layout_quality.mjs --warn-only`: `0` errors, `15` accepted warnings;
- final extracted PPTX text residue and overclaim checks;
- `audit-ai-tropes` heuristic scan with accepted false positives;
- `unzip -t` on final PPTX.

## Claim Boundary

V3 keeps these boundaries:

- predictive validity remains unproven;
- Agent Tuning effect remains unproven;
- adapter differences are named ACUT configuration evidence;
- current MAE evidence is traction with a small edge;
- no new performance claim was added from old exploratory data.

## Residual Risks

- Slide 4 formula is editable text rather than a native PowerPoint equation.
- The deck still mixes Chinese with necessary technical English terms; the
  accepted technical terms are listed in `text-style-audit-v3.zh.md`.
- This is a presentation artifact. It does not change experiment results,
  paid-run readiness, or validation protocol status.

## Recommended Next Action

Use V3 for reader review or circulation. Any future revision should stay within
the current claim boundary and avoid restoring standalone process diagnostics
or product-boundary negative phrasing.
