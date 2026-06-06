# KapexAI — AI Consultant (Multi-agent, Financial Advice)

Basic scaffold for an AI Consultant system that aggregates multiple agents' outputs
and generates a PowerPoint report (SWOT, Porter's Five Forces, financial summary).

Quick start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set your OpenAI API key (or other LLM provider env vars):

```bash
export OPENAI_API_KEY="sk-..."
```

3. Run the demo (uses pure-Python agents by default):

```bash
python examples/run_demo.py
```

What's here

- `src/agents/pure_python_agents.py`: simple rule-based agents (SWOT, Porter, financial summary).
- `src/agents/langchain_agents.py`: skeleton for LangChain / LangGraph-based agents.
- `src/ppt_generator.py`: create a PPTX from agents' outputs using `python-pptx`.
- `examples/run_demo.py`: example that ties everything together.

Next steps

- Implement full LangChain and LangGraph agents.
- Add templates and styling for PPT slides.
- Add orchestration to run agents in parallel and aggregate results.
