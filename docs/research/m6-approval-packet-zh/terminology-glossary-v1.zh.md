# Barcarolle 中文术语表 V1

状态：中文补充包术语表，2026-06-01。

用途：稳定 M6 中文立项交付包的术语，避免后续改稿扩大声明或引入不必要的新概念。

| English source term | 中文工作用语 | 用法说明 |
| --- | --- | --- |
| Barcarolle | Barcarolle | 项目名不翻译。首次出现时可说明为“面向特定仓库的 benchmark 编译器”。 |
| repo-specific benchmark | 面向特定仓库的 benchmark | 保留 `benchmark`，避免把它窄化成普通测试集。 |
| benchmark compiler | benchmark 编译器 | 指选择、认证、切分、刷新、加权或不加权、解释 benchmark release 的系统层。 |
| Agent Configuration Under Test / ACUT | 被测 Agent 配置（ACUT） | 首次出现用全称，后续可直接写 `ACUT`。ACUT 保留自己的 harness。 |
| predictive validity | 预测效度 | 当前只能说“尚未建立”或“未来验证目标”，不能说已经证明。 |
| MAE | MAE | 平均绝对误差；越低表示 benchmark 估计越接近观察到的未来工作表现。 |
| fallback | fallback / 回退选择 | 用于说明当前 selector 的支持不足或组合性质，不能隐藏。 |
| tuning and regression feedback | 调优与回归反馈 | 是计划交付能力和产品路径，效果声明仍待验证。 |
| budgeted and gated evaluation | 有预算、有闸门的评测 | 强调付费 ACUT 评测必须在 release、baseline、score join 和成功标准冻结后执行。 |
| claim boundary | 声明边界 | 说明当前证据能支持什么、不能支持什么。中文材料必须保持显眼。 |
| current evidence / preliminary evidence | 当前证据 / 初步证据 | 用于替代内部阶段叙述。 |
| bounded traction | 有边界的牵引性证据 | 表示足以支持项目审批，但不足以支持正式预测效度声明。 |
| credible validation path | 可信的验证路径 | 指未来通过冻结 release、命名 ACUT 配置、简单 baseline 和 outcome-unseen evidence 获得更强证据。 |
| source of truth | 主参考文本 / 长文论证基准 | 中文包的长文事实和声明边界以 V5 为准。 |
| evidence appendix | 证据附录 | 映射声明、关键数字、来源和限制，不是完整实验日志。 |

## 固定占位符

中文材料保留下列用户自有值，不自行补写：

- `[待用户决定：项目人员配置]`
- `[待用户决定：项目周期]`
- `[待用户决定：有闸门 ACUT 评测的预算上限]`
- `[待用户决定：审批路径或审批负责人]`
- `[待用户决定：对外材料中的交付负责人类别]`

## 表述边界

中文材料应使用这些边界表达：

- 预测效度仍未建立；
- 调优与回归反馈仍是计划交付能力；
- adapter 差异是 ACUT 配置结果，不能写成单纯模型结论；
- 付费评测必须有预算、有闸门，并在协议冻结后执行；
- 当前证据支持项目审批，不支持扩大为最终有效性声明。
