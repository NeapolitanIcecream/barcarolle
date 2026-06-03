# Barcarolle 项目展示 Deck V4 术语减负审计

状态：V4 terminology reduction audit，2026-06-03。

用途：在 V4 PPTX 编辑前锁定逐页术语替换。原则是能翻译就翻译；必须保留的技术词首次出现时用短中文解释。

## Replacement Rules

| V3 term | V4 replacement or explanation |
| --- | --- |
| target-repo | 目标仓库 |
| future work | 未来工作 |
| benchmark release | 评测 release / 仓库级评测包 |
| selector | 任务选择器 |
| selection | 任务选择 |
| support | 样本支撑 |
| fallback | 兜底来源；必要时保留 `fallback` 并解释为“支撑不足时的替代来源” |
| baseline | 对照基线 |
| source caps | 来源上限 |
| slice stability | 切片稳定性 |
| outcome-unseen | 未看未来结果 |
| prediction gap | 预测缺口 |
| scorecard | 结果卡 / scorecard |
| regression signal | 回归信号 |

## Slide-By-Slide Audit

| Slide | Heavy terms in V3 | V4 replacement or explanation | Accepted terms |
| --- | --- | --- | --- |
| 1 项目定位 | benchmark release, repo-specific release, harness, prompt, runtime budget, solver-visible, diff capture, verifier replay, score/cost/latency accounting | 主标题改为“仓库级评测包”；正文用“目标仓库”“未来仓库工作”“可冻结 release”。ACUT 首次解释保留；边界说明拆成“Barcarolle 组织 release evidence”和“ACUT 保留 harness / prompt / tools / model / budget”。 | ACUT, release, harness, prompt |
| 2 问题与代价 | target-repo future-work evidence, benchmark score, prediction gap, deployment choice, configuration tuning, governance decision, review norms, failure modes | 副标题改为“部署、调优和治理都需要目标仓库未来证据”。gap 写作“预测缺口”；下方三项改为“部署选择”“配置调优”“治理决策”。 | benchmark |
| 3 相关工作与缺口 | coding-agent evaluation, outcome-unseen release selection, quality gate, source caps, support, selection rule, executable environment, verifier material | 保留相关工作英文专名；表头和解释用中文。`outcome-unseen` 改为“未看未来结果”；`quality gate` 改为“质量门槛”；`source caps` 改为“来源上限”。 | SWE-bench, SWE-bench Verified, SWE-bench-Live, SWE-Bench++, SWE-smith, R2E-Gym |
| 4 研究目标 | outcome-unseen predictive validity, benchmark score, MAE, benchmark estimate, observed future performance, claim boundary | 标题改为“未看未来结果时，评测分数要贴近真实表现”。MAE 首次解释为“平均绝对误差”；公式保留必要英文变量。 | MAE, W_r(a) |
| 5 方法 | supply, support, selection rule, split, fallback labels, replayability, oracle, leakage, source quality, environment, ambiguity, score / refresh | 正文改用“候选供应、任务认证、目标画像、组装规则、冻结 release、结果与刷新”。认证维度压缩成中文 checklist。 | release, oracle |
| 6 执行边界 | solver workspace, captured diff, verifier workspace, hidden oracle, ACUT harness, adapter, terminal status, sanitized artifacts | 标题保留 solver / verifier 作为边界术语；每个术语在图内用中文说明。`hidden oracle` 解释为“验证侧材料”。 | solver workspace, verifier workspace, hidden oracle, ACUT |
| 7 算法问题 | task selection, target-repo estimate, support, fallback, baseline comparison, compiler algorithm, weighted target-profile design, sparse support | 标题改为“任务选择器决定有限预算估计”。正文用“样本支撑、兜底来源、来源上限、切片稳定性、对照基线”。旧 weighted 只作历史诊断。 | selector（括注）, fallback（括注） |
| 8 当前证据 | source repair, MAE signal, Reader question, Evidence, Current reading, random, validity claim, tuning-loop improvement | 表头改中文；问题改为“协议能跑通吗、source 质量能修复吗、选择器是否有初步信号、现在还不能证明什么”。 | source, MAE |
| 9 研究路线 | task-selection algorithm evolution, future holdout, rolling-origin validation, candidate supply, feature support, random/simple baselines, practical MAE margin, freeze release, named ACUTs | 标题改为“下一步是改进任务选择器并冻结验证”。`future holdout` 和 `rolling-origin` 保留为验证路线名，旁边用中文解释。 | future holdout, rolling-origin, ACUT, MAE |
| 10 Agent License | deployment governance, scoped evidence, risk status, uncertainty, evidence layer, source quality, scoped use decision, adapter note | 标题保留产品名 Agent License；正文用“部署治理、证据范围、风险状态、不确定性、使用范围决定”。输出项中文化。 | Agent License, ACUT |
| 11 Agent Tuning | dev feedback, eval release, canary release, failure taxonomy, scorecard, regression signal, runtime budget, future validation material | 标题保留产品名 Agent Tuning；图内保留 dev / eval / canary，并分别解释为“开发反馈 / 评测 release / 金丝雀 release”。`regression signal` 改为“回归信号”。 | Agent Tuning, dev, eval, canary |

## Accepted Technical Terms

V4 可保留以下术语，因为中文替换会降低精度或破坏已知产品/研究对象名称：

```text
ACUT
benchmark
release
harness
prompt
solver workspace
verifier workspace
hidden oracle
source
oracle
MAE
W_r(a)
future holdout
rolling-origin
Agent License
Agent Tuning
dev / eval / canary
```

## QA Rules

- 同一短句中避免堆叠三个以上未解释英文术语。
- 表头默认中文。
- 第一次出现 ACUT 时解释完整含义。
- 第一次出现 MAE 时解释为平均绝对误差。
- `fallback` 只在括注或短说明中保留。
- reader-facing deck 不使用 runbook、handoff 或过程批评语言。
