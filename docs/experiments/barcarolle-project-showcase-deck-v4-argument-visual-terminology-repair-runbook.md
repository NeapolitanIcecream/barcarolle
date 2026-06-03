# Barcarolle Project Showcase Deck V4 Argument, Visual, And Terminology Repair Runbook

Status: Chinese project-showcase deck V4 targeted repair runbook, 2026-06-03.

## Goal

Revise the active Chinese project-showcase deck from V3 to V4 by repairing the
remaining reader-facing weaknesses:

```text
1. Rebuild the Slide 7/8 argument so the algorithm problem is not justified by
   a deliberately weak or failed old design.
2. Redraw malformed or weak diagrams on Slides 1, 2, 5, 9, 10, and 11.
3. Reduce terminology load across the whole deck.
```

V4 is a targeted repair. Preserve the overall V3 story shape unless a local
slide merge or title adjustment is needed to make the argument clearer.

Source deck:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx
```

Target deck:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v4.zh.pptx
```

Plain-language target:

```text
把 V3 修成更像可展示的版本：图形不再像代码临时画错，算法问题不再靠旧失败
设计立论，术语能翻译就翻译，必须保留的术语首次出现时解释。
```

## Boundary

Allowed:

- create V4 files under `docs/research/barcarolle-project-showcase-deck-zh/`;
- keep the V3 `11`-slide structure, or make a small local adjustment if the V4
  architecture note justifies it;
- rewrite Slides 7 and 8 at argument level;
- redraw all diagrams and layout objects on the affected slides;
- reduce English terminology and add short in-slide explanations for necessary
  terms;
- verify the random-control and MAE evidence numbers against committed reports;
- update `README.md` and `PROCESS.md` after V4 succeeds;
- create process and decision closeout artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- broad literature review or new recommendation gathering;
- changing score tables, selected task IDs, split labels, source eligibility,
  task statements, hidden-oracle material, or completed experiment decisions;
- adding new performance claims from old exploratory data;
- claiming predictive validity has been established;
- claiming Barcarolle has already improved an agent tuning loop;
- claiming adapter differences prove model-only superiority;
- using `imagegen`, decorative generated images, abstract AI art, or generated
  raster assets;
- leaving prompt-like instructions, process critique, or runbook language in
  reader-facing slides;
- using direct binary-reframe phrasing such as `不是……而是……` or
  `是……不是……`;
- using product-boundary phrasing such as `但不负责` or `不接管`;
- using the old weighted-design failure as the main proof that algorithm design
  matters.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/research/barcarolle-proposal-report-v5.md
docs/research/barcarolle-project-showcase-deck-zh/README.md
docs/research/barcarolle-project-showcase-deck-zh/deck-architecture-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/reader-review-audit-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/text-style-audit-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_v3_revision_decision.md
```

Use for evidence accuracy:

```text
docs/research/phase-1-proposal-evidence-package.md
docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
```

Use for source and related-work boundaries if needed:

```text
docs/research/barcarolle-project-showcase-deck-zh/related-work-source-sanity-v3.zh.md
```

Do not mention local `Downloads` paths in reader-facing outputs.

## User Feedback To Address

The executor must treat the following as the V4 reader-review input:

- Slide 1: the right-side diagram still looks like it has a drawing error.
- Slide 2: the `Prediction Gap` visual is unattractive, and the relationship
  between the top diagram and the three lower decision boxes is unclear.
- Slide 5: the six small bottom shapes are unclear, and the bottom line contains
  process-like wording.
- Slide 7: there is a layout problem. More importantly, proving the algorithm
  problem by showing a worse old algorithm is not a good argument.
- Slide 8: the content problem is similar to Slide 7. It should not rely on the
  failed old weighted design as the main proof.
- Slide 9: the left-side graphic is misaligned.
- Slide 10: there is a layout problem.
- Slide 11: the graphic still looks incorrectly drawn.
- Overall: almost every slide carries too much terminology.

## V4 Argument Repair

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/argument-repair-v4.zh.md
```

This file must state the new logic for Slides 7 and 8 before any PPTX editing.

Required argument:

```text
1. A repo-specific benchmark release is a finite-budget estimator of future
   target-repo work.
2. The task selector decides which limited observations enter that estimator.
3. Source support, fallback, source caps, slice stability, adapter reporting,
   and baseline comparison can change the estimate or its credibility.
4. Therefore task selection is the benchmark compiler's core algorithm problem.
5. Current evidence shows the comparison environment exists and has traction,
   but it does not establish predictive validity.
```

What to do with old weighted-design failure:

- It may appear only as a small historical diagnostic or backup note.
- It must not be the main proof of research necessity.
- If retained, explain it as evidence that naive profile matching can be
  fragile under sparse support, not as proof that "any worse algorithm makes the
  problem real."

What to do with random-control evidence:

- Verify the exact committed value before writing it into the deck.
- Current committed reports appear to support `93.4%` beats/ties out of `1000`
  same-budget random selections.
- The M4 validation hardening gate records that this is below the future
  `95.0%` gate.
- Do not write `>=95%` unless a committed report proves that exact value.
- If there is a perceived mismatch between user memory and committed evidence,
  record it in the V4 evidence audit and use the committed value in PPT text.

## Expected V4 Architecture

Target `11` slides, preserving V3's high-level sequence:

1. 项目定位
2. 问题与代价
3. 相关工作与缺口
4. 研究目标
5. 方法
6. 执行边界
7. 算法问题
8. 当前证据
9. 研究路线
10. Agent License
11. Agent Tuning

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/deck-architecture-v4.zh.md
```

The architecture note must document each V4 slide's role, the V3 source slide,
the V4 repair, and whether the slide's terminology was reduced.

## Slide-Specific Repair Requirements

### Slide 1 - Project Positioning

Redraw the right-side visual from scratch.

Requirements:

- Keep first-use ACUT explanation.
- Do not use `被测 ACUT`.
- Use a clean, aligned relationship:

```text
目标仓库 -> 仓库级评测 release -> ACUT 运行与结果
```

- Show ownership boundaries in simple text:
  - Barcarolle organizes release evidence;
  - ACUT owns harness / prompt / tools / model / budget.
- Remove decorative dots or connector endpoints that look accidental.

### Slide 2 - Problem And Cost

Repair the visual logic.

Requirements:

- Replace the floating `Prediction Gap` badge with a clear bridge or gap band.
- The lower three decision consequences must visibly flow from the top gap:
  deployment choice, configuration tuning, governance decision.
- Use connector lines, a shared rail, or a single cause-to-effect layout.
- Avoid treating the lower three boxes as unrelated cards.

### Slide 5 - Method

Remove unclear bottom material.

Requirements:

- Delete the six small bottom shapes unless they are turned into a clearly
  labeled, readable certification checklist.
- Delete process-like wording such as `这个流程只画一次`.
- Keep only the workflow and one concise explanation of why certification,
  target profile, selection, split, fallback, and release metadata matter.
- Reduce English stage labels where possible.

### Slide 7 - Algorithm Problem

Rewrite the slide's argument.

Requirements:

- Do not center the slide on the old weighted failure chart.
- Center the slide on the estimator problem:

```text
有限预算 -> 任务选择 -> 估计偏差/覆盖不足/不稳定 -> 需要 selector 规则
```

- Use Chinese labels where possible:
  - `任务选择器` for selector;
  - `样本支撑` for support;
  - `兜底来源` or `fallback` with one short explanation;
  - `对照基线` for baseline;
  - `切片稳定性` for slice stability.
- If old weighted numbers are kept, place them as a small "历史诊断" note, not
  the main proof object.

### Slide 8 - Current Evidence

Rebuild the evidence slide around traction, not process data or bad-algorithm
proof.

Requirements:

- Recommended reader questions:
  - `协议能跑通吗？`
  - `source 质量能修复吗？`
  - `选择器是否有初步信号？`
  - `现在还不能证明什么？`
- Keep only evidence that answers those questions.
- Random-control evidence should be more prominent than old weighted failure if
  space is limited.
- State the evidence boundary plainly:

```text
这些结果支持继续优化 selector；还不能证明预测效度。
```

- Avoid table headers left in English.

### Slide 9 - Research Route

Repair alignment and reduce terminology.

Requirements:

- Align the left algorithm-evolution loop on a clear grid.
- Use Chinese labels for the major nodes.
- Treat `future holdout` / `rolling-origin` as validation route labels, with
  short Chinese explanations.
- Keep release freezing, named ACUTs, baselines, and success criteria as gates,
  not as the main research contribution.

### Slide 10 - Agent License

Repair layout.

Requirements:

- Integrate the bottom output strip into the main flow or remove it.
- Avoid a detached annotation-box look.
- Keep positive use-case language.
- Do not use `但不负责`, `不接管`, or similar negative boundary phrasing.

### Slide 11 - Agent Tuning

Redraw the feedback loop.

Requirements:

- Make the connection path visually unambiguous:

```text
配置变更 -> dev feedback -> eval release -> canary release -> regression signal
```

- Show protected future-validation material as clearly isolated but not as a
  broken or floating connector target.
- Use Chinese labels where possible; keep `dev / eval / canary` only if paired
  with a short explanation.

## Terminology Reduction

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/terminology-reduction-v4.zh.md
```

The file must include a slide-by-slide terminology audit with:

| Slide | Heavy terms in V3 | V4 replacement or explanation | Accepted terms |
| --- | --- | --- | --- |

Rules:

- Translate terms when the Chinese replacement is clear.
- Keep essential terms only when translation would reduce precision.
- Explain essential terms on first use.
- Avoid multiple unexplained English terms in the same sentence.
- Table headers in Chinese unless there is a strong reason.

Suggested replacements:

| V3 term | Preferred V4 wording |
| --- | --- |
| target-repo | 目标仓库 |
| future work | 未来工作 |
| benchmark release | 评测 release / 仓库级评测包 |
| selector | 任务选择器 |
| selection | 任务选择 |
| support | 样本支撑 |
| fallback | 兜底来源 / fallback |
| baseline | 对照基线 |
| source caps | 来源上限 |
| slice stability | 切片稳定性 |
| outcome-unseen | 未看未来结果 |
| prediction gap | 预测缺口 |
| scorecard | 结果卡 / scorecard |
| regression signal | 回归信号 |

## Evidence Accuracy Audit

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/evidence-accuracy-audit-v4.zh.md
```

It must verify:

- MAE candidate value;
- best simple aggregate baseline MAE;
- MAE edge;
- random-control seed count;
- random beats/ties share;
- status of the future `95.0%` gate;
- `120/120` planned cells;
- scoreability `1.0`;
- click source repair `30/30`.

The audit must explicitly state whether any `>=95%` claim is supported. If not,
the deck must use `93.4%` and state that this is traction below the future gate.

## Expected Outputs

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/argument-repair-v4.zh.md
docs/research/barcarolle-project-showcase-deck-zh/deck-architecture-v4.zh.md
docs/research/barcarolle-project-showcase-deck-zh/terminology-reduction-v4.zh.md
docs/research/barcarolle-project-showcase-deck-zh/evidence-accuracy-audit-v4.zh.md
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v4.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v4.zh.pptx
docs/research/barcarolle-project-showcase-deck-zh/reader-review-audit-v4.zh.md
docs/research/barcarolle-project-showcase-deck-zh/text-style-audit-v4.zh.md
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v4.zh.md
```

Update after V4 succeeds:

```text
docs/research/barcarolle-project-showcase-deck-zh/README.md
PROCESS.md
```

Create closeout artifacts:

```text
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_v4_repair_process.md
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_v4_repair_decision.md
experiments/phase1_compiler/results/barcarolle_project_showcase_deck_v4_repair_decision.json
```

Do not overwrite V1, V2, or V3 artifacts. V3 remains the input/reference deck.

## Presentation Workflow

Use the Presentations skill with artifact-tool presentation JSX.

Task mode: targeted repair from existing content. If artifact-tool edit/import
of V3 creates awkward inherited geometry, rebuild V4 from clean editable JSX
using V3 as content source.

Primary deck profile: `engineering-platform`.

The final deck must pass:

- artifact-tool export to PPTX;
- slide PNG render;
- layout JSON extraction;
- contact sheet review;
- full-size review of all `11` slides, or all final slides if slide count
  changes;
- explicit diagram sanity checks for Slides `1`, `2`, `5`, `7`, `9`, `10`, and
  `11`;
- explicit terminology check for every slide;
- no orphan rectangles, dangling connectors, accidental dots, unexplained
  labels, or visible process residue.

## Reader Review Audit

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/reader-review-audit-v4.zh.md
```

Required rows:

| Review item | V4 answer | Evidence slide(s) | Pass/fail | If fail, repair |
| --- | --- | --- | --- | --- |
| Slide 1 right diagram looks wrong | | | | |
| Slide 2 gap/consequence visual relation unclear | | | | |
| Slide 5 bottom shapes/process text unclear | | | | |
| Slide 7 layout problem | | | | |
| Slide 7 weak bad-algorithm argument | | | | |
| Slide 8 weak bad-algorithm/process-evidence argument | | | | |
| Slide 9 left graphic alignment | | | | |
| Slide 10 layout problem | | | | |
| Slide 11 graphic looks wrong | | | | |
| Overall terminology burden | | | | |

Every row must be `pass`, `accepted residual risk`, or `fail`. A `fail`
requires repair before closeout.

## Text And Claim QA

Extract final PPTX text and check both outline and extracted PPTX text.

Forbidden residue:

```text
被测 ACUT|但不负责|不接管|不是|而是|是[^。；，\n]{0,30}不是|runbook|handoff|M1|M2|M3|M4|M5|M6|过程性文本|AI 写|我们刚才讨论|读者不关心|这个流程只画一次|当前 deck|旧 weighted design 是负面诊断
```

Overclaim patterns:

```text
已证明预测效度|预测效度已(经)?建立|已经建立预测效度|已经证明.*调优|调优.*已经证明|已验证.*调优闭环|模型能力更强|>=95%|≥95%
```

The `>=95%` / `≥95%` check may be waived only if
`evidence-accuracy-audit-v4.zh.md` proves the committed evidence supports that
exact value. Otherwise, the deck must not use it.

Also check:

```text
rg -n "/Users/chenmohan/Downloads" docs/research/barcarolle-project-showcase-deck-zh/*.md
```

Use the `audit-ai-tropes` skill or script on:

```text
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v4.zh.md
<final extracted PPTX text>
```

Accepted technical terms must be listed in `text-style-audit-v4.zh.md`, with a
brief reason for each.

## Visual QA

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v4.zh.md
```

It must include:

- final slide count;
- contact sheet path under ignored `outputs/`;
- full-size slides inspected;
- layout-check result;
- warnings and why they are acceptable;
- before/after note for the V3 visual complaints;
- confirmation that:
  - Slide 1 has no malformed right-side geometry;
  - Slide 2's top gap and lower consequences are visually connected;
  - Slide 5 has no unclear bottom shape row and no process sentence;
  - Slide 7 has no layout issue and no bad-algorithm proof structure;
  - Slide 9's algorithm loop is aligned;
  - Slide 10 has no detached bottom annotation strip unless it is clearly
    integrated;
  - Slide 11's feedback loop has clear connector direction;
  - all Chinese and mixed-language labels fit inside their containers.

If visual QA finds a malformed diagram, repair the slide and rerender before
closeout.

## Commit And Closeout Discipline

Follow step-level acceptance:

1. Commit the V4 argument repair, terminology audit, evidence audit, and
   architecture docs.
2. Commit the V4 outline.
3. Commit the V4 PPTX and QA reports after render/visual QA passes.
4. Commit README/PROCESS updates and closeout reports.

Do not make one large commit that mixes planning, PPTX generation, QA, and
closeout if the work can be separated.

The closeout decision report must state:

- final active deck path;
- slide count and slide list;
- how Slides 1, 2, 5, 7, 8, 9, 10, and 11 were repaired;
- how the Slide 7/8 argument changed;
- whether `>=95%` was supported or rejected;
- terminology reduction summary;
- visual QA status;
- claim boundary status;
- remaining residual risks;
- recommended next action.

## Stop Conditions

Stop and write a blocker report if:

- the final PPTX cannot be rendered or exported through the presentation
  workflow;
- the Slide 7/8 argument cannot be repaired without making a new unsupported
  research claim;
- evidence audit cannot verify the random-control and MAE numbers;
- the formula, diagrams, or mixed-language labels cannot be made readable after
  visual QA iterations;
- reader-review audit has a fail that cannot be repaired without changing
  facts or making a new research claim.

