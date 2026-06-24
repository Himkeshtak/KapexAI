"""Command-line interface for KapexAI."""

import argparse
import json
from pathlib import Path

from kapexai.env_loader import load_environment
from kapexai.tools.analysis import run_all
from kapexai.tools.presentation import build_ppt
from kapexai.workers import AgentManager, ConsultationRequest


def _consult(args: argparse.Namespace) -> None:
    request = ConsultationRequest(company=args.company, goal=args.goal)
    result = AgentManager().consult(request)
    print(json.dumps(result, indent=2))


def _report(args: argparse.Namespace) -> None:
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    build_ppt(args.topic, run_all(args.topic), str(output))
    print(f"Wrote report to {output}")


def _serve(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run(
        "kapexai.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kapexai")
    subparsers = parser.add_subparsers(dest="command", required=True)

    consult = subparsers.add_parser("consult", help="Run a consultation")
    consult.add_argument("company")
    consult.add_argument("goal")
    consult.set_defaults(handler=_consult)

    report = subparsers.add_parser("report", help="Generate a PowerPoint report")
    report.add_argument("topic")
    report.add_argument("-o", "--output", default="output/kapex_report.pptx")
    report.set_defaults(handler=_report)

    serve = subparsers.add_parser("serve", help="Start the API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(handler=_serve)

    return parser


def main() -> None:
    load_environment()
    args = build_parser().parse_args()
    args.handler(args)
