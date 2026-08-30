# Barcarolle：面向未来真实工作的持续可信评测

本目录保存 2026-08-13 务虚会/立项材料、清洗后的讨论总结和可编辑配图。
原始聊天、下载来源及其本地完整性索引保持 ignored，不进入版本库。

> 状态：日期化讨论与调研档案，不是当前项目路线权威。2026-08-30
> 确定的三项目标、开放方法空间和初步实验设计见
> [`../../research-program.md`](../../research-program.md)；发生冲突时以后者为准。
> 扩展后的文献综述见
> [`../../literature-review.md`](../../literature-review.md)。本目录为保留历史原貌，仍会出现
> `future-grounded`、`later-real`、`level/gap error` 等已停止用于当前公开文档的旧表达；
> 不要把这些表达复制到新文档或新实验。

## 本批材料入口

新版主材料以原始聊天为主要来源，不展开仓库实验过程和具体算法结果。

- [`strategic-briefing.md`](strategic-briefing.md)：完整战略叙事，依次回答领域版图、项目位置、核心问题、相关工作缺口、拟议方案、验证方法和预计效果。
- [`strategic-slide-outline.md`](strategic-slide-outline.md)：面向技术转管理评委的 12 页 PPT 结构，每页包含一句主结论、页内内容、对应配图和口头边界。
- [`figures/story/README.md`](figures/story/README.md)：七张内容型示意图的索引；每张都有 PNG 和可编辑 SVG。
- [`strategic-source-map.md`](strategic-source-map.md)：新版各节与原始 11 轮聊天的对应关系，以及被后续讨论撤回的方向。

## 本地原始材料

`raw/` 下的聊天原件、来源原件、提取报告、来源索引和完整性清单只在
授权的本地工作区保存，并由 `raw/.gitignore` 排除。公开归档不保存可重新
打开原始对话的共享链接，也不以整理稿替代本地原件。

## 保留的技术底稿

以下文件用于追溯第一版调研和证据审计，不应作为当前研究合同：

- `discussion-synthesis.md`：11 轮讨论的收敛过程、被排除方向与最终边界；
- `claim-evidence-matrix.md`、`research-contract.md`：论断边界与研究审计规则；
- `research/landscape.md`：领域版图与相关工作差距分析。
- `research/barcarolle-position.md`：仓库现状、已有证据、限制与新增工作包。
- `research/adaptive-validity.md`：失败机制、三层有效性、指标与分阶段实验协议。
- `research/notation.md`：技术附录符号与 workload/outcome/utility 口径。
- `research/research-audit.md`：11 轮覆盖映射、证据分层和 Gate A–F 机器检查。
- `figures/`：内容示意图和第一版技术图。
- `scripts/`：可复现图表脚本与输入数据。

旧的 ImageGen 主视觉及完整生成 prompt 已按 artifact-hygiene 规则从公开
归档移除。新版使用 `figures/story/` 中解释具体论点的示意图。

原始聊天中的判断不会自动升级为项目事实。所有示意数字和目标曲线均明确标为示意或待验证。

## 原始材料核验

聊天原件核验脚本为
[`scripts/verify_chat_archive.py`](scripts/verify_chat_archive.py)。本地原件和
本地完整性清单齐全时运行：

```bash
uv run python docs/briefings/2026-08-13-future-grounded-evaluation/scripts/verify_chat_archive.py
```

脚本验证 11 轮/22 条消息的角色顺序、字符计数、Markdown 精确文本和两份
聊天原件摘要；本地 manifest 另外覆盖 `raw/sources/` 下全部 PDF/HTML。
这些材料保持 ignored，不应为核验而移动、重写或提交。
