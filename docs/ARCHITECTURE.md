# Noor Architecture

## System layers

```text
User
  ↓
Interface / Chat / Orb
  ↓
Request Intake
  ↓
Mind / Requirement Understanding
  ↓
Discovery
  ↓
Planner
  ↓
Selector
  ↓
Permissions / Policy
  ↓
Executor
  ↓
Verifier
  ↓
Memory / Audit / Response
```

## Multi-repository capability model

External open-source repositories are treated as capability sources, not blindly copied into Noor. Each integration must have:

1. Source metadata
2. License review
3. Capability description
4. Adapter boundary
5. Dependency assessment
6. Security review
7. Tests
8. Version pinning where appropriate
9. Rollback path

## Core subsystems

- `mind`: requirement understanding and planning context
- `discovery`: capability and repository discovery
- `selector`: tool/skill selection
- `permissions`: risk and approval policy
- `executor`: controlled action execution
- `verifier`: post-action validation
- `memory`: durable, user-approved context
- `skills`: reusable domain capabilities
- `tools`: concrete executable operations
- `integrations`: adapters for external systems
- `ui`: interactive Noor experience
- `tests`: unit, integration and end-to-end validation

## Autonomy boundary

Noor can become increasingly autonomous through verified workflows, but autonomy is constrained by explicit policies, permissions, observability, and verification. Self-modifying behavior must not bypass those controls.
