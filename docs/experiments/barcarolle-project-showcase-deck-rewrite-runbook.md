# Barcarolle Project Showcase Deck Rewrite Runbook

Status: Chinese project-showcase deck rewrite runbook, 2026-06-02.

## Goal

Replace the current Chinese approval-packet deck with a new Chinese project
showcase deck that explains Barcarolle's problem, method, current effects, and
future directions.

The new deck is not an approval-request deck. It should present the project
state and trajectory:

```text
Barcarolle solves the target-repository prediction problem for coding-agent
evaluation by compiling repo-specific benchmark releases. The project has
already built the execution boundary, evidence machinery, and early algorithm
evaluation environment. Future work should improve benchmark-selection
algorithms and validate predictive validity, with productization paths in
agent-license governance and agent tuning.
```

## Why This Rewrite Exists

The current M6 Chinese deck is structurally wrong for this purpose. It is a
localized approval packet and mostly maps a subset of V5/M6 into slides. That
made it process-heavy and incomplete as a project presentation.

This runbook intentionally starts from the reader-facing argument rather than
from V5 section order, M6 slide order, or evidence-index order. Use the
`academic-paper-writing` method:

```text
readers -> problem -> consequence -> response
claim -> reasons -> evidence -> warrants -> objections -> future work
```

The old M6/V2 deck may be mined for facts and constraints, but it must not be
used as the structural template.

## Boundary

Allowed:

- create a new project-showcase deck package under `docs/research/`;
- write a fresh Chinese argument map before writing slides;
- write a new Chinese deck outline from the argument map;
- build a new Chinese editable PPTX;
- reuse evidence numbers, diagrams, and source references from V5/M6 when they
  serve the new argument;
- integrate related-work positioning into the main narrative;
- include current state, achieved effects, limitations, expected future
  effects, and productization directions;
- update roadmap and `PROCESS.md` after the new deck passes QA;
- add process and decision closeout artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- public browsing unless a committed public citation is found to be broken or
  materially ambiguous;
- changing score tables, selected task IDs, split labels, source eligibility,
  task statements, hidden-oracle material, or completed experiment decisions;
- using the old M6 approval deck as the new slide structure;
- preserving approval-request framing as the deck's main purpose;
- making a new long-form proposal report;
- claiming predictive validity has been established;
- claiming Barcarolle has already improved an agent tuning loop;
- claiming adapter differences prove model-only superiority;
- turning Barcarolle into an ACUT harness, generic task factory, or public
  leaderboard;
- using `imagegen`, decorative generated images, abstract AI art, or generated
  raster assets;
- putting process instructions, internal criticism, or self-referential
  writing advice into reader-facing slides.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/research/barcarolle-proposal-report-v5.md
docs/research/m6-approval-packet-zh/README.md
docs/research/m6-approval-packet-zh/terminology-glossary-v1.zh.md
docs/research/m6-approval-packet-zh/approval-deck-outline-v1.zh.md
docs/research/m6-approval-packet-zh/barcarolle-approval-deck-v1.zh.pptx
experiments/phase1_compiler/reports/proposal_approval_packet_zh_supplement_decision.md
```

Also read these for method/evidence support as needed:

```text
docs/research/phase-1-proposal-evidence-package.md
docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_decision.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md
```

Use V5 as the long-form factual and claim-boundary source. Use the old Chinese
M6 packet only as a fact source and negative example of what not to structure
around.

If working in a Codex desktop environment with the Presentations skill
available, use its editable artifact-tool workflow for the final PPTX and
rendered QA. Do not use `python-pptx`, direct OOXML edits, or LibreOffice
round trips for the final deck when the Presentations workflow is available.

## Expected Outputs

Create a new package:

```text
docs/research/barcarolle-project-showcase-deck-zh/
```

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/README.md
docs/research/barcarolle-project-showcase-deck-zh/project-argument-map-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/related-work-positioning-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v1.zh.pptx
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/text-and-claim-audit-v1.zh.md
```

Optional only if useful and final:

```text
docs/research/barcarolle-project-showcase-deck-zh/assets/
```

Do not commit temporary presentation workspaces, generated slide source,
preview PNGs, contact sheets, scratch scripts, layout JSON, extracted PPTX
text, or prompt files unless they are explicitly promoted as final audit
artifacts.

Create closeout artifacts:

```text
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_rewrite_process.md
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_rewrite_decision.md
experiments/phase1_compiler/results/barcarolle_project_showcase_deck_rewrite_decision.json
```

Update if the rewrite succeeds:

```text
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

Do not overwrite existing M6 or M6 Chinese approval-packet artifacts.

## Reader And Genre Contract

Audience:

- technical project reviewers;
- coding-agent evaluation researchers;
- agent product/tuning stakeholders;
- readers who have not followed the internal runbook history.

Reader questions the deck must answer:

1. What problem does Barcarolle solve?
2. Why is this problem not already solved by public benchmarks, live
   benchmarks, or generated task systems?
3. What method does Barcarolle use?
4. What has already been built or learned?
5. What has not yet been proven?
6. Why is algorithm discovery and evolution now possible?
7. What future effects should the project aim to achieve?
8. How can this become useful in agent-license governance and agent tuning?

The deck's genre is project showcase / research-product trajectory. It is not:

- approval request;
- evidence appendix;
- runbook summary;
- protocol memo;
- budget packet;
- internal milestone report.

## Reader-Facing Slide Architecture

Target length: 13-15 slides. Fewer is acceptable if the argument remains
complete. More than 15 requires a recorded reason.

Default architecture:

| Slide | Working title | Reader question answered |
| --- | --- | --- |
| 1 | Barcarolle 一句话 | What is the project? |
| 2 | 现有评测缺少目标仓库预测层 | What problem exists? |
| 3 | 这个缺口为什么有代价 | Why should readers care? |
| 4 | 相关工作解决了相邻问题 | What do SWE-bench, Verified, Live, SWE-smith, and R2E-Gym contribute? |
| 5 | Barcarolle 的位置 | What gap does Barcarolle occupy? |
| 6 | 北极星：预测效度 | What is the long-term research target? |
| 7 | 方法总览：编译 benchmark release | What method does Barcarolle use? |
| 8 | ACUT 边界与 verifier replay | Why is the benchmark-side boundary credible? |
| 9 | 核心算法问题：benchmark 不是随机抽题 | What algorithmic problem is being solved? |
| 10 | 已准备好的算法演进环境 | How can future algorithms be discovered and compared? |
| 11 | 当前已经达到的效果 | What has been shown so far? |
| 12 | 当前尚未达到的效果 | What remains unproven or fragile? |
| 13 | 后续研究路线 | How does the project move toward stronger predictive-validity evidence? |
| 14 | 产品化方向：Agent License | How can this support governance or deployment eligibility? |
| 15 | 产品化方向：Agent Tuning | How can this support configuration selection, tuning, and regression monitoring? |

The final deck may merge slides 4-5 or 14-15 if the resulting story is clearer.
Do not merge away the problem, method, current effects, limitations, or future
directions.

## Content Requirements

### Problem

The problem is target-repository prediction:

```text
现有 coding-agent 评测很难直接回答：一个给定 Agent 配置在某个目标仓库未来真实工作中的表现会怎样？
```

Do not frame the problem as "we need an approval packet" or "we need a better
slide deck."

### Related Work

Compare related work by role, not by dismissing it:

- SWE-bench: real repository issue-resolution tasks and execution scoring;
- SWE-bench Verified: human-validated task quality;
- SWE-bench-Live: freshness through newer tasks;
- SWE-smith: scalable task generation;
- R2E-Gym: executable environments and training/evaluation infrastructure.

Barcarolle's position:

```text
这些系统提供任务、质量、鲜度、规模或环境；Barcarolle 研究的是：
给定一个目标仓库和被测 Agent 配置，应该怎样编译一个 benchmark release，
使它更有可能预测未来仓库工作表现。
```

Do not write that related work "fails" or is "not useful." The claim is that
they answer different questions.

### Method

The method section must cover both what has been built and what the project is
setting up for future algorithm evolution:

- candidate supply;
- certification and leakage/source-quality checks;
- task selection, split construction, weighting or unweighting;
- fallback labeling and support thresholds;
- workspace ACUT execution with captured diff;
- verifier replay with hidden oracle isolation;
- adapter-stratified reporting;
- MAE and baseline comparison;
- random controls and baseline envelopes;
- future holdout or preregistered rolling-origin validation.

This section should show that algorithm discovery is now an experimental
system, not hand-wavy future work.

### Effects

Current achieved effects should be high-level and selective:

- naive weighted construction failed materially, so the construction problem is
  real;
- workspace ACUT execution and verifier replay ran through exploratory pilots,
  so the benchmark-side boundary is feasible;
- source-quality repair is tractable;
- early selection-policy evidence affects MAE and beats/ties many random
  same-budget selections, so there is an optimization target;
- evidence remains preliminary.

Preserve key numbers when used:

```text
0.3148
0.7481
0.25
0.125
120/120
1.0
30/30
0.209
0.2149
0.0059
93.4%
1000
6/18
6/6
```

Do not force all numbers onto one slide. Use only the numbers that help the
argument.

### Limitations

Limitations should be framed as live research problems, not as defensive
process disclaimers:

- predictive validity has not been established;
- MAE edge is currently small;
- adapter/repo/window support is fragile;
- fallback remains visible and must be reduced or scoped;
- tuning-loop improvement has not been empirically proven;
- future validation needs frozen releases and outcome-unseen evidence.

### Future Work

Future work must cover:

- benchmark-selection algorithm evolution;
- stronger source/task supply and feature support;
- preregistered rolling-origin or future-holdout validation;
- multi-configuration or multi-ACUT extension when needed;
- agent-license governance path;
- agent-tuning and regression-feedback path.

Agent License wording:

```text
Barcarolle 本身不是 license 产品，但可以成为 license / deployment governance
的证据层：某个 Agent 配置在某个仓库、任务类别或风险等级下是否具有足够证据支持使用。
```

Agent Tuning wording:

```text
Barcarolle 不接管调优闭环，但可以提供 dev/eval/canary release、failure taxonomy、
scorecard 和 regression signal，帮助团队比较 prompt、retrieval、skills、tool policy
和 runtime budget 的变化。
```

## Reader-Facing Forbidden Language

These phrases or concepts must not appear in the final PPTX, speaker notes,
reader-facing summary, or visible deck outline except inside a clearly labeled
internal audit report:

```text
不是请求批准
而是项目路线
请求批准
审批请求
approval request
approval packet
M6
M5
V1
V2
runbook
closeout
claim spine
proof object
source evidence
claim limit
placeholder
用户自有值
no-paid
Visual QA
AI 写
参考 academic-paper-writing
这份材料是为了
直接从 V5 映射
旧 PPT 可以丢掉
读者不关心
```

Also avoid visible English process labels such as `Claim:`, `Proof object:`,
`Source evidence:`, and `Claim limit:`. Those labels may be used internally in
the argument map but must be removed from reader-facing slides.

It is acceptable for internal audit files to mention these terms when checking
that they do not appear in the deck.

## Visual And Reader QA Contract

The executor must QA the deck as a skeptical reviewer, not as the author.

Before final export, run at least three review passes:

1. **Reader Argument Pass**
   - Can a reviewer explain the project after only the deck?
   - Does the deck answer problem, method, current effects, limitations, and
     future directions?
   - Is related work integrated into the argument rather than dumped into an
     appendix?

2. **Process-Language Pass**
   - Extract PPTX text and search forbidden terms.
   - Manually inspect every slide for meta-writing, internal instructions, and
     phrases that sound like a prompt or runbook.
   - If any slide contains wording like "this deck is not..." or "we should...",
     rewrite it as a direct project claim or delete it.

3. **Visual QA Pass**
   - Render a contact sheet and selected full-size slide previews.
   - Check for clipped text, dense tables, unreadable labels, repeated generic
     card layouts, and low-information slides.
   - Check that titles are claims, not topic labels.
   - Check that no slide reads like an evidence appendix copied into a deck.

If the deck fails any pass, iterate the weakest slides before closeout.

## Worker Prompt

Use this prompt to start the execution worker:

```text
You are executing docs/experiments/barcarolle-project-showcase-deck-rewrite-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read this runbook and follow it with step-level acceptance and scoped
commits.

Main goal: create a new Chinese project showcase deck under
docs/research/barcarolle-project-showcase-deck-zh/. The deck should explain
what problem Barcarolle solves, how it works, what has already been achieved,
what remains unproven, how the algorithm-discovery environment is now prepared,
and what future work/productization paths exist, especially Agent License and
Agent Tuning.

Do not preserve the old M6 approval-packet structure. Do not write a new
approval-request deck. Do not run paid ACUT cells, paid LLM calls, external
reviewer calls, or public browsing. Do not change evidence numbers, score
tables, task IDs, split labels, source eligibility, task statements,
hidden-oracle material, or completed experiment decisions. Do not claim
predictive validity or tuning-loop improvement has been established. Do not use
imagegen or decorative generated images. Before closeout, review the deck as a
skeptical reader and remove all visible process language, internal planning
phrases, and AI-prompt-like wording from reader-facing artifacts.
```

## Step 0: Preflight And Supersession Boundary

Actions:

1. Record branch, HEAD, date, worktree status, and input availability in the
   process report.
2. Confirm the current Chinese M6 packet exists and record why it is being
   superseded for deck use:
   - it is an approval-packet localization;
   - it is too closely mapped from V5/M6;
   - it includes process vocabulary and reader-irrelevant structure;
   - it does not fully present problem, method, effects, limitations, and
     future product paths.
3. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/
```

4. Record that the old Chinese approval packet remains traceability material,
   not the new deck structure.

Acceptance:

- no paid/external calls made;
- source materials are present;
- process report records the supersession boundary;
- no reader-facing deck content has been drafted yet.

Suggested commit:

```text
Record project showcase deck rewrite preflight
```

## Step 1: Build The Reader Argument Map

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/project-argument-map-v1.zh.md
```

2. Use this structure:

```text
Audience
Reader questions
Condition
Consequence
Response
Main claim
Reasons
Evidence
Warrants
Strongest objections
Responses
Future work
```

3. The argument map must explicitly cover:
   - the target-repository prediction problem;
   - why related work is adjacent rather than sufficient;
   - Barcarolle's benchmark-compiler method;
   - algorithm discovery/evolution environment;
   - achieved effects;
   - unproven limits;
   - Agent License;
   - Agent Tuning.

Acceptance:

- argument map exists;
- it is organized by reader questions, not prior report sections;
- it does not use approval-request framing as the main claim;
- it preserves the current evidence boundary.

Suggested commit:

```text
Draft project showcase argument map
```

## Step 2: Write Related-Work Positioning

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/related-work-positioning-v1.zh.md
```

2. Position each related-work direction by contribution and remaining gap:
   - SWE-bench;
   - SWE-bench Verified;
   - SWE-bench-Live;
   - SWE-smith;
   - R2E-Gym.
3. Use only already committed/source-approved claims from V5 unless a public
   citation must be checked.
4. The comparison should prepare slide content, not become a literature review.

Acceptance:

- related-work note exists;
- it does not dismiss related work;
- it clearly explains Barcarolle's distinct layer;
- citation/source claims do not exceed V5.

Suggested commit:

```text
Draft related-work positioning for showcase deck
```

## Step 3: Draft The New Deck Outline

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v1.zh.md
```

2. Use the default slide architecture unless a recorded reader-facing reason
   justifies a change.
3. For every slide, write:
   - visible slide title;
   - main message in one sentence;
   - visual object;
   - essential evidence or example;
   - what to omit from the slide.
4. Do not use visible process labels such as `Claim`, `Proof object`,
   `Source evidence`, or `Claim limit`.
5. Run the forbidden-language audit on the outline and fix reader-facing
   matches.

Acceptance:

- outline exists;
- it covers problem, method, effects, limitations, and future work;
- related work appears in the main story;
- Agent License and Agent Tuning are included as future productization paths;
- old M6 approval structure is not preserved;
- forbidden reader-facing language is absent.

Suggested commit:

```text
Draft project showcase deck outline
```

## Step 4: Build The New Chinese PPTX

Actions:

1. Build:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v1.zh.pptx
```

2. Use the Presentations skill and artifact-tool JSX workflow when available:
   - create a thread-scoped presentation workspace under `outputs/...`;
   - choose `engineering-platform` as the primary deck profile;
   - write editable slides;
   - render previews and layout JSON;
   - inspect contact sheet and full-size slides;
   - export only after QA passes;
   - copy only the final PPTX into the package directory.
3. Use a restrained technical presentation style:
   - diagrams, timelines, comparison matrices, and concise evidence callouts;
   - no decorative generated images;
   - no generic card-grid filler;
   - no dense appendix tables in the main story;
   - Chinese-friendly font such as `PingFang SC` or `Noto Sans CJK SC`.
4. Prioritize these visual objects:
   - target-repo prediction gap diagram;
   - related-work positioning matrix;
   - Barcarolle benchmark compiler workflow;
   - ACUT boundary/verifier replay diagram;
   - algorithm evolution environment map;
   - achieved-current-effect callout;
   - limitation-to-future-work bridge;
   - Agent License and Agent Tuning application maps.

Acceptance:

- PPTX exists and is editable;
- deck follows the new showcase architecture;
- Chinese text fits every slide;
- no slide reads as an approval request, internal process note, or evidence
  appendix;
- predictive validity and tuning-loop improvement remain unproven.

Suggested commit:

```text
Build project showcase presentation deck
```

## Step 5: Reader-Facing Text And Claim Audit

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/text-and-claim-audit-v1.zh.md
```

2. Extract PPTX text to an ignored scratch path and audit it together with the
   reader-facing Markdown files.
3. Run forbidden-language checks against the outline and extracted PPTX text:

```bash
rg -n "不是请求批准|而是项目路线|请求批准|审批请求|approval request|approval packet|M6|M5|V1|V2|runbook|closeout|claim spine|proof object|source evidence|claim limit|placeholder|用户自有值|no-paid|Visual QA|AI 写|参考 academic-paper-writing|这份材料是为了|直接从 V5 映射|旧 PPT 可以丢掉|读者不关心" docs/research/barcarolle-project-showcase-deck-zh/*.md
rg -n "已证明预测效度|预测效度已(经)?建立|已经建立预测效度|已经证明.*调优|调优.*已经证明|已验证.*调优闭环|模型能力更强" docs/research/barcarolle-project-showcase-deck-zh/*.md
rg -n "/Users/chenmohan/Downloads" docs/research/barcarolle-project-showcase-deck-zh/*.md
git diff --check
```

4. Run the same forbidden-language and overclaim checks on extracted PPTX text.
5. Manually inspect for softer process language not caught by regex, including:
   - "这页要说明";
   - "这里放";
   - "不要";
   - "我们应该";
   - "保留边界";
   - "本材料";
   - "旧版本";
   - "内部";
   - prompt-like instructions.

Acceptance:

- text-and-claim audit exists;
- all regex checks pass or intentional internal-audit matches are explained;
- extracted PPTX text has no forbidden reader-facing phrase;
- no slide claims predictive validity or tuning-loop improvement is proven;
- `git diff --check` passes.

Suggested commit:

```text
Audit project showcase deck text and claims
```

## Step 6: Visual QA As A Skeptical Reviewer

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v1.zh.md
```

2. Render a contact sheet and selected full-size previews using the
   Presentations workflow or equivalent artifact-tool rendering.
3. Review every slide as if the reviewer will notice AI-generated process
   residue. Use this checklist:
   - Does the title make a project claim rather than name a topic?
   - Does any slide reveal internal drafting instructions?
   - Does any slide contain phrases that explain what the deck is trying not
     to be?
   - Does the slide answer a reader question?
   - Is the visual object carrying information?
   - Is the amount of text readable in presentation mode?
   - Are related work, method, evidence, limitation, and future work visually
     distinguishable?
   - Does the deck avoid repeated generic card grids?
4. Repair any failing slide and rerun preview QA before closeout.

Acceptance:

- visual QA report exists;
- contact sheet and full-size review were performed;
- no clipped text, label collision, or unreadable chart remains;
- no visible process-language or AI-prompt-like wording remains;
- the final deck can be understood without the old M6 packet open beside it.

Suggested commit:

```text
Complete visual QA for project showcase deck
```

## Step 7: Handoff Updates

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/README.md
```

2. README must state:
   - this directory contains the active Chinese project-showcase deck;
   - old M6 approval-packet materials are superseded for deck use;
   - V5 remains the long-form factual source;
   - future reviewer-facing deck edits should start here.
3. Update roadmap and `PROCESS.md` with the new active deck package.

Acceptance:

- README exists;
- handoff docs point to the new project-showcase deck;
- `PROCESS.md` remains concise;
- old M6 artifacts remain available but no longer described as the active deck.

Suggested commit:

```text
Align project showcase deck handoff
```

## Step 8: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_rewrite_process.md
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_rewrite_decision.md
experiments/phase1_compiler/results/barcarolle_project_showcase_deck_rewrite_decision.json
```

2. Stop with one label:

```text
barcarolle_project_showcase_deck_rewrite_complete
blocked_showcase_argument_unclear
blocked_related_work_positioning_unclear
blocked_project_deck_overclaims
blocked_process_language_remains_in_pptx
blocked_visual_qa_failed
blocked_pptx_generation_tool_unavailable
```

Decision report must state:

- whether the new showcase deck is complete;
- whether it supersedes old M6 approval decks for reader-facing presentation
  use;
- where the PPTX, argument map, related-work note, outline, text audit, visual
  QA report, and README are;
- whether the deck presents problem, method, effects, limits, and future work;
- whether related work, Agent License, and Agent Tuning are included;
- whether predictive validity and tuning-loop improvement remain unproven;
- whether process-language audit and visual QA passed;
- whether paid/external calls or generated images were used.

Suggested commit:

```text
Close project showcase deck rewrite
```

## Final Report Expectations

The closeout should say:

```text
What changed:
  The old Chinese approval-packet deck was superseded for presentation use by
  a new Chinese project showcase deck organized around problem, method,
  current effects, limitations, future validation, Agent License, and Agent
  Tuning.

Why it matters:
  The deck now presents Barcarolle as a research/product project rather than a
  compressed approval packet or runbook summary.

What remains:
  Review the new deck for audience-specific emphasis before circulation. Do
  not restore approval-request framing or internal process vocabulary.
```

Do not draft a follow-up runbook unless the user explicitly asks after
reviewing the new showcase deck.
