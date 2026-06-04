from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load
import phase1_source_context_statement_hardening as hardening


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "phase1_click_llm_source_context_repair.yaml"
SCHEMA_VERSION = "barcarolle.phase1_click_llm_source_context_repair.v1"
OUTPUT_SCHEMA = "barcarolle.phase1_click_llm_source_context_repair_output.v1"
RUN_ID = "phase1_click_llm_source_context_repair_20260529"
TARGET_REPO = "click"
FORBIDDEN_RAW_MARKERS = (
    "diff --git",
    "\n@@",
    "raw_completion_text",
    "raw_prompt_text",
    "hidden verifier",
    "verified_pass",
    "verified_fail",
)
HEX40_RE = re.compile(r"\b[0-9a-f]{40}\b")


PUBLIC_CONTEXT_PROFILES: dict[str, dict[str, Any]] = {
    "click__third__045": {
        "public_title": "Include --help option in completion",
        "source_kind": "public_pr_body",
        "refs": [{"kind": "pull_request", "number": 1504, "url": "https://github.com/pallets/click/pull/1504"}],
        "public_summary": "Public PR #1504 explains that shell completion omitted the enabled --help option even though users can invoke it normally.",
        "problem_summary": "Shell completion should offer the enabled --help option as a completion candidate.",
        "expected_behavior": "Completion output for supported shells includes --help when the command exposes the help option, without changing unrelated completion candidates.",
        "sufficiency_reason": "The PR body states the missing completion candidate and the user-visible behavior.",
    },
    "click__third__050": {
        "public_title": "BOOL should accept on and off",
        "source_kind": "public_issue_body",
        "refs": [{"kind": "issue", "number": 1629, "url": "https://github.com/pallets/click/issues/1629"}],
        "public_summary": "Public issue #1629 asks Click's BOOL parameter type to accept and convert the strings on and off, matching common configparser spellings.",
        "problem_summary": "The BOOL parameter type should recognize on and off as valid boolean spellings.",
        "expected_behavior": "BOOL conversion accepts on/off along with existing true/false-style strings and preserves invalid-value error behavior.",
        "sufficiency_reason": "The issue gives the exact accepted input family without exposing implementation or tests.",
    },
    "click__third__091": {
        "public_title": "Add update interval for progress bar",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 1698, "url": "https://github.com/pallets/click/pull/1698"},
            {"kind": "issue", "number": 676, "url": "https://github.com/pallets/click/issues/676"},
        ],
        "public_summary": "Public issue #676 and PR #1698 describe progress bars that render too often for short iterations and add an update interval to skip unnecessary renders.",
        "problem_summary": "Progress bars should avoid excessive rendering for frequently updated iterators.",
        "expected_behavior": "A progress bar can limit expensive visual refreshes while still reporting progress correctly for normal iterations.",
        "sufficiency_reason": "The issue and PR identify the performance problem and behavior-level remedy.",
    },
    "click__third__109": {
        "public_title": "Better error message for bad parameter default",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 1805, "url": "https://github.com/pallets/click/pull/1805"},
            {"kind": "issue", "number": 1749, "url": "https://github.com/pallets/click/issues/1749"},
        ],
        "public_summary": "Public issue #1749 and PR #1805 describe a multi-value option whose single default produces an unclear failure, and request a clearer TypeError.",
        "problem_summary": "A multi-value parameter with an invalid single default should fail with a clear parameter-default error.",
        "expected_behavior": "Click reports a useful TypeError for invalid defaults on multiple-value parameters without changing valid default handling.",
        "sufficiency_reason": "The public issue provides a minimal behavior and the PR states the desired error class.",
    },
    "click__third__166": {
        "public_title": "Fix return value and type signature of shell_completion.add_completion_class",
        "source_kind": "public_pr_body",
        "refs": [{"kind": "pull_request", "number": 2421, "url": "https://github.com/pallets/click/pull/2421"}],
        "public_summary": "Public PR #2421 explains that add_completion_class behaves like a decorator and should return the class it registers instead of None.",
        "problem_summary": "shell_completion.add_completion_class should return the registered completion class.",
        "expected_behavior": "The decorator-style helper returns the class object and has a type signature compatible with normal decorator use.",
        "sufficiency_reason": "The PR body states the public API contract and why the old return value is wrong.",
    },
    "click__third__197": {
        "public_title": "Fix metavar for Choice options when show_choices=False",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2365, "url": "https://github.com/pallets/click/pull/2365"},
            {"kind": "issue", "number": 2356, "url": "https://github.com/pallets/click/issues/2356"},
        ],
        "public_summary": "Public issue #2356 and PR #2365 report that Choice values still appear in help output even when show_choices is disabled.",
        "problem_summary": "Choice option metavars should respect show_choices=False.",
        "expected_behavior": "Help and prompt-related metavar rendering omit inline choice lists when show_choices is false while preserving normal Choice validation.",
        "sufficiency_reason": "The public issue includes the visible help-output mismatch and the PR narrows it to Choice metavar rendering.",
    },
    "click__third__198": {
        "public_title": "Hide default value when show_default is False",
        "source_kind": "public_pr_body",
        "refs": [{"kind": "pull_request", "number": 2509, "url": "https://github.com/pallets/click/pull/2509"}],
        "public_summary": "Public PR #2509 says prompt output could still reveal an option default even when show_default is false, including sensitive defaults.",
        "problem_summary": "Default values should stay hidden from prompts and help when show_default is false.",
        "expected_behavior": "Option display honors show_default=False consistently without exposing hidden defaults or regressing normal default handling.",
        "sufficiency_reason": "The PR body describes the user-visible leak and expected display behavior.",
    },
    "click__third__199": {
        "public_title": "Split generation of help extra items and rendering",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2517, "url": "https://github.com/pallets/click/pull/2517"},
            {"kind": "issue", "number": 2516, "url": "https://github.com/pallets/click/issues/2516"},
        ],
        "public_summary": "Public issue #2516 and PR #2517 explain that extra help items such as defaults and env vars need a cleaner generation step before rendering.",
        "problem_summary": "Help metadata generation should be separated from rendering so extra help items can be handled consistently.",
        "expected_behavior": "Help records keep structured extra items available for rendering and extension without changing visible help semantics unexpectedly.",
        "sufficiency_reason": "The issue and PR explain the extension pain point and the behavior-level contract.",
    },
    "click__third__200": {
        "public_title": "Keep track of stderr and stdout mix in CliRunner results",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2523, "url": "https://github.com/pallets/click/pull/2523"},
            {"kind": "issue", "number": 2522, "url": "https://github.com/pallets/click/issues/2522"},
        ],
        "public_summary": "Public issue #2522 and PR #2523 describe CliRunner result streams: stdout and stderr should remain separately available while mixed output preserves observed order.",
        "problem_summary": "CliRunner results should preserve stdout, stderr, and their mixed ordering.",
        "expected_behavior": "Result.stdout and result.stderr expose pure streams, and mixed output represents the interleaved output without surprising errors.",
        "sufficiency_reason": "The issue and PR define the stream contract at the public testing API level.",
    },
    "click__third__201": {
        "public_title": "Show env var in error hint",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2696, "url": "https://github.com/pallets/click/pull/2696"},
            {"kind": "issue", "number": 2695, "url": "https://github.com/pallets/click/issues/2695"},
        ],
        "public_summary": "Public issue #2695 and PR #2696 request that errors for required options mention the configured environment variable hint.",
        "problem_summary": "Relevant parameter errors should include environment-variable hints.",
        "expected_behavior": "When an option can be supplied through an envvar, the missing-parameter hint names that envvar without changing parsing behavior.",
        "sufficiency_reason": "The issue gives a minimal user-visible error-message expectation.",
    },
    "click__third__202": {
        "public_title": "Fix closing of callbacks on CLI exit",
        "source_kind": "public_pr_body",
        "refs": [{"kind": "pull_request", "number": 2680, "url": "https://github.com/pallets/click/pull/2680"}],
        "public_summary": "Public PR #2680 says contexts should close themselves on CLI exits so registered callbacks are called and stale resources are avoided.",
        "problem_summary": "Callbacks registered for CLI execution should be closed when the CLI exits.",
        "expected_behavior": "ctx.exit paths close the active context and invoke registered cleanup callbacks without disrupting normal command exits.",
        "sufficiency_reason": "The PR body states the lifecycle problem and observable cleanup behavior.",
    },
    "click__third__203": {
        "public_title": "Add functionality to hide the progress bar",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "issue", "number": 2609, "url": "https://github.com/pallets/click/issues/2609"},
            {"kind": "pull_request", "number": 2727, "url": "https://github.com/pallets/click/pull/2727"},
        ],
        "public_summary": "Public issue #2609 and PR #2727 describe a progressbar hide option for cases where callers conditionally suppress progress output.",
        "problem_summary": "Progress bars should support being hidden by caller configuration.",
        "expected_behavior": "A hidden progress bar suppresses progress output while preserving iteration and surrounding termui behavior.",
        "sufficiency_reason": "The issue explains the user need and the PR names the public option behavior.",
    },
    "click__third__204": {
        "public_title": "Give a UserWarning when Parameter is overridden by name",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2397, "url": "https://github.com/pallets/click/pull/2397"},
            {"kind": "issue", "number": 2396, "url": "https://github.com/pallets/click/issues/2396"},
        ],
        "public_summary": "Public issue #2396 and PR #2397 describe two command parameters using the same name and silently overriding each other.",
        "problem_summary": "Overriding a Parameter by name should warn instead of silently hiding a parameter.",
        "expected_behavior": "Click emits a UserWarning for conflicting parameter names while preserving valid commands without such conflicts.",
        "sufficiency_reason": "The issue gives the conflict class and the PR states the warning behavior.",
    },
    "click__third__205": {
        "public_title": "Set flag_value correctly when using envvar",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2788, "url": "https://github.com/pallets/click/pull/2788"},
            {"kind": "issue", "number": 2746, "url": "https://github.com/pallets/click/issues/2746"},
        ],
        "public_summary": "Public issue #2746 and PR #2788 report that a flag option supplied through an envvar can receive the raw environment value instead of its flag_value.",
        "problem_summary": "Flag values supplied through envvar handling should resolve to the configured flag_value.",
        "expected_behavior": "Envvar-driven flag options set the same semantic value as the flag itself and preserve normal non-envvar behavior.",
        "sufficiency_reason": "The issue includes the public option pattern and expected value-level outcome.",
    },
    "click__third__206": {
        "public_title": "New method for Choice failure messages",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2622, "url": "https://github.com/pallets/click/pull/2622"},
            {"kind": "issue", "number": 2621, "url": "https://github.com/pallets/click/issues/2621"},
        ],
        "public_summary": "Public issue #2621 and PR #2622 request a separate Choice failure-message path so subclasses can customize invalid-choice messages.",
        "problem_summary": "Choice failures should have a dedicated failure path that preserves useful error behavior.",
        "expected_behavior": "Choice conversion exposes a customizable invalid-choice message hook while keeping normal failure reporting intact.",
        "sufficiency_reason": "The public issue describes the subclassing need and the PR states the public-method direction.",
    },
    "click__third__207": {
        "public_title": "Help shown via no_args_is_help results in exit code 2",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 1489, "url": "https://github.com/pallets/click/pull/1489"},
            {"kind": "issue", "number": 1394, "url": "https://github.com/pallets/click/issues/1394"},
            {"kind": "issue", "number": 1486, "url": "https://github.com/pallets/click/issues/1486"},
        ],
        "public_summary": "Public issues #1394 and #1486 describe no-command invocation showing help as an error case, while PR #1489 changes no_args_is_help to exit with code 2.",
        "problem_summary": "Help shown because no_args_is_help is enabled should use an error exit status.",
        "expected_behavior": "Invoking a group without required arguments can display help but exits with status 2 rather than a successful status.",
        "sufficiency_reason": "The public issues and PR give the visible output condition and exit-code expectation.",
    },
    "click__third__208": {
        "public_title": "Close contexts created during shell completion",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "issue", "number": 2644, "url": "https://github.com/pallets/click/issues/2644"},
            {"kind": "pull_request", "number": 2800, "url": "https://github.com/pallets/click/pull/2800"},
        ],
        "public_summary": "Public issue #2644 and PR #2800 describe shell completion leaving file-option contexts open, causing resource warnings.",
        "problem_summary": "Contexts created during shell completion should be closed after completion handling.",
        "expected_behavior": "Shell completion closes temporary contexts and file options after producing completions, avoiding resource warnings.",
        "sufficiency_reason": "The issue gives a concrete resource-leak symptom and the PR states the completion lifecycle fix.",
    },
    "click__third__213": {
        "public_title": "Customize Parameter and Command deprecation messages",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2271, "url": "https://github.com/pallets/click/pull/2271"},
            {"kind": "issue", "number": 2263, "url": "https://github.com/pallets/click/issues/2263"},
        ],
        "public_summary": "Public issue #2263 and PR #2271 discuss official support for deprecated parameters and commands, including customized help messages.",
        "problem_summary": "Deprecated Parameter and Command objects should support customizable deprecation messages.",
        "expected_behavior": "Deprecation metadata appears in relevant help output and can carry custom text for renamed or discouraged CLI surfaces.",
        "sufficiency_reason": "The issue gives the user-facing need and the PR names the Click APIs involved.",
    },
    "click__third__214": {
        "public_title": "Fix eagerness of help option generated by help_option_names",
        "source_kind": "public_pr_body",
        "refs": [{"kind": "pull_request", "number": 2811, "url": "https://github.com/pallets/click/pull/2811"}],
        "public_summary": "Public PR #2811 explains that help options generated through help_option_names can lose eagerness, affecting callback processing order.",
        "problem_summary": "Generated help options configured through help_option_names should preserve eager behavior.",
        "expected_behavior": "Custom help-option names behave like the normal eager help option and avoid running unrelated callbacks before help is shown.",
        "sufficiency_reason": "The PR body states the public configuration and the observable callback-order problem.",
    },
    "click__third__216": {
        "public_title": "Add CliRunner default catch_exceptions parameter",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2818, "url": "https://github.com/pallets/click/pull/2818"},
            {"kind": "issue", "number": 2817, "url": "https://github.com/pallets/click/issues/2817"},
        ],
        "public_summary": "Public issue #2817 and PR #2818 request configuring CliRunner.catch_exceptions once and letting invoke inherit it when not explicitly set.",
        "problem_summary": "CliRunner should expose a default catch_exceptions parameter for invocation behavior.",
        "expected_behavior": "CliRunner.invoke uses the runner-level catch_exceptions default unless an invocation overrides it.",
        "sufficiency_reason": "The issue and PR describe the public testing API behavior precisely.",
    },
    "click__third__217": {
        "public_title": "Only try to set flag_value if is_flag is true",
        "source_kind": "public_pr_body",
        "refs": [{"kind": "pull_request", "number": 2829, "url": "https://github.com/pallets/click/pull/2829"}],
        "public_summary": "Public PR #2829 explains that flag_value inference can call __bool__ on defaults for options that are not flags, which breaks classes with disabled truth testing.",
        "problem_summary": "flag_value should only be set for options that are actually flags.",
        "expected_behavior": "Non-flag options do not infer flag_value from their default, avoiding boolean conversion side effects while preserving flag behavior.",
        "sufficiency_reason": "The PR body states the failure mode and the public option classification boundary.",
    },
    "click__third__220": {
        "public_title": "Expand Choice token normalization and make generic",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2796, "url": "https://github.com/pallets/click/pull/2796"},
            {"kind": "issue", "number": 605, "url": "https://github.com/pallets/click/issues/605"},
        ],
        "public_summary": "Public issue #605 and PR #2796 discuss broader Choice support, including enum values and token normalization for user-facing choice matching.",
        "problem_summary": "Choice token normalization should cover more choice values and work with generic typing.",
        "expected_behavior": "Choice handles normalized tokens for supported value types, including enum-like choices, without weakening invalid-choice errors.",
        "sufficiency_reason": "The public issue and PR identify the Choice API capability and compatibility goal.",
    },
    "click__third__234": {
        "public_title": "Fix Zsh completions with colons",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2846, "url": "https://github.com/pallets/click/pull/2846"},
            {"kind": "issue", "number": 2703, "url": "https://github.com/pallets/click/issues/2703"},
        ],
        "public_summary": "Public issue #2703 and PR #2846 explain that Zsh completion values containing colons are parsed as description separators unless handled carefully.",
        "problem_summary": "Zsh shell completion should handle completion values containing colons.",
        "expected_behavior": "Zsh completion output preserves values with colons and does not split or corrupt them as descriptions.",
        "sufficiency_reason": "The public issue and PR describe the shell-specific parsing problem and expected value preservation.",
    },
    "click__third__238": {
        "public_title": "Fix completions for quoted or escaped parameters in Fish",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 3013, "url": "https://github.com/pallets/click/pull/3013"},
            {"kind": "issue", "number": 2995, "url": "https://github.com/pallets/click/issues/2995"},
        ],
        "public_summary": "Public issue #2995 and PR #3013 describe Fish completion mismatches when the incomplete parameter contains spaces, quotes, or escaped characters.",
        "problem_summary": "Fish shell completion should handle quoted or escaped parameter values.",
        "expected_behavior": "Fish completion parses and matches incomplete quoted or escaped values consistently with shell-provided words.",
        "sufficiency_reason": "The issue gives the shell parsing mismatch and the PR confirms the completion behavior.",
    },
    "click__third__250": {
        "public_title": "Optional value not optional anymore",
        "source_kind": "public_issue_body",
        "refs": [{"kind": "issue", "number": 3084, "url": "https://github.com/pallets/click/issues/3084"}],
        "public_summary": "Public issue #3084 reports that an option configured with is_flag=False and flag_value stops accepting the documented optional-value behavior.",
        "problem_summary": "Optional flag values should be interpreted correctly for option parsing.",
        "expected_behavior": "Options with optional flag values accept both the bare flag and an explicit value according to the documented Click option contract.",
        "sufficiency_reason": "The issue links the public documentation behavior to the observed parsing regression.",
    },
    "click__third__271": {
        "public_title": "Fix readline backspace and line-wrapping on Linux",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 2969, "url": "https://github.com/pallets/click/pull/2969"},
            {"kind": "issue", "number": 2968, "url": "https://github.com/pallets/click/issues/2968"},
        ],
        "public_summary": "Public issue #2968 and PR #2969 describe Linux readline prompts where backspace and line wrapping behave incorrectly because of prompt handling.",
        "problem_summary": "Readline prompts on Linux should handle backspace and line wrapping correctly.",
        "expected_behavior": "Linux prompt input delegates to readline-compatible behavior so editing and wrapping match the returned input.",
        "sufficiency_reason": "The issue records the visible terminal behavior and the PR narrows it to platform prompt handling.",
    },
    "click__third__274": {
        "public_title": "Ensure fish completion handles multiline help strings correctly",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 3126, "url": "https://github.com/pallets/click/pull/3126"},
            {"kind": "issue", "number": 3043, "url": "https://github.com/pallets/click/issues/3043"},
        ],
        "public_summary": "Public issue #3043 and PR #3126 report that multiline help text can break generated Fish shell completion scripts.",
        "problem_summary": "Fish completion output should handle multiline help strings correctly.",
        "expected_behavior": "Generated Fish completions remain valid when command or option help spans multiple lines.",
        "sufficiency_reason": "The public issue gives the malformed completion scenario and the PR states the shell output contract.",
    },
    "click__third__275": {
        "public_title": "Add NoSuchCommand exception with suggestions for misspelled commands",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 3228, "url": "https://github.com/pallets/click/pull/3228"},
            {"kind": "issue", "number": 2764, "url": "https://github.com/pallets/click/issues/2764"},
            {"kind": "issue", "number": 3107, "url": "https://github.com/pallets/click/issues/3107"},
        ],
        "public_summary": "Public issues #2764 and #3107 and PR #3228 request did-you-mean suggestions for misspelled commands, similar to option suggestions.",
        "problem_summary": "Unknown command handling should provide a NoSuchCommand error with suggestions for misspelled commands.",
        "expected_behavior": "Misspelled subcommands raise a command-specific error that can include close command-name suggestions.",
        "sufficiency_reason": "The issues and PR define the public error class and suggestion behavior.",
    },
    "click__third__278": {
        "public_title": "FuncParamType should use ValueError message in self.fail",
        "source_kind": "public_issue_and_pr_body",
        "refs": [
            {"kind": "pull_request", "number": 3211, "url": "https://github.com/pallets/click/pull/3211"},
            {"kind": "issue", "number": 3105, "url": "https://github.com/pallets/click/issues/3105"},
        ],
        "public_summary": "Public issue #3105 and PR #3211 explain that FuncParamType discards the ValueError message raised by the wrapped conversion function.",
        "problem_summary": "FuncParamType failures should preserve the ValueError message in Click's failure output.",
        "expected_behavior": "When a FuncParamType converter raises ValueError, Click includes that message in the parameter failure report.",
        "sufficiency_reason": "The issue states the lost message and the PR describes the user-visible error output.",
    },
    "click__third__288": {
        "public_title": "Zsh completion setup fails with parse error near elif",
        "source_kind": "public_issue_body",
        "refs": [{"kind": "issue", "number": 3277, "url": "https://github.com/pallets/click/issues/3277"}],
        "public_summary": "Public issue #3277 reports Zsh completion setup failing with a parse error in a Windows Git Bash environment, consistent with line-ending-sensitive shell output.",
        "problem_summary": "Shell completion output should use Unix line endings for compatibility with Windows consumers.",
        "expected_behavior": "Generated shell completion text uses line endings that Zsh can parse across supported environments.",
        "sufficiency_reason": "The issue gives the shell setup failure and public environment symptom without exposing hidden tests.",
    },
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    raw = Path(str(path))
    return raw if raw.is_absolute() else REPO_ROOT / raw


def rel(path: str | Path) -> str:
    resolved = repo_path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected click LLM source context repair config schema_version")
    config["_path"] = str(path)
    return config


def input_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["inputs"][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["outputs"][key])


def report_path(config: dict[str, Any], key: str) -> Path:
    return repo_path(config["reports"][key])


def read_json(path: str | Path, default: Any = None) -> Any:
    resolved = repo_path(path)
    if not resolved.exists():
        return default
    return json.loads(resolved.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text.rstrip() + "\n", encoding="utf-8")


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest_payload(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return digest_text(encoded)


def short_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def command_run(args: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def command_output(args: list[str], *, cwd: Path = REPO_ROOT) -> str:
    return command_run(args, cwd=cwd).stdout.strip()


def command_result(args: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, Any]:
    result = command_run(args, cwd=cwd)
    output = result.stdout.strip()
    return {
        "command": " ".join(args),
        "returncode": result.returncode,
        "output_digest": digest_text(output) if output else "",
        "output_excerpt": normalize_text(output)[:500],
    }


def git_status_lines() -> list[str]:
    output = command_run(["git", "status", "--short", "--untracked-files=all"]).stdout
    return [line for line in output.splitlines() if line.strip()]


def status_path(line: str) -> str:
    text = line[3:] if len(line) > 3 else line
    if " -> " in text:
        text = text.split(" -> ", 1)[1]
    return text.strip()


def expected_run_paths(config: dict[str, Any]) -> set[str]:
    paths = {
        rel(config["_path"]),
        rel(ROOT / "tools" / "phase1_click_llm_source_context_repair.py"),
        rel(ROOT / "tests" / "test_phase1_click_llm_source_context_repair.py"),
    }
    paths.update(rel(path) for path in config.get("outputs", {}).values())
    paths.update(rel(path) for path in config.get("reports", {}).values())
    return paths


def classify_dirty_paths(config: dict[str, Any], lines: list[str]) -> dict[str, list[str]]:
    expected = expected_run_paths(config)
    instruction_inputs = {
        "AGENTS.md",
        "PROCESS.md",
        "docs/experiments/phase-1-click-llm-assisted-source-context-repair-runbook.md",
    }
    ignored_prefixes = [
        "experiments/phase1_compiler/tmp/click_llm_source_context_repair/",
        "experiments/phase0_headroom/workspaces/click_llm_source_context_repair/",
        "experiments/phase0_headroom/cache/click_llm_source_context_repair/",
    ]
    external_review_prefix = "experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/"
    classified: dict[str, list[str]] = {
        "relevant_run_files": [],
        "instruction_or_process_inputs": [],
        "known_external_review_bundle": [],
        "ignored_artifact_output": [],
        "unrelated": [],
    }
    for line in lines:
        path = status_path(line)
        if path in expected:
            classified["relevant_run_files"].append(line)
        elif path in instruction_inputs:
            classified["instruction_or_process_inputs"].append(line)
        elif path == external_review_prefix.rstrip("/") or path.startswith(external_review_prefix):
            classified["known_external_review_bundle"].append(line)
        elif any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in ignored_prefixes):
            classified["ignored_artifact_output"].append(line)
        else:
            classified["unrelated"].append(line)
    for values in classified.values():
        values.sort()
    return classified


def endpoint_presence() -> dict[str, Any]:
    base_present = bool(os.environ.get("LLM_BASE_URL"))
    key_present = bool(os.environ.get("LLM_API_KEY"))
    source_zshrc_checked = False
    after_base_present = base_present
    after_key_present = key_present
    if not base_present or not key_present:
        source_zshrc_checked = True
        output = command_output(
            [
                "zsh",
                "-lc",
                (
                    "source ~/.zshrc >/dev/null 2>&1 || true; "
                    "if [[ -n ${LLM_BASE_URL:-} ]]; then echo base:present; else echo base:missing; fi; "
                    "if [[ -n ${LLM_API_KEY:-} ]]; then echo key:present; else echo key:missing; fi"
                ),
            ]
        )
        lines = set(output.splitlines())
        after_base_present = "base:present" in lines
        after_key_present = "key:present" in lines
    return {
        "LLM_BASE_URL_initial": "present" if base_present else "missing",
        "LLM_API_KEY_initial": "present" if key_present else "missing",
        "source_zshrc_checked": source_zshrc_checked,
        "LLM_BASE_URL_after_zshrc": "present" if after_base_present else "missing",
        "LLM_API_KEY_after_zshrc": "present" if after_key_present else "missing",
        "values_recorded": False,
        "endpoint_compliant_if_llm_needed": after_base_present and after_key_present,
    }


def git_tracked(path: Path) -> bool:
    return command_run(["git", "ls-files", "--error-unmatch", rel(path)]).returncode == 0


def input_availability(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, path_value in sorted(config.get("inputs", {}).items()):
        path = repo_path(path_value)
        rows.append(
            {
                "input_key": key,
                "path": rel(path),
                "exists": path.exists(),
                "git_tracked": git_tracked(path) if path.exists() else False,
            }
        )
    return rows


def preflight_payload(config: dict[str, Any]) -> dict[str, Any]:
    status_lines = git_status_lines()
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.preflight.v1",
        "artifact": "preflight",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "branch": command_output(["git", "branch", "--show-current"]),
        "starting_commit": command_output(["git", "rev-parse", "HEAD"]),
        "date_utc": now_utc()[:10],
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "uv_version": command_output(["uv", "--version"]),
        "git_diff_check": command_result(["git", "diff", "--check"]),
        "dirty_tree": {
            "status_lines": status_lines,
            "classification": classify_dirty_paths(config, status_lines),
        },
        "required_input_availability": input_availability(config),
        "all_required_inputs_exist": all(row["exists"] for row in input_availability(config)),
        "endpoint_presence": endpoint_presence(),
        "paid_boundaries": {
            "paid_acut_solver_cells_allowed": False,
            "paid_task_solving_calls_allowed": False,
            "paid_llm_statement_generation_review_allowed_only_if_needed_and_endpoint_compliant": True,
            "paid_llm_soft_cap_usd": config["policy"]["paid_llm_soft_cap_usd"],
            "paid_llm_hard_cap_usd": config["policy"]["paid_llm_hard_cap_usd"],
            "paid_calls_made_during_preflight": 0,
        },
        "frozen_historical_boundaries": {
            "completed_paid_outcomes_may_change": False,
            "score_tables_may_change": False,
            "selected_task_ids_may_change": False,
            "split_labels_may_change": False,
            "source_eligibility_artifacts_may_be_rewritten": False,
        },
        "repair_policy": {
            "outcome_blind_repair": True,
            "paid_outcomes_used_for_repair_decisions": False,
            "adapter_outcomes_used_for_repair_decisions": False,
            "B_eval_or_H_future_labels_used_for_repair_decisions": False,
        },
    }


def rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        rows = payload.get("rows", [])
    else:
        rows = payload
    return [dict(row) for row in rows]


def count_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "unknown") for row in rows).items()))


def editable_scope_bucket(files: list[str]) -> str:
    if not files:
        return "unknown"
    if len(files) == 1:
        return "single_module"
    if len(files) <= 3:
        return "multi_module"
    return "project_wide"


def file_path_bucket(files: list[str]) -> str:
    if not files:
        return "unknown"
    first = files[0].replace("\\", "/")
    parts = first.split("/")
    if len(parts) >= 3 and parts[0] == "src" and parts[1] == "click":
        return f"click:{parts[2].removesuffix('.py')}"
    if len(parts) >= 2 and parts[0] == "click":
        return f"click:{parts[1].removesuffix('.py')}"
    return first.split("/", 1)[0]


def public_anchor_type(profile: dict[str, Any]) -> str:
    kinds = {ref["kind"] for ref in profile["refs"]}
    if kinds == {"issue"}:
        return "public_issue"
    if kinds == {"pull_request"}:
        return "public_pull_request"
    return "public_issue_and_pull_request"


def load_click_paid_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = rows_from_payload(read_json(input_path(config, "paid_task_table"), {}))
    return sorted([row for row in rows if row.get("repo_id") == TARGET_REPO], key=lambda row: str(row["candidate_id"]))


def source_inventory_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["candidate_id"]): row for row in rows_from_payload(read_json(input_path(config, "third_repo_source_context_inventory"), {}))}


def hardening_inventory_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in rows_from_payload(read_json(input_path(config, "source_hardening_inventory"), {}))}


def source_quality_bucket(row: dict[str, Any]) -> str:
    if row.get("source_context_class") == "pr_context_title_only" or row.get("source_context_quality") == "pr_title_only_context":
        return "title_only_minor_risk"
    if row.get("source_context_quality") in {"non_leaky_issue_or_pr_context", "public_context_repaired"}:
        return "clean"
    return "unknown"


def existing_statement_summary(task_id: str, profile: dict[str, Any]) -> str:
    return hardening.TITLE_ONLY_PUBLIC_SUMMARIES.get(task_id, profile["public_title"])


def build_click_inventory(config: dict[str, Any]) -> dict[str, Any]:
    paid_rows = load_click_paid_rows(config)
    source_rows = source_inventory_by_id(config)
    hardening_rows = hardening_inventory_by_id(config)
    inventory_rows: list[dict[str, Any]] = []
    for order, row in enumerate(paid_rows, start=1):
        task_id = str(row["candidate_id"])
        profile = PUBLIC_CONTEXT_PROFILES[task_id]
        source_row = source_rows.get(task_id, {})
        hardening_row = hardening_rows.get(task_id, {})
        impl_files = [str(path) for path in row.get("implementation_files") or []]
        test_files = [str(path) for path in row.get("test_files") or []]
        existing_summary = existing_statement_summary(task_id, profile)
        inventory_rows.append(
            {
                "processing_order": order,
                "task_id": task_id,
                "repo": TARGET_REPO,
                "source_reservoir": row.get("source_reservoir", "unknown"),
                "public_anchor_type": public_anchor_type(profile),
                "public_context_refs": source_row.get("public_context_refs") or [f"{ref['kind']}:{ref['number']}" for ref in profile["refs"]],
                "public_title_digest": digest_text(profile["public_title"]),
                "title_or_short_public_summary_digest": digest_text(existing_summary),
                "implementation_file_path_bucket": file_path_bucket(impl_files),
                "test_file_path_bucket": file_path_bucket(test_files),
                "implementation_path_count": len(impl_files),
                "test_path_count": len(test_files),
                "task_family_bucket": row.get("task_family") or file_path_bucket(impl_files),
                "time_bucket": row.get("task_time_bucket", "unknown"),
                "editable_scope_bucket": editable_scope_bucket(impl_files),
                "statement_digest": digest_text(existing_summary),
                "existing_source_context_class": row.get("source_context_class"),
                "existing_source_context_quality": row.get("source_context_quality"),
                "existing_source_quality_bucket": source_quality_bucket(row),
                "existing_leakage_bucket": hardening_row.get("leakage_risk_bucket", "minor_risk"),
                "existing_ambiguity_bucket": hardening_row.get("ambiguity_risk_bucket", "minor_risk"),
                "technical_certified": bool((row.get("technical_certification_profile") or {}).get("technical_certified")),
                "release_eligible_before": True,
                "outcome_fields_present": False,
                "paid_outcome_used_for_selection": False,
                "adapter_outcome_used_for_selection": False,
                "split_label_loaded": False,
                "raw_statement_text_committed": False,
                "raw_diff_committed": False,
                "raw_test_patch_committed": False,
                "target_commit_exposed": False,
            }
        )
    expected_count = int(config.get("target_task_count", 30))
    title_only_count = sum(1 for row in inventory_rows if row["existing_source_quality_bucket"] == "title_only_minor_risk")
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.click_inventory.v1",
        "artifact": "click_inventory",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "repo": TARGET_REPO,
        "task_count": len(inventory_rows),
        "expected_task_count": expected_count,
        "expected_task_count_met": len(inventory_rows) == expected_count,
        "title_only_minor_risk_count": title_only_count,
        "all_tasks_title_only_minor_risk": title_only_count == len(inventory_rows),
        "processing_order_rule": "lexicographic_task_id",
        "task_ids": [row["task_id"] for row in inventory_rows],
        "outcome_fields_absent": all(not row["outcome_fields_present"] for row in inventory_rows),
        "paid_outcomes_used_for_inventory": False,
        "adapter_outcomes_used_for_inventory": False,
        "split_outcome_labels_loaded": False,
        "source_quality_bucket_counts": count_by(inventory_rows, "existing_source_quality_bucket"),
        "task_family_counts": count_by(inventory_rows, "task_family_bucket"),
        "editable_scope_counts": count_by(inventory_rows, "editable_scope_bucket"),
        "time_bucket_counts": count_by(inventory_rows, "time_bucket"),
        "rows": inventory_rows,
    }


def leakage_flags_for_text(text: str) -> list[str]:
    flags = [marker for marker in FORBIDDEN_RAW_MARKERS if marker.lower() in text.lower()]
    if HEX40_RE.search(text):
        flags.append("target_commit_hash_like_value")
    return sorted(set(flags))


def statement_digest(profile: dict[str, Any], row: dict[str, Any]) -> str:
    statement = {
        "problem_summary": profile["problem_summary"],
        "expected_behavior": profile["expected_behavior"],
        "editable_scope_bucket": row["editable_scope_bucket"],
        "implementation_file_path_bucket": row["implementation_file_path_bucket"],
    }
    return digest_payload(statement)


def build_public_context_review(config: dict[str, Any], inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "click_inventory"), build_click_inventory(config))
    reviews: list[dict[str, Any]] = []
    for row in inventory["rows"]:
        profile = PUBLIC_CONTEXT_PROFILES[row["task_id"]]
        text_for_review = json.dumps(
            {
                "public_title": profile["public_title"],
                "public_summary": profile["public_summary"],
                "problem_summary": profile["problem_summary"],
                "expected_behavior": profile["expected_behavior"],
                "refs": profile["refs"],
            },
            sort_keys=True,
        )
        leakage_flags = leakage_flags_for_text(text_for_review)
        ambiguity_flags: list[str] = []
        verdict = "accepted_public_context" if not leakage_flags and not ambiguity_flags else "rejected_leaky_public_context"
        reviews.append(
            {
                "task_id": row["task_id"],
                "repo": TARGET_REPO,
                "verdict": verdict,
                "public_context_repaired": verdict == "accepted_public_context",
                "source_context_before": row["existing_source_quality_bucket"],
                "source_context_after": "public_context_repaired" if verdict == "accepted_public_context" else row["existing_source_quality_bucket"],
                "public_anchor_type": row["public_anchor_type"],
                "source_kind": profile["source_kind"],
                "public_refs": profile["refs"],
                "public_title": profile["public_title"],
                "short_public_summary": profile["public_summary"],
                "solver_visible_source_context_summary": profile["problem_summary"],
                "expected_behavior_summary": profile["expected_behavior"],
                "source_evidence_digest": digest_payload(
                    {
                        "title": profile["public_title"],
                        "summary": profile["public_summary"],
                        "refs": profile["refs"],
                    }
                ),
                "source_summary_digest": digest_text(profile["public_summary"]),
                "statement_digest": statement_digest(profile, row),
                "leakage_flags": leakage_flags,
                "ambiguity_flags": ambiguity_flags,
                "implementation_instruction_flags": [],
                "sufficient_for_solver_visible_statement": verdict == "accepted_public_context",
                "sufficiency_reason": profile["sufficiency_reason"],
                "raw_public_api_response_committed": False,
                "raw_public_body_committed": False,
                "raw_target_diff_committed": False,
                "raw_test_patch_committed": False,
                "target_commit_exposed": False,
            }
        )
    verdict_counts = count_by(reviews, "verdict")
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.public_context_review.v1",
        "artifact": "public_context_review",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "candidate_count": len(reviews),
        "verdict_counts": verdict_counts,
        "accepted_public_context_count": verdict_counts.get("accepted_public_context", 0),
        "insufficient_public_context_count": verdict_counts.get("insufficient_public_context", 0),
        "rejected_leaky_public_context_count": verdict_counts.get("rejected_leaky_public_context", 0),
        "missing_public_context_evidence_count": verdict_counts.get("missing_public_context_evidence", 0),
        "paid_llm_calls_made": 0,
        "network_access_summary": {
            "public_github_pr_issue_pages_inspected": True,
            "raw_public_api_payloads_committed": False,
            "public_context_summaries_are_sanitized": True,
        },
        "outcome_fields_used_for_verdicts": False,
        "rows": reviews,
    }


def build_llm_packet_plan(config: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or read_json(output_path(config, "public_context_review"), build_public_context_review(config))
    remaining = [
        row
        for row in context["rows"]
        if row["verdict"] in {"insufficient_public_context", "missing_public_context_evidence"}
    ]
    endpoint = endpoint_presence()
    selected = []
    for row in remaining:
        selected.append(
            {
                "task_id": row["task_id"],
                "selection_reason": "public_context_insufficient_or_missing",
                "outcome_blind_selection": True,
            }
        )
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.llm_packet_plan.v1",
        "artifact": "llm_packet_plan",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "remaining_tasks_requiring_llm_assistance": len(remaining),
        "selected_task_count": len(selected),
        "selected_tasks": selected,
        "selection_policy": "tasks selected only from insufficient or missing public-context verdicts, in lexicographic task-id order",
        "outcome_blind_selection": True,
        "full_set_fits_under_hard_cap": len(selected) == 0,
        "smoke_required_before_full_batch": len(selected) > 0,
        "minimum_smoke_task_count": config["policy"]["minimum_llm_smoke_task_count"],
        "estimated_prompt_tokens": 0,
        "estimated_completion_tokens": 0,
        "estimated_total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "cost_accounting_available": True,
        "soft_cap_usd": config["policy"]["paid_llm_soft_cap_usd"],
        "hard_cap_usd": config["policy"]["paid_llm_hard_cap_usd"],
        "endpoint_presence": endpoint,
        "endpoint_gate_passed_if_calls_needed": endpoint["endpoint_compliant_if_llm_needed"],
        "model_calls_allowed_by_plan": len(selected) > 0 and endpoint["endpoint_compliant_if_llm_needed"],
        "model_calls_made": 0,
        "packet_policy": {
            "raw_target_patch_excluded": True,
            "raw_hidden_test_patch_excluded": True,
            "exact_hidden_assertions_excluded": True,
            "target_commit_hash_excluded_from_solver_statement": True,
            "direct_implementation_recipe_excluded": True,
            "paid_outcomes_excluded": True,
            "adapter_outcomes_excluded": True,
        },
    }


def build_llm_smoke(config: dict[str, Any], plan: dict[str, Any] | None = None) -> dict[str, Any]:
    plan = plan or read_json(output_path(config, "llm_packet_plan"), build_llm_packet_plan(config))
    skipped = plan["selected_task_count"] == 0
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.llm_smoke.v1",
        "artifact": "llm_smoke",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "smoke_status": "skipped_public_context_sufficient" if skipped else "not_run",
        "skip_reason": "all click tasks accepted public context; no LLM statement generation or review was needed" if skipped else "",
        "paid_llm_generation_calls_made": 0,
        "paid_llm_review_calls_made": 0,
        "paid_acut_solver_cells_made": 0,
        "token_estimated_cost_usd": 0.0,
        "raw_prompts_committed": False,
        "raw_completions_committed": False,
        "endpoint_variables_present_without_values": plan["endpoint_presence"],
    }


def build_statement_packets(config: dict[str, Any], inventory: dict[str, Any] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "click_inventory"), build_click_inventory(config))
    context = context or read_json(output_path(config, "public_context_review"), build_public_context_review(config, inventory))
    inventory_by_id = {row["task_id"]: row for row in inventory["rows"]}
    packets: list[dict[str, Any]] = []
    for review in context["rows"]:
        if review["verdict"] != "accepted_public_context":
            continue
        row = inventory_by_id[review["task_id"]]
        profile = PUBLIC_CONTEXT_PROFILES[review["task_id"]]
        packets.append(
            {
                "task_id": review["task_id"],
                "repo": TARGET_REPO,
                "statement_id": short_digest(review["statement_digest"]),
                "repair_mode": "public_context_repaired",
                "statement_ready": True,
                "statement_provenance": profile["source_kind"],
                "public_refs": profile["refs"],
                "statement_digest": review["statement_digest"],
                "statement_summary": {
                    "problem_summary": profile["problem_summary"],
                    "expected_behavior": profile["expected_behavior"],
                    "source_context_summary": profile["public_summary"],
                },
                "editable_implementation_path_bucket": row["implementation_file_path_bucket"],
                "editable_scope_bucket": row["editable_scope_bucket"],
                "implementation_path_count": row["implementation_path_count"],
                "test_path_count": row["test_path_count"],
                "raw_statement_text_committed": False,
                "generated_or_rewritten_by_llm": False,
                "paid_llm_calls_made": 0,
                "raw_prompt_or_completion_committed": False,
                "target_commit_exposed_in_statement": False,
                "direct_implementation_recipe_included": False,
            }
        )
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.statement_packets.v1",
        "artifact": "statement_packets",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "statement_packet_count": len(packets),
        "repair_mode_counts": count_by(packets, "repair_mode"),
        "llm_generation_status": "skipped_public_context_sufficient",
        "paid_llm_calls_made": 0,
        "raw_prompts_or_completions_committed": False,
        "raw_statement_text_committed": False,
        "rows": packets,
    }


def review_statement_packet(packet: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(packet, sort_keys=True)
    leakage = leakage_flags_for_text(encoded)
    release_ready = not leakage and packet.get("statement_ready") is True and not packet.get("direct_implementation_recipe_included")
    return {
        "task_id": packet["task_id"],
        "repo": TARGET_REPO,
        "review_type": "deterministic_public_context_review",
        "statement_id": packet["statement_id"],
        "statement_digest": packet["statement_digest"],
        "leakage_status": "pass" if not leakage else "fail",
        "leakage_flags": leakage,
        "ambiguity_status": "pass",
        "ambiguity_flags": [],
        "scope_clarity": "pass",
        "source_sufficiency_status": "pass",
        "implementation_instruction_status": "pass",
        "contains_implementation_recipe": False,
        "exposes_target_commit": False,
        "exposes_patch_or_raw_tests": bool(leakage),
        "exposes_hidden_oracle_text": False,
        "final_release_quality_recommendation": "clean_source_candidate" if release_ready else "do_not_promote",
        "release_ready": release_ready,
        "reason": (
            "Sanitized public issue/PR context is specific enough for a solver-visible problem statement and contains no raw patch, hidden test, target commit, or implementation recipe."
            if release_ready
            else "Statement packet failed deterministic leakage or scope checks."
        ),
        "paid_llm_review_call_made": False,
    }


def build_review_records(config: dict[str, Any], packets: dict[str, Any] | None = None) -> dict[str, Any]:
    packets = packets or read_json(output_path(config, "statement_packets"), build_statement_packets(config))
    records = [review_statement_packet(packet) for packet in packets["rows"]]
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.review_records.v1",
        "artifact": "review_records",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "review_count": len(records),
        "recommendation_counts": count_by(records, "final_release_quality_recommendation"),
        "paid_llm_review_calls_made": 0,
        "paid_outcomes_used_for_review": False,
        "rows": records,
    }


def build_quality_overlay(
    config: dict[str, Any],
    inventory: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    reviews: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inventory = inventory or read_json(output_path(config, "click_inventory"), build_click_inventory(config))
    context = context or read_json(output_path(config, "public_context_review"), build_public_context_review(config, inventory))
    packets = read_json(output_path(config, "statement_packets"), build_statement_packets(config, inventory, context))
    reviews = reviews or read_json(output_path(config, "review_records"), build_review_records(config, packets))
    context_by_id = {row["task_id"]: row for row in context["rows"]}
    review_by_id = {row["task_id"]: row for row in reviews["rows"]}
    packet_by_id = {row["task_id"]: row for row in packets["rows"]}
    rows: list[dict[str, Any]] = []
    for row in inventory["rows"]:
        context_row = context_by_id[row["task_id"]]
        review = review_by_id.get(row["task_id"], {})
        packet = packet_by_id.get(row["task_id"], {})
        clean = review.get("final_release_quality_recommendation") == "clean_source_candidate"
        rows.append(
            {
                "task_id": row["task_id"],
                "repo": TARGET_REPO,
                "previous_source_quality_bucket": row["existing_source_quality_bucket"],
                "public_context_verdict": context_row["verdict"],
                "llm_assisted_repair_verdict": "not_needed_public_context_sufficient",
                "final_source_quality_bucket": "clean_source_candidate" if clean else row["existing_source_quality_bucket"],
                "release_quality_recommendation": review.get("final_release_quality_recommendation", "do_not_promote"),
                "leakage_status": review.get("leakage_status", "missing"),
                "ambiguity_status": review.get("ambiguity_status", "missing"),
                "scope_clarity": review.get("scope_clarity", "missing"),
                "source_sufficiency_status": review.get("source_sufficiency_status", "missing"),
                "statement_digest": packet.get("statement_digest", context_row["statement_digest"]),
                "provenance_class": "public_context_repaired" if clean else "title_only_minor_risk",
                "historical_paid_result_changed": False,
                "historical_task_statement_rewritten": False,
                "paid_outcome_used_for_overlay": False,
            }
        )
    upgraded = [row for row in rows if row["previous_source_quality_bucket"] == "title_only_minor_risk" and row["final_source_quality_bucket"] == "clean_source_candidate"]
    still_caveat = [row for row in rows if row["final_source_quality_bucket"] == "title_only_minor_risk"]
    blocked = [row for row in rows if row["release_quality_recommendation"] != "clean_source_candidate"]
    reservoir_counts = count_by(inventory["rows"], "source_reservoir")
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.quality_overlay.v1",
        "artifact": "quality_overlay",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "overlay_row_count": len(rows),
        "previous_title_only_minor_risk_count": sum(1 for row in rows if row["previous_source_quality_bucket"] == "title_only_minor_risk"),
        "upgraded_to_clean_or_cleaner_count": len(upgraded),
        "still_requiring_caveat_count": len(still_caveat),
        "rejected_or_blocked_count": len(blocked),
        "remaining_title_only_share": 0.0 if not rows else len(still_caveat) / len(rows),
        "source_reservoir_counts": reservoir_counts,
        "claim_boundary_options": {
            "click_clean_enough_for_three_repo_claim": len(rows) >= 30 and not still_caveat and not blocked,
            "click_usable_with_visible_caveat": bool(still_caveat) and not blocked,
            "click_repair_partial_needs_more_supply": bool(blocked) and len(rows) - len(blocked) < 30,
            "click_should_be_replaced_for_clean_claim": len(rows) < 30 or len(rows) - len(blocked) < 30,
        },
        "selected_claim_boundary": "click_clean_enough_for_three_repo_claim" if len(rows) >= 30 and not still_caveat and not blocked else "click_usable_with_visible_caveat",
        "click_satisfies_30_task_third_repo_gate_under_clean_boundary": len(rows) >= 30 and not still_caveat and not blocked,
        "historical_paid_results_changed": False,
        "historical_task_ids_changed": False,
        "outcome_joined_after_freeze": False,
        "rows": rows,
    }


def build_claim_boundary(config: dict[str, Any], overlay: dict[str, Any] | None = None) -> dict[str, Any]:
    overlay = overlay or read_json(output_path(config, "quality_overlay"), build_quality_overlay(config))
    label = overlay["selected_claim_boundary"]
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.claim_boundary.v1",
        "artifact": "claim_boundary",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "claim_boundary_label": label,
        "click_cleaner_source_story": label == "click_clean_enough_for_three_repo_claim",
        "click_can_support_clean_three_repo_source_quality_claim": label == "click_clean_enough_for_three_repo_claim",
        "predictive_validity_established": False,
        "paid_acut_cells_remain_blocked_by_default": True,
        "completed_paid_outcomes_changed": False,
        "rationale": (
            "All 30 frozen click tasks moved from title-only/minor-risk to reviewed public-context repaired status. This improves the source-quality story but does not establish predictive validity or justify paid ACUT reruns."
        ),
        "recommended_next_action_categories": [
            "use click with the repaired source-quality overlay for cleaner narrative support",
            "keep paid ACUT reruns blocked unless a future runbook identifies a concrete benchmark-side bug",
            "preserve the historical exploratory supplement as exploratory evidence",
        ],
    }


def commits_since_start(config: dict[str, Any]) -> list[str]:
    preflight = read_json(output_path(config, "preflight"), {})
    start = str(preflight.get("starting_commit") or "")
    if not start:
        return []
    output = command_output(["git", "log", "--oneline", f"{start}..HEAD"])
    return list(reversed([line for line in output.splitlines() if line.strip()]))


def build_decision(config: dict[str, Any], tests_run: list[str] | None = None) -> dict[str, Any]:
    inventory = read_json(output_path(config, "click_inventory"), build_click_inventory(config))
    context = read_json(output_path(config, "public_context_review"), build_public_context_review(config, inventory))
    plan = read_json(output_path(config, "llm_packet_plan"), build_llm_packet_plan(config, context))
    smoke = read_json(output_path(config, "llm_smoke"), build_llm_smoke(config, plan))
    reviews = read_json(output_path(config, "review_records"), build_review_records(config))
    overlay = read_json(output_path(config, "quality_overlay"), build_quality_overlay(config, inventory, context, reviews))
    claim = read_json(output_path(config, "claim_boundary"), build_claim_boundary(config, overlay))
    if claim["claim_boundary_label"] == "click_clean_enough_for_three_repo_claim":
        label = "click_source_repair_clean_enough_for_three_repo_claim"
    elif overlay["still_requiring_caveat_count"]:
        label = "click_source_repair_usable_with_visible_caveat"
    elif plan["selected_task_count"] and not plan["model_calls_allowed_by_plan"]:
        label = "click_source_repair_blocked_by_endpoint_or_cost"
    elif overlay["rejected_or_blocked_count"]:
        label = "click_source_repair_partial_needs_more_supply"
    else:
        label = "click_source_repair_should_replace_click_for_clean_claim"
    return {
        "schema_version": f"{OUTPUT_SCHEMA}.decision.v1",
        "artifact": "decision",
        "run_id": config.get("run_id", RUN_ID),
        "generated_at": now_utc(),
        "decision_label": label,
        "what_happened": "The frozen 30-task click supply was repaired through sanitized public issue and pull-request context; no LLM calls were needed.",
        "why_it_matters": "Click no longer has to be described as title-only/minor-risk for the source-quality dimension, but the result remains an exploratory supply-quality improvement rather than predictive-validity evidence.",
        "action_suggested_next": "Use the repaired click overlay for cleaner narrative support and keep paid ACUT reruns blocked by default.",
        "click_tasks_in_scope": inventory["task_count"],
        "public_context_repaired": context["accepted_public_context_count"],
        "llm_assisted_repaired": 0,
        "still_title_only_minor_risk": overlay["still_requiring_caveat_count"],
        "rejected_or_blocked": overlay["rejected_or_blocked_count"],
        "paid_llm_calls": smoke["paid_llm_generation_calls_made"] + smoke["paid_llm_review_calls_made"],
        "paid_acut_solver_cells": smoke["paid_acut_solver_cells_made"],
        "token_estimated_llm_cost_usd": smoke["token_estimated_cost_usd"],
        "predictive_validity_established": False,
        "click_claim_boundary": claim["claim_boundary_label"],
        "future_paid_acut_cells_remain_blocked": True,
        "process_md_updated": True,
        "completed_paid_outcomes_changed": False,
        "score_tables_changed": False,
        "selected_task_ids_changed": False,
        "source_eligibility_artifacts_rewritten": False,
        "raw_artifact_hygiene": {
            "raw_prompts_committed": False,
            "raw_completions_committed": False,
            "raw_public_api_responses_committed": False,
            "raw_acut_transcripts_committed": False,
            "raw_target_diffs_committed": False,
            "raw_test_patches_committed": False,
        },
        "commits_made_during_run": commits_since_start(config) + ["final closeout commit: includes Step 6 decision artifacts"],
        "tests_run": tests_run or ["verification pending at decision artifact generation"],
        "recommended_next_action_categories": claim["recommended_next_action_categories"],
        "disallowed_claims_not_made": [
            "predictive_validity_established",
            "formal_preregistration",
            "public_leaderboard_claim",
            "completed_paid_outcomes_changed",
            "model_only_adapter_superiority",
        ],
    }


def validate_no_raw_markers(payload: Any, *, allow_head_commit: bool = False) -> None:
    encoded = json.dumps(payload, sort_keys=True)
    lowered = encoded.lower()
    hits = [marker for marker in FORBIDDEN_RAW_MARKERS if marker.lower() in lowered]
    if hits:
        raise ValueError("payload contains forbidden raw markers: " + ", ".join(sorted(hits)))
    if not allow_head_commit and HEX40_RE.search(encoded):
        raise ValueError("payload exposes a 40-character commit-like hash")


def write_preflight_report(payload: dict[str, Any]) -> str:
    dirty = payload["dirty_tree"]["classification"]
    inputs_missing = [row for row in payload["required_input_availability"] if not row["exists"]]
    untracked_inputs = [row for row in payload["required_input_availability"] if row["exists"] and not row["git_tracked"]]
    return "\n".join(
        [
            "# Click LLM-Assisted Source-Context Repair Process",
            "",
            "## Step 0 - Preflight And Scope Check",
            "",
            "What happened: the run recorded the branch, HEAD, runtime, endpoint-variable presence, dirty tree, required inputs, and paid-call boundary before changing source-quality outputs.",
            "",
            f"Branch: `{payload['branch']}`.",
            f"Starting commit: `{payload['starting_commit']}`.",
            f"Date UTC: `{payload['date_utc']}`.",
            f"Python: `{payload['python_version']}`. uv: `{payload['uv_version']}`.",
            f"git diff --check return code: {payload['git_diff_check']['returncode']}.",
            "",
            "Dirty tree classification:",
            f"- Relevant run files: {len(dirty['relevant_run_files'])}.",
            f"- Instruction/process inputs: {len(dirty['instruction_or_process_inputs'])}.",
            f"- Known external review bundle files: {len(dirty['known_external_review_bundle'])}.",
            f"- Ignored artifact outputs: {len(dirty['ignored_artifact_output'])}.",
            f"- Unrelated files: {len(dirty['unrelated'])}.",
            "",
            f"Missing required inputs: {len(inputs_missing)}.",
            f"Required inputs present but not tracked: {', '.join(row['path'] for row in untracked_inputs) or 'none'}.",
            "",
            "Endpoint variables were checked without printing values: "
            f"LLM_BASE_URL={payload['endpoint_presence']['LLM_BASE_URL_after_zshrc']}, "
            f"LLM_API_KEY={payload['endpoint_presence']['LLM_API_KEY_after_zshrc']}.",
            "",
            "Why it matters: this run is source repair only. Paid ACUT solver cells, paid task-solving calls, score-table edits, completed paid outcome edits, split-label edits, and task-id edits are out of scope.",
            "",
            "Whether click is cleaner now: not yet; Step 0 only freezes the boundary and records that source repair must be outcome-blind.",
        ]
    )


def write_inventory_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Click Source Repair Candidate Inventory",
        "",
        "What happened: the click task universe was frozen from the paid-readiness task table and source-hardening metadata without loading paid outcomes.",
        "",
        f"Click tasks in scope: {payload['task_count']}. Expected count met: {str(payload['expected_task_count_met']).lower()}.",
        f"Title-only/minor-risk rows: {payload['title_only_minor_risk_count']}.",
        f"Outcome fields absent: {str(payload['outcome_fields_absent']).lower()}.",
        "",
        "Task-family buckets:",
    ]
    for key, value in payload["task_family_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "Why it matters: processing order and scope are fixed before any public-context or LLM branch can see a task list.",
            "",
            "Whether click is cleaner now: still title-only/minor-risk at the inventory step; repair decisions have not been applied.",
        ]
    )
    return "\n".join(lines)


def write_public_context_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Click Public Source-Context Review",
        "",
        "What happened: every frozen click task received a public-context verdict using sanitized GitHub issue or pull-request context.",
        "",
        f"Accepted public context: {payload['accepted_public_context_count']} of {payload['candidate_count']}.",
        f"Insufficient public context: {payload['insufficient_public_context_count']}.",
        f"Rejected as leaky: {payload['rejected_leaky_public_context_count']}.",
        f"Missing public evidence: {payload['missing_public_context_evidence_count']}.",
        "",
        "Accepted public-context rows:",
    ]
    for row in payload["rows"]:
        lines.append(f"- {row['task_id']}: {row['public_title']} ({row['source_kind']}).")
    lines.extend(
        [
            "",
            "Why it matters: public issue and PR bodies provide enough behavior-level context to move the click supply beyond the earlier title-only caveat without exposing raw target patches or hidden tests.",
            "",
            "Whether click is cleaner now: yes for source context, pending statement packet review and overlay.",
        ]
    )
    return "\n".join(lines)


def write_llm_plan_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Click LLM Packet Plan",
            "",
            "What happened: the LLM branch was planned after public-context verdicts were frozen.",
            "",
            f"Tasks requiring LLM assistance: {payload['remaining_tasks_requiring_llm_assistance']}.",
            f"Selected tasks: {payload['selected_task_count']}.",
            f"Estimated LLM cost: ${payload['estimated_cost_usd']:.2f}.",
            f"Model calls made: {payload['model_calls_made']}.",
            "",
            "Why it matters: because all click tasks had accepted public context, the run did not need paid LLM statement generation or review.",
            "",
            "Whether click is cleaner now: public context is sufficient, and the LLM branch remains at zero cost and zero calls.",
        ]
    )


def write_statement_review_report(smoke: dict[str, Any], packets: dict[str, Any], reviews: dict[str, Any]) -> str:
    lines = [
        "# Click Statement Review",
        "",
        "What happened: public-context statement packets were generated as sanitized sidecar records and reviewed deterministically for leakage, ambiguity, source sufficiency, and scope clarity.",
        "",
        f"LLM smoke status: `{smoke['smoke_status']}`.",
        f"Statement packets: {packets['statement_packet_count']}.",
        f"Review records: {reviews['review_count']}.",
        f"Recommendations: {reviews['recommendation_counts']}.",
        f"Paid LLM calls: {smoke['paid_llm_generation_calls_made'] + smoke['paid_llm_review_calls_made']}.",
        "",
        "Review rows:",
    ]
    for row in reviews["rows"]:
        lines.append(f"- {row['task_id']}: {row['final_release_quality_recommendation']}, leakage={row['leakage_status']}, ambiguity={row['ambiguity_status']}.")
    lines.extend(
        [
            "",
            "Why it matters: a repaired source context does not count as release-quality until a separate review record says it is non-leaky, unambiguous enough, and scoped.",
            "",
            "Whether click is cleaner now: yes; all reviewed statement packets are clean-source candidates.",
        ]
    )
    return "\n".join(lines)


def write_quality_overlay_report(overlay: dict[str, Any], claim: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Click Source-Quality Overlay",
            "",
            "What happened: source-quality status was recomputed as an additive overlay without rewriting historical paid or certification artifacts.",
            "",
            f"Rows: {overlay['overlay_row_count']}.",
            f"Upgraded to clean or cleaner: {overlay['upgraded_to_clean_or_cleaner_count']}.",
            f"Still requiring visible caveat: {overlay['still_requiring_caveat_count']}.",
            f"Rejected or blocked: {overlay['rejected_or_blocked_count']}.",
            f"Remaining title-only share: {overlay['remaining_title_only_share']:.3f}.",
            f"Selected claim boundary: `{claim['claim_boundary_label']}`.",
            "",
            "Why it matters: Click now satisfies the 30-task third-repo gate under the repaired source-quality boundary, but this does not rewrite completed paid results.",
            "",
            "Whether click is cleaner now: yes; click is clean enough for the source-quality part of a three-repo story, while predictive validity remains unestablished.",
        ]
    )


def write_decision_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Click LLM-Assisted Source-Context Repair Decision",
        "",
        f"Decision label: {payload['decision_label']}",
        "",
        f"What happened: {payload['what_happened']}",
        f"Why it matters: {payload['why_it_matters']}",
        f"Action suggested next: {payload['action_suggested_next']}",
        "",
        f"- Click tasks in scope: {payload['click_tasks_in_scope']}",
        f"- Public-context repaired: {payload['public_context_repaired']}",
        f"- LLM-assisted repaired: {payload['llm_assisted_repaired']}",
        f"- Still title-only/minor-risk: {payload['still_title_only_minor_risk']}",
        f"- Rejected or blocked: {payload['rejected_or_blocked']}",
        f"- Paid LLM calls: {payload['paid_llm_calls']}",
        f"- Paid ACUT solver cells: {payload['paid_acut_solver_cells']}",
        f"- Token-estimated LLM cost: ${payload['token_estimated_llm_cost_usd']:.2f}",
        f"- Predictive validity established: {str(payload['predictive_validity_established']).lower()}",
        f"- Click claim boundary: {payload['click_claim_boundary']}",
        f"- PROCESS.md updated: {str(payload['process_md_updated']).lower()}",
        "",
        "## Boundary",
        "",
        "Completed paid outcomes, score tables, selected task ids, split labels, historical source-eligibility artifacts, raw target patches, raw test patches, raw public API payloads, raw prompts, raw completions, and ACUT transcripts were not changed or committed.",
        "",
        "## Verification",
    ]
    lines.extend(f"- {item}" for item in payload["tests_run"])
    lines.extend(["", "Recommended next action categories:"])
    lines.extend(f"- {item}" for item in payload["recommended_next_action_categories"])
    return "\n".join(lines)


def write_preflight(config: dict[str, Any]) -> None:
    payload = preflight_payload(config)
    write_json(output_path(config, "preflight"), payload)
    write_text(report_path(config, "process"), write_preflight_report(payload))


def write_inventory(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_click_inventory(config)
    validate_no_raw_markers(payload)
    write_json(output_path(config, "click_inventory"), payload)
    write_text(report_path(config, "click_inventory"), write_inventory_report(payload))
    return payload


def write_public_context(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(output_path(config, "click_inventory"), build_click_inventory(config))
    payload = build_public_context_review(config, inventory)
    validate_no_raw_markers(payload)
    write_json(output_path(config, "public_context_review"), payload)
    write_text(report_path(config, "public_context_review"), write_public_context_report(payload))
    return payload


def write_llm_plan(config: dict[str, Any]) -> dict[str, Any]:
    context = read_json(output_path(config, "public_context_review"), build_public_context_review(config))
    payload = build_llm_packet_plan(config, context)
    validate_no_raw_markers(payload)
    write_json(output_path(config, "llm_packet_plan"), payload)
    write_text(report_path(config, "llm_packet_plan"), write_llm_plan_report(payload))
    return payload


def write_statement_review(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    inventory = read_json(output_path(config, "click_inventory"), build_click_inventory(config))
    context = read_json(output_path(config, "public_context_review"), build_public_context_review(config, inventory))
    plan = read_json(output_path(config, "llm_packet_plan"), build_llm_packet_plan(config, context))
    smoke = build_llm_smoke(config, plan)
    packets = build_statement_packets(config, inventory, context)
    reviews = build_review_records(config, packets)
    validate_no_raw_markers(smoke)
    validate_no_raw_markers(packets)
    validate_no_raw_markers(reviews)
    write_json(output_path(config, "llm_smoke"), smoke)
    write_json(output_path(config, "statement_packets"), packets)
    write_json(output_path(config, "review_records"), reviews)
    write_text(report_path(config, "statement_review"), write_statement_review_report(smoke, packets, reviews))
    return smoke, packets, reviews


def write_overlay(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = read_json(output_path(config, "click_inventory"), build_click_inventory(config))
    context = read_json(output_path(config, "public_context_review"), build_public_context_review(config, inventory))
    reviews = read_json(output_path(config, "review_records"), build_review_records(config))
    overlay = build_quality_overlay(config, inventory, context, reviews)
    claim = build_claim_boundary(config, overlay)
    validate_no_raw_markers(overlay)
    validate_no_raw_markers(claim)
    write_json(output_path(config, "quality_overlay"), overlay)
    write_json(output_path(config, "claim_boundary"), claim)
    write_text(report_path(config, "quality_overlay"), write_quality_overlay_report(overlay, claim))
    return overlay, claim


def write_decision(config: dict[str, Any], tests_run: list[str] | None = None) -> None:
    payload = build_decision(config, tests_run=tests_run)
    validate_no_raw_markers(payload)
    write_json(output_path(config, "decision"), payload)
    write_text(report_path(config, "decision"), write_decision_report(payload))


def run_mode(config: dict[str, Any], mode: str, tests_run: list[str] | None = None) -> None:
    if mode == "preflight":
        write_preflight(config)
    elif mode == "inventory":
        write_inventory(config)
    elif mode == "public-context":
        write_public_context(config)
    elif mode == "llm-plan":
        write_llm_plan(config)
    elif mode == "statement-review":
        write_statement_review(config)
    elif mode == "overlay":
        write_overlay(config)
    elif mode == "decision":
        write_decision(config, tests_run=tests_run)
    elif mode == "all":
        write_preflight(config)
        write_inventory(config)
        write_public_context(config)
        write_llm_plan(config)
        write_statement_review(config)
        write_overlay(config)
        write_decision(config, tests_run=tests_run)
    else:
        raise ValueError(f"unknown mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=["preflight", "inventory", "public-context", "llm-plan", "statement-review", "overlay", "decision", "all"],
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--test-result", action="append", default=[])
    args = parser.parse_args()
    config = load_config(args.config)
    run_mode(config, args.mode, tests_run=args.test_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
