# Barcarolle Project Showcase Deck V3 Reader-Centered Revision Runbook

Status: Chinese project-showcase deck V3 revision runbook, 2026-06-02.

## Goal

Revise the active Chinese project-showcase deck into a reader-centered V3 that
answers the project questions directly:

```text
What problem exists?
How does Barcarolle address it?
What evidence shows the route is worth pursuing?
How will the benchmark compiler algorithms and validation protocol evolve?
How do Agent License and Agent Tuning use the evidence layer?
```

V3 is a structural revision, not a cosmetic polish. The executor must use the
slide-by-slide user feedback handoff as an internal review source, then rebuild
the outline and PPTX so that the deck is easier to read, less process-heavy, and
less dependent on project-internal terminology.

Source deck:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v2.zh.pptx
```

Target deck:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx
```

Plain-language target:

```text
把 V2 从“内部模块说明”改成“评审能顺着读完的项目展示”。合并原 2/3，
重写相关工作和研究路线，保留必要证据，删掉或吸收过程性诊断页。每个
图都要一眼看出它在证明什么。
```

## Boundary

Allowed:

- create V3 files under `docs/research/barcarolle-project-showcase-deck-zh/`;
- change slide titles, slide count, slide order, and page roles when the V3
  story requires it;
- merge V2 slides that repeat the same reader question;
- delete V2 slides whose useful content can be absorbed elsewhere;
- rewrite visible copy in Chinese;
- simplify or redraw all diagrams;
- run a narrow related-work source sanity check against primary public sources;
- use existing committed evidence, V5 proposal facts, and local research notes;
- update `README.md` and `PROCESS.md` after V3 succeeds;
- create process and decision closeout artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- broad literature review or recommendation gathering;
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
- using product-boundary phrasing such as `但不负责` or `不接管` in the deck.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/research/barcarolle-proposal-report-v5.md
docs/research/barcarolle-project-showcase-deck-zh/README.md
docs/research/barcarolle-project-showcase-deck-zh/slide-by-slide-reader-review-handoff-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/page-responsibility-matrix-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/duplication-audit-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/text-style-audit-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v2.zh.pptx
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_pruning_style_decision.md
```

Use as source-of-truth or supporting context:

```text
docs/research/barcarolle-project-showcase-deck-zh/project-argument-map-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/related-work-positioning-v1.zh.md
docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md
docs/research/phase-1-proposal-evidence-package.md
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md
experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md
experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md
```

Optional historical note if present:

```text
/Users/chenmohan/Downloads/barcarolle-research-0526-1.md
```

Do not mention local `Downloads` paths in reader-facing outputs.

## Related-Work Source Sanity Check

Create a short source sanity report before rewriting the related-work slide:

```text
docs/research/barcarolle-project-showcase-deck-zh/related-work-source-sanity-v3.zh.md
```

Use primary or near-primary sources only. At minimum check:

- SWE-bench paper/project;
- SWE-bench Verified;
- SWE-bench quality/contamination follow-up if used;
- SWE-bench-Live;
- SWE-Bench++;
- SWE-smith;
- R2E-Gym.

The report should record for each source:

```text
full name;
one-line contribution;
one-line unresolved issue for Barcarolle;
link or citation label;
whether it belongs on the main slide or backup/source note only.
```

Do not turn this into a broad survey. Its purpose is to make the deck's
related-work claims concrete and readable.

## Expected V3 Architecture

Target `11` or `12` slides. Fewer is acceptable if the story remains complete.
More than `12` requires explicit justification in the architecture note.

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/deck-architecture-v3.zh.md
```

Recommended architecture:

| V3 slide | Role | Source material | Required change |
| --- | --- | --- | --- |
| 1 | Project positioning | V2 Slide 1 | Explain `ACUT = Agent Configuration Under Test`; remove `被测 ACUT`; redraw the right-side diagram as a clean target repo / benchmark release / ACUT relationship. |
| 2 | Problem and cost | V2 Slides 2-3 | Merge the abstract gap and consequence pages. Make the decision problem concrete: general scores do not directly estimate future work in this target repo. |
| 3 | Related work and remaining gap | V2 Slide 4 plus source sanity check | Write full names, add SWE-Bench++, and state each remaining issue in plain language. |
| 4 | Research target | V2 Slide 5 | Make predictive validity and MAE intuitive. Use a LaTeX-rendered equation, not plain text. Remove `Formal scope`, `Route finding`, and `Boundary` cards unless their content is rewritten into useful prose. |
| 5 | Method | V2 Slide 6 | Keep the compiler workflow but reduce terminology. Remove unexplained bottom rectangles and any process residue. |
| 6 | Execution boundary | V2 Slide 7 | Translate visible text into Chinese and explain solver workspace, captured diff, verifier workspace, and hidden oracle in simple terms. |
| 7 | Algorithm problem | V2 Slides 8-9 | Merge selection/support/fallback and algorithm environment. Show why task selection changes estimates and why an algorithm lab is needed. |
| 8 | Current evidence | V2 Slide 10 plus selected V2 Slide 8/9 evidence | Organize evidence by reader question: problem exists, execution is feasible, source repair works, random control gives a baseline, MAE edge is a traction signal. Avoid process-data dumping. |
| 9 | Research route | V2 Slide 12 plus algorithm roadmap | Put task-selection algorithm evolution at the center. Treat future holdout / rolling-origin as validation route. Treat release freezing and success criteria as protocol prerequisites, not the main future research contribution. |
| 10 | Productization direction: Agent License | V2 Slide 13 | Use positive use-case language. Remove `但不负责` / `不接管` style claims. Redraw the governance visual with no orphan rectangles. |
| 11 | Productization direction: Agent Tuning | V2 Slide 14 | Use positive use-case language. Redraw a protected dev/eval/canary feedback loop with clear connectors and no orphan rectangles. |

Optional `12th` slide:

- Use only if a separate evidence-boundary or risk slide clearly answers a
  reader question that cannot fit in Slides 8-9.
- Do not preserve V2 Slide 11 merely as a process diagnostics page.

## Slide-Specific Requirements

### Slide 1

- Define ACUT visibly on first use:

```text
ACUT = Agent Configuration Under Test，一次被评估的 agent 配置。
```

- Do not write `被测 ACUT`.
- Prefer `ACUT` or `agent 配置` after first definition.
- Redraw the diagram from scratch if needed. It should not contain awkward
  connector geometry, dangling shapes, or unexplained entities.

### Slides 2-3

- Merge V2 Slides 2 and 3 unless the architecture note gives a strong reason not
  to.
- Make the problem specific:
  - existing benchmark scores are useful general signals;
  - deployment still needs a target-repo future-work estimate;
  - wrong estimates affect deployment, tuning, and governance decisions.
- Fold related-work overlap into the related-work slide, not into repeated
  problem statements.

### Related Work

- Write full names:
  - `SWE-bench`;
  - `SWE-bench Verified`;
  - `SWE-bench-Live`;
  - `SWE-Bench++`;
  - `SWE-smith`;
  - `R2E-Gym`.
- Do not use standalone labels such as `Verified` or `Live`.
- Keep each unresolved issue concrete. Examples:
  - quality filtering does not decide which tasks form this target repo's
    frozen release;
  - live updates reduce staleness but still need outcome-unseen release rules;
  - generated tasks expand supply but need local certification and source caps;
  - executable environments help run tasks but do not answer target-repo
    predictive validity.

### Research Target

- Use a formula block that is visually typeset as LaTeX. The outline should use
  LaTeX source, for example:

```latex
W_r(a)=\mathbb{E}[\mathrm{success}(a,\ \mathrm{future\ work\ in\ repo}\ r)]
```

- If the presentation tooling cannot export native PowerPoint equations, render
  the formula as a high-quality equation object or carefully typeset math block
  and record the limitation in QA. Do not leave it as raw plain text in the
  reader-facing slide.
- Explain MAE in Chinese:

```text
MAE 表示 benchmark 预测值和未来真实表现之间平均差多少；越低，预测越贴近未来结果。
```

- Remove the `Formal scope`, `Route finding`, and `Boundary` cards unless each
  is rewritten into a reader-facing explanation with clear value.

### Method And Boundary

- Keep the method workflow, but reduce English terminology.
- Translate Slide 7-style boundary copy into Chinese.
- Retain essential terms only when they preserve technical meaning.
- Explain hidden oracle only as a verifier-side validation material, not as an
  internal implementation digression.

### Algorithm And Evidence

- Slides 8, 9, 10, and 11 in V2 must be reconsidered together.
- The reader-facing evidence slide should answer:
  - Is the problem real?
  - Can Barcarolle execute the benchmark-side protocol?
  - Can weak sources be repaired or filtered?
  - Is there an initial algorithm signal beyond random selection?
  - What remains unproven?
- Keep traction evidence concise:
  - `120/120` planned cells completed;
  - scoreability `1.0`;
  - click source repair `30/30`;
  - candidate MAE `0.209` vs baseline `0.2149`;
  - random beats/ties `93.4%` of `1000` selections.
- Do not overstate the small MAE edge.
- Avoid preserving fallback/adapter diagnostics as standalone process detail
  unless they directly support the research route.

### Research Route

- Treat these as prerequisites or gates, not research contributions:
  - freeze release;
  - fix named ACUT configurations;
  - set baseline suite;
  - set success criteria.
- Treat these as central future research:
  - task-selection algorithm evolution;
  - source support and source caps;
  - fallback policy;
  - LLM-enhanced task generation or statement repair as candidate supply;
  - random and simple-baseline comparison;
  - slice stability and practical margin;
  - true future holdout or preregistered rolling-origin validation.

### Productization Slides

- Keep Agent License and Agent Tuning as distinct use cases.
- Use positive capability language:
  - evidence status for deployment governance;
  - protected dev/eval/canary feedback for tuning.
- Do not write `但不负责`, `不接管`, or equivalent negative boundary claims.
- Redraw visuals to remove orphan white rectangles and unclear connector paths.

## Expected Outputs

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/related-work-source-sanity-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/deck-architecture-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx
docs/research/barcarolle-project-showcase-deck-zh/reader-review-audit-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/text-style-audit-v3.zh.md
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v3.zh.md
```

Update after V3 succeeds:

```text
docs/research/barcarolle-project-showcase-deck-zh/README.md
PROCESS.md
```

Create closeout artifacts:

```text
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_v3_revision_process.md
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_v3_revision_decision.md
experiments/phase1_compiler/results/barcarolle_project_showcase_deck_v3_revision_decision.json
```

Do not overwrite V1 or V2 artifacts. V2 remains the input/reference deck.

## Presentation Workflow

Use the Presentations skill with artifact-tool presentation JSX.

Task mode: `targeted-edit` or `create-from-existing-content`, depending on
which route gives cleaner editable output. If using V2 as a template creates
awkward layout inheritance, rebuild V3 with a consistent project-showcase visual
system and export a clean editable PPTX.

Primary deck profile: `engineering-platform`.

The final deck must pass:

- artifact-tool export to PPTX;
- slide PNG render;
- layout JSON extraction;
- contact sheet review;
- full-size review of every changed slide;
- explicit diagram sanity checks for Slides 1, 5, 6, 10, and 11 in the V3
  architecture;
- no orphan rectangles, dangling connectors, unexplained labels, or visible
  process residue.

## Reader Review Audit

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/reader-review-audit-v3.zh.md
```

This audit must answer each question from:

```text
docs/research/barcarolle-project-showcase-deck-zh/slide-by-slide-reader-review-handoff-v3.zh.md
```

Required rows:

| Review item | V3 answer | Evidence slide(s) | Pass/fail | If fail, repair |
| --- | --- | --- | --- | --- |

Every original user concern must be marked `pass`, `accepted residual risk`, or
`fail`. A `fail` requires repair before closeout.

## Text And Claim QA

Run text extraction on the final PPTX and check the outline plus extracted PPTX
text for forbidden residue:

```text
rg -n "被测 ACUT|但不负责|不接管|不是|而是|是[^。；，\\n]{0,30}不是|runbook|handoff|M1|M2|M3|M4|M5|M6|过程性文本|AI 写|我们刚才讨论|读者不关心" docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v3.zh.md
```

Run the equivalent check on extracted PPTX text.

Also check:

```text
rg -n "已证明预测效度|预测效度已(经)?建立|已经建立预测效度|已经证明.*调优|调优.*已经证明|已验证.*调优闭环|模型能力更强" docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v3.zh.md
rg -n "/Users/chenmohan/Downloads" docs/research/barcarolle-project-showcase-deck-zh/*.md
```

Use the `audit-ai-tropes` skill or its script on:

```text
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v3.zh.md
<final extracted PPTX text>
```

Accepted technical terms must be listed in `text-style-audit-v3.zh.md`.

## Visual QA

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v3.zh.md
```

It must include:

- final slide count;
- contact sheet path under ignored `outputs/`;
- full-size slides inspected;
- layout-check result;
- any warnings and why they are acceptable;
- screenshot/render confirmation that:
  - Slide 1 diagram is geometrically coherent;
  - no slide has orphan white rectangles;
  - no slide has dangling connectors or malformed visual code output;
  - the formula slide renders cleanly;
  - all Chinese text fits inside its containers;
  - related-work names are fully visible;
  - productization diagrams have clear flow.

If the visual QA finds a malformed diagram, repair the slide and rerender before
closeout.

## Commit And Closeout Discipline

Follow step-level acceptance:

1. Commit the handoff/runbook intake and architecture docs if they were not
   already committed.
2. Commit the related-work sanity report and V3 outline.
3. Commit the V3 PPTX and QA reports after render/visual QA passes.
4. Commit README/PROCESS updates and closeout reports.

Do not make one large commit that mixes outline planning, PPTX generation, QA,
and process closeout if the work can be separated.

The closeout decision report must state:

- final active deck path;
- slide count and slide list;
- which V2 slides were merged or deleted;
- how each user feedback group was resolved;
- source sanity status for related work;
- formula rendering approach;
- visual QA status;
- claim boundary status;
- remaining residual risks;
- recommended next action.

## Stop Conditions

Stop and write a blocker report if:

- the final PPTX cannot be rendered or exported through the presentation
  workflow;
- source sanity check finds a related-work claim that cannot be supported by a
  primary or near-primary source;
- the formula cannot be represented better than raw plain text and no acceptable
  workaround is available;
- reader-review audit has a fail that cannot be repaired without changing facts
  or making a new research claim;
- the executor cannot remove process residue from reader-facing materials.
