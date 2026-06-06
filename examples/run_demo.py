"""Example script that runs the pure-Python agents and produces a PPTX."""
import os
from pathlib import Path

from src.agents.pure_python_agents import run_all_pure
from src.ppt_generator import build_ppt


def main():
    topic = "Acme Financial Services"
    aggregated = run_all_pure(topic)
    out = Path("output")
    out.mkdir(exist_ok=True)
    ppt_path = out / "kapex_report.pptx"
    build_ppt(topic, aggregated, str(ppt_path))
    print(f"Wrote report to {ppt_path}")


if __name__ == "__main__":
    main()
