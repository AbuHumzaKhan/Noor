# Noor Automation Engine

## Objective

Provide one controlled runtime that can turn a user command into a sequence of
validated, observable tasks. Data profiling and analysis are first-class task
categories, but the engine is intentionally generic so coding, quality checks,
report generation, file operations, and other capabilities can be added without
rewriting the runner.

## Architecture

```text
User command
    |
    v
Request normalization
    |
    v
Planner / task selection
    |
    v
Policy + capability checks
    |
    v
TaskRegistry ----> approved task handler
    |
    v
AutomationRunner
    |
    +--> trace / timings / errors
    +--> structured outputs
    |
    v
Verifier / report / next action
```

## Initial task contract

`data.profile` accepts a local CSV, Excel, or Parquet path and returns:

- row and column counts
- duplicate-row count
- memory usage
- per-column data type
- missing count and percentage
- unique-value count
- constant-column detection

The output is JSON-serializable so downstream automation stages can consume it.

## Planned task families

1. **Data ingestion** — CSV, Excel, Parquet, JSON, database/query sources.
2. **Data profiling** — schema, distributions, cardinality, missingness,
   duplicates, outliers, and drift.
3. **Data quality** — validation rules, anomaly detection, reconciliation,
   and quality scoring.
4. **Data cleaning** — explicit, auditable transformations with before/after
   metrics.
5. **Analysis** — descriptive statistics, segmentation, correlations,
   trends, cohort analysis, and business KPIs.
6. **Visualization** — chart specifications and rendered artifacts.
7. **Reporting** — executive summary, analytical report, and machine-readable
   evidence package.
8. **Coding** — inspect, modify, test, lint, and explain code through approved
   tools.
9. **Verification** — test outputs, validate assumptions, and surface
   uncertainty rather than silently guessing.
10. **Automation** — reusable multi-step workflows and scheduled jobs.

## Design constraints

- Tasks are explicitly registered; arbitrary Python execution is not exposed
  through the registry.
- Each task receives a dictionary context and returns structured output.
- Failures are captured in the result and trace instead of being swallowed.
- Dry-run mode is available before side effects are introduced.
- Analytics dependencies remain optional for the core runtime.
- Future planners must produce an inspectable task plan before execution.

## Next implementation stages

### Phase 1 — Foundation

- task registry
- request/result models
- runner and trace
- first profiling task
- unit tests

### Phase 2 — Data intelligence

- ingestion abstraction
- data-quality engine
- cleaning engine
- statistical analysis tasks
- visualization specifications

### Phase 3 — Autonomous planning

- intent classification
- plan generation
- dependency-aware task graph
- policy and permission gates
- verifier loop

### Phase 4 — Production automation

- persistent job state
- artifact storage
- scheduled execution
- retry/idempotency rules
- observability
- CI/CD and release automation
