# Barcarolle 项目展示 Deck V4 架构说明

状态：V4 targeted repair architecture，2026-06-03。

用途：锁定 V4 的 11 页结构、每页职责、V3 来源、局部修复和术语减负决定。本文是内部执行与审计材料，不作为 reader-facing PPT 文案。

## Architecture Decision

V4 保留 V3 的 `11` 页结构。当前问题集中在局部论证、图形和术语负担，不需要新增页或恢复已删除的独立限制页、过程诊断页、approval-packet 页。

V4 主线保持：

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

核心修复是第 7、8 页：算法问题从“旧设计失败”改为“有限预算估计器的任务选择问题”；当前证据从“坏算法证明和过程证据”改为“协议、source repair、selector traction、claim boundary”。

## Slide Plan

| V4 slide | Role | V3 source slide | V4 repair | Terminology reduced? |
| --- | --- | --- | --- | --- |
| 1 项目定位 | 定义 Barcarolle、目标仓库、评测 release 和 ACUT 边界。 | V3 Slide 1 | 右侧三方图从头重画为 `目标仓库 -> 仓库级评测 release -> ACUT 运行与结果`；删除圆点端点；所有连接对齐。 | Yes：用“目标仓库”“仓库级评测包”“运行与结果”；ACUT 首次解释保留。 |
| 2 问题与代价 | 说明通用分数到目标仓库未来工作的预测缺口，以及三类决策后果。 | V3 Slide 2 | 用连续桥接带替代浮动 `prediction gap` 圆点；下方三项通过共享 rail 从 gap 流出。 | Yes：三类后果改为中文；`prediction gap` 改为“预测缺口”。 |
| 3 相关工作与缺口 | 展示相邻工作提供的任务、质量、鲜度、规模和环境输入，以及 Barcarolle 的 release-selection gap。 | V3 Slide 3 | 保留内容与表格节奏，仅压缩英文解释。 | Partial：英文专名保留；解释和表头中文化。 |
| 4 研究目标 | 定义未来成功率估计与 MAE 解释，并保持 claim boundary。 | V3 Slide 4 | 保持公式页，不扩大声明；标题和注释更少英文。 | Yes：MAE 首次解释为平均绝对误差。 |
| 5 方法 | 展示候选任务到冻结 release 的 compiler workflow。 | V3 Slide 5 | 删除六个底部小形状和过程句；把认证维度改为清晰 checklist，并把说明集中在 workflow 下方。 | Yes：stage label 和 checklist 中文化；保留 release / oracle。 |
| 6 执行边界 | 显示 solver 与 verifier 分离，hidden oracle 只在验证侧出现。 | V3 Slide 6 | 维持 V3 图形主线；微调术语解释和 spacing。 | Partial：边界术语保留，图内中文解释。 |
| 7 算法问题 | 说明任务选择器如何决定有限预算估计质量。 | V3 Slide 7 | 全面重写：中心图为 `有限预算 -> 任务选择器 -> 估计风险 -> selector 规则`；旧 weighted failure 降级为小号历史诊断。 | Yes：用“任务选择器、样本支撑、兜底来源、来源上限、切片稳定性、对照基线”。 |
| 8 当前证据 | 用证据回答四个读者问题，同时声明预测效度未建立。 | V3 Slide 8 | 全面重写表格和层级；随机对照 `93.4%` 比旧 weighted failure 更显眼；表头中文化。 | Yes：Reader question / Evidence / Current reading 改中文。 |
| 9 研究路线 | 说明下一步怎样优化 selector 并进行 outcome-unseen 验证。 | V3 Slide 9 | 左侧算法演进 loop 对齐到网格；节点中文化；future holdout / rolling-origin 作为验证路线标签。 | Yes：major nodes 中文化；保留两个验证路线名并解释。 |
| 10 Agent License | 展示仓库级证据状态如何服务部署治理。 | V3 Slide 10 | 去掉或整合底部输出 strip；主流程内直接承载输出信息，避免 detached annotation。 | Yes：用“部署治理、证据状态、使用范围决定、不确定性”。 |
| 11 Agent Tuning | 展示受保护 dev / eval / canary 反馈回路。 | V3 Slide 11 | 重画为单一路径：`配置变更 -> dev feedback -> eval release -> canary release -> regression signal`；未来验证材料独立隔离但不作为断裂目标。 | Yes：图内为 dev/eval/canary 配中文解释；`regression signal` 改为“回归信号”。 |

## Visual System

V4 继承 V3 的视觉系统：

- slide size: `1280x720`;
- left rail title system;
- light green paper background;
- PingFang SC typeface;
- teal / blue / amber / green / violet / red accent system;
- editable native shapes and text through artifact-tool presentation JSX.

V4 局部视觉规则：

- 不使用 generated raster images、decorative AI art 或 imagegen；
- 不使用看似端点残留的圆点；
- connector 只在关系真实存在时出现；
- equal-role nodes 保持统一宽高、padding 和 alignment；
- 表格表头默认中文；
- 技术词不靠缩小字号硬塞进框内，必要时删词或换行。

## Source Boundary

V4 事实边界来自：

- `docs/research/barcarolle-proposal-report-v5.md`
- `docs/research/phase-1-proposal-evidence-package.md`
- `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md`
- `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md`
- V3 deck package artifacts.

V4 不修改 score tables、selected task IDs、split labels、source eligibility、task statements、hidden-oracle material 或已完成实验决定。
