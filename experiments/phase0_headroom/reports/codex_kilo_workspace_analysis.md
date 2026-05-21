# Codex Kilo Workspace Analysis

The Codex/Kilo cross-harness comparison is not scoreable yet. Post-run diagnosis resolved endpoint proof for both harnesses, but the experiment still stopped before smoke and full matrix execution because scoreable workspace command templates have not been run.

The main decision is operational rather than statistical: no `same_model_cross_harness` estimate should be computed from this run. The adapter code can isolate multiple harnesses, and both candidates now have proven endpoint/provider shapes, but neither has a scoreable ACUT smoke result.

Required next evidence:

- Codex and Kilo workspace command templates that read `{statement_file}`, mutate `{workspace}`, and leave `git diff` as the submission artifact.
- A four-cell smoke matrix using the now-proven endpoint/provider shapes before any full matrix run.
