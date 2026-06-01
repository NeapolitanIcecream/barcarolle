# Proposal Approval Packet Chinese Supplement Runbook

Status: supplemental approval-packet localization runbook, 2026-06-01.

## Goal

Deliver a Chinese-language version of the completed M6 approval packet and make
the Chinese packet the active editing surface for later reviewer-facing work.

Plain-language target:

```text
把英文 M6 立项交付包改写成中文主线材料：中文 PPT、中文一页摘要、
中文证据附录、中文检查清单和术语表。后续修改优先改中文版材料，
英文 M6 包保留为来源和审计基准。
```

This is not a new experiment, new proposal argument, or new evidence run. It is
translation, localization, presentation QA, and handoff realignment.

## Translation Thesis

Do not perform a literal sentence-by-sentence translation when that would make
the material harder to read in Chinese. The Chinese packet should be a
decision-facing rewrite that preserves all claims, numbers, caveats, and
evidence boundaries from the English packet.

Use this framing:

```text
The Chinese packet is the active approval packet for future edits.
The English M6 packet remains the source/reference version.
V5 remains the long-form source of truth.
Predictive validity and tuning-loop improvement remain unproven.
```

## Boundary

Allowed:

- create a Chinese approval-packet directory;
- translate and reader-optimize the executive summary, deck outline, evidence
  appendix, checklist, and PPTX;
- create a Chinese terminology/glossary file to stabilize future edits;
- reuse the English M6 deck structure and proof objects;
- adjust slide line breaks, font sizes, and layout for Chinese text;
- update roadmap and `PROCESS.md` after the Chinese packet passes;
- add process and decision closeout artifacts.

Not allowed:

- paid ACUT solver calls;
- paid LLM calls;
- external reviewer calls;
- public browsing;
- changing score tables, selected task IDs, split labels, source eligibility,
  task statements, hidden-oracle material, or completed experiment decisions;
- adding new evidence or deleting caveats;
- claiming predictive validity has been established;
- claiming Barcarolle has already improved an agent tuning loop;
- turning the Chinese deck into a broader sales/marketing deck;
- using `imagegen`, decorative generated images, or generated raster assets;
- silently replacing unresolved user-owned placeholders with invented values;
- making the English packet the future editing surface after this supplement
  completes.

## Required Inputs

Read first:

```text
AGENTS.md
PROCESS.md
docs/experiments/proposal-approval-packet-m6-runbook.md
experiments/phase1_compiler/reports/proposal_approval_packet_m6_decision.md
docs/research/barcarolle-proposal-report-v5.md
docs/research/m6-approval-packet/executive-summary-v1.md
docs/research/m6-approval-packet/approval-deck-outline-v1.md
docs/research/m6-approval-packet/appendix-evidence-index-v1.md
docs/research/m6-approval-packet/approval-packet-checklist-v1.md
docs/research/m6-approval-packet/barcarolle-approval-deck-v1.pptx
```

Use the English M6 packet as the direct source for Chinese artifacts. Use V5
only to resolve claim-boundary ambiguity or evidence traceability.

If working in a Codex desktop environment with the Presentations skill
available, use its editable artifact-tool workflow for the Chinese PPTX. Do
not use `python-pptx`, direct OOXML edits, or LibreOffice round trips for the
final deck when the Presentations workflow is available.

## Expected Outputs

Create:

```text
docs/research/m6-approval-packet-zh/README.md
docs/research/m6-approval-packet-zh/terminology-glossary-v1.zh.md
docs/research/m6-approval-packet-zh/executive-summary-v1.zh.md
docs/research/m6-approval-packet-zh/approval-deck-outline-v1.zh.md
docs/research/m6-approval-packet-zh/appendix-evidence-index-v1.zh.md
docs/research/m6-approval-packet-zh/approval-packet-checklist-v1.zh.md
docs/research/m6-approval-packet-zh/barcarolle-approval-deck-v1.zh.pptx
```

Optional only if final committed, auditable assets are needed:

```text
docs/research/m6-approval-packet-zh/assets/
```

Do not commit temporary presentation workspaces, preview images, contact
sheets, generated slide source, scratch scripts, layout JSON, or extracted
PPTX text unless explicitly promoted as final audit artifacts.

Create closeout artifacts:

```text
experiments/phase1_compiler/reports/proposal_approval_packet_zh_supplement_process.md
experiments/phase1_compiler/reports/proposal_approval_packet_zh_supplement_decision.md
experiments/phase1_compiler/results/proposal_approval_packet_zh_supplement_decision.json
```

Update if the supplement succeeds:

```text
docs/research/phase-1-proposal-roadmap-and-claim-planning.md
PROCESS.md
```

Do not overwrite English M6 artifacts.

## Chinese Material Contract

The Chinese packet must preserve the English M6 packet's structure and
evidence, but it should read like native Chinese decision material.

Reader-facing Chinese style:

- concise, direct, decision-facing;
- use short paragraphs and slide labels;
- preserve English acronyms where they are the clearest terms: `ACUT`, `MAE`,
  `V5`, `PPTX`;
- avoid excessive self-made terminology;
- avoid internal process labels in reader-facing material unless a file path is
  intentionally being cited;
- keep caveats prominent, not buried in footnotes.

Recommended terminology:

| English source term | Chinese working term |
| --- | --- |
| repo-specific benchmark | 面向特定仓库的 benchmark |
| benchmark compiler | benchmark 编译器 |
| target-repository prediction problem | 目标仓库预测问题 |
| predictive validity | 预测效度 |
| Agent Configuration Under Test / ACUT | 被测 Agent 配置（ACUT） |
| current evidence / preliminary evidence | 当前证据 / 初步证据 |
| bounded traction | 有边界的牵引性证据 |
| credible validation path | 可信的验证路径 |
| tuning and regression feedback | 调优与回归反馈 |
| budgeted and gated evaluation | 有预算、有闸门的评测 |
| source of truth | 主参考文本 / 长文论证基准 |
| evidence appendix | 证据附录 |
| claim boundary | 声明边界 |
| fallback | fallback / 回退选择 |

The glossary may refine these terms, but it must keep the claim boundary clear.

## Placeholder Policy

Keep user-owned placeholders visible in Chinese. Do not invent values.

Translate the placeholders as:

```text
[待用户决定：项目人员配置]
[待用户决定：项目周期]
[待用户决定：有闸门 ACUT 评测的预算上限]
[待用户决定：审批路径或审批负责人]
[待用户决定：对外材料中的交付负责人类别]
```

If the English source has a placeholder that should be removed because the
user has since supplied the value, record the user-provided value and source in
the process report before changing the Chinese packet.

## Worker Prompt

Use this prompt to start the execution worker:

```text
You are executing docs/experiments/proposal-approval-packet-zh-supplement-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md and PROCESS.md first.
Then read this runbook and follow it with step-level acceptance and scoped
commits.

Main goal: create a Chinese-language version of the completed M6 approval
packet under docs/research/m6-approval-packet-zh/. The Chinese packet becomes
the active editing surface for later reviewer-facing work. The English M6
packet remains the source/reference version, and V5 remains the long-form
source of truth.

Do not run paid ACUT cells, paid LLM calls, external reviewer calls, or public
browsing. Do not change evidence numbers, score tables, task IDs, split labels,
source eligibility, task statements, hidden-oracle material, or completed
experiment decisions. Do not claim predictive validity or tuning-loop
improvement has been established. Do not use imagegen or decorative generated
images. Keep user-owned placeholders visible unless the user has provided the
values in the current conversation or committed context.
```

## Step 0: Preflight And Source Audit

Actions:

1. Record branch, HEAD, date, worktree status, and input availability in the
   process report.
2. Confirm the English M6 decision stop label is:

```text
proposal_approval_packet_m6_complete
```

3. Confirm the source artifacts exist:
   - English PPTX;
   - English executive summary;
   - English deck outline;
   - English evidence appendix;
   - English checklist.
4. Create:

```text
docs/research/m6-approval-packet-zh/
```

5. Record that the Chinese packet will become the active editing surface after
   this supplement passes.

Acceptance:

- no paid/external calls made;
- source artifacts are present;
- process report records the English source packet and V5 source-of-truth role;
- no Chinese artifacts drafted yet except directory setup if needed.

Suggested commit:

```text
Record Chinese approval packet preflight
```

## Step 1: Create Chinese Glossary And README

Actions:

1. Create:

```text
docs/research/m6-approval-packet-zh/README.md
docs/research/m6-approval-packet-zh/terminology-glossary-v1.zh.md
```

2. README must state:
   - Chinese packet is the active editing surface after completion;
   - English M6 packet is source/reference;
   - V5 is the long-form source of truth;
   - predictive validity and tuning-loop improvement remain unproven;
   - user-owned placeholders remain visible.
3. Glossary must define stable Chinese terms for:
   - Barcarolle;
   - repo-specific benchmark;
   - benchmark compiler;
   - ACUT;
   - predictive validity;
   - MAE;
   - fallback;
   - tuning and regression feedback;
   - budgeted and gated evaluation;
   - claim boundary.

Acceptance:

- README and glossary exist;
- terminology is concise and suitable for later edits;
- glossary does not over-explain or invent new concepts;
- future editors can tell which files to modify first.

Suggested commit:

```text
Add Chinese packet glossary and handoff
```

## Step 2: Deliver Chinese Markdown Packet

Actions:

1. Create:

```text
docs/research/m6-approval-packet-zh/executive-summary-v1.zh.md
docs/research/m6-approval-packet-zh/approval-deck-outline-v1.zh.md
docs/research/m6-approval-packet-zh/appendix-evidence-index-v1.zh.md
```

2. Translate and localize from the English M6 Markdown artifacts.
3. Preserve every key number exactly:

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
6/18
6/6
1000
```

4. Preserve all current non-claims:
   - no formal predictive validity claim;
   - no tuning-loop improvement claim;
   - no model-only superiority claim;
   - no ungated paid-evaluation authorization.
5. Keep placeholders visible in Chinese.

Acceptance:

- Chinese summary, outline, and appendix exist;
- each artifact reads naturally in Chinese;
- all key numbers are present and unchanged where relevant;
- claim limits are at least as visible as in English;
- no local `/Users/chenmohan/Downloads` paths appear.

Suggested commit:

```text
Draft Chinese approval packet markdown
```

## Step 3: Build Chinese PPTX

Actions:

1. Build:

```text
docs/research/m6-approval-packet-zh/barcarolle-approval-deck-v1.zh.pptx
```

2. Use the English PPTX and Chinese outline as sources.
3. Keep the same 12-slide decision story unless Chinese readability requires a
   minor merge or split. If slide count changes, record the reason in the
   process report.
4. Use Chinese-friendly fonts such as `PingFang SC`, `Noto Sans CJK SC`, or
   another available CJK font. Record the chosen font.
5. Refit text manually:
   - no clipped Chinese text;
   - no line collisions;
   - no evidence table overflow;
   - placeholders remain readable;
   - diagrams remain interpretable at slide size.
6. If using the Presentations skill, follow its artifact-tool JSX workflow and
   render previews/contact sheets before export.
7. Do not use generated images or decorative raster assets.

Acceptance:

- Chinese PPTX exists;
- it is editable;
- it preserves the English deck story and claim boundary;
- Chinese text fits on every slide;
- rendered preview or equivalent visual QA passes.

Suggested commit:

```text
Build Chinese approval presentation deck
```

## Step 4: Chinese Packet Audit

Actions:

1. Create:

```text
docs/research/m6-approval-packet-zh/approval-packet-checklist-v1.zh.md
```

2. Checklist must cover:
   - Chinese packet active-editing status;
   - English M6 source/reference preservation;
   - V5 long-form source-of-truth preservation;
   - evidence number preservation;
   - predictive-validity non-claim;
   - tuning-loop non-claim;
   - placeholder visibility;
   - PPTX readability;
   - no generated-image usage.
3. Extract Chinese PPTX text to an ignored scratch path and audit it together
   with Chinese Markdown.
4. Run English and Chinese overclaim checks:

```bash
rg -n "validated predictive benchmark compiler|established predictive validity|tuning validation established|improves agent tuning|multi-ACUT residual validity established" docs/research/m6-approval-packet-zh/*.md
rg -n "已证明预测效度|预测效度已(经)?建立|已经建立预测效度|已经证明.*调优|调优.*已经证明|已证明.*tuning|已验证.*调优闭环|模型能力更强" docs/research/m6-approval-packet-zh/*.md
rg -n "/Users/chenmohan/Downloads" docs/research/m6-approval-packet-zh/*.md
git diff --check
```

5. Run the same checks against extracted PPTX text.

Acceptance:

- checklist exists and passes;
- Markdown checks pass or every intentional match is explained;
- PPTX text checks pass or every intentional match is explained;
- `git diff --check` passes;
- visual QA confirms no clipped Chinese text.

Suggested commit:

```text
Audit Chinese approval packet
```

## Step 5: Update Handoff State

Actions:

1. Update roadmap to add the Chinese supplement under M6 and state that the
   Chinese packet is the active editing surface for subsequent reviewer-facing
   revisions.
2. Update `PROCESS.md` with a concise current-state entry:
   - Chinese packet produced;
   - English packet remains source/reference;
   - V5 remains long-form source of truth;
   - future edits should target Chinese packet first;
   - predictive validity and tuning-loop improvement remain unproven.

Acceptance:

- handoff docs point future editing to `docs/research/m6-approval-packet-zh/`;
- `PROCESS.md` remains concise;
- no stale handoff says the English packet is the only active reviewer-facing
  artifact.

Suggested commit:

```text
Align Chinese approval packet handoff
```

## Step 6: Closeout

Actions:

1. Write:

```text
experiments/phase1_compiler/reports/proposal_approval_packet_zh_supplement_process.md
experiments/phase1_compiler/reports/proposal_approval_packet_zh_supplement_decision.md
experiments/phase1_compiler/results/proposal_approval_packet_zh_supplement_decision.json
```

2. Stop with one label:

```text
proposal_approval_packet_zh_supplement_complete
blocked_chinese_pptx_generation_tool_unavailable
blocked_translation_claim_boundary_unclear
blocked_chinese_packet_overclaims
blocked_chinese_layout_unreadable
blocked_missing_m6_source_artifacts
```

Decision report must state:

- whether the Chinese packet is complete;
- where the Chinese PPTX, summary, outline, appendix, checklist, glossary, and
  README are;
- whether Chinese packet is now the active editing surface;
- whether English M6 remains source/reference;
- whether V5 remains the long-form source of truth;
- whether claims and key numbers were preserved;
- whether generated images or paid/external calls were used;
- what user-owned placeholders remain.

Suggested commit:

```text
Close Chinese approval packet supplement
```

## Final Report Expectations

The closeout should say:

```text
What changed:
  The English M6 approval packet was localized into a Chinese approval packet
  with PPTX, one-page summary, deck outline, evidence appendix, checklist,
  README, and glossary.

Why it matters:
  Future reviewer-facing edits can now happen on the Chinese materials instead
  of repeatedly translating from the English packet.

What remains:
  Fill or explicitly leave visible the staffing, duration, gated-evaluation
  budget, approval-path, and owner-category placeholders before circulation.
```

Do not draft a follow-up runbook unless the user explicitly asks after
reviewing the Chinese packet.
