Please execute the runbook at:

`/Users/chenmohan/gits/barcarolle/docs/research/agent-tuning-task-generator-evolution-runbook-2026-06-17.md`

Work autonomously and keep going. The goal is to evolve and refactor the Task
Generator until it can produce enough exact certified tasks for both `sphinx`
and `mypy`: at least 80 tasks and at least two corrected rolling-origin windows
per repository, with 100 tasks and three windows preferred.

Do not stop because one hypothesis, repository adapter, verifier profile, or
oracle extraction method fails. Propose hypotheses, implement bounded changes,
run no-paid certification experiments, compare results, keep what works, reject
what does not, and continue. Use the boltons Agent Selection Demo as a success
precedent and use SWE-bench-family primary sources for practical task-generation
ideas.

If task statement generation, statement repair, ambiguity review, leakage
review, or public-context extraction needs LLM experiments, you may spend up to
`$100` total, using only `LLM_BASE_URL` and `LLM_API_KEY`, with sanitized
artifacts and cost accounting. This budget does not authorize paid solver Agent
cells, paid tuner/proposer calls, paid baseline discovery, or before/after
tuning experiments.

Do not stop by merely recommending next steps while executable no-paid or
budgeted LLM experiments remain. Do not ask for human intervention. Before
closeout, refactor the Task Generator so the submitted code keeps the final
effective logic and not the whole experimental pile. Commit focused changes by
package and finish with the closeout artifacts required by the runbook.
