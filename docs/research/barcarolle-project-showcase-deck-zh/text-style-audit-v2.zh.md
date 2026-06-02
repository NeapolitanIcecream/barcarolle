# Barcarolle 项目展示 Deck 文本风格审计 V2

状态：文本风格与声明审计，2026-06-02。

## Scope

审计对象：

- `showcase-deck-outline-v2.zh.md`
- `barcarolle-project-showcase-deck-v2.zh.pptx` 的抽取文本

PPTX 文本抽取位置：

```text
outputs/manual-20260602-114006-showcase-pruning/presentations/barcarolle-project-showcase-deck-pruning-style/qa/v2-pptx-text.txt
```

Scanner 输出位置：

```text
outputs/manual-20260602-114006-showcase-pruning/presentations/barcarolle-project-showcase-deck-pruning-style/qa/outline-ai-tropes-v2.md
outputs/manual-20260602-114006-showcase-pruning/presentations/barcarolle-project-showcase-deck-pruning-style/qa/pptx-ai-tropes-v2.md
```

`README.md` 的 V2 handoff 尚未在本步骤更新；handoff 更新后会重新运行同类检查。

## Result

结论：通过。

| 检查项 | 结果 |
| --- | --- |
| 二分式句法检查 | `0` matches |
| reader-facing process-language 检查 | `0` matches |
| 预测效度和调优效果过度声明检查 | `0` matches |
| 本机 Downloads 路径检查 | `0` matches |
| `git diff --check` | passed |

检查对象包括 V2 outline 和 V2 PPTX 抽取文本。

## Scanner Findings

`audit-ai-tropes` scanner findings:

| Source | Finding | Disposition |
| --- | --- | --- |
| V2 outline | `short punchy fragment run` | Accepted as a false positive from slide-by-slide outline metadata and bullets. |
| V2 outline | unicode quotation marks around one cited phrase | Accepted in internal outline metadata; not part of PPTX visible copy. |
| V2 outline | repeated `harness` | Accepted technical term required by ACUT boundary explanation. |
| V2 PPTX text | repeated `harness` | Accepted technical term required by ACUT boundary explanation. |

Manual review found no remaining reader-facing drafting instructions, prompt-like comments, old-stage labels, or visible binary-reframe language in the target PPTX text.

## Claim Boundary

The V2 deck preserves these boundaries:

- predictive validity remains unproven;
- tuning-loop improvement remains unproven;
- adapter differences are reported as named ACUT configuration evidence;
- current MAE evidence is presented as traction with a small edge;
- no paid or external calls were used for this revision.
