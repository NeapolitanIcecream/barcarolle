# Task Manifest Notes

status: prepared_not_started
updated: 2026-04-28T15:34:59+08:00
repository: `pallets/click`
locked_target_commit: `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`

## Scope

Prepared concrete repository-specific task manifests for the budget-constrained
core subset:

- `experiments/core_narrative/configs/tasks/rbench_click.yaml`: 8 `RBench` tasks.
- `experiments/core_narrative/configs/tasks/rwork_click.yaml`: 6 `RWork` tasks.

The run manifest remains `prepared_not_started`. No broad ACUT execution,
model call, or patch-generation attempt was started.

## Source And Selection Basis

Anchors were selected from public `pallets/click` commit, issue, and pull
request history through GitHub commit search and compare metadata. The shell
checkout could not be unshallowed because DNS resolution for `github.com`
failed, so base/target pairs were resolved from GitHub compare metadata rather
than local history.

Selection rules:

- Prefer compact behavior changes with focused tests.
- Exclude docs-only, dependency-only, release-only, CI-only, and workflow-only
  anchors unless a repository behavior change is exercised by tests.
- Keep `RBench` and `RWork` anchors disjoint.
- Use historical pre-2024 behavior anchors for `RBench`.
- Use recent 2025-2026 maintainer-style behavior anchors for `RWork`.
- Avoid tasks that require a real terminal, Windows-only behavior, shell
  behavior, color state, or locale state. Where terminal-adjacent behavior is
  used, verifier candidates are in-process pytest tests.

## RBench Anchors

| Task | Anchor | Source target commit | Source base commit | Behavior |
| --- | --- | --- | --- | --- |
| `click__rbench__001` | PR `pallets/click#252` | `39e51d961b9e69c050bb948b1db11275f9630542` | `4a7fe69f942bd02b811548ff8f02a08fff7429c1` | Option help rendering for `multiple=True` list defaults. |
| `click__rbench__002` | PR `pallets/click#151` | `637447f9ccf882d5c810540ca261e8ba2af9cb1c` | `b557743f3bc26a4cdbf610b221e7e81d609aa65d` | `CliRunner.invoke` exception catching controls. |
| `click__rbench__003` | Commit `02ea9ee7e864581258b4902d6e6c1264b0226b9f` | `02ea9ee7e864581258b4902d6e6c1264b0226b9f` | `d3f36e884e18f374c3e4e6cf062ba19f100d0fd6` | Choice values in prompt text. |
| `click__rbench__004` | PR `pallets/click#868` | `fdceb39d344603fc73a4d9761766b5701f69236d` | `b1b4449cda6767f022372890998d6b0eb895d041` | Separated stdout/stderr in `CliRunner` results. |
| `click__rbench__005` | PR `pallets/click#887` | `c70d4636831e391016895587f7ed10e96f49773e` | `a00e01845100ce2b3d5288a2b655aad260346361` | Case-insensitive `Choice` conversion. |
| `click__rbench__006` | Commit `5fe0b7e7795f9bb04ae926d00868cfeb1fa33187` | `5fe0b7e7795f9bb04ae926d00868cfeb1fa33187` | `6e62332349db6e93decf47666c4cd6fe20df6b02` | Default `DateTime` format accepting a space separator. |
| `click__rbench__007` | PR `pallets/click#1312` | `990ca8e664a0610fe0583f3aa8924fd49f928a74` | `563b1a7116a6806e699d31d327dd9bca93c40cb3` | `CliRunner` command return value capture. |
| `click__rbench__008` | PR `pallets/click#1618` | `8efb348e2bc820aeba60d4cce6939708c6b2b11c` | `7332f00ed4c27d8da041788ca6a7aa405f062c76` | Optional value prompt/default behavior. |

## RWork Anchors

| Task | Anchor | Source target commit | Source base commit | Behavior |
| --- | --- | --- | --- | --- |
| `click__rwork__001` | PR `pallets/click#2956` | `565f36d5bc4a15d304337b749e113fb4477b1843` | `5c1239b0116b66492cdd0848144ab3c78a04495a` | Flag envvar/default/flag_value/type reconciliation. |
| `click__rwork__002` | PR `pallets/click#2940` | `2a0e3ba907927ade6951d5732b775f11b54cb766` | `36deba8a95a2585de1a2aa4475b7f054f52830ac` | `CliRunner` EOF behavior for stdin file arguments. |
| `click__rwork__003` | Commit `1c20dc6e724cd5625faaa17b715ba928d44c08bf` | `1c20dc6e724cd5625faaa17b715ba928d44c08bf` | `6a1c0d077311f180b356965914e2de5b9e0fdb44` | Shared-parameter default preservation before UNSET normalization. |
| `click__rwork__004` | Commit `546f2851f414b07413777ebcae89b2c21a685252` | `546f2851f414b07413777ebcae89b2c21a685252` | `ae46cfd6bc997804893adc799589248eadcdbc29` | Callable `flag_value` should not be instantiated as a default. |
| `click__rwork__005` | Commit `4f9086bf8fd98aca1d804bf742f4f1ceb6c12295` | `4f9086bf8fd98aca1d804bf742f4f1ceb6c12295` | `1339fd3323357119a9c7a6326c788f80295954ce` | `pdb` stream handling inside `CliRunner`. |
| `click__rwork__006` | Commit `c653ec820093ed1dda41aae8d35bff7834b0344a` | `c653ec820093ed1dda41aae8d35bff7834b0344a` | `878de46100e9c29aea9dab5b385b8116863cb5e3` | Default value passing versus flag activation. |

## Verifier Discovery

The locked checkout was recreated under the ignored path by copying the
repo-runtime-lock checkout:

- `experiments/core_narrative/external_repos/click`

The checkout is at the locked target commit and has a local Python 3.12 virtual
environment. Targeted verifier discovery passed:

```text
./.venv/bin/python -m pytest -q \
  tests/test_options.py::test_multiple_default_help \
  tests/test_testing.py::test_catch_exceptions \
  tests/test_testing.py::test_catch_exceptions_cli_runner \
  tests/test_termui.py::test_choices_list_in_prompt \
  tests/test_testing.py::test_stderr \
  tests/test_options.py::test_case_insensitive_choice \
  tests/test_options.py::test_case_insensitive_choice_returned_exactly \
  tests/test_basic.py::test_datetime_option_default \
  tests/test_testing.py::test_command_standalone_mode_returns_value \
  tests/test_termui.py::test_prompt_required_with_required \
  tests/test_termui.py::test_prompt_required_false \
  tests/test_options.py::test_envvar_string_flag_value \
  tests/test_chain.py::test_pipeline \
  tests/test_defaults.py::test_shared_param_prefers_first_default \
  tests/test_options.py::test_callable_flag_value_not_instantiated \
  tests/test_testing.py::test_pdb_uses_real_streams \
  tests/test_testing.py::test_pdb_explicit_streams_honored \
  tests/test_testing.py::test_pdb_init_restored_after_invoke \
  tests/test_options.py::test_flag_value_and_default
```

Result: `187 passed in 0.26s`.

## Risks And Follow-Ups

- The local ignored checkout is shallow at the locked target commit because
  shell DNS prevented fetching history. Future workspace preparation for these
  historical base commits will need a full local history fetch or another
  source of the pinned base/target objects.
- Several historical RBench anchors predate Click's `src/` layout, so task
  packaging must use each source base tree, not the locked target tree path
  layout.
- Verifier commands are candidates from the locked checkout. For historical
  base workspaces, the runner may need hidden regression tests or packaged test
  files rather than assuming those node IDs already exist in the base tree.
- The `pdb` RWork task is terminal-adjacent but selected tests assert stream
  object behavior without opening an interactive debugger.
