# 项目故事示意图

本目录包含七张用于务虚会和 PPT 编辑的内容型示意图。它们只整理原始 11 轮聊天中的项目逻辑，不使用仓库实验数值。

统一颜色：

- 灰色：相关工作、自动改进系统等 Barcarolle 之外的要素；
- 蓝色：Barcarolle 的研究起点、拟议方法和研究目标；
- 橙色：风险、尚未闭合的问题和待验证的预期；
- 绿色：后来真实工作，以及由它提供的外部校准锚。

每张图都在右上角和页脚注明性质。“机制示意”表示从聊天归纳出的风险机制；“相关工作事实 + 位置/缺口归纳”表示相关工作的能力来自聊天引用，而位置或缺口是本文归纳；“拟议”表示尚待验证的方法或实验。它们都不应被表述为 Barcarolle 已取得的实验结果。

## 文件索引

1. `01-evaluation-becomes-objective`：为什么 Agent 自动优化以后，固定评测会从尺子变成优化目标。对应对话第 6、7、10、11 轮。
2. `02-landscape-and-position`：以“是否进入连续优化闭环”和“是否由后来真实工作对账”为轴，标出相关工作、Barcarolle 的研究起点和目标。对应第 2、8、9 轮。
3. `03-related-work-gap`：相关工作分别补上哪一块，为什么仍没有闭合 adaptive evaluation 问题。对应第 7、8、9 轮。
4. `04-generator-validation`：以“支持新的序列化类型”为例，说明需求方向、独立成题、Agent 相对表现和后来真实任务校准之间的关系。对应第 8、9、10、11 轮。
5. `05-barcarolle-loop`：Barcarolle 在 Agent 自动改进内环和后来真实工作外部锚之间负责什么。对应第 7、8、9 轮。
6. `06-controlled-evaluator-test`：固定同一初始 Agent、同一自动优化器和同样预算，只更换评测器的双通道对照实验。曲线是待验证的目标走势，没有实验数值。对应第 7、8、10、11 轮。
7. `07-research-roadmap`：从固定 Agent 到持续刷新评测器的四个可证伪关卡。对应第 6、8、9、11 轮。

每张图同时提供：

- 2400×1350 PNG，适合直接插入 PPT；
- 保留文本、形状和连线的 SVG，适合在 Figma、Illustrator、Inkscape 或 PowerPoint 中继续编辑。

## 重新生成

在仓库根目录运行：

```bash
uv run --with matplotlib \
  python docs/briefings/2026-08-13-future-grounded-evaluation/scripts/make_story_diagrams.py
```

脚本使用 `Hiragino Sans GB`；在没有该字体的平台运行时，应先把脚本中的 `FONT` 改为可用的简体中文无衬线字体，并检查 SVG 中文字体替换。
