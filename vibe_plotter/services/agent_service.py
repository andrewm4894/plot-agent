"""Agent service for managing PlotAgent instances."""

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import pandas as pd

from plot_agent.agent import PlotAgent
from vibe_plotter.config import config

# Thread pool for running synchronous agent operations
_executor = ThreadPoolExecutor(max_workers=4)


class AgentService:
    """Service for managing PlotAgent instances and operations."""

    @staticmethod
    def create_agent(session_id: str) -> PlotAgent:
        """
        Create a new PlotAgent instance with PostHog session tracking.

        Args:
            session_id: The session ID for PostHog tracking.

        Returns:
            Configured PlotAgent instance.
        """
        # Set session ID for PostHog tracking
        os.environ["POSTHOG_AI_SESSION_ID"] = session_id
        os.environ["POSTHOG_DISTINCT_ID"] = session_id

        agent = PlotAgent(
            model=config.LLM_MODEL,
            verbose=True,
            debug=config.DEBUG,
        )

        return agent

    @staticmethod
    def initialize_agent_with_df(
        agent: PlotAgent,
        df: pd.DataFrame,
        sql_query: Optional[str] = None
    ) -> None:
        """
        Initialize an agent with a DataFrame.

        Args:
            agent: The PlotAgent instance.
            df: The DataFrame to set.
            sql_query: Optional SQL query that generated the DataFrame.
        """
        agent.set_df(df, sql_query=sql_query)

    @staticmethod
    async def process_message_async(agent: PlotAgent, message: str) -> str:
        """
        Process a message asynchronously using the thread pool.

        Args:
            agent: The PlotAgent instance.
            message: The user's message.

        Returns:
            The agent's response.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, agent.process_message, message)

    @staticmethod
    def process_message_sync(agent: PlotAgent, message: str) -> str:
        """
        Process a message synchronously.

        Args:
            agent: The PlotAgent instance.
            message: The user's message.

        Returns:
            The agent's response.
        """
        return agent.process_message(message)

    @staticmethod
    def get_visualization_data(agent: PlotAgent) -> dict:
        """
        Get the current visualization data from an agent.

        Args:
            agent: The PlotAgent instance.

        Returns:
            Dict with figure, title, summary, and code.
        """
        return {
            "figure": agent.get_figure(),
            "title": agent.get_plot_title(),
            "summary": agent.get_plot_summary(),
            "code": agent.export_code(),
        }

    @staticmethod
    def has_visualization(agent: PlotAgent) -> bool:
        """
        Check if the agent has a visualization.

        Args:
            agent: The PlotAgent instance.

        Returns:
            True if a figure exists.
        """
        return agent.get_figure() is not None
