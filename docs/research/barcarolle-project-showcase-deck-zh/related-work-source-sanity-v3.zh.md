# Barcarolle 相关工作来源核查 V3

状态：V3 related-work source sanity check，2026-06-02。

用途：为 V3 相关工作页提供短来源核查。本文只核查主张是否可由
primary 或 near-primary source 支持，不扩展成综述。

## Source Matrix

| Source | Full name | One-line contribution | Barcarolle unresolved issue | Link / citation label | Placement |
| --- | --- | --- | --- | --- | --- |
| SWE-bench | SWE-bench: Can Language Models Resolve Real-World GitHub Issues? | 用真实 GitHub issue / pull request 构造 repository-level issue-resolution tasks，并用测试执行评分。 | 它提供真实任务和 evaluation harness，但不决定某个目标仓库、某个 ACUT 和某个预算下哪些任务进入冻结 release。 | `SWE-bench-2024` / https://proceedings.iclr.cc/paper_files/paper/2024/file/edac78c3e300629acfe6cbe9ca88fb84-Paper-Conference.pdf | Main slide |
| SWE-bench Verified | SWE-bench Verified | 通过专业开发者人工审核，筛出更可靠的 SWE-bench 子集，并公开 annotations。 | 质量审核可以成为 release gate，但不等于 target-repo future-work prediction，也不定义 selection / split / fallback 规则。 | `SWE-bench-Verified-2024` / https://openai.com/index/introducing-swe-bench-verified/ | Main slide |
| SWE-bench quality follow-up | Why SWE-bench Verified no longer measures frontier coding capabilities | OpenAI 后续审计指出 Verified 在 frontier setting 下仍有测试拒绝正确解、数据接触等解释风险。 | Barcarolle 需要把 source quality、leakage、hidden-oracle handling 和 release freezing 写入 release protocol，而不是把 benchmark score 直接当成稳定能力结论。 | `SWE-bench-Verified-2026` / https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/ | Backup / source note |
| SWE-bench-Live | SWE-bench-Live | 采用与 SWE-bench 类似的 issue-resolution task，并通过自动化流程持续加入较新的实例以缓解 staleness / contamination pressure。 | fresh supply 仍要 outcome-unseen 地冻结、编译和验证，才能支持目标仓库未来表现声明。 | `SWE-bench-Live-2025` / https://openreview.net/pdf/a4780ae0897403f6c7756edbcfe7226153eab1ba.pdf | Main slide |
| SWE-Bench++ | SWE-Bench++: A Framework for the Scalable Generation of Software Engineering Benchmarks from Open-Source Repositories | 从 pull requests 生成大规模、多语言、可执行的 repository-level tasks，并包含 sourcing、environment synthesis、oracle extraction 和 QA stages。 | scalable supply 需要本地 certification、source caps、support checks 和 release-selection rules；规模本身不回答 target-repo prediction。 | `SWE-Bench++-2025` / https://arxiv.org/abs/2512.17419 | Main slide |
| SWE-smith | SWE-smith: Scaling Data for Software Engineering Agents | 为 GitHub repositories 生成大量 SWE-agent task instances，并展示生成 supply 可用于训练 agent。 | generated tasks 只有通过 source sufficiency、oracle、leakage、environment 和 ambiguity checks 后，才可进入 Barcarolle candidate pool。 | `SWE-smith-2025` / https://swesmith.com/ | Main slide |
| R2E-Gym | R2E-Gym: Procedural Environments and Hybrid Verifiers for Scaling Open-Weights SWE Agents | 构造可执行训练环境，并结合 execution-based / execution-free verifier 以提升 open-weight SWE agents。 | executable environments 和 verifier 有助于训练与评测，但 Barcarolle 仍要围绕 ACUT boundary 编译 release、隔离 verifier material，并记录 score / cost / latency / artifacts。 | `R2E-Gym-2025` / https://github.com/R2E-Gym/R2E-Gym and https://arxiv.org/abs/2504.07164 | Main slide |

## Deck Implication

V3 相关工作页应把这些来源组织成三层：

| Layer | Sources | Reader-facing point |
| --- | --- | --- |
| Real tasks and quality | SWE-bench, SWE-bench Verified, SWE-bench quality follow-up | 真实任务和质量审核是必要输入；release 解释还需要目标仓库选择和 outcome-unseen rules。 |
| Freshness and scale | SWE-bench-Live, SWE-Bench++, SWE-smith | 更新和生成扩大 candidate pool；Barcarolle 需要认证、source caps、support checks 和 selection rule。 |
| Environments and verifiers | R2E-Gym | 可执行环境和 verifier 支撑训练/评测；Barcarolle 的贡献是 benchmark release compilation 与 ACUT boundary accounting。 |

## Sanity Result

通过。V3 可以在主相关工作页写全 SWE-bench、SWE-bench Verified、
SWE-bench-Live、SWE-Bench++、SWE-smith 和 R2E-Gym，并把 OpenAI 的
Verified 后续质量说明作为 source note 或口头备查背景。没有发现需要停止的
unsupported related-work claim。
