"""Reusable analysis and reporting tools."""

from kapexai.tools.analysis import run_all
from kapexai.tools.charts import (
    create_bar_chart,
    create_candlestick_chart,
    create_donut_chart,
    create_line_chart,
    create_waterfall_chart,
)
from kapexai.tools.presentation import build_ppt
from kapexai.tools.debt_calculators import DEBT_CALCULATOR_TOOLS
from kapexai.tools.equity_calculators import EQUITY_CALCULATOR_TOOLS
from kapexai.tools.finance_calculators import FINANCE_CALCULATOR_TOOLS
from kapexai.tools.registry import (
    get_tool,
    get_tools_for_agent,
    list_tool_metadata,
)
from kapexai.tools.runtime import (
    InMemoryTTLCache,
    RedisToolCache,
    configure_tool_cache,
)

__all__ = [
    "build_ppt",
    "create_bar_chart",
    "create_candlestick_chart",
    "create_donut_chart",
    "create_line_chart",
    "create_waterfall_chart",
    "configure_tool_cache",
    "DEBT_CALCULATOR_TOOLS",
    "EQUITY_CALCULATOR_TOOLS",
    "FINANCE_CALCULATOR_TOOLS",
    "get_tool",
    "get_tools_for_agent",
    "InMemoryTTLCache",
    "list_tool_metadata",
    "RedisToolCache",
    "run_all",
]
