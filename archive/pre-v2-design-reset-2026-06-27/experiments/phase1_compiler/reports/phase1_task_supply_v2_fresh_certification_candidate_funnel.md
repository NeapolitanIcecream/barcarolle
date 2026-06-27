# Fresh Certification Candidate Funnel

What happened: all `829` raw v2 candidates entered the fresh certification funnel.

Why it matters: raw inventory is not counted as certified supply. Candidates without usable changed-test oracles stay visible as inventory-only rows.

Readiness direction: this step measures supply shape; paid readiness still depends on local certification and source-context policy.

Counts by repo and terminal pre-certification subgate:

```json
{
  "attrs": {
    "material_leakage_risk": 18,
    "not_attempted_cap_deferred": 87,
    "oracle_missing_inventory_only": 35,
    "selected_for_certification": 160
  },
  "boltons": {
    "material_leakage_risk": 8,
    "not_attempted_cap_deferred": 113,
    "oracle_missing_inventory_only": 32,
    "selected_for_certification": 80
  },
  "humanize": {
    "oracle_missing_inventory_only": 8,
    "selected_for_certification": 84
  },
  "toolz": {
    "not_attempted_cap_deferred": 34,
    "oracle_missing_inventory_only": 10,
    "selected_for_certification": 160
  }
}
```

Source context quality by repo:

```json
{
  "attrs": {
    "commit_message_only_context": 160,
    "material_leakage_risk": 18,
    "non_leaky_issue_or_pr_context": 120,
    "pr_title_only_context": 2
  },
  "boltons": {
    "commit_message_only_context": 165,
    "material_leakage_risk": 8,
    "non_leaky_issue_or_pr_context": 60
  },
  "humanize": {
    "commit_message_only_context": 92
  },
  "toolz": {
    "commit_message_only_context": 198,
    "non_leaky_issue_or_pr_context": 6
  }
}
```

Selected for execution by repo:

```json
{
  "attrs": {
    "false": 140,
    "true": 160
  },
  "boltons": {
    "false": 153,
    "true": 80
  },
  "humanize": {
    "false": 8,
    "true": 84
  },
  "toolz": {
    "false": 44,
    "true": 160
  }
}
```
