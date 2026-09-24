"""Capability federation manifest.

External projects are treated as capability providers. Noor owns the contract,
policy, orchestration, and verification; providers supply implementations or
patterns only after review.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityProvider:
    name: str
    repository: str
    capabilities: tuple[str, ...]
    role: str
    integration_mode: str = "adapter"


PROVIDERS: tuple[CapabilityProvider, ...] = (
    CapabilityProvider("RATH", "Kanaries/RATH", ("data.explore", "data.visualize"), "EDA and visualization provider", "adapter"),
    CapabilityProvider("YData Profiling", "ydataai/ydata-profiling", ("data.profile",), "data profiling provider", "library"),
    CapabilityProvider("Data Quality Gate", "provectus/data-quality-gate", ("data.validate", "data.quality"), "data quality provider", "pattern"),
    CapabilityProvider("WrenAI", "Canner/WrenAI", ("sql.generate", "sql.explain"), "semantic text-to-SQL provider", "adapter"),
    CapabilityProvider("Text-to-SQL Agent", "Mani9333/text-to-sql-agent", ("sql.validate", "sql.execute"), "guarded SQL provider", "pattern"),
    CapabilityProvider("Text2SQL Agent", "Sakeeb91/text2sql-agent", ("sql.repair", "sql.self_correct"), "SQL self-correction provider", "pattern"),
    CapabilityProvider("SQL Query Engine", "codeadeel/sqlqueryengine", ("sql.generate", "sql.repair"), "SQL generation and repair provider", "adapter"),
    CapabilityProvider("SmolSQLAgents", "montraydavis/SmolSQLAgents", ("sql.schema.inspect", "sql.relationships"), "database discovery provider", "pattern"),
    CapabilityProvider("Excel Automation", "god233012yamil/Excel-Automation-Using-Python", ("excel.read", "excel.write", "excel.format"), "workbook automation provider", "library"),
    CapabilityProvider("Excel Native Automation", "trenton3983/Excel_Automation_with_Python", ("excel.native", "excel.pivot"), "Windows Excel automation provider", "adapter"),
    CapabilityProvider("ExcelTurboLLM", "SHRUTI-SHAR/ExcelTurboLLM", ("excel.formula.generate", "excel.formula.explain"), "Excel formula intelligence provider", "pattern"),
    CapabilityProvider("Power BI MCP Automation", "Yugandhar2807/powerbi-mcp-automation", ("powerbi.inspect", "powerbi.automate"), "Power BI tool provider", "adapter"),
    CapabilityProvider("Power BI MCP Local", "inerthel-agi/powerbi-mcp-local", ("powerbi.query", "powerbi.metadata"), "local Power BI tool provider", "adapter"),
    CapabilityProvider("Power BI Cleaning Automation", "ayaan-23/powerbi-data-cleaning-automation", ("powerbi.clean", "powerbi.transform"), "Power BI preparation provider", "pattern"),
    CapabilityProvider("Debug Agent", "millionco/debug-agent", ("code.debug", "code.reproduce", "code.verify"), "evidence-driven debugging provider", "pattern"),
    CapabilityProvider("Autonomous Coding Agent", "talalnafees-ai/Autonomous-Coding-Agent", ("code.implement", "code.test"), "coding agent reference", "pattern"),
)


def providers_for(capability: str) -> tuple[CapabilityProvider, ...]:
    return tuple(provider for provider in PROVIDERS if capability in provider.capabilities)
