# KapexAI

KapexAI is a multi-agent consulting scaffold with a FastAPI service and
PowerPoint report generation.

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
python -m kapexai consult "Acme" "Increase revenue"
python -m kapexai report "Acme Financial Services"
python -m kapexai serve --reload
python example.py
```

The API exposes `POST /consult`, `GET /diagram`, and `GET /health`.

## Structure

- `kapexai/`: application package and entry points
- `kapexai/tools/`: reusable analysis, LLM, and presentation tools
- `experimental/`: prototypes and research
- `logs/`: runtime logs
