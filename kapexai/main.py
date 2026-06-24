"""FastAPI application for KapexAI."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from kapexai.workers import AgentManager, ConsultationRequest


app = FastAPI(title="KapexAI Consulting API")


@app.post("/consult")
async def consult(payload: dict):
    try:
        request = ConsultationRequest(**payload)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    return JSONResponse(AgentManager().consult(request))


@app.get("/diagram", response_class=HTMLResponse)
async def diagram():
    mermaid = """
graph LR
    C[Client Request] --> MA(MarketAnalysis)
    MA --> FM(FinancialModeling)
    FM --> ST(Strategy)
    ST --> CP(Compliance)
    CP --> R(Recommendation)
"""
    html = f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>KapexAI - Agent Flow</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  </head>
  <body>
    <div class="mermaid">{mermaid}</div>
    <script>mermaid.initialize({{startOnLoad: true}})</script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@app.get("/health")
async def health():
    return {"status": "ok"}
