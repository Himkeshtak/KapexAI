"""Agent definitions and orchestration."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConsultationRequest(BaseModel):
    company: str
    goal: str
    context: Dict[str, Any] = Field(default_factory=dict)


class Agent:
    def __init__(self, name: str):
        self.name = name

    def run(self, request: ConsultationRequest) -> Dict[str, Any]:
        recommendation = (
            f"For {request.company} aiming to {request.goal}, {self.name} suggests: "
            "conduct targeted analysis and produce a prioritized action list."
        )
        return {"agent": self.name, "recommendation": recommendation}


class AgentManager:
    def __init__(self, agents: Optional[List[Agent]] = None):
        self.agents = agents or [
            Agent("MarketAnalysis"),
            Agent("FinancialModeling"),
            Agent("Strategy"),
            Agent("Compliance"),
        ]

    def consult(self, request: ConsultationRequest) -> Dict[str, Any]:
        details = [agent.run(request) for agent in self.agents]
        summary = "\n".join(
            f"- {item['agent']}: {item['recommendation']}" for item in details
        )
        return {"summary": summary, "details": details}
