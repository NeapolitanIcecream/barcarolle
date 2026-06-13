# Second Repository No-Paid Gate

生成日期：2026-06-13

## Decision

Second repo candidate：`python-attrs/attrs`。

结论：`conditional_no_go_for_immediate_paid_matrix`。

`attrs` 是合适的第二仓库候选，并且 task supply 在 committed overlay 后达到 30+ release-eligible；但是当前 Agent selection demo 自动化仍有 boltons-specific packaging 假设，不能今天直接启动 second-repo paid matrix。最小修补完成后，`attrs` 可以作为下一轮 paid matrix 的 second repo。

本 package 未运行任何 second-repo paid Agent cell。

## Checkout/setup gate

本地 checkout：

- Path：`experiments/phase0_headroom/external_repos/attrs`
- Commit：`89fae8300f484544c1b7678cea5efe58c551fbb9`
- `.git` 与 `.venv` 均在 ignored external repo path 下，未纳入 committed artifacts。

Visible setup/test probe：

```text
uv run --group tests python -m pytest tests/test_funcs.py tests/test_validators.py -q
```

在 `experiments/phase0_headroom/external_repos/attrs` 下运行结果：`216 passed in 2.18s`。

第一次从 Barcarolle root 运行同一相对 pytest path 时因 cwd 错误返回 file-not-found；修正 cwd 后通过。

## Task supply

Committed phase0 attrs certified task files：

| Source | Count |
| --- | ---: |
| `attrs_clean_outcome_unseen_supply_certified_tasks.jsonl` | 18 |
| `attrs_supply_expansion_20260526_certified_tasks.jsonl` | 10 |
| total directly materialized JSONL | 28 |

Later committed source-repair overlay：

- `phase1_attrs_source_repair_release_eligibility_overlay.json`
- before overlay：`28`
- promoted tasks：`attrs__v2__218`、`attrs__v2__231`、`attrs__v2__237`
- after overlay：`31`
- `attrs_reached_30_release_eligible=true`

Paid-readiness context：

- `phase1_attrs_source_repair_paid_readiness_gate.json` records `attrs=31` and `boltons=35` release-eligible.
- That older gate remains `paid_ready=false` only because that program required at least three repos with 30 release-eligible tasks.
- For this strict runbook's narrower second-repo gate, attrs has enough supply after the overlay.

## Hidden verifier replay feasibility

Replay probe used lower-level workspace verifier mechanics:

- archive attrs base commit into a fresh temp workspace;
- apply target implementation diff for allowed code files;
- inject target test-file diff as hidden oracle material;
- run pytest verifier with phase0 uv project and explicit attrs test dependencies.

Sampled replay results:

| Task | Code patch | Hidden test injection | Verifier result |
| --- | --- | --- | --- |
| `attrs__hist__001` | applied | injected | failed under current dependency resolution |
| `attrs__hist__003` | applied | injected | failed under current dependency resolution |
| `attrs__hist__004` | applied | injected | failed under current dependency resolution |
| `attrs__hist__008` | applied | injected | passed |

The passing probe was:

- task：`attrs__hist__008`
- code files：`changelog.d/669.change.rst`、`docs/api.rst`、`src/attr/__init__.py`...
- test files：`tests/test_next_gen.py`、`tests/typing_example.py`
- verifier exit：`0`
- duration：`0.18s`

The failing `test_make.py` probes reached pytest after code patch and hidden-test injection, but one old Hypothesis-based test failed under the current Python/dependency resolution. This is a verifier environment pinning issue, not evidence that patch replay or hidden test injection is impossible.

## Automation gaps blocking immediate paid matrix

Current `experiments/agent_selection_demo/tools/agent_selection_demo.py` is not yet second-repo-clean:

- `load_task_pool()` builds `TaskPackage(repo_id="boltons")` instead of using `config["target_repo"]`.
- fallback statement text says "Repair the boltons behavior..." when rows do not provide a full solver-facing statement.
- there is no committed `attrs_target_profile.json`; the attrs fallback config only records a command template in `third_repo_replacement_attrs_v1.yaml`.
- the 31-task release-eligible set is split across 28 materialized phase0 JSONL rows plus a phase1 overlay; a paid matrix should first write or reference a single frozen attrs release manifest.
- verifier command should pin the attrs historical test environment enough to avoid current Hypothesis/Python drift on older tasks.

Minimum repair work:

1. Add an attrs target profile with repo id, visible verifier command, dependency pins, and Python version policy.
2. Fix demo task packaging to derive `repo_id`, repo name, and fallback statement wording from config rather than boltons constants.
3. Materialize or formally reference the 31-task attrs release-eligible manifest, including the three overlay-promoted tasks.
4. Run a no-paid attrs repository gate with at least three reference replay samples and one split/freeze dry run.
5. Only then run paid second-repo cells, still using `LLM_BASE_URL` and `LLM_API_KEY`.

## Cost estimate

Existing boltons demo stages after smoke usage recovery:

| Stage | Scheduled cells | Estimated cost |
| --- | ---: | ---: |
| smoke | 4 | `$0.90167305` |
| selection | 80 | `$35.1392395` |
| holdout | 40 | `$18.2878365` |
| total | 124 | `$54.32874905` |

Per scheduled boltons cell estimate：`$0.43813507`。

For an attrs 31-task matrix with the same four candidates and a `20 selection / 10 holdout / 1 smoke` split:

- cells：`31 * 4 = 124`
- estimated cost from boltons average：`$54.33`

For a strict 30-task, four-candidate matrix without smoke:

- cells：`30 * 4 = 120`
- estimated cost：`$52.58`

These are conservative demo estimates, not provider-billed cost. They include missing-usage conservative estimates from existing Kilo rows.

## Tests

Ran:

```text
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_attrs_source_repair.py -q
```

Result：`5 passed in 5.98s`。

## Final gate

No paid second-repo cells were run.

`attrs` is supply-ready after the committed overlay, and local checkout/setup is healthy. It is not yet immediate-paid-matrix-ready in the current demo CLI because packaging and verifier-environment repairs are required first.
