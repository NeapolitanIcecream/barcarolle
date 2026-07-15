# Codex CLI Harness Example

This directory shows one way to run Codex CLI as a Barcarolle Agent harness.
It is an example command, not a Barcarolle requirement. Barcarolle sees the
harness as a shell command that edits the solver worktree.

The harness reads `.barcarolle/TASK.md`, includes it once in the initial
`codex exec --json` prompt, and tells the Agent not to reread the same file.
Codex JSON events go to stdout. Diagnostics go to stderr.

## Required Environment

Set these variables before running benchmark or evidence-producing Codex calls:

- `OPENAI_BASE_URL`: endpoint base URL for the benchmark LLM provider.
- `OPENAI_API_KEY`: API key for that endpoint.
- `BARCAROLLE_CODEX_HOME`: dedicated Codex home for this run. Use a fresh path
  under an ignored output directory.
- `BARCAROLLE_CODEX_MODEL`: optional model name. If unset, the example uses
  `gpt-5.4`. Evidence-producing runs should set it explicitly and bind the same
  value into the Agent identity.
- `BARCAROLLE_CODEX_REASONING_EFFORT`: optional `none`, `low`, `medium`, `high`,
  or `xhigh`. Evidence-producing runs must also bind it into Agent identity.

The harness sources `~/.zshrc` only if `OPENAI_BASE_URL` or `OPENAI_API_KEY` is
missing. It then refuses to run if either variable is still absent.

## Endpoint And Authentication

Benchmark and evidence-producing runs must not use local Codex subscription
auth. This harness sets `CODEX_HOME` to `BARCAROLLE_CODEX_HOME`, runs Codex with
`--ignore-user-config`, and passes a custom provider named
`barcarolle_openai`:

- `base_url` comes from `OPENAI_BASE_URL`.
- `env_key` is `OPENAI_API_KEY`.
- `wire_api` is `responses`.
- request and stream retries are both zero; the benchmark driver owns any
  decision to spend another call.

Before invoking Codex, the harness disables Codex plugins, uses an ephemeral
session, excludes `OPENAI_API_KEY` and `OPENAI_BASE_URL` from Agent-launched
subprocesses, and unsets alternate ambient provider credentials: `LLM_API_KEY`,
`LLM_BASE_URL`, `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`,
`GOOGLE_API_KEY`, and `GEMINI_API_KEY`.
It ignores and unsets `OPENAI_MODEL`; only `BARCAROLLE_CODEX_MODEL` or the fixed
default controls the explicit Codex model argument.
The reasoning-effort environment value is converted to an explicit Codex
configuration argument and then removed from the Codex process environment.

## Bind The Harness

Bind the command to an `AgentRecord` the same way you would bind any other
shell harness:

```python
from pathlib import Path

from barcarolle.workspace import bind_agent_harness

harness = Path("examples/harnesses/codex-cli/run-agent.zsh").resolve()
bind_agent_harness(agent, (str(harness),))
```

Use a resolved path because Barcarolle runs the harness from the solver
worktree, not from the Barcarolle repository root.
The binder validates this argv but does not hash `run-agent.zsh`. If results
will be reused, the Agent identity must change when the script or its
behavior-changing configuration changes.

The command edits files in the solver worktree. Barcarolle captures the final
diff, replays it in a verifier worktree, injects private check material only
there, and records the normalized result.

## Usage Extraction

Usage extraction belongs to the harness. Barcarolle core does not parse Codex
output; it reads a normalized `.barcarolle/usage.json` object after the harness
exits.

The optional `extract-usage.py` helper reads the explicit
`turn.completed.usage` object from line-delimited `codex exec --json` output.
It preserves finite, nonnegative numeric keys and derives uncached input from
the reported input and cached-input counts:

```json
{"cached_input_tokens": 100, "input_tokens": 123, "output_tokens": 45, "uncached_input_tokens": 23}
```

It does not recursively search unrelated objects or translate alternate token
names. An unrecognized event therefore leaves usage unknown instead of
guessing a billable quantity.

`run-agent.zsh` preserves the Codex JSON stream on stdout, feeds the same stream
to this helper, and writes the mapping to `.barcarolle/usage.json`. The Workspace
runner then stores it in `WorkspaceRunRecord.usage`. Barcarolle computes cost
from user-provided `ScoringConfig.cost_rates`; this example does not define
provider pricing. If usage is absent, no rates are configured, or any priced
key is missing, total cost remains unknown (`null`). A measured zero requires
an explicit zero rate.
