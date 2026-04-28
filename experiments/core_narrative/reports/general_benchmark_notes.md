# General Benchmark Notes

## Basis

`G_score` should use a direct-run slice of SWE-Bench Pro Public, not public leaderboard scores. The selected basis is `gscore_swebench_pro_public_22_v1`, defined in `experiments/core_narrative/configs/general_benchmark.yaml`.

The benchmark population is the `ScaleAI/SWE-bench_Pro` `default/test` split at the pinned Hugging Face snapshot. The data file is locked by commit and content hash in the manifest. The evaluator is the public `scaleapi/SWE-bench_Pro-os` harness pinned to its March 31, 2026 main-branch commit.

The task subset is not handpicked. It is a deterministic 22-task slice: two rows per public repository, ordered by `sha256("barcarolle-core-narrative-gscore-v1\n" + instance_id)`. The coordinator should materialize the concrete IDs once, verify gold-patch infrastructure health, apply only predeclared global-infra replacements if needed, and then lock the slice before any ACUT run.

## Rationale

SWE-Bench Pro Public is the best available general coding-agent basis for this experiment because it is a cross-repository issue-resolution benchmark, it uses executable repository tests, and it is newer and more challenging than SWE-bench Verified. This makes it closer to the repository-work setting than function-level coding tests while still being general across repositories.

The direct-run basis matters. Public benchmark scores usually combine a model, scaffold, prompt, retrieval policy, budget, retry policy, and execution environment. Using those scores would compare external systems, not the ACUT manifests in this experiment. A direct run keeps the evaluated subject aligned: the same ACUTs that receive `R_score` and `W_score` also receive `G_score`.

SWE-bench Verified was not selected as the primary basis because it is now a weaker frontier signal. OpenAI's February 23, 2026 note says Verified has material test-design and contamination problems and recommends SWE-Bench Pro for current public reporting. Verified remains useful background, but using it as the primary `G_score` would make ranking reversals easier to dismiss as an artifact of an aging public benchmark.

## Anti-Cherry-Picking Controls

- Freeze the dataset snapshot, evaluator revision, selection salt, and slice algorithm before ACUT runs.
- Select by hash over `instance_id`, stratified only by repository. Do not inspect gold patches, hidden tests, public per-task results, or ACUT outputs during selection.
- Use exactly two tasks per repository to prevent a single public repository from dominating the general score.
- Run the same locked task IDs, visible context fields, budget policy, evaluator, and scoring formula for every ACUT.
- Count patch apply failures, invalid submissions, timeouts, verification failures, and ACUT runtime errors as zero.
- Allow replacement only for global infrastructure failures found by gold-patch smoke tests before ACUT scoring begins.
- Do not drop tasks after seeing ACUT results. If the locked slice proves globally unreliable after scoring starts, abort or rerun the whole `G_score` basis rather than pruning cases.
- Treat public leaderboard scores as background only. They must not decide task inclusion, ACUT rank, or post-hoc interpretation.

## Mismatch Risks

- SWE-Bench Pro public leaderboard entries may use SWE-Agent, mini-SWE-agent, custom harnesses, high turn limits, uncapped cost, or Modal settings that differ from ACUT manifests.
- The public Pro dataset is more heterogeneous than the eventual target repository. A repository-context-heavy ACUT may look weaker on Pro but stronger on the selected repository.
- The selected 22-task slice is small. It is enough to freeze a general ordering signal for the experiment, but it should be reported with uncertainty and not treated as an official leaderboard result.
- Public benchmark tasks may be represented in model training data or online discussions. Network access must follow the same policy used for ACUT repository tasks, and any network-enabled run should be flagged.
- SWE-Bench Pro evaluates test passing. It does not include the Barcarolle-style held-out work review rubric for maintainability, local conventions, or merge quality.
- Dataset fields such as `requirements` and `interface` may give more structured task context than the ACUT receives on repository-specific manifests, or less repository history than a context-heavy ACUT expects.
- Local Docker versus Modal can change runtime reliability. The run report must record backend, image tags, timeouts, and infra failures.

## Self-Check

- Benchmark name, snapshot, split, row count, data hash, and evaluator revision are explicit in the YAML.
- The task subset is predeclared by a deterministic algorithm with a fixed salt and no score-aware selection.
- Direct-run versus external-score basis is explicit: direct-run is primary; external scores are only weaker fallback evidence and not valid for the core claim.
- Normalization, denominator policy, replacement rules, and failure handling are fixed before execution.
- The remaining gap is materialization of the concrete instance IDs, which should happen before any ACUT run and be recorded by the coordinator as a locked run artifact.
