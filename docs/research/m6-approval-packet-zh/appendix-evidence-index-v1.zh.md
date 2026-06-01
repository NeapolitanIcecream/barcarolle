# Barcarolle 中文立项交付包证据附录 V1

状态：简版证据附录，2026-06-01。

用途：把中文立项交付包中的关键声明映射到已提交证据，同时保留声明边界。V5 仍是长文论证基准。路径级审计线索保留在：

```text
experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md
```

| Evidence label | 面向评审者的作用 | 关键数字或结论 | Canonical source | 声明限制 |
| --- | --- | --- | --- | --- |
| Weighted design pilot | 显示朴素 benchmark 构建会出现实质性失败。 | Weighted gaps: attrs `0.3148`, boltons `0.7481`; simple same-budget baselines: `0.25` and `0.125`. | V5 section 7.1; V5 appendix evidence index; internal evidence manifest. | 这是 diagnostic negative result，不是成功 compiler 结果。 |
| Local algorithm bakeoff | 说明旧 weighted objective 不应被提升为主线。 | 简单 stratified design 仍是保守 baseline，直到更强设计有更好证据。 | V5 section 7.1; V5 appendix evidence index; internal evidence manifest. | 本地诊断分析，不是未来验证。 |
| Three-repo workspace execution pilot | 显示 benchmark 侧执行可以保留 ACUT 边界。 | `120/120` exploratory cells completed with scoreability `1.0`. | V5 section 7.2; V5 appendix evidence index; internal evidence manifest. | 干净执行不证明未来预测。 |
| Click source-context repair | 显示 source-quality gap 可以修复，且不重写已完成 outcome。 | `30/30` frozen click tasks repaired using public issue and pull-request context. | V5 section 7.2; V5 appendix evidence index; internal evidence manifest. | source-quality repair 不改变已完成 pilot outcome。 |
| Adapter fairness diagnostics | 支持按命名配置报告结果。 | Adapter differences are treated as ACUT-configuration evidence rather than pooled away. | V5 sections 6 and 7.3; V5 appendix evidence index; internal evidence manifest. | 不支持单纯模型结论，也不支持跨 adapter 的一般有效性声明。 |
| Random-baseline comparison | 显示 retrospective directional traction。 | Candidate beats or ties `93.4%` of `1000` same-budget random selections on MAE. | V5 sections 1 and 7.3; V5 appendix evidence index; internal evidence manifest. | retrospective replay 只支持牵引性证据和 debugging。 |
| Baseline-envelope comparison | 将 candidate 与 best simple aggregate baseline 比较。 | Candidate MAE `0.209`; best simple aggregate baseline MAE `0.2149`; edge `0.0059`. | V5 sections 1 and 7.3; V5 appendix evidence index; internal evidence manifest. | 优势太小且脆弱，不能支持正式有效性声明。 |
| Fallback-share accounting | 让 composite selector behavior 可见。 | `6/18` selected slots use fallback; boltons is `6/6` fallback. | V5 section 7.3; V5 appendix evidence index; internal evidence manifest. | 必须修复 feature support，或在未来声明中收窄范围。 |
| Validation-protocol hardening | 定义从牵引性证据走向更强声明的路径。 | Future claims require frozen releases, named ACUT configurations, simple baselines, score joins after outcomes, and success criteria fixed in advance. | V5 sections 3, 6, and Appendix C; internal evidence manifest. | 协议标准是未来验证路径，不是当前证明。 |
| V5 proposal report | 提供完整 proposal argument 和当前声明边界。 | 当前证据提供有边界的牵引性证据和可信的验证路径；预测效度仍未建立。 | `docs/research/barcarolle-proposal-report-v5.md`. | V5 是声明主参考文本；本附录只是索引。 |
