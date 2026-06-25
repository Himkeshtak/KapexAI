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

## Structure

- `kapexai/`: application package and entry points
- `kapexai/tools/`: reusable analysis, LLM, and presentation tools
- `Frontend/`: standalone Next.js and TypeScript application
- `experimental/`: prototypes and research
- `logs/`: runtime logs
