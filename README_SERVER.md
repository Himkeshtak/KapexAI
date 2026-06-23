# KapexAI Server (FastAPI + LangChain)

This folder contains a lightweight multi-agent consulting framework and a FastAPI server.

Quick start

1. Install server dependencies:

```bash
python -m pip install -r server_requirements.txt
```

2. Run locally:

```bash
python examples/run_server.py
# or
uvicorn src.server.main:app --reload --port 8000
```

Endpoints

- `POST /consult` — JSON body: `{ "company": "Name", "goal": "Increase revenue", "context": {...} }`
- `GET /diagram` — Mermaid visualization of agent flow (renders in browser)
- `GET /health` — simple healthcheck

Files added

- `src/multi_agent_framework.py` — core agents and `AgentManager` orchestration
- `src/server/main.py` — FastAPI application
- `examples/run_server.py` — helper to run `uvicorn`
- `server_requirements.txt` — server-specific dependencies to install

Notes

- Implementation is intentionally small and easy to extend. Replace `Agent.run` with LangChain chains or other LLM-backed logic to integrate real models.
- Mermaid is served client-side via CDN to avoid adding heavy frontend tooling.
