## Barcarolle Agent Tuning Demo Appendix

For mypy benchmark tasks in module families core_or_other, semantic_analysis, type_checker, first identify whether the failure is semantic-analysis,
incremental-cache, or type-checker behavior. Keep the patch inside the declared implementation paths, preserve public APIs,
and avoid touching generated files, tests, or test-data fixtures. If the first hypothesis is uncertain, inspect the smallest
neighboring implementation and test-data examples before editing, then run the targeted check command.
