# Barcarolle Approval Packet Evidence Index V1

Status: concise evidence appendix, 2026-06-01.

Purpose: map approval-packet claims to committed evidence while preserving the
claim boundary. V5 remains the long-form source of truth. Path-level audit
traceability is preserved in
`experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md`.

| Evidence label | Reader-facing role | Key numbers or conclusion | Canonical source | Claim limit |
| --- | --- | --- | --- | --- |
| Weighted design pilot | Shows that naive benchmark construction can fail materially. | Weighted gaps: attrs `0.3148`, boltons `0.7481`; simple same-budget baselines: `0.25` and `0.125`. | V5 section 7.1; V5 appendix evidence index; internal evidence manifest. | Diagnostic negative result, not a successful compiler result. |
| Local algorithm bakeoff | Explains why the old weighted objective should not be promoted. | Simple stratified designs remain the conservative baseline until stronger designs have better evidence. | V5 section 7.1; V5 appendix evidence index; internal evidence manifest. | Local diagnostic analysis, not future validation. |
| Three-repo workspace execution pilot | Shows that benchmark-side execution can preserve the ACUT boundary. | `120/120` exploratory cells completed with scoreability `1.0`. | V5 section 7.2; V5 appendix evidence index; internal evidence manifest. | Clean execution does not prove future prediction. |
| Click source-context repair | Shows that source-quality gaps can be repaired without rewriting completed outcomes. | `30/30` frozen click tasks repaired using public issue and pull-request context. | V5 section 7.2; V5 appendix evidence index; internal evidence manifest. | Source-quality repair does not change completed pilot outcomes. |
| Adapter fairness diagnostics | Supports named-configuration reporting. | Adapter differences are treated as ACUT-configuration evidence rather than pooled away. | V5 sections 6 and 7.3; V5 appendix evidence index; internal evidence manifest. | Does not prove model-only superiority or adapter-general validity. |
| Random-baseline comparison | Shows retrospective directional traction. | Candidate beats or ties `93.4%` of 1000 same-budget random selections on MAE. | V5 sections 1 and 7.3; V5 appendix evidence index; internal evidence manifest. | Retrospective replay supports traction and debugging only. |
| Baseline-envelope comparison | Compares the candidate against the best simple aggregate baseline. | Candidate MAE `0.209`; best simple aggregate baseline MAE `0.2149`; edge `0.0059`. | V5 sections 1 and 7.3; V5 appendix evidence index; internal evidence manifest. | Edge is too small and fragile for a formal validity claim. |
| Fallback-share accounting | Makes composite selector behavior visible. | `6/18` selected slots use fallback; boltons is `6/6` fallback. | V5 section 7.3; V5 appendix evidence index; internal evidence manifest. | Feature support must be repaired or the future claim narrowed. |
| Validation-protocol hardening | Defines the path from traction evidence to stronger claims. | Future claims require frozen releases, named ACUT configurations, simple baselines, score joins after outcomes, and success criteria fixed in advance. | V5 sections 3, 6, and Appendix C; internal evidence manifest. | Protocol standards are a future validation path, not current proof. |
| V5 proposal report | Provides the full proposal argument and current claim boundary. | Current evidence supplies traction and a credible validation path; formal predictive validity remains unproven. | `docs/research/barcarolle-proposal-report-v5.md`. | V5 is the source of truth for claims; this appendix is only an index. |
