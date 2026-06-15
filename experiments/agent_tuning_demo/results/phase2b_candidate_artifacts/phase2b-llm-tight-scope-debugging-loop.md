## When a repair is unstable
- Work from the smallest reproducible input and verify each transformation step in isolation before broadening the fix.
- If progress stalls, reduce the change surface instead of widening it; prefer a local correction over a redesign.
- Re-run the targeted checks after each meaningful adjustment so regressions are caught while the context is still fresh.
- Keep the fix aligned with the observed failure mode, not with incidental implementation details that may vary across similar cases.
