# Kilo Non-Interactive Command Shape Check

Generated: `2026-05-21T14:37:00+00:00`.

## Scope

This side check tested whether the Kilo workspace harness failures could be
explained by an incorrect non-interactive `kilo run` command shape.

The check did not call the paid endpoint. It used a temporary `HOME` and XDG
config/data/cache/state tree plus a local mock OpenAI-compatible
`/v1/chat/completions` server. The user's local Kilo environment was not used.

Installed Kilo version:

```text
7.3.1
```

Relevant docs checked:

- https://kilo.ai/docs/code-with-ai/platforms/cli
- https://kilo.ai/docs/code-with-ai/platforms/cli-reference

The docs define `kilo run [message..]`, `--auto` for autonomous mode, and
`--file` as an array option for attached files.

## Command-Shape Findings

Mock probe variants:

| Variant | Shape | Result | Prompt delivered | Statement delivered |
| --- | --- | ---: | --- | --- |
| current adapter | `kilo run <prompt> ... --file <statement>` | `0` | yes | yes |
| options then prompt then file | `kilo run ... <prompt> --file <statement>` | `0` | yes | yes |
| file before prompt | `kilo run ... --file <statement> <prompt>` | `1` | no request | no request |
| file equals before prompt | `kilo run ... --file=<statement> <prompt>` | `1` | no request | no request |
| file before prompt with separator | `kilo run ... --file <statement> -- <prompt>` | `0` | yes | yes |
| no file | `kilo run ... <prompt>` | `0` | yes | no |

The failing forms exit before any model request with:

```text
File not found: PROMPT_MARKER: reply exactly DONE after reading attached file.
```

Conclusion: in Kilo `7.3.1`, placing `--file` before the prompt is unsafe
unless `--` separates option parsing from the message. The current workspace
adapter already uses the safe prompt-first form:

```text
kilo run <prompt> --pure --auto --format json --model openai-compatible/gpt-5.4-mini --dir <workspace> --file <statement>
```

## Workspace Evidence

The original `codex_kilo_workspace` run had Kilo timeouts, but they were not
consistent with command parsing failure:

- `6/10` Kilo rows ended as `acut_harness_error`.
- The diagnosis classified them as `adapter_timeout_nonempty_diff_nonexit`.
- Timeout workspaces had implementation diffs, so Kilo had entered the task and
  edited files before failing to exit.

Later Kilo runs show normal non-interactive operation with the repaired
`strict-final` prompt mode:

| Result set | Kilo rows | Scoreable | Harness-error rows | Raw stdout ending |
| --- | ---: | ---: | ---: | --- |
| `kilo_completion_probe` | 3 | 3 | 0 | `text`, `step_finish` |
| `codex_kilo_workspace_followup` | 10 | 9 | 1 policy row | `text`, `step_finish` |
| `codex_kilo_workspace_stability` | 10 | 9 | 1 policy row | `text`, `step_finish` |
| `humanize_pre_phase1_workspace` | 4 | 4 | 0 | `text`, `step_finish` |

Sample solver workspaces also contain normal implementation diffs:

- `toolz__hist__001`: `toolz/functoolz.py`, 4 insertions.
- `humanize__hist__005`: `src/humanize/number.py`, 2 insertions.
- original timeout `toolz__hist__002`: `toolz/functoolz.py`, 10 insertions.

## Conclusion

The command-shape risk is real but not the current adapter's failure mode. The
safe rule is:

- keep the prompt before `--file`, or put `--` before the prompt if `--file`
  must appear first;
- keep `--auto` for non-interactive execution;
- keep isolated Kilo config/state for probes and matrix cells;
- do not use a `--file <statement> <prompt>` shape.

The original Kilo failures are better explained by completion/non-exit behavior
after successful editing, not by endpoint availability or argument parsing.
