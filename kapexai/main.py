"""FastAPI application for KapexAI."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kapexai.env_loader import load_environment
from kapexai.workers import AgentManager, ConsultationRequest
from kapexai.tools.registry import list_tool_metadata


load_environment()
app = FastAPI(title="KapexAI Consulting API")

frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "KAPEXAI_FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "KapexAI Consulting API",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/consult")
async def consult(payload: dict):
    try:
        request = ConsultationRequest(**payload)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    return JSONResponse(AgentManager().consult(request))


@app.get("/agents")
async def agents(include_prompts: bool = False):
    return {
        "agents": AgentManager().list_agents(include_prompts=include_prompts)
    }


@app.get("/agents/{agent_key}/prompt")
async def agent_prompt(agent_key: str):
    try:
        agent = AgentManager().get_agent(agent_key)
    except KeyError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    return {
        "key": agent.key,
        "name": agent.name,
        "system_prompt": agent.system_prompt,
    }


@app.get("/tools")
async def tools(agent_key: str | None = None):
    if agent_key:
        try:
            agent = AgentManager().get_agent(agent_key)
        except KeyError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        agent_key = agent.key
    return {"tools": list_tool_metadata(agent_key)}


@app.get("/agents/{agent_key}/tools")
async def agent_tools(agent_key: str):
    try:
        agent = AgentManager().get_agent(agent_key)
    except KeyError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    return {
        "agent": agent.metadata(),
        "tools": list_tool_metadata(agent.key),
    }


@app.get("/diagram")
async def diagram():
    return {
        "format": "mermaid",
        "source": AgentManager().workflow_mermaid(),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
