## Repair discipline
- Preserve the public contract first: confirm return shapes, mutation effects, and exception text behavior before changing implementation details.
- Treat incomplete or irregular inputs as expected cases when the surrounding API already accepts them; prefer robust parsing over assuming a fully populated structure.
- Keep field boundaries and state transitions explicit so one missing piece of data does not shift or corrupt the rest of the result.
- Make the smallest change that restores the intended behavior, and re-check that existing success cases still behave the same.
