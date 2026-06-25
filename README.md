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

The financial agent includes 201 deterministic calculator tools:

- 60 general calculators in `kapexai/tools/finance_calculators.py`
- 43 equity calculators in `kapexai/tools/equity_calculators.py`
- 23 debt and fixed-income calculators in `kapexai/tools/debt_calculators.py`
- 47 tax and salary calculators in `kapexai/tools/tax_salary_calculators.py`
- 28 mortgage and real-estate calculators in
  `kapexai/tools/real_estate_calculators.py`

Coverage includes returns and growth, interest and time value of money,
capital budgeting, stock valuation, dividends, equity multiples, CAPM, beta,
WACC, profitability and capital-efficiency ratios, bond pricing and YTM,
duration, convexity, credit risk, leverage, liquidity, payroll, salary,
progressive tax, sales tax, RMDs, mortgages, refinancing, property operations,
hedging, drawdown, moving averages, and Value at Risk. Relevant subsets are
also available to the market, economist, management, strategy, and legal
agents.

All rates use decimal form (`0.08` means 8%) unless a tool field explicitly
says `percent`. Cash-flow lists for NPV and IRR begin at time zero. Calculator
outputs are estimates and do not include taxes, trading costs, institution-
specific conventions, or legal/accounting judgments unless supplied as inputs.
Core conventions were cross-checked against the
[SEC Investor.gov compound-interest calculator](https://www.investor.gov/financial-tools-calculators/calculators/compound-interest-calculator),
[Microsoft NPV](https://support.microsoft.com/en-us/excel/functions/npv-function),
[IRR](https://support.microsoft.com/en-us/excel/functions/irr-function), and
[MIRR](https://support.microsoft.com/en-us/excel/functions/mirr-function)
definitions, the
[SEC Investor.gov P/E definition](https://www.investor.gov/introduction-investing/investing-basics/glossary/price-earnings-pe-ratio),
and Basel market-risk guidance for VaR.

Tax rules, state and local rates, political proposals, mortgage insurance, and
loan-program terms can change. The tools expose tax-year, rate, bracket, credit,
and program inputs where needed instead of presenting historical assumptions as
current legal advice. FICA defaults follow
[IRS Topic 751](https://www.irs.gov/taxtopics/tc751), RMD logic follows the
[IRS RMD guidance](https://www.irs.gov/retirement-plans/retirement-plan-and-ira-required-minimum-distributions-faqs),
and adjustable-rate mortgage behavior follows
[CFPB consumer guidance](https://www.consumerfinance.gov/ask-cfpb/what-is-an-adjustable-rate-mortgage-arm-en-1949/).

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
