# Noor V1 — Excel Orchestra

## Unified Mind

Noor owns planning, provider selection, dependency management, execution policy, retries, verification, and final response. External repositories are capability providers, not independent agents.

## V1 Excel responsibilities

| Capability | Responsibility |
|---|---|
| `excel.inspect` | Inspect workbook structure and sheets |
| `data.profile` | Profile tabular data |
| `result.verify` | Verify structural correctness of outputs |

## Execution contract

```text
Natural language request
        ↓
Planner
        ↓
TaskGraph
        ↓
Provider selection
        ↓
Dependency-aware execution
        ↓
Retry on provider failure
        ↓
Verification
        ↓
Final response
```

## Provider rule

A provider must expose a stable Noor capability. Providers do not decide the overall workflow. Noor decides which provider is responsible for each task.

## V1 scope

V1 intentionally starts with deterministic Excel inspection and data profiling. Formula generation, workbook mutation, charts, formatting, Power Query/M, and advanced Excel reasoning can be added as separate capabilities after the execution contract is proven.
