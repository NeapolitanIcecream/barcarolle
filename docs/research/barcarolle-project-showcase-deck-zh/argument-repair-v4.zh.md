# Barcarolle 项目展示 Deck V4 论证修复

状态：V4 Slides 7-8 argument repair，2026-06-03。

用途：在编辑 PPTX 前锁定 V4 第 7、8 页的新论证。本文是执行与审计材料，不作为读者可见幻灯片文案。

## 修复目标

V3 第 7、8 页把旧 weighted target-profile 失败放在主要证明位置。V4 改为从 benchmark compiler 的估计问题立论：仓库级评测包是在有限预算下估计未来目标仓库工作的工具，任务选择器决定哪些有限观察进入这个估计，因此任务选择、样本支撑、兜底来源、来源上限、切片稳定性、adapter 报告和对照基线都会影响估计值或可信度。

旧 weighted failure 只保留为历史诊断：它说明朴素 profile matching 在稀疏样本支撑下可能脆弱。它不再承担“算法问题为何存在”的主要证明职责。

## Required Argument

V4 第 7、8 页采用以下逻辑：

1. 仓库级评测 release 是一个有限预算估计器，用来估计目标仓库未来工作上的表现。
2. 任务选择器决定哪些有限观察进入这个估计器。
3. 样本支撑、兜底来源、来源上限、切片稳定性、adapter 报告和对照基线都可能改变估计值或可信度。
4. 因此，任务选择是 benchmark compiler 的核心算法问题。
5. 当前证据显示比较环境已经跑通，并且 selector 有初步 traction；它还没有建立预测效度。

## Slide 7 Repair

Slide 7 从“旧算法失败证明问题真实”改为“有限预算估计器为什么需要 selector 规则”。

目标主张：

```text
有限预算下，任务选择器决定估计偏差、覆盖不足和稳定性。
```

目标视觉：

```text
有限预算 -> 任务选择器 -> 估计风险 -> selector 规则
```

主要节点：

| 节点 | 读者含义 | V4 处理 |
| --- | --- | --- |
| 有限预算 | 只能运行有限数量的任务，不能观察全部未来工作。 | 放在图形左端，作为约束起点。 |
| 任务选择器 | 选择哪些认证任务进入 release。 | 使用中文主标签，首次出现时可括注 selector。 |
| 估计风险 | 偏差、覆盖不足、不稳定。 | 用三个短标签呈现，不写成长段过程说明。 |
| selector 规则 | 样本支撑、兜底来源、来源上限、切片稳定性、对照基线。 | 作为右侧规则清单，显示需要被算法化。 |

历史诊断如保留，应位于页面底部或角落：

```text
历史诊断：旧 weighted 方案在稀疏样本支撑下脆弱，不能作为主线结论。
```

## Slide 8 Repair

Slide 8 从“旧失败加过程数据”改为“当前证据回答哪些读者问题”。

目标主张：

```text
当前证据支持继续优化 selector；还不能证明预测效度。
```

目标问题板：

| 读者问题 | 可用证据 | 边界 |
| --- | --- | --- |
| 协议能跑通吗？ | `120/120` planned cells；scoreability `1.0`。 | 可审计执行，不等于未来预测成立。 |
| source 质量能修复吗？ | click `30/30` frozen tasks repaired。 | 不重写历史 paid outcomes。 |
| 选择器是否有初步信号？ | MAE `0.209` vs `0.2149`，edge `0.0059`；1000-seed random beats/ties `93.4%`。 | traction below future gate；edge 太小。 |
| 现在还不能证明什么？ | M4 gate 未通过：MAE margin、random share、adapter、repo/window、fallback 等仍失败或脆弱。 | 预测效度未建立；tuning-loop improvement 未验证。 |

旧 weighted 失败若出现，只能作为备注明细：

```text
历史诊断：naive weighting 在 sparse support 下失败，提示 selector 规则需要样本支撑检查。
```

## Claim Boundary

V4 可以说：

- 任务选择会影响仓库级评测估计；
- 现有比较环境可以运行并记录证据；
- MAE 和随机对照显示初步 traction；
- 下一阶段应优化 selector 并做 outcome-unseen 验证。

V4 不能说：

- 把预测效度写成已建立状态；
- 当前 selector 已经通过未来 gate；
- Agent Tuning 效果已经实证；
- adapter 差异证明模型本身更强；
- 旧 weighted 失败本身证明任何新算法都会有效。
