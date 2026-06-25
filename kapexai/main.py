"""FastAPI application for KapexAI."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kapexai.workers import AgentManager, ConsultationRequest


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


@app.get("/diagram")
async def diagram():
    mermaid = """
graph LR
    C[Client Request] --> MA(MarketAnalysis)
    MA --> FM(FinancialModeling)
    FM --> ST(Strategy)
    ST --> CP(Compliance)
    CP --> R(Recommendation)
"""
    return {"format": "mermaid", "source": mermaid.strip()}


@app.get("/health")
async def health():
    return {"status": "ok"}
