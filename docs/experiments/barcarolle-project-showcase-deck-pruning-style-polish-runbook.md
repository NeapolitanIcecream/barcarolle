# Barcarolle Project Showcase Deck Pruning And Style Polish Runbook

Status: Chinese project-showcase deck pruning/style runbook, 2026-06-02.

## Goal

Revise the Chinese project-showcase deck by pruning duplicate slide content,
merging or removing pages that do not have a unique reader-facing role, and
polishing the language to remove AI-like binary reframing and process residue.

This is a focused revision of the current project-showcase deck, not another
full narrative rewrite.

Source deck:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v1.zh.pptx
```

Target deck:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v2.zh.pptx
```

Plain-language target:

```text
保留当前“问题 -> 方法 -> 效果 -> 限制 -> 未来路线 -> 产品化方向”的大结构，
但先做逐页职责审计。没有独立职责的页要合并或删除；保留页的页眉 title
不改。正文去掉“不是……而是……”“是……不是……”这类 AI 味很重的二分式句法。
```

## Why This Revision Exists

The V1 project-showcase deck fixed the main architecture problem, but it still
has two issues:

1. **Content duplication.** Some pages repeat positioning or workflow content.
   Examples include Slide 1 vs Slide 5, and the repeated release/freeze/
   validation flow across Slides 5, 6, 7, and 13. These are examples only; the
   executor must audit all slides.
2. **AI-like language patterns.** The deck still uses visible binary reframes
   such as "不是……而是……" and "是……不是……". Those should be replaced with direct
   claims.

The next run must not merely remove repeated diagrams. It must first decide
whether pages should be kept, merged, or deleted.

## Boundary

Allowed:

- create V2 files under `docs/research/barcarolle-project-showcase-deck-zh/`;
- audit all slide responsibilities before editing the deck;
- merge or delete slides that lack a unique reader-facing purpose;
- preserve the current top-level slide title labels for retained slides;
- rewrite subtitles, body copy, diagram labels, and callouts for clarity;
- alter visual objects when needed to reduce repetition;
- use V1 facts, V5 facts, and committed evidence reports as source material;
- update `README.md`, roadmap, and `PROCESS.md` if V2 succeeds;
- add process and decision closeout artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- public browsing unless a committed public citation is discovered to be
  broken or materially ambiguous;
- changing score tables, selected task IDs, split labels, source eligibility,
  task statements, hidden-oracle material, or completed experiment decisions;
- changing the top-level slide title labels of retained slides;
- preserving a slide only because it existed in V1;
- only redrawing diagrams while leaving duplicate page roles intact;
- restoring approval-request framing;
- adding process instructions, internal critique, prompt-like text, or
  self-referential writing advice to reader-facing materials;
- using `imagegen`, decorative generated images, abstract AI art, or generated
  raster assets;
- claiming predictive validity has been established;
- claiming Barcarolle has already improved an agent tuning loop;
- claiming adapter differences prove model-only superiority.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/research/barcarolle-proposal-report-v5.md
docs/research/barcarolle-project-showcase-deck-zh/README.md
docs/research/barcarolle-project-showcase-deck-zh/project-argument-map-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/related-work-positioning-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/text-and-claim-audit-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v1.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v1.zh.pptx
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_rewrite_decision.md
```

Use these for evidence boundaries as needed:

```text
docs/research/phase-1-proposal-evidence-package.md
docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
experiments/phase1_compiler/reports/phase1_proposal_evidence_package_decision.md
experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md
```

If working in a Codex desktop environment with the Presentations skill
available, use the editable artifact-tool workflow for the final PPTX and
rendered QA. Do not use `python-pptx`, direct OOXML edits, or LibreOffice
round trips for the final deck when the Presentations workflow is available.

## Expected Outputs

Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/page-responsibility-matrix-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/duplication-audit-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v2.zh.pptx
docs/research/barcarolle-project-showcase-deck-zh/text-style-audit-v2.zh.md
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v2.zh.md
```

Update if V2 succeeds:

```text
docs/research/barcarolle-project-showcase-deck-zh/README.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

Create closeout artifacts:

```text
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_pruning_style_process.md
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_pruning_style_decision.md
experiments/phase1_compiler/results/barcarolle_project_showcase_deck_pruning_style_decision.json
```

Do not overwrite V1 artifacts. V1 remains the first project-showcase deck and
source/reference for V2.

## Title Preservation Rule

For retained slides, do not change the top-level slide title labels. These
labels include the current visible page headers such as:

```text
项目定位
问题
代价
相关工作
项目位置
研究目标
方法
执行边界
算法问题
算法环境
当前效果
限制
研究路线
产品化方向
```

Allowed:

- delete a slide after the page-responsibility matrix justifies deletion;
- merge a slide's useful content into another slide;
- keep the receiving slide's existing title label unchanged;
- rewrite subtitles, body copy, callouts, legends, and diagram labels.

Not allowed:

- changing a retained slide's top-level title label to a stronger claim;
- using title changes to hide duplicate content;
- renumbering alone as a substitute for slide-role cleanup.

If deleting a slide changes numbering, renumbering is allowed. The rule applies
to visible title labels, not slide numbers.

## Page Responsibility Standard

Before editing the PPTX, build a page-responsibility matrix. For each V1 slide,
answer:

```text
What reader question does this slide uniquely answer?
What would the reader fail to understand if this slide disappeared?
Which other slides repeat its content, visual object, evidence, or vocabulary?
Can the unique content be merged into another slide?
Decision: keep / merge / delete
Merge destination if any
Facts or visuals to preserve
Text or visuals to remove
```

A slide should be kept only if it has a unique reader-facing role. If deletion
does not remove a distinct argument step, merge or delete it.

Known duplication suspects that must be evaluated:

- Slide 1 `项目定位` and Slide 5 `项目位置`;
- Slides 5, 6, 7, and 13 around release/freeze/validation workflow;
- Slide 10 `算法环境` and Slide 13 `研究路线` around baselines and future
  validation;
- Slide 11 `当前效果` and Slide 12 `限制` around MAE edge, fallback, and support;
- Slide 14 and Slide 15 around productization direction framing.

These are not the only possible duplicates. Audit all slides.

## Expected Pruning Direction

Do not treat these as mandatory decisions, but use them as a starting
hypothesis to test in the matrix:

- Slide 5 is the strongest deletion or merge candidate because its positioning
  role overlaps with Slides 1, 4, and 7.
- Slide 7 should be the only complete compiler workflow slide.
- Slide 6 should focus on the prediction target, not another process strip.
- Slide 13 should focus on future validation protocol, not repeat the compiler
  workflow or algorithm-lab map.
- Slide 10 should focus on the existing algorithm-evaluation environment, not
  the future validation route.
- Slide 11 should show traction evidence only.
- Slide 12 should map current weaknesses to repair/validation actions only.
- Slides 14 and 15 may remain separate if their visual structures and product
  roles are clearly different; otherwise merge them into one productization
  slide.

Target length: 12-14 slides. A 15-slide deck may pass only if the matrix proves
that every slide has a distinct role.

## Language Style Contract

Use `audit-ai-tropes` principles for all reader-facing material:

- direct claims;
- ordinary verbs;
- concrete actors and consequences;
- fewer symmetrical contrast sentences;
- no prompt-like comments;
- no internal process vocabulary;
- no polished sentence templates that outrun the evidence.

Reader-facing material includes:

- V2 PPTX visible text;
- V2 deck outline;
- V2 README changes;
- any reader-facing appendix or summary created by the executor.

Internal audit files may discuss banned language when explaining checks.

### Absolute Sentence-Pattern Ban

Do not use these patterns in reader-facing V2 material:

```text
不是……而是……
是……不是……
不只是……
不再是……
not ... but ...
not ... rather ...
not ... instead ...
```

Also avoid close variants that keep the same rhetorical shape.

Examples of direct replacements:

| Current pattern | Direct style |
| --- | --- |
| `Barcarolle 是 benchmark 编译器，不是 ACUT harness。` | `Barcarolle 负责 benchmark 编译层；ACUT 保留自己的 harness。` |
| `问题不是通用 benchmark 无用，而是...` | `通用 benchmark 提供总体能力信号；仓库级未来估计需要单独建模。` |
| `Barcarolle 的输出不是原始任务列表，而是...` | `Barcarolle 输出带 source、oracle、split、fallback、ACUT 边界和验证规则的 release。` |
| `Benchmark 选择不是随机抽题。` | `Benchmark 选择需要显式建模 support、fallback 和 baseline。` |
| `这些是 traction evidence，不是 predictive-validity result。` | `这些结果属于 traction evidence；预测效度仍待未来验证。` |
| `Barcarolle 本身不是 license 产品。` | `Agent License 可以使用 Barcarolle 作为 deployment governance 的 evidence layer。` |

### Process-Language Ban

Do not expose these in reader-facing V2 material:

```text
M6
M5
V1
V2
runbook
closeout
Visual QA
AI 写
claim spine
proof object
source evidence
claim limit
placeholder
用户自有值
旧 PPT
读者不关心
我们刚才讨论
这份材料
先看看下一轮效果
```

Use file versions only in internal runbook/process/QA artifacts.

## Worker Prompt

Use this prompt to start the execution worker:

```text
You are executing docs/experiments/barcarolle-project-showcase-deck-pruning-style-polish-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read this runbook and follow it with step-level acceptance and scoped
commits.

Main goal: revise the active Chinese project-showcase deck by auditing all
slides for duplicate content, merging or deleting slides that do not have a
unique reader-facing role, preserving retained slides' top-level title labels,
and removing AI-like binary reframing such as "不是……而是……" and "是……不是……"
from reader-facing materials.

Do not only redraw repeated diagrams. Start with a page-responsibility matrix.
Do not change evidence numbers, score tables, task IDs, split labels, source
eligibility, task statements, hidden-oracle material, or completed experiment
decisions. Do not claim predictive validity or tuning-loop improvement has
been established. Do not run paid ACUT cells, paid LLM calls, external reviewer
calls, or public browsing. Do not use imagegen or decorative generated images.
```

## Step 0: Preflight And Text Extraction

Actions:

1. Record branch, HEAD, date, worktree status, and input availability in the
   process report.
2. Extract V1 PPTX text to an ignored scratch path.
3. Record V1 slide count and visible top-level title labels.
4. Search V1 PPTX text and V1 outline for:
   - binary reframe patterns;
   - repeated workflow vocabulary;
   - repeated slide roles.
5. Record known issues without changing deck content yet.

Acceptance:

- no paid/external calls made;
- V1 text extraction succeeded;
- process report records V1 slide count and title labels;
- initial duplicate/style issues are recorded.

Suggested commit:

```text
Record showcase deck pruning preflight
```

## Step 1: Page Responsibility Matrix

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/page-responsibility-matrix-v2.zh.md
```

2. Audit all V1 slides, not just the examples named by the user.
3. Use the page responsibility standard above.
4. Decide keep / merge / delete for each slide.
5. For every merge/delete decision, state:
   - why the page lacks a unique role;
   - where the useful content goes;
   - which facts or visuals must survive;
   - what will be removed.

Acceptance:

- matrix covers every V1 slide;
- deletion/merge candidates are explicitly justified;
- retained slides have unique roles;
- the matrix considers Slide 1/5, Slide 5/6/7/13, Slide 10/13,
  Slide 11/12, and Slide 14/15 overlap;
- target slide count is stated before deck editing begins.

Suggested commit:

```text
Draft showcase deck page responsibility matrix
```

## Step 2: Duplication Audit And Pruning Plan

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/duplication-audit-v2.zh.md
```

2. Audit duplication across:
   - page roles;
   - visual objects;
   - key vocabulary;
   - evidence numbers;
   - release/freeze/validation process elements;
   - productization framing.
3. A simple local script may be used in ignored scratch space to compute
   repeated terms or slide-to-slide text overlap, but manual judgment is
   required.
4. Convert the audit into a pruning plan:
   - final slide order;
   - slide count;
   - merge map;
   - unique role of every retained slide;
   - flow/process visual distribution.

Acceptance:

- duplication audit exists;
- it identifies all material repetitions that affect reader comprehension;
- pruning plan states which slides are deleted or merged;
- no retained pair repeats the same primary visual role;
- compiler workflow, prediction target, algorithm environment, and future
  validation are assigned to distinct slides.

Suggested commit:

```text
Audit duplicate content in showcase deck
```

## Step 3: Draft V2 Outline

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md
```

2. Apply the pruning plan.
3. Preserve top-level title labels for retained slides.
4. For each retained slide, specify:
   - retained V1 source slide;
   - title label, unchanged;
   - unique reader-facing role;
   - rewritten subtitle/body claim;
   - visual object;
   - content moved in or out;
   - forbidden patterns removed.
5. Avoid visible process labels such as `Claim`, `Proof object`,
   `Source evidence`, and `Claim limit`.
6. Run the binary-reframe and process-language checks against the outline.

Acceptance:

- V2 outline exists;
- slide count matches pruning plan;
- retained slide title labels are unchanged;
- merged/deleted content is accounted for;
- outline contains no reader-facing binary reframe patterns;
- outline contains no reader-facing process vocabulary.

Suggested commit:

```text
Draft pruned showcase deck outline
```

## Step 4: Build V2 PPTX

Actions:

1. Build:

```text
docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v2.zh.pptx
```

2. Use the V2 outline and current V1 deck as sources.
3. Use the Presentations skill and artifact-tool JSX workflow when available:
   - create a thread-scoped presentation workspace under `outputs/...`;
   - choose `engineering-platform` as the primary deck profile;
   - build editable slides;
   - render previews and layout JSON;
   - inspect contact sheet and selected full-size slides;
   - export only after QA passes;
   - copy only the final PPTX into the package directory.
4. Keep retained slide top-level title labels unchanged.
5. Reduce repeated visual structures:
   - one complete compiler workflow slide at most;
   - prediction target should not look like the compiler workflow;
   - future validation route should not duplicate the compiler workflow;
   - productization pages should use distinct visual grammars if both remain.
6. Preserve claim boundaries and key evidence numbers where they still serve
   the revised argument.

Acceptance:

- V2 PPTX exists and is editable;
- slide count matches V2 outline;
- retained top-level title labels are unchanged;
- no deleted slide remains by accident;
- no reader-facing binary reframe pattern appears;
- visual repetition is materially reduced;
- predictive validity and tuning-loop improvement remain unproven.

Suggested commit:

```text
Build pruned showcase presentation deck
```

## Step 5: Text Style Audit

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/text-style-audit-v2.zh.md
```

2. Extract V2 PPTX text to an ignored scratch path.
3. Run these checks against V2 outline, README changes, and extracted PPTX
   text:

```bash
rg -n "不是|而是|不只是|不再是|是[^。；，\\n]{0,30}不是|not .*but|not .*rather|not .*instead" docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md
rg -n "M6|M5|runbook|closeout|Visual QA|AI 写|claim spine|proof object|source evidence|claim limit|placeholder|用户自有值|旧 PPT|读者不关心|我们刚才讨论|这份材料|先看看下一轮效果" docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md
rg -n "已证明预测效度|预测效度已(经)?建立|已经建立预测效度|已经证明.*调优|调优.*已经证明|已验证.*调优闭环|模型能力更强" docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md
rg -n "/Users/chenmohan/Downloads" docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md
git diff --check
```

4. Run the same checks on extracted PPTX text.
5. Run the `audit-ai-tropes` scanner on the V2 outline and extracted PPTX text:

```bash
python3 /Users/chenmohan/.codex/skills/audit-ai-tropes/scripts/audit_ai_tropes.py docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v2.zh.md --format markdown
```

Use the scanner as a heuristic. Fix repeated sentence templates, inflated
diction, and unnecessary symmetrical contrasts. Do not weaken technical claims
just to satisfy a heuristic.

Acceptance:

- text-style audit exists;
- binary reframe checks pass on reader-facing V2 materials;
- process-language checks pass on reader-facing V2 materials;
- overclaim checks pass;
- local path checks pass;
- `git diff --check` passes;
- any scanner findings left unfixed are explained.

Suggested commit:

```text
Audit showcase deck style and claims
```

## Step 6: Visual QA And Reader Repetition Review

Actions:

1. Create:

```text
docs/research/barcarolle-project-showcase-deck-zh/visual-qa-report-v2.zh.md
```

2. Render contact sheet and selected full-size previews.
3. Review as a skeptical reader:
   - Does any slide feel redundant after the previous slide?
   - Does any retained page repeat the same workflow or proof object?
   - Can the reader state each slide's unique role?
   - Does any visual resemble a lightly edited copy of another visual?
   - Are top-level title labels unchanged for retained slides?
   - Are all subtitles and body text readable?
   - Is any slide too dense after merged content?
   - Are there any binary-reframe or process-language residues?
4. If a slide fails, repair it and rerun preview QA.

Acceptance:

- visual QA report exists;
- contact sheet was inspected;
- selected full-size slides were inspected;
- no clipped text or incoherent overlap remains;
- no repeated workflow/proof-object sequence remains without a clear purpose;
- slide count and merge/delete decisions match the matrix;
- deck can be read without V1 or old M6 materials open beside it.

Suggested commit:

```text
Complete visual QA for pruned showcase deck
```

## Step 7: Handoff Updates

Actions:

1. Update:

```text
docs/research/barcarolle-project-showcase-deck-zh/README.md
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

2. Handoff should state:
   - V2 is the active Chinese project-showcase deck;
   - V1 remains reference;
   - V2 was pruned for page responsibility and duplicate content;
   - retained slide title labels were preserved;
   - reader-facing binary reframe patterns were removed;
   - predictive validity and tuning-loop improvement remain unproven.

Acceptance:

- handoff docs point to V2;
- `PROCESS.md` remains concise;
- old approval decks remain reference material only;
- no handoff implies V2 proves predictive validity.

Suggested commit:

```text
Align pruned showcase deck handoff
```

## Step 8: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_pruning_style_process.md
experiments/phase1_compiler/reports/barcarolle_project_showcase_deck_pruning_style_decision.md
experiments/phase1_compiler/results/barcarolle_project_showcase_deck_pruning_style_decision.json
```

2. Stop with one label:

```text
barcarolle_project_showcase_deck_pruning_style_complete
blocked_page_responsibility_unclear
blocked_duplicate_content_remains
blocked_retained_titles_changed
blocked_binary_reframe_language_remains
blocked_process_language_remains
blocked_visual_qa_failed
blocked_pptx_generation_tool_unavailable
```

Decision report must state:

- whether V2 is complete;
- V2 slide count and deleted/merged slides;
- whether retained slide title labels were preserved;
- where the page responsibility matrix, duplication audit, V2 outline, V2
  PPTX, style audit, and visual QA report are;
- whether binary reframe and process-language audits passed;
- whether visual repetition was reduced;
- whether predictive validity and tuning-loop improvement remain unproven;
- whether paid/external calls or generated images were used.

Suggested commit:

```text
Close showcase deck pruning and style polish
```

## Final Report Expectations

The closeout should say:

```text
What changed:
  The project-showcase deck was pruned at page level, not just redrawn. Duplicate
  page roles were merged or removed, retained title labels were preserved, and
  reader-facing binary reframe language was removed.

Why it matters:
  The deck should now feel less like a generated artifact and more like a
  deliberate presentation where each page has a distinct role.

What remains:
  Review V2 for audience-specific emphasis before circulation. Do not restore
  deleted duplicate pages or binary-reframe phrasing.
```

Do not draft another follow-up runbook unless the user explicitly asks after
reviewing V2.
