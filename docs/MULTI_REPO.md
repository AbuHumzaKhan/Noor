# Multi-Repository Integration Strategy

## Goal
Allow Noor to gain capabilities from multiple open-source repositories without turning the codebase into an uncontrolled collection of copied projects.

## Integration record
Each candidate repository should be represented by:

- repository URL
- owner/name
- license
- capability summary
- supported platforms
- dependency footprint
- security considerations
- adapter status
- tests
- pinned version/commit when required

## Integration levels

### L0 — Discovered
Repository identified as potentially useful.

### L1 — Evaluated
License, maintenance, dependencies and architecture reviewed.

### L2 — Adapted
Noor adapter or isolated component created.

### L3 — Verified
Real Noor workflow tested successfully.

### L4 — Production capability
Monitoring, failure handling, documentation and rollback are in place.

No repository should be considered a Noor capability solely because its source code has been discovered.
