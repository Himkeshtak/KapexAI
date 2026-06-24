"""Generate a sample KapexAI PowerPoint report."""

from pathlib import Path

from kapexai.tools import build_ppt, run_all


def main() -> None:
    topic = "Acme Financial Services"
    output = Path("output/kapex_report.pptx")
    output.parent.mkdir(parents=True, exist_ok=True)
    build_ppt(topic, run_all(topic), str(output))
    print(f"Wrote report to {output}")


if __name__ == "__main__":
    main()
