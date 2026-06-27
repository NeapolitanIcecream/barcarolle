# Boltons repository-selection fallback audit

Generated at: `2026-06-15T05:08:30+00:00`. Paid cells run: `0`.

## Recommendation If Boltons Does Not Continue

Best fallback: `python-attrs/attrs`.

`attrs` has `31` release-eligible tasks after overlay and a passed local setup probe in the second-repo gate. It is not immediate-paid-ready because packaging and verifier-environment repairs remain, but those repairs are concrete and no-paid.

`click` is the supply-only runner-up: committed gates show `30` release-eligible tasks and the later source-context repair cleaned the click context without paid calls. It is a good backup if the coordinator prefers a click-targeted packaging pass, but it is less aligned with the current attrs handoff.

## Comparison

| Repo | Raw | Certified/technical | Release/projected | Readiness | Repairs |
| --- | --- | --- | --- | --- | --- |
| attrs | 178 | 28 | 31 | conditional_no_go_until_packaging_and_env_repairs | attrs target profile, package-map generalization, frozen 31-task manifest, verifier env pin |
| boltons | 162 | 35 | 57 | single_window_ready_only | source-context repair plus fresh baseline discovery |
| toolz | 16 | 6 | 5 | not_paid_ready_supply_below_threshold | broad mining/source repair |
| humanize | 16 | 12 | 12 | not_paid_ready_supply_below_threshold | broad mining/source repair |
| click | 298 | 75 | 30 | supply_ready_packaging_needed | click target profile/package-map generalization and split dry run |
