"""
Plot Agent - An AI-powered data visualization assistant using Plotly.
"""

from .agent import PlotAgent
from .constants import (
    DEFAULT_MODEL,
    DEFAULT_VERBOSE,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_LLM_TIMEOUT,
    DEFAULT_LLM_MAX_RETRIES,
)

__version__ = "0.4.0"
__all__ = [
    "PlotAgent",
    "DEFAULT_MODEL",
    "DEFAULT_VERBOSE", 
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_LLM_TEMPERATURE",
    "DEFAULT_LLM_TIMEOUT",
    "DEFAULT_LLM_MAX_RETRIES",
]
