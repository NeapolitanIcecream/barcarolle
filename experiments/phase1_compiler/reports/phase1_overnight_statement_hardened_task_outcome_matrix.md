# Statement-Hardened Task Outcome Matrix

Task count: `16`. Cell count: `32`.

- Both-adapter failures: `['attrs__hist__003', 'attrs__hist__012', 'attrs__hist__013', 'boltons__hist__022', 'boltons__hist__027']`.
- Adapter disagreements: `['boltons__hist__011']`.

## Both Adapters Failed

| Task | Repo split | Family | Source | Statement source | Codex | Kilo |
| --- | --- | --- | --- | --- | --- | --- |
| attrs__hist__003 | attrs/B_eval | attrs:attr._make | pull_request | reused_codex_loop | verified_fail | verified_fail |
| attrs__hist__012 | attrs/H_future | attrs:attr._make | issue | reused_codex_loop | verified_fail | verified_fail |
| attrs__hist__013 | attrs/H_future | attrs:attr._next_gen | pull_request | reused_codex_loop | verified_fail | verified_fail |
| boltons__hist__022 | boltons/H_future | boltons:boltons.iterutils | pull_request | new_codex_loop | verified_fail | verified_fail |
| boltons__hist__027 | boltons/H_future | boltons:boltons.cacheutils | pull_request | new_codex_loop | verified_fail | verified_fail |

## Adapter Disagreement

| Task | Repo split | Family | Source | Statement source | Codex | Kilo |
| --- | --- | --- | --- | --- | --- | --- |
| boltons__hist__011 | boltons/B_eval | boltons:boltons.iterutils | pull_request | new_codex_loop | verified_pass | verified_fail |

## H Future Failures

| Task | Repo split | Family | Source | Statement source | Codex | Kilo |
| --- | --- | --- | --- | --- | --- | --- |
| attrs__hist__012 | attrs/H_future | attrs:attr._make | issue | reused_codex_loop | verified_fail | verified_fail |
| attrs__hist__013 | attrs/H_future | attrs:attr._next_gen | pull_request | reused_codex_loop | verified_fail | verified_fail |
| boltons__hist__022 | boltons/H_future | boltons:boltons.iterutils | pull_request | new_codex_loop | verified_fail | verified_fail |
| boltons__hist__027 | boltons/H_future | boltons:boltons.cacheutils | pull_request | new_codex_loop | verified_fail | verified_fail |

## B Eval Failures

| Task | Repo split | Family | Source | Statement source | Codex | Kilo |
| --- | --- | --- | --- | --- | --- | --- |
| attrs__hist__003 | attrs/B_eval | attrs:attr._make | pull_request | reused_codex_loop | verified_fail | verified_fail |
| boltons__hist__011 | boltons/B_eval | boltons:boltons.iterutils | pull_request | new_codex_loop | verified_pass | verified_fail |

## Full Matrix

| Task | Repo split | Time | Module | Adapter passes | Both pass | Both fail | Disagreement | Old policy flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attrs__hist__001 | attrs/B_eval | 2020H1 | attr._make | 2 | True | False | False | False |
| attrs__hist__003 | attrs/B_eval | 2020H1 | attr._make | 0 | False | True | False | False |
| attrs__hist__004 | attrs/B_eval | 2020H1 | attr._make | 2 | True | False | False | False |
| attrs__hist__008 | attrs/B_eval | 2020H2 | attr.__init__, attr._next_gen | 2 | True | False | False | False |
| attrs__hist__012 | attrs/H_future | 2020H2 | attr._make | 0 | False | True | False | False |
| attrs__hist__013 | attrs/H_future | 2020H2 | attr._next_gen | 0 | False | True | False | False |
| attrs__hist__023 | attrs/H_future | 2021H1 | attr._make | 2 | True | False | False | False |
| attrs__hist__027 | attrs/H_future | 2021H1 | attr.__init__, attr._funcs | 2 | True | False | False | True |
| boltons__clean_ext__001 | boltons/B_eval | 2020H1 | boltons.iterutils | 2 | True | False | False | False |
| boltons__clean_ext__008 | boltons/B_eval | 2020H1 | boltons.setutils | 2 | True | False | False | False |
| boltons__clean_ext__010 | boltons/B_eval | 2020H1 | boltons.setutils | 2 | True | False | False | False |
| boltons__hist__011 | boltons/B_eval | 2020H1 | boltons.iterutils | 1 | False | False | True | False |
| boltons__clean_ext__017 | boltons/H_future | 2022H2 | boltons.timeutils | 2 | True | False | False | False |
| boltons__hist__022 | boltons/H_future | 2023H1 | boltons.iterutils | 0 | False | True | False | False |
| boltons__hist__023 | boltons/H_future | 2023H1 | boltons.tbutils | 2 | True | False | False | False |
| boltons__hist__027 | boltons/H_future | 2023H2 | boltons.cacheutils | 0 | False | True | False | False |
