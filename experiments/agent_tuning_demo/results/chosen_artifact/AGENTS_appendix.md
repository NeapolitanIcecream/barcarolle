# Barcarolle target-repo repair discipline

- First localize the failing behavior to the listed editable implementation paths.
- Preserve public behavior and do not edit tests, generated metadata, or benchmark artifacts.
- Keep the patch minimal and compatible with existing boltons style.
- Before final answer, run the most targeted public pytest command named in the task statement when feasible.
- If the targeted command is too broad or unavailable, run the narrowest relevant public check and state that choice briefly.

## Failure-driven additions
- For API behavior changes, inspect adjacent tests and existing docstrings to preserve edge-case semantics before changing code.
- Prefer one direct implementation path and one focused verification loop; stop exploring once the relevant function is found.
- Do not include task-specific file names in this appendix; apply these rules generally across boltons tasks.
