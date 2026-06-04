# Blocked Split Supplement Action Matrix

What happened: diagnostic findings were mapped to next-action categories.
Why it matters: follow-up should separate no-paid analysis from paid reruns.
Action suggested next: accept the adapter difference as ACUT evidence and keep paid reruns blocked unless a concrete benchmark bug appears.

- `accept_adapter_difference_as_acut_result`: `recommended`, cost `no_paid`, blocking `False`. Evidence: Fairness conclusion is fair_enough_to_interpret_as_acut_difference; endpoint/model/workspace/verifier/accounting checks are clean enough.
- `fix_adapter_endpoint_or_model_config`: `not_recommended_now`, cost `no_paid_if_needed`, blocking `False`. Evidence: Committed endpoint and model evidence is clean for both adapters.
- `improve_sanitized_invalid_output_logging`: `recommended_minor`, cost `no_paid`, blocking `False`. Evidence: The invalid row proves invalid_output but does not preserve enough sanitized cause detail to distinguish no diff from unparseable diff.
- `investigate_codex_attrs_invalid_output_contract`: `recommended_no_paid`, cost `no_paid`, blocking `False`. Evidence: Only Codex attrs__v2__157 is non-scoreable; Kilo completed the same task as verified_fail.
- `repo_level_gap_deep_dive_no_paid`: `recommended`, cost `no_paid`, blocking `False`. Evidence: Repo gaps are concentrated in Codex click, Kilo boltons, and Codex attrs non-scoreable sensitivity.
- `proceed_to_next_repo_or_supply_expansion`: `allowed_after_no_paid_review`, cost `depends_on_next_work`, blocking `False`. Evidence: Supplement is fair enough to interpret, but click caveat and repo gaps should inform next supply decisions.
- `do_not_run_more_paid_cells_yet`: `recommended`, cost `saves_paid_budget`, blocking `True`. Evidence: No benchmark bug was found that justifies paid reruns; repo-level gaps can be studied without paid cells.
- `paid_rerun_only_if_benchmark_bug_confirmed`: `recommended_policy`, cost `paid_only_if_later_justified`, blocking `False`. Evidence: The one invalid output is non-scoreable and logging-limited, not proof of a benchmark bug.
