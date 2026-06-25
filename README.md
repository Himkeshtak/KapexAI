# KapexAI

KapexAI combines a FastAPI backend with a standalone Next.js frontend for
interactive financial scenario analysis and PowerPoint report generation.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add provider credentials when using
LLM-backed tools.

## Commands

```powershell
# Backend
python -m kapexai consult "Acme" "Increase revenue"
python -m kapexai report "Acme Financial Services"
python -m kapexai serve --reload
python example.py

# Frontend
cd Frontend
.\run.cmd install
.\run.cmd dev
```

The frontend runs at `http://localhost:3000` and connects to the FastAPI
service at `http://127.0.0.1:8000` by default. Copy
`Frontend/.env.local.example` to `Frontend/.env.local` to change the API URL.
The launcher uses the workspace-local Node runtime when Node is not installed
globally.

The API exposes `POST /consult`, `GET /diagram`, and `GET /health`.

## Agent Tools

KapexAI provides a LangChain-compatible tool registry with public-data,
research, finance, legal, planning, chart, PowerPoint, Mermaid, and foresight
tools. Tool metadata is available at:

- `GET /tools`
- `GET /tools?agent_key=market_analysis`
- `GET /agents/{agent_key}/tools`

Most tools need no credentials. Optional free-service credentials belong in
`.env`:

```text
SEC_USER_AGENT=KapexAI your-real-email@example.com
OPENALEX_API_KEY=
COURTLISTENER_API_TOKEN=
CROSSREF_MAILTO=
```

Each agent receives only its curated tool subset through
`get_tools_for_agent(agent_key)`. The default development cache is an in-memory
TTL cache. When Redis is available, configure the same layer without changing
tool code:

```python
from kapexai.tools import RedisToolCache, configure_tool_cache

configure_tool_cache(RedisToolCache(redis_client))
```

### Finance calculators

The financial agent includes 60 deterministic calculator tools in
`kapexai/tools/finance_calculators.py`. They cover returns and growth, interest
and time value of money, deposits and investments, valuation and capital
budgeting, fund and financing costs, performance ratios, hedging, drawdown,
moving averages, and Value at Risk. Relevant subsets are also available to the
market, economist, management, and strategy agents.

All rates use decimal form (`0.08` means 8%) unless a tool field explicitly
says `percent`. Cash-flow lists for NPV and IRR begin at time zero. Calculator
outputs are estimates and do not include taxes, trading costs, institution-
specific conventions, or legal/accounting judgments unless supplied as inputs.
Core conventions were cross-checked against the
[SEC Investor.gov compound-interest calculator](https://www.investor.gov/financial-tools-calculators/calculators/compound-interest-calculator),
[Microsoft NPV](https://support.microsoft.com/en-us/excel/functions/npv-function),
[IRR](https://support.microsoft.com/en-us/excel/functions/irr-function), and
[MIRR](https://support.microsoft.com/en-us/excel/functions/mirr-function)
definitions, plus Basel market-risk guidance for VaR.

## Specialist Agents

KapexAI includes ten separately scoped agents:

- Orchestrator
- Market Analysis
- Business Management Consultant
- Economist
- Business Strategist and Planner
- Astrologer and Future Predictor
- Financial, Accounting, and Asset Management
- Legal Advisor
- Presentation and Designer
- Mermaid Diagram and Workflow

Use `GET /agents` for the registry, `GET /agents?include_prompts=true` for all
system prompts, or `GET /agents/{agent_key}/prompt` for one prompt. The
`POST /consult` payload may include `requested_agents`, or
`context.include_all_agents=true` to route work to every specialist.

## Structure

- `kapexai/`: application package and entry points
- `kapexai/tools/`: reusable analysis, LLM, and presentation tools
- `Frontend/`: standalone Next.js and TypeScript application
- `experimental/`: prototypes and research
- `logs/`: runtime logs
