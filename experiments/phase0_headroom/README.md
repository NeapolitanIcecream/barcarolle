# Headroom And Task-Supply Evidence

This directory preserves the lightweight Phase 0 evidence that the compiler
prototype still uses: repository-history candidate sources, certified-task
tables, release manifests, target profiles, workspace-adapter tools, and small
score summaries.

It is historical support material, not the active project entry point. Start
from `docs/research/project-state-after-proposal.md` for the current state.

Run retained tests from the repository root:

```bash
uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools -q
```

Expected retained layout:

```text
configs/
candidate_sources/
target_profiles/
certified_tasks/
releases/
results/        # small summaries only
reports/        # selected historical reports
tools/
```

Do not commit raw Agent transcripts, submissions, verifier result streams,
solver or verifier workspaces, cloned target repositories, local virtual
environments, or cost ledgers. Those are intentionally ignored.
