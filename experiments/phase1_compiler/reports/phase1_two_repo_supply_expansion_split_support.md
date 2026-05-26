# Two-Repo Split Support

Generated: `2026-05-26T07:25:44Z`.

| Repo | Count | Windows | Min Window | B Eval | H Future |
| --- | --- | --- | --- | --- | --- |
| attrs | 20 | 7 | 1 | 10 | 10 |
| boltons | 27 | 12 | 1 | 13 | 14 |

Local bakeoff rerun meaningful: `false`.
Blocker: `expanded supply does not add paid local outcomes, so B_eval/H_future gap metrics remain limited to the previous 10 attrs and 12 boltons outcome-seen tasks`.
H_future was kept as a validation holdout concept, not a target profile.
