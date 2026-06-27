# Blocked Split Supplement Adapter Fairness Audit

Fairness conclusion: `fair_enough_to_interpret_as_acut_difference`.

What happened: endpoint, model, workspace, verifier, score-table, and accounting evidence were checked from committed sanitized artifacts.
Why it matters: Kilo and Codex can differ without that being a benchmark bug if both ACUT configurations followed the same benchmark rules.
Action suggested next: report the adapter gap as an ACUT configuration difference, not a model-only result.

## Dimensions

### required_endpoint_variables

- Classification: `clean`.
- What happened: Both adapters require LLM_BASE_URL and LLM_API_KEY, all supplement batch summaries record endpoint variables present, and the final decision records endpoint compliance pass.
- Why it matters: The adapter comparison is not explained by one harness using a different auth path in the committed evidence.
- Action suggested: Keep this endpoint rule for paid work.

### model_identifier_or_family

- Classification: `clean`.
- What happened: Adapter config and score tables record gpt-5.4-mini for both ACUT configurations.
- Why it matters: The observed gap should not be reported as a model-only result, but the model identifier is aligned across adapters.
- Action suggested: Report the difference as a same-model cross-harness ACUT configuration difference.

### pricing_and_accounting

- Classification: `clean`.
- What happened: Cost reconciliation is complete with usage observed for all new cells; exact provider billing is explicitly unavailable.
- Why it matters: Cost/latency interpretation can use token-estimated accounting but must not claim exact provider spend.
- Action suggested: Keep cost claims token-estimated unless provider billing becomes available.

### solver_visible_task_statement_source

- Classification: `clean`.
- What happened: Ready-package integrity records solver-visible statements, statement digests, no raw diff marker, and no target commit exposure for the new supplement package.
- Why it matters: The paid supplement was driven by task statements rather than hidden oracle material.
- Action suggested: Use sanitized statement digests when auditing future packages.

### base_commit_and_workspace_construction

- Classification: `clean`.
- What happened: Ready-package rows record resolvable base commits and source repos for the supplement missing-cell package.
- Why it matters: Both adapters should have worked from comparable clean task workspaces.
- Action suggested: No paid rerun is suggested by workspace construction evidence.

### allowed_edit_paths_and_prohibited_tests_or_oracle

- Classification: `clean`.
- What happened: Allowed code paths and test paths were recorded, tests were non-editable, policy violations were zero, and raw oracle exposure was false.
- Why it matters: Adapter pass-rate differences are not explained by committed evidence of path-policy or oracle leakage.
- Action suggested: Continue treating policy violations as hard gates.

### verifier_replay_policy

- Classification: `clean`.
- What happened: System design and supplement runbook require diff replay in fresh verifier workspaces, and ready-package rows record verifier commands.
- Why it matters: The score table is benchmark-side verification evidence, not self-reported ACUT success.
- Action suggested: No verifier-policy blocker found.

### timeout_concurrency_retry_policy

- Classification: `documented_acut_difference`.
- What happened: Both adapters use the same recorded timeout and paid concurrency is one; Kilo uses strict-final completion mode as a documented harness setting.
- Why it matters: Harness/tooling differences are part of the ACUT configuration unless they break benchmark rules.
- Action suggested: Report adapter results separately and avoid model-only superiority claims.

### score_table_import_rules

- Classification: `clean`.
- What happened: The combined manifest covers all 120 selected cells, preserves the one non-scoreable cell, and the completed paid decision was not changed.
- Why it matters: Denominators are explicit and the invalid output was not silently converted into a pass or fail.
- Action suggested: Keep the invalid cell non-scoreable in analysis.

### usage_and_cost_record_completeness

- Classification: `clean`.
- What happened: Cost reconciliation and adapter metrics mark cost/latency accounting complete for the supplement.
- Why it matters: Cost and latency comparisons are usable as token-estimated diagnostics.
- Action suggested: Do not claim exact billed dollars.

## Limitations

- Raw solver transcripts and raw ACUT logs were intentionally not read. Effect: Exact invalid-output text cannot be reconstructed; committed sanitized score tables are sufficient for scoreability and fairness denominators.
