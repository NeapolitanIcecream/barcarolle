# Agent Prompt: Sphinx Target Prep

Please execute this runbook end to end:

`/Users/chenmohan/gits/barcarolle/docs/research/sphinx-target-prep-runbook-2026-06-17.md`

Work in `/Users/chenmohan/gits/barcarolle`.

This is a no-paid Sphinx target-prep gate for the Agent Tuning Demo. Do not run
paid Agent cells, paid LLM calls, paid tuner/proposer calls, paid baseline
discovery, or before/after tuning experiments.

The goal is to decide whether `sphinx-doc/sphinx` is a practical next target:
target profile, version-aware verifier pinning, bounded no-paid replay/
certification, and a simple rolling-origin policy. Keep the work tied to this
decision. Do not overdesign plotting, window policies, environment solving, or
general target-repo infrastructure.

Follow the runbook's packages, outputs, PROCESS update, verification, hygiene,
and commit requirements. If Sphinx needs a bounded repair, document that clearly
and stop at the repair gate. If Sphinx fails structurally, complete the negative
result honestly rather than pivoting to another repository in this run.
