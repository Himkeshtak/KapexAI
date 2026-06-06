"""Skeleton for LangChain / LangGraph based agents.

This module provides minimal wrappers showing how to plug an LLM-driven agent
into the same output format as the pure-Python agents.

Note: installing and configuring LangChain/LLM credentials is required before
using these classes.
"""
from typing import Dict

try:
    from langchain.llms import OpenAI
    from langchain import PromptTemplate, LLMChain
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None
    PromptTemplate = None
    LLMChain = None


class LangChainAgent:
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.2):
        if OpenAI is None:
            raise RuntimeError("langchain or OpenAI LLM not installed")
        self.llm = OpenAI(model_name=model_name, temperature=temperature)

    def _call_llm(self, prompt: str) -> str:
        return self.llm(prompt)

    def generate_swot(self, topic: str) -> Dict:
        prompt = (
            f"Provide a concise SWOT analysis for the following topic: {topic}."
        )
        raw = self._call_llm(prompt)
        # TODO: parse LLM output into structured dict. For now return raw text.
        return {"topic": topic, "raw": raw}
