"""Curated LangChain tool registry for each KapexAI specialist."""

from dataclasses import dataclass
from typing import Iterable

from langchain_core.tools import BaseTool

from kapexai.tools.artifact_tools import (
    create_finance_chart,
    create_presentation_from_outline,
    render_mermaid_svg,
    validate_mermaid,
)
from kapexai.tools.consulting import (
    kpi_tree_builder,
    market_size_model,
    raci_validator,
    risk_register,
    scenario_projection,
    weighted_decision_matrix,
)
from kapexai.tools.economics import (
    bls_time_series,
    exchange_rate_series,
    world_bank_country_profile,
    world_bank_indicator,
)
from kapexai.tools.finance_tools import (
    calculate_financial_ratios,
    discounted_cash_flow,
    investment_return_metrics,
    sec_company_facts,
    sec_company_lookup,
    sec_company_submissions,
)
from kapexai.tools.finance_calculators import FINANCE_CALCULATOR_TOOLS
from kapexai.tools.foresight import (
    future_signpost_matrix,
    jpl_horizons_ephemeris,
)
from kapexai.tools.legal_tools import (
    courtlistener_case_search,
    federal_register_search,
    legal_issue_register,
)
from kapexai.tools.research import (
    crossref_research_search,
    gdelt_news_search,
    openalex_research_search,
    wikipedia_search,
)


@dataclass(frozen=True)
class ToolDefinition:
    tool: BaseTool
    agents: tuple[str, ...]
    category: str
    source: str
    free_service: bool = True
    required_env: tuple[str, ...] = ()

    def metadata(self) -> dict:
        return {
            "name": self.tool.name,
            "description": self.tool.description,
            "agents": list(self.agents),
            "category": self.category,
            "source": self.source,
            "free_service": self.free_service,
            "required_env": list(self.required_env),
            "input_schema": self.tool.args_schema.model_json_schema()
            if self.tool.args_schema
            else {},
        }


CORE_DEFINITIONS = (
    ToolDefinition(
        gdelt_news_search,
        ("market_analysis", "economist", "business_strategy", "legal_advisor"),
        "research",
        "GDELT DOC 2.0",
    ),
    ToolDefinition(
        crossref_research_search,
        ("market_analysis", "economist", "business_strategy", "legal_advisor"),
        "research",
        "Crossref REST API",
    ),
    ToolDefinition(
        openalex_research_search,
        ("market_analysis",),
        "research",
        "OpenAlex API",
        required_env=("OPENALEX_API_KEY",),
    ),
    ToolDefinition(
        wikipedia_search,
        ("market_analysis",),
        "research",
        "Wikimedia MediaWiki API",
    ),
    ToolDefinition(
        world_bank_indicator,
        ("market_analysis", "economist", "business_strategy"),
        "economics",
        "World Bank Indicators API",
    ),
    ToolDefinition(
        world_bank_country_profile,
        ("market_analysis", "economist", "legal_advisor"),
        "economics",
        "World Bank Indicators API",
    ),
    ToolDefinition(
        bls_time_series,
        ("market_analysis", "economist", "business_management"),
        "economics",
        "U.S. Bureau of Labor Statistics Public Data API",
    ),
    ToolDefinition(
        exchange_rate_series,
        ("economist", "financial_accounting_asset", "business_strategy"),
        "finance",
        "Frankfurter API",
    ),
    ToolDefinition(
        sec_company_lookup,
        ("market_analysis", "financial_accounting_asset", "legal_advisor"),
        "finance",
        "SEC EDGAR",
        required_env=("SEC_USER_AGENT",),
    ),
    ToolDefinition(
        sec_company_submissions,
        ("market_analysis", "financial_accounting_asset", "legal_advisor"),
        "finance",
        "SEC EDGAR",
        required_env=("SEC_USER_AGENT",),
    ),
    ToolDefinition(
        sec_company_facts,
        ("financial_accounting_asset",),
        "finance",
        "SEC EDGAR XBRL API",
        required_env=("SEC_USER_AGENT",),
    ),
    ToolDefinition(
        calculate_financial_ratios,
        ("financial_accounting_asset", "business_management"),
        "analysis",
        "Local deterministic model",
    ),
    ToolDefinition(
        discounted_cash_flow,
        ("financial_accounting_asset", "business_strategy"),
        "analysis",
        "Local deterministic model",
    ),
    ToolDefinition(
        investment_return_metrics,
        ("financial_accounting_asset",),
        "analysis",
        "Local deterministic model",
    ),
    ToolDefinition(
        market_size_model,
        ("market_analysis", "business_strategy"),
        "analysis",
        "Local deterministic model",
    ),
    ToolDefinition(
        weighted_decision_matrix,
        ("orchestrator", "business_management", "business_strategy"),
        "analysis",
        "Local deterministic model",
    ),
    ToolDefinition(
        scenario_projection,
        ("economist", "business_strategy", "financial_accounting_asset"),
        "analysis",
        "Local deterministic model",
    ),
    ToolDefinition(
        risk_register,
        (
            "orchestrator",
            "business_management",
            "business_strategy",
            "financial_accounting_asset",
        ),
        "analysis",
        "Local deterministic model",
    ),
    ToolDefinition(
        raci_validator,
        ("business_management",),
        "operations",
        "Local deterministic model",
    ),
    ToolDefinition(
        kpi_tree_builder,
        ("business_management",),
        "operations",
        "Local deterministic model",
    ),
    ToolDefinition(
        federal_register_search,
        ("legal_advisor", "economist", "market_analysis"),
        "legal",
        "FederalRegister.gov API",
    ),
    ToolDefinition(
        courtlistener_case_search,
        ("legal_advisor",),
        "legal",
        "CourtListener REST API",
        required_env=("COURTLISTENER_API_TOKEN",),
    ),
    ToolDefinition(
        legal_issue_register,
        ("legal_advisor", "orchestrator"),
        "legal",
        "Local deterministic model",
    ),
    ToolDefinition(
        create_finance_chart,
        ("presentation_designer", "financial_accounting_asset"),
        "artifact",
        "Local Matplotlib renderer",
    ),
    ToolDefinition(
        create_presentation_from_outline,
        ("presentation_designer",),
        "artifact",
        "Local python-pptx renderer",
    ),
    ToolDefinition(
        validate_mermaid,
        ("mermaid_workflow",),
        "artifact",
        "Local Mermaid validation",
    ),
    ToolDefinition(
        render_mermaid_svg,
        ("mermaid_workflow", "presentation_designer"),
        "artifact",
        "Kroki HTTP API",
    ),
    ToolDefinition(
        future_signpost_matrix,
        ("astrologer_future", "economist", "business_strategy"),
        "foresight",
        "Local deterministic model",
    ),
    ToolDefinition(
        jpl_horizons_ephemeris,
        ("astrologer_future",),
        "foresight",
        "NASA JPL Horizons API",
    ),
)

ECONOMIST_CALCULATORS = {
    "apy_calculator",
    "basis_point_calculator",
    "compound_interest_rate_calculator",
    "discount_rate_calculator",
    "ear_calculator",
    "effective_annual_yield_calculator",
    "effective_interest_rate_calculator",
    "equivalent_rate_aer_calculator",
    "real_rate_of_return_calculator",
}

MANAGEMENT_CALCULATORS = {
    "mva_calculator",
    "nopat_calculator",
    "opportunity_cost_calculator",
    "roce_calculator",
    "roi_calculator",
    "ttm_calculator",
    "week_over_week_calculator",
}

MARKET_CALCULATORS = {
    "annualized_rate_of_return_calculator",
    "appreciation_calculator",
    "cagr_calculator",
    "capital_gains_yield_calculator",
    "holding_period_return_calculator",
    "maximum_drawdown_calculator",
    "moving_average_calculator",
    "percentage_return_calculator",
    "rate_of_return_calculator",
    "value_at_risk_calculator",
}

STRATEGY_CALCULATORS = {
    "dcf_calculator",
    "discount_rate_calculator",
    "expected_return_calculator",
    "expected_utility_calculator",
    "irr_calculator",
    "mirr_calculator",
    "mva_calculator",
    "nopat_calculator",
    "npv_calculator",
    "opportunity_cost_calculator",
    "perpetuity_calculator",
    "present_value_calculator",
    "roce_calculator",
    "roi_calculator",
}


def _calculator_agents(tool_name: str) -> tuple[str, ...]:
    agents = ["financial_accounting_asset"]
    if tool_name in ECONOMIST_CALCULATORS:
        agents.append("economist")
    if tool_name in MANAGEMENT_CALCULATORS:
        agents.append("business_management")
    if tool_name in MARKET_CALCULATORS:
        agents.append("market_analysis")
    if tool_name in STRATEGY_CALCULATORS:
        agents.append("business_strategy")
    return tuple(agents)


CALCULATOR_DEFINITIONS = tuple(
    ToolDefinition(
        calculator,
        _calculator_agents(calculator.name),
        "finance_calculator",
        "Local deterministic standard finance formula",
    )
    for calculator in FINANCE_CALCULATOR_TOOLS
)

DEFINITIONS = (*CORE_DEFINITIONS, *CALCULATOR_DEFINITIONS)

TOOL_REGISTRY = {definition.tool.name: definition for definition in DEFINITIONS}


def get_tool_definitions_for_agent(agent_key: str) -> list[ToolDefinition]:
    return [
        definition
        for definition in DEFINITIONS
        if agent_key in definition.agents
    ]


def get_tools_for_agent(agent_key: str) -> list[BaseTool]:
    return [
        definition.tool
        for definition in get_tool_definitions_for_agent(agent_key)
    ]


def list_tool_metadata(agent_key: str | None = None) -> list[dict]:
    definitions: Iterable[ToolDefinition] = (
        get_tool_definitions_for_agent(agent_key)
        if agent_key
        else DEFINITIONS
    )
    return [definition.metadata() for definition in definitions]


def get_tool(name: str) -> BaseTool:
    try:
        return TOOL_REGISTRY[name].tool
    except KeyError as exc:
        raise KeyError(f"Unknown tool: {name}") from exc
