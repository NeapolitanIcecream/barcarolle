# Barcarolle 项目展示 Deck V3 文本风格审计

状态：V3 text and claim audit，2026-06-02。

## Scope

审计对象：

- `docs/research/barcarolle-project-showcase-deck-zh/showcase-deck-outline-v3.zh.md`
- `docs/research/barcarolle-project-showcase-deck-zh/barcarolle-project-showcase-deck-v3.zh.pptx` 的抽取文本

PPTX 文本抽取位置：

```text
outputs/019e8755-8880-7371-835c-73415d32af4a/presentations/barcarolle-project-showcase-deck-v3/qa/v3-pptx-text.txt
```

## Required Checks

| Check | Target | Result |
| --- | --- | --- |
| forbidden residue pattern | V3 outline | `0` matches |
| forbidden residue pattern | extracted V3 PPTX text | `0` matches |
| overclaim pattern | V3 outline and extracted PPTX text | `0` matches |
| local Downloads path | project-showcase Markdown files | `0` matches |
| PPTX zip integrity | V3 PPTX | passed |

Forbidden residue pattern checked:

```text
被测 ACUT|但不负责|不接管|不是|而是|是[^。；，\n]{0,30}不是|runbook|handoff|M1|M2|M3|M4|M5|M6|过程性文本|AI 写|我们刚才讨论|读者不关心
```

Overclaim pattern checked:

```text
已证明预测效度|预测效度已(经)?建立|已经建立预测效度|已经证明.*调优|调优.*已经证明|已验证.*调优闭环|模型能力更强
```

## Scanner Findings

`audit-ai-tropes` scanner findings:

| Source | Finding | Disposition |
| --- | --- | --- |
| V3 outline | `short punchy fragment run` | Accepted false positive from slide-outline metadata, headings, and table-like structure. |
| V3 outline | stock diction: `harness` | Accepted technical term required by ACUT boundary explanation. |
| V3 PPTX text | repeated sentence openings around `simple same-budget baseline` | Accepted false positive from evidence labels on the algorithm slide. |
| V3 PPTX text | stock diction: `harness` | Accepted technical term required by the ACUT boundary slide. |

## Accepted Technical Terms

The following terms remain because they preserve technical meaning:

```text
ACUT
benchmark
release
harness
solver workspace
verifier workspace
hidden oracle
captured diff
source quality
support
fallback
adapter
named ACUT configuration
MAE
outcome-unseen
future holdout
rolling-origin
dev / eval / canary
scorecard
regression signal
```

## Claim Boundary

V3 preserves these boundaries:

- predictive validity remains unproven;
- tuning-loop improvement remains unproven;
- adapter differences are reported as named ACUT configuration evidence;
- MAE evidence is presented as traction with a small edge;
- no paid ACUT calls, paid LLM calls, external reviewer calls, imagegen, or generated raster assets were used for the revision.
