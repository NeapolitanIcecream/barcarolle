# Repository-Local Rich-W20 Protocol Readiness

Status: `preregistered_reduced_protocol_primary_not_run`
Protocol: `repository-local-rich-w20-v1`

## Boundary

The 0514 frozen protocol remains terminally blocked before primary runs. This artifact preregisters a reduced-scale Rich-W20 decision-validity pilot; it does not claim to satisfy the original 5-reserve or 40-candidate-pool gates.

## Denominators

- W*: `20` primary tasks; reserve required: `false`.
- R: `20` primary tasks; `5` accepted reserve tasks retained.
- ACUTs: A0 generic, A1 inert, A3 repository-calibrated, A4 localization.

## Pre-Primary Checks

- No-op fails all primary tasks: `true`
- Reference passes all primary tasks: `true`
- Hidden verifier digest recorded: `true`
- Public statement digest recorded: `true`
- Leakage reviewed: `true`

## Current Blockers

- Primary ACUT attempts are still not run in this artifact.
- A reduced-protocol owner start decision and live API/cost preflight must be recorded before primary attempts.

## Privacy

The readiness JSON records digests and private artifact roots only. Raw commits, raw subjects, reference patch bodies, and hidden verifier files remain outside committed public artifacts.
