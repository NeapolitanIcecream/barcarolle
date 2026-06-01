# Proposal Approval Packet Chinese Supplement Process

Status: in progress, 2026-06-01.

## Step 0: Preflight And Source Audit

Recorded: 2026-06-01 22:54:35 CST.

Branch:

```text
codex/restart-benchmark-compiler
```

HEAD:

```text
5559d467e8769da4f7db685e6d9f770c9d648f92
```

Initial worktree status before Chinese supplement edits:

```text
 M PROCESS.md
 M docs/research/phase-1-proposal-roadmap-and-claim-planning.md
?? docs/experiments/proposal-approval-packet-zh-supplement-runbook.md
```

These pre-existing changes point the handoff state at the Chinese supplement
runbook and are treated as related setup context for this execution.

Input availability:

| Input | Status |
| --- | --- |
| `AGENTS.md` | present and read |
| `PROCESS.md` | present and read |
| `docs/experiments/proposal-approval-packet-m6-runbook.md` | present and read |
| `experiments/phase1_compiler/reports/proposal_approval_packet_m6_decision.md` | present and read |
| `docs/research/barcarolle-proposal-report-v5.md` | present and read |
| `docs/research/m6-approval-packet/executive-summary-v1.md` | present and read |
| `docs/research/m6-approval-packet/approval-deck-outline-v1.md` | present and read |
| `docs/research/m6-approval-packet/appendix-evidence-index-v1.md` | present and read |
| `docs/research/m6-approval-packet/approval-packet-checklist-v1.md` | present and read |
| `docs/research/m6-approval-packet/barcarolle-approval-deck-v1.pptx` | present |

The English M6 decision report records the stop label:

```text
proposal_approval_packet_m6_complete
```

Source packet role:

- The English M6 packet under `docs/research/m6-approval-packet/` is the
  source/reference packet for the Chinese supplement.
- `docs/research/barcarolle-proposal-report-v5.md` remains the long-form
  source of truth for claim-boundary and evidence-traceability questions.
- The Chinese packet under `docs/research/m6-approval-packet-zh/` will become
  the active editing surface after this supplement passes.

Boundary status:

- Paid ACUT solver calls: `0`.
- Paid LLM calls: `0`.
- External reviewer calls: `0`.
- Public browsing: `false`.
- Score tables, selected task IDs, split labels, source eligibility, task
  statements, hidden-oracle material, and completed experiment decisions were
  not changed.
- No Chinese reader-facing artifacts have been drafted yet.

## Step 1: Chinese Glossary And Handoff

Recorded: 2026-06-01.

Created:

```text
docs/research/m6-approval-packet-zh/README.md
docs/research/m6-approval-packet-zh/terminology-glossary-v1.zh.md
```

The README records that, after this supplement passes, the Chinese packet is
the active editing surface for later reviewer-facing revisions. It also records
that the English M6 packet remains the source/reference version and V5 remains
the long-form source of truth.

The glossary stabilizes concise Chinese terms for Barcarolle, repo-specific
benchmark, benchmark compiler, ACUT, predictive validity, MAE, fallback, tuning
and regression feedback, budgeted and gated evaluation, and claim boundary.

User-owned placeholders remain visible in Chinese:

```text
[待用户决定：项目人员配置]
[待用户决定：项目周期]
[待用户决定：有闸门 ACUT 评测的预算上限]
[待用户决定：审批路径或审批负责人]
[待用户决定：对外材料中的交付负责人类别]
```

Boundary status:

- Predictive validity remains unproven.
- Tuning-loop improvement remains unproven.
- No paid ACUT solver calls, paid LLM calls, external reviewer calls, public
  browsing, generated images, or decorative raster assets were used.

## Step 2: Chinese Markdown Packet

Recorded: 2026-06-01.

Created:

```text
docs/research/m6-approval-packet-zh/executive-summary-v1.zh.md
docs/research/m6-approval-packet-zh/approval-deck-outline-v1.zh.md
docs/research/m6-approval-packet-zh/appendix-evidence-index-v1.zh.md
```

Source artifacts:

- `docs/research/m6-approval-packet/executive-summary-v1.md`
- `docs/research/m6-approval-packet/approval-deck-outline-v1.md`
- `docs/research/m6-approval-packet/appendix-evidence-index-v1.md`
- `docs/research/barcarolle-proposal-report-v5.md`

Localization notes:

- The Chinese text is a decision-facing rewrite, not a sentence-by-sentence
  literal translation.
- The English M6 packet remains the source/reference version.
- V5 remains the long-form source of truth.
- User-owned placeholders remain visible in Chinese.

Key-number preservation:

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

Non-claim preservation:

- Predictive validity remains unproven.
- Tuning-loop improvement remains unproven.
- Adapter differences are not reported as model-only superiority.
- Paid evaluation remains budgeted and gated.

Audit commands run after drafting:

```bash
rg -n "0\.3148|0\.7481|0\.25|0\.125|120/120|1\.0|30/30|0\.209|0\.2149|0\.0059|93\.4%|6/18|6/6|1000" docs/research/m6-approval-packet-zh/{executive-summary-v1.zh.md,approval-deck-outline-v1.zh.md,appendix-evidence-index-v1.zh.md}
rg -n "validated predictive benchmark compiler|established predictive validity|tuning validation established|improves agent tuning|multi-ACUT residual validity established" docs/research/m6-approval-packet-zh/*.md
rg -n "已证明预测效度|预测效度已(经)?建立|已经建立预测效度|已经证明.*调优|调优.*已经证明|已证明.*tuning|已验证.*调优闭环|模型能力更强" docs/research/m6-approval-packet-zh/*.md
rg -n "/Users/chenmohan/Downloads" docs/research/m6-approval-packet-zh/*.md
git diff --check
```

Expected result: key-number search returns all required numbers; overclaim and
local-path checks return no matches; `git diff --check` passes.
