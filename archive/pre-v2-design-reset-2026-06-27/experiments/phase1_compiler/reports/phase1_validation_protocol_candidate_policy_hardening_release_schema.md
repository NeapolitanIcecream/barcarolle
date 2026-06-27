# Benchmark Release Artifact Schema

| Field | Description | Claim function |
| --- | --- | --- |
| release_id | unique release identifier | reproducibility |
| freeze_commit | git commit containing frozen protocol and release manifests | outcome blindness |
| target_repo | repository under test | future validation support |
| base_commit | task base commit | reproducibility |
| task_id | stable task identifier | reproducibility |
| task_source | issue, PR, commit, regression, synthetic, manual, or external adapter source | source quality |
| source_reservoir | specific reservoir label | source quality |
| source_license_status | license and redistribution status | source quality |
| provenance_digest | digest of sanitized provenance record | artifact hygiene |
| task_statement_path | solver-visible statement path | reproducibility |
| solver_visible_context_path | allowed context path | hidden-oracle protection |
| oracle_source | real changed tests, generated/synthetic oracle, or manual oracle | source quality |
| oracle_path_or_digest | hidden oracle path in verifier workspace or digest only | hidden-oracle protection |
| hidden_verifier_path_or_digest | verifier reference without committing private material | hidden-oracle protection |
| environment_setup | setup commands and dependency lock reference | reproducibility |
| dependency_lock | lockfile or digest | reproducibility |
| certification_status | certified, rejected, or repair-needed | source quality |
| leakage_check_status | oracle and statement leakage gate | hidden-oracle protection |
| source_quality_gate | source sufficiency and context status | source quality |
| candidate_policy_id | selection policy identifier | outcome blindness |
| selected_status | selected or not selected | future validation support |
| fallback_label | fallback selected flag and design | future validation support |
| fallback_reason | why fallback was used | future validation support |
| split_label | B_eval, H_future, or other frozen split | outcome blindness |
| time_cutoff | cutoff used for future or rolling-origin mode | outcome blindness |
| feature_values | frozen feature vector | future validation support |
| tie_break_value | frozen deterministic tie-break value | outcome blindness |
| acut_adapter_id | named ACUT configuration | adapter accounting |
| endpoint_compliance_status | LLM_BASE_URL and LLM_API_KEY compliance for paid cells | adapter accounting |
| cost_latency_accounting | cost, latency, and retry accounting | adapter accounting |
| terminal_status | terminal status category | adapter accounting |
| score_row_digest | digest of sanitized score row | future validation support |
| sanitized_artifact_manifest | committed manifest of allowed artifacts | artifact hygiene |
| raw_artifact_storage_policy | ignored location for raw prompts, transcripts, workspaces, diffs, and verifier material | artifact hygiene |
| ignored_path_confirmation | confirmation raw paths are ignored | artifact hygiene |

Rules:
- external candidates are untrusted until locally certified with source, license, oracle, environment, leakage, and provenance fields.
- generated or synthetic oracles must be labeled separately from real changed tests.
- raw prompts, raw completions, ACUT transcripts, workspaces, raw diffs, and hidden verifier material are stored only under ignored paths.
- Paid-validation authorization remains `false`.
