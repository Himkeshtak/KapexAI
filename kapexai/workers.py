"""Specialist agent definitions and orchestration for KapexAI."""

import json
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from pydantic import BaseModel, Field

from kapexai.prompts import AGENT_PROMPTS


class ConsultationRequest(BaseModel):
    """A consulting engagement submitted to the agent team."""

    company: str
    goal: str
    context: Dict[str, Any] = Field(default_factory=dict)
    requested_agents: List[str] = Field(default_factory=list)


class Agent:
    """Base definition for a specialist that can receive scoped work."""

    key = "general"
    name = "General Consulting Agent"
    role = "General business analysis"
    system_prompt = ""
    capabilities: Sequence[str] = ()
    deliverables: Sequence[str] = ()
    dependencies: Sequence[str] = ()
    assignment_scope = "Analyze the decision through this specialist lens."

    def __init__(self, name: Optional[str] = None):
        # Preserve compatibility with the original Agent("Name") interface.
        if name:
            self.name = name
            self.key = _slugify(name)

    def build_prompt(
        self,
        request: ConsultationRequest,
        assignment: Optional[str] = None,
        upstream_outputs: Optional[Mapping[str, Any]] = None,
    ) -> str:
        """Build the complete prompt sent to this specialist."""
        context = json.dumps(request.context, indent=2, default=str, sort_keys=True)
        upstream = (
            json.dumps(upstream_outputs, indent=2, default=str, sort_keys=True)
            if upstream_outputs
            else "No upstream outputs have been supplied."
        )
        task = assignment or self.default_assignment(request)
        tool_descriptions = "\n".join(
            f"- {tool.name}: {tool.description}"
            for tool in self.get_tools()
        ) or "- No executable tools are configured for this specialist."
        prompt = self.system_prompt or (
            "You are a business specialist. Analyze only the assignment within "
            "your stated role and make assumptions explicit."
        )
        return (
            f"{prompt}\n\n"
            "ENGAGEMENT BRIEF\n"
            f"Company or subject: {request.company}\n"
            f"Primary goal: {request.goal}\n"
            f"Your scoped assignment: {task}\n"
            f"Context supplied by the user:\n{context}\n\n"
            f"UPSTREAM SPECIALIST OUTPUTS\n{upstream}\n\n"
            f"AVAILABLE TOOLS\n{tool_descriptions}\n\n"
            "TOOL USE PROTOCOL\n"
            "- Use tools when current facts, calculations, or artifacts are needed.\n"
            "- Treat tool results as evidence, preserve their source, date, and caveats.\n"
            "- Never invent a successful result when a service or credential is unavailable.\n"
            "- Cross-check high-impact claims when more than one source is available.\n\n"
            "Complete the assignment using your required output structure. "
            "Do not answer outside your mandate; instead name the specialist "
            "whose input is required."
        )

    def default_assignment(self, request: ConsultationRequest) -> str:
        return (
            f"For {request.company}, evaluate '{request.goal}'. "
            f"{self.assignment_scope}"
        )

    def run(
        self,
        request: ConsultationRequest,
        assignment: Optional[str] = None,
        upstream_outputs: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return a work order until an LLM execution adapter is configured."""
        scoped_assignment = assignment or self.default_assignment(request)
        result: Dict[str, Any] = {
            "agent": self.name,
            "key": self.key,
            "role": self.role,
            "status": "planned",
            "assignment": scoped_assignment,
            "capabilities": list(self.capabilities),
            "deliverables": list(self.deliverables),
            "dependencies": list(self.dependencies),
            "tools": self.tool_names(),
            "recommendation": (
                f"{self.name} is assigned to {scoped_assignment} "
                "and is ready for LLM-backed execution."
            ),
        }
        if request.context.get("include_agent_prompts"):
            result["prompt"] = self.build_prompt(
                request,
                scoped_assignment,
                upstream_outputs,
            )
        return result

    def metadata(self, include_prompt: bool = False) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            "key": self.key,
            "name": self.name,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "deliverables": list(self.deliverables),
            "dependencies": list(self.dependencies),
            "tools": self.tool_names(),
        }
        if include_prompt:
            metadata["system_prompt"] = self.system_prompt
        return metadata

    def get_tools(self) -> list[Any]:
        """Return this specialist's curated LangChain BaseTool objects."""
        from kapexai.tools.registry import get_tools_for_agent

        return get_tools_for_agent(self.key)

    def tool_names(self) -> List[str]:
        return [tool.name for tool in self.get_tools()]


class OrchestratorAgent(Agent):
    key = "orchestrator"
    name = "Orchestrator Agent"
    role = "Engagement decomposition, routing, coordination, and synthesis"
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "problem framing",
        "agent routing",
        "dependency planning",
        "quality control",
        "conflict resolution",
        "executive synthesis",
    )
    deliverables = (
        "engagement brief",
        "agent routing plan",
        "execution waves",
        "quality gates",
        "synthesis plan",
    )

    def create_plan(
        self,
        request: ConsultationRequest,
        available_agents: Mapping[str, Agent],
    ) -> Dict[str, Any]:
        selected_keys = self._select_agents(request, available_agents)
        assignments = [
            {
                "agent": available_agents[key].name,
                "key": key,
                "assignment": available_agents[key].default_assignment(request),
                "dependencies": [
                    dependency
                    for dependency in available_agents[key].dependencies
                    if dependency in selected_keys
                ],
            }
            for key in selected_keys
        ]
        waves = _execution_waves(selected_keys, available_agents)
        return {
            "orchestrator": self.name,
            "decision_statement": (
                f"Determine how {request.company} should achieve: {request.goal}"
            ),
            "selected_agents": selected_keys,
            "assignments": assignments,
            "execution_waves": waves,
            "quality_gates": [
                "Facts, assumptions, forecasts, and recommendations are labeled.",
                "Material claims have evidence or are marked as evidence gaps.",
                "Financial and legal caveats survive final synthesis.",
                "Conflicting specialist conclusions are surfaced and reconciled.",
                "Presentation and diagram agents use approved findings only.",
                "Astrological material remains optional and non-evidentiary.",
            ],
        }

    def _select_agents(
        self,
        request: ConsultationRequest,
        available_agents: Mapping[str, Agent],
    ) -> List[str]:
        explicit = request.requested_agents or _as_string_list(
            request.context.get("requested_agents")
        )
        include_all = bool(request.context.get("include_all_agents"))

        if include_all or any(_slugify(item) == "all" for item in explicit):
            return list(available_agents)

        if explicit:
            selected = []
            for requested in explicit:
                key = resolve_agent_key(requested)
                if key in available_agents and key not in selected:
                    selected.append(key)
            return selected

        text = " ".join(
            [
                request.company,
                request.goal,
                json.dumps(request.context, default=str),
            ]
        ).lower()
        selected = list(CORE_AGENT_KEYS)
        for key, keywords in ROUTING_KEYWORDS.items():
            if any(keyword in text for keyword in keywords) and key not in selected:
                selected.append(key)
        return [key for key in selected if key in available_agents]


class MarketAnalysisAgent(Agent):
    key = "market_analysis"
    name = "Market Analysis Agent"
    role = "Market sizing, customer insight, competition, pricing, and channels"
    assignment_scope = (
        "Define the addressable market, customer segments, demand, competitors, "
        "pricing, channels, and evidence needed to validate market attractiveness."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "TAM/SAM/SOM sizing",
        "customer segmentation",
        "competitive intelligence",
        "pricing analysis",
        "channel analysis",
        "market-entry validation",
    )
    deliverables = (
        "market definition",
        "market sizing model",
        "segment attractiveness",
        "competitive landscape",
        "go-to-market implications",
    )


class BusinessManagementConsultantAgent(Agent):
    key = "business_management"
    name = "Business Management Consultant Agent"
    role = "Operating model, organization, process, governance, and transformation"
    assignment_scope = (
        "Diagnose execution constraints and design the operating model, processes, "
        "governance, capabilities, KPIs, and change roadmap required to deliver it."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "operating-model diagnosis",
        "process redesign",
        "organization design",
        "governance and RACI",
        "KPI systems",
        "change management",
    )
    deliverables = (
        "management diagnosis",
        "target operating model",
        "process and governance design",
        "KPI tree",
        "transformation roadmap",
    )
    dependencies = ("market_analysis", "financial_accounting_asset")


class EconomistAgent(Agent):
    key = "economist"
    name = "Economist Agent"
    role = "Macroeconomics, policy, industry cycles, and economic scenarios"
    assignment_scope = (
        "Assess the economic regime, transmission channels, three scenarios, "
        "business impacts, leading indicators, and decision triggers."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "economic regime analysis",
        "policy transmission",
        "interest-rate and inflation analysis",
        "currency and commodity exposure",
        "economic scenario planning",
        "leading-indicator design",
    )
    deliverables = (
        "economic outlook",
        "scenario assumptions",
        "transmission-channel analysis",
        "business impact assessment",
        "monitoring indicators",
    )


class BusinessStrategistPlannerAgent(Agent):
    key = "business_strategy"
    name = "Business Strategist and Planner Agent"
    role = "Strategic choices, competitive advantage, portfolio, and execution"
    assignment_scope = (
        "Develop distinct strategic choices, evaluate their value and feasibility, "
        "recommend where to play and how to win, and build an execution roadmap."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "strategic diagnosis",
        "option generation",
        "competitive advantage assessment",
        "portfolio strategy",
        "resource allocation",
        "roadmaps and OKRs",
    )
    deliverables = (
        "strategic options",
        "option evaluation",
        "recommended strategic choices",
        "initiative portfolio",
        "execution roadmap",
    )
    dependencies = (
        "market_analysis",
        "business_management",
        "economist",
        "financial_accounting_asset",
        "legal_advisor",
    )


class AstrologerFuturePredictorAgent(Agent):
    key = "astrologer_future"
    name = "Astrologer and Future Predictor Agent"
    role = "Evidence-based foresight plus optional non-scientific symbolic reflection"
    assignment_scope = (
        "Develop plausible evidence-based futures and signposts; include symbolic "
        "astrology only when requested and label it as non-scientific reflection."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "scenario foresight",
        "weak-signal analysis",
        "future signposts",
        "uncertainty mapping",
        "optional symbolic astrology",
    )
    deliverables = (
        "plausible future scenarios",
        "observable signposts",
        "optional symbolic interpretation",
        "limitations and prohibited uses",
    )


class FinancialAccountingAssetManagementAgent(Agent):
    key = "financial_accounting_asset"
    name = "Financial, Accounting, and Asset Management Agent"
    role = "Financial analysis, accounting, valuation, treasury, and asset risk"
    assignment_scope = (
        "Analyze financial quality, forecasts, cash, leverage, valuation, capital "
        "allocation, accounting implications, and risk-adjusted asset decisions."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "financial statement analysis",
        "forecasting and scenarios",
        "valuation",
        "capital allocation",
        "liquidity and leverage analysis",
        "portfolio risk analysis",
    )
    deliverables = (
        "quality-of-earnings assessment",
        "three-scenario financial model",
        "cash and leverage assessment",
        "valuation range",
        "capital-allocation implications",
    )


class LegalAdvisorAgent(Agent):
    key = "legal_advisor"
    name = "Legal Advisor Agent"
    role = "Legal issue spotting, regulation, contracts, governance, and compliance"
    assignment_scope = (
        "Identify jurisdictions, legal issues, regulatory and contract exposure, "
        "risk controls, required actions, and matters for licensed counsel."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "jurisdictional issue spotting",
        "regulatory research",
        "contract risk review",
        "compliance planning",
        "governance analysis",
        "legal risk registers",
    )
    deliverables = (
        "legal issue tree",
        "source-status summary",
        "legal risk matrix",
        "compliance actions",
        "counsel escalation brief",
    )


class PresentationDesignerAgent(Agent):
    key = "presentation_designer"
    name = "Presentation and Designer Agent"
    role = "Executive storytelling, information design, and PowerPoint production"
    assignment_scope = (
        "Convert approved findings into an executive narrative, slide storyboard, "
        "chart specifications, design system, and PowerPoint build manifest."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "executive storytelling",
        "slide architecture",
        "financial visualization",
        "PowerPoint build manifests",
        "design systems",
        "presentation quality assurance",
    )
    deliverables = (
        "narrative strategy",
        "slide storyboard",
        "chart specifications",
        "design system",
        "PowerPoint build manifest",
    )
    dependencies = (
        "market_analysis",
        "business_management",
        "economist",
        "business_strategy",
        "financial_accounting_asset",
        "legal_advisor",
    )


class MermaidWorkflowAgent(Agent):
    key = "mermaid_workflow"
    name = "Mermaid Diagram and Workflow Agent"
    role = "Workflow architecture, process mapping, and Mermaid diagram code"
    assignment_scope = (
        "Normalize the approved process or system and produce valid Mermaid code, "
        "a walkthrough, unresolved transitions, and a validation checklist."
    )
    system_prompt = AGENT_PROMPTS[key]
    capabilities = (
        "workflow normalization",
        "process mapping",
        "system diagrams",
        "dependency visualization",
        "Mermaid syntax generation",
        "diagram validation",
    )
    deliverables = (
        "diagram specification",
        "Mermaid code",
        "plain-language walkthrough",
        "node and edge inventory",
        "validation checklist",
    )
    dependencies = ("business_management", "business_strategy")


SPECIALIST_AGENT_CLASSES = (
    MarketAnalysisAgent,
    BusinessManagementConsultantAgent,
    EconomistAgent,
    BusinessStrategistPlannerAgent,
    AstrologerFuturePredictorAgent,
    FinancialAccountingAssetManagementAgent,
    LegalAdvisorAgent,
    PresentationDesignerAgent,
    MermaidWorkflowAgent,
)

CORE_AGENT_KEYS = (
    "market_analysis",
    "business_management",
    "economist",
    "business_strategy",
    "financial_accounting_asset",
    "legal_advisor",
)

ROUTING_KEYWORDS: Dict[str, Sequence[str]] = {
    "astrologer_future": (
        "astrolog",
        "horoscope",
        "zodiac",
        "birth chart",
        "symbolic forecast",
    ),
    "presentation_designer": (
        "presentation",
        "powerpoint",
        "ppt",
        "slide deck",
        "slides",
    ),
    "mermaid_workflow": (
        "mermaid",
        "diagram",
        "workflow",
        "flowchart",
        "process map",
    ),
}

AGENT_ALIASES = {
    "orchestrator_agent": "orchestrator",
    "market": "market_analysis",
    "market_analysis_agent": "market_analysis",
    "business_consultant": "business_management",
    "business_management_consultant": "business_management",
    "business_management_consultant_agent": "business_management",
    "economist_agent": "economist",
    "strategist": "business_strategy",
    "business_strategist": "business_strategy",
    "business_strategist_and_planner_agent": "business_strategy",
    "astrologer": "astrologer_future",
    "future_predictor": "astrologer_future",
    "astrologer_and_future_predictor_agent": "astrologer_future",
    "finance": "financial_accounting_asset",
    "financial_agent": "financial_accounting_asset",
    "financial_accounting_and_asset_management_agent": (
        "financial_accounting_asset"
    ),
    "legal": "legal_advisor",
    "legal_advisor_agent": "legal_advisor",
    "presentation": "presentation_designer",
    "presentation_and_designer_agent": "presentation_designer",
    "ppt": "presentation_designer",
    "mermaid": "mermaid_workflow",
    "workflow": "mermaid_workflow",
    "mermaid_diagram_and_workflow_agent": "mermaid_workflow",
}


class AgentManager:
    """Own the specialist registry and produce orchestrated work plans."""

    def __init__(
        self,
        agents: Optional[Iterable[Agent]] = None,
        orchestrator: Optional[OrchestratorAgent] = None,
    ):
        specialist_agents = (
            list(agents)
            if agents is not None
            else [agent_class() for agent_class in SPECIALIST_AGENT_CLASSES]
        )
        self.orchestrator = orchestrator or OrchestratorAgent()
        self.agents: Dict[str, Agent] = {
            agent.key: agent for agent in specialist_agents
        }

    def consult(self, request: ConsultationRequest) -> Dict[str, Any]:
        plan = self.orchestrator.create_plan(request, self.agents)
        assignment_map = {
            assignment["key"]: assignment["assignment"]
            for assignment in plan["assignments"]
        }
        details = [
            self.agents[key].run(request, assignment_map[key])
            for key in plan["selected_agents"]
        ]
        summary = "\n".join(
            f"- {item['agent']}: {item['assignment']}" for item in details
        )
        return {
            "summary": summary,
            "status": "planned",
            "orchestration": plan,
            "details": details,
        }

    def list_agents(self, include_prompts: bool = False) -> List[Dict[str, Any]]:
        agents = [self.orchestrator, *self.agents.values()]
        return [agent.metadata(include_prompt=include_prompts) for agent in agents]

    def get_agent(self, name_or_key: str) -> Agent:
        key = resolve_agent_key(name_or_key)
        if key == self.orchestrator.key:
            return self.orchestrator
        try:
            return self.agents[key]
        except KeyError as exc:
            raise KeyError(f"Unknown agent: {name_or_key}") from exc

    def workflow_mermaid(self) -> str:
        lines = [
            "flowchart LR",
            '    USER["Client request"] --> ORCH["Orchestrator Agent"]',
            '    subgraph ANALYSIS["Specialist analysis"]',
        ]
        for key in CORE_AGENT_KEYS:
            agent = self.agents[key]
            lines.append(f'        {key}["{agent.name}"]')
        lines.append("    end")
        lines.extend(
            f"    ORCH --> {key}" for key in CORE_AGENT_KEYS
        )
        lines.extend(
            [
                "    market_analysis --> business_management",
                "    financial_accounting_asset --> business_management",
                "    market_analysis --> business_strategy",
                "    business_management --> business_strategy",
                "    economist --> business_strategy",
                "    financial_accounting_asset --> business_strategy",
                "    legal_advisor --> business_strategy",
                '    business_strategy --> PPT["Presentation and Designer Agent"]',
                '    business_strategy --> FLOW["Mermaid Diagram and Workflow Agent"]',
                '    ORCH -. optional .-> ASTRO["Astrologer and Future Predictor Agent"]',
                "    PPT --> ORCH",
                "    FLOW --> ORCH",
                "    ASTRO -. non-evidentiary appendix .-> ORCH",
                '    ORCH --> RESULT["Reviewed final deliverables"]',
            ]
        )
        return "\n".join(lines)


def resolve_agent_key(name_or_key: str) -> str:
    normalized = _slugify(name_or_key)
    if normalized in AGENT_PROMPTS:
        return normalized
    return AGENT_ALIASES.get(normalized, normalized)


def _execution_waves(
    selected_keys: Sequence[str],
    available_agents: Mapping[str, Agent],
) -> List[Dict[str, Any]]:
    remaining = list(selected_keys)
    completed: set[str] = set()
    waves: List[Dict[str, Any]] = []
    while remaining:
        ready = [
            key
            for key in remaining
            if all(
                dependency not in selected_keys or dependency in completed
                for dependency in available_agents[key].dependencies
            )
        ]
        if not ready:
            # Preserve progress if a custom registry introduces a dependency cycle.
            ready = [remaining[0]]
        waves.append(
            {
                "wave": len(waves) + 1,
                "agents": ready,
                "parallel": len(ready) > 1,
            }
        )
        completed.update(ready)
        remaining = [key for key in remaining if key not in completed]
    return waves


def _as_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _slugify(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.lower())).strip(
        "_"
    )


__all__ = [
    "Agent",
    "AgentManager",
    "AstrologerFuturePredictorAgent",
    "BusinessManagementConsultantAgent",
    "BusinessStrategistPlannerAgent",
    "ConsultationRequest",
    "EconomistAgent",
    "FinancialAccountingAssetManagementAgent",
    "LegalAdvisorAgent",
    "MarketAnalysisAgent",
    "MermaidWorkflowAgent",
    "OrchestratorAgent",
    "PresentationDesignerAgent",
    "resolve_agent_key",
]
