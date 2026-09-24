# Noor Automation Orchestra

## Purpose

Noor combines heterogeneous open-source capabilities behind one control plane. External repositories are **providers**, not independent agents with authority.

## Unified responsibility model

```text
User request
    |
    v
Noor Mind / Planner
    |
    v
Automation Orchestra
    |
    +--> capability selection
    +--> dependency ordering
    +--> policy / permissions
    +--> provider selection
    +--> execution
    +--> verification
    +--> evidence / artifacts
    |
    v
Final result
```

## Provider responsibilities

| Provider | Primary responsibility |
|---|---|
| RATH | EDA and visualization patterns |
| YData Profiling | Dataset profiling |
| Data Quality Gate | Data validation and quality gates |
| WrenAI | Semantic text-to-SQL |
| Text-to-SQL Agent | Guarded SQL execution patterns |
| Text2SQL Agent | SQL self-correction |
| SQL Query Engine | SQL generation and repair |
| SmolSQLAgents | Database schema/relationship discovery |
| Excel Automation | Workbook manipulation |
| Excel Native Automation | Native Windows Excel operations |
| ExcelTurboLLM | Formula intelligence patterns |
| Power BI MCP Automation | Power BI automation patterns |
| Power BI MCP Local | Local Power BI tooling patterns |
| Power BI Cleaning Automation | Power BI preparation patterns |
| Debug Agent | Evidence-driven debugging |
| Autonomous Coding Agent | Coding-agent patterns |

## Authority model

Providers do **not** own planning or permissions. Noor owns:

1. intent and planning
2. task selection
3. provider selection
4. dependency ordering
5. permission boundaries
6. execution contracts
7. verification
8. evidence collection
9. final response

This avoids creating a collection of competing autonomous agents. The repositories become specialized capability providers under one unified mind.

## Integration modes

- `library`: reusable implementation may be imported after license/security review.
- `adapter`: Noor exposes a stable interface around the external implementation.
- `pattern`: architecture or algorithms are studied and reimplemented rather than copied.

No external repository is automatically trusted or merged into Noor.

## Example

A request such as:

> Analyze this Excel sales file and explain the major business trends.

can eventually become:

```text
excel.read
  -> data.profile
  -> data.validate
  -> data.clean [only when required]
  -> data.analyze
  -> data.visualize
  -> insight.summarize
  -> result.verify
```

Each step has one responsibility, while the Orchestra maintains the shared execution context and passes verified outputs between steps.
