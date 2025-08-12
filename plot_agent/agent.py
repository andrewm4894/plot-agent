"""
This module contains the PlotAgent class, which is used to generate Plotly code based on a user's plot description.
"""

import pandas as pd
from io import StringIO
import os
import re
import logging
from typing import Optional
from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import Tool, StructuredTool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from plot_agent.prompt import DEFAULT_SYSTEM_PROMPT
from plot_agent.models import (
    GeneratedCodeInput,
    DoesFigExistInput,
    ViewGeneratedCodeInput,
)
from plot_agent.execution import PlotAgentExecutionEnvironment


class PlotAgent:
    """
    A class that uses an LLM to generate Plotly code based on a user's plot description.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        system_prompt: Optional[str] = None,
        verbose: bool = True,
        max_iterations: int = 10,
        early_stopping_method: str = "force",
        handle_parsing_errors: bool = True,
        llm_temperature: float = 0.0,
        llm_timeout: int = 60,
        llm_max_retries: int = 1,
        debug: bool = False,
    ):
        """
        Initialize the PlotAgent.

        Args:
            model (str): The model to use for the LLM.
            system_prompt (Optional[str]): The system prompt to use for the LLM.
            verbose (bool): Whether to print verbose output from the agent.
            max_iterations (int): Maximum number of iterations for the agent to take.
            early_stopping_method (str): Method to use for early stopping.
            handle_parsing_errors (bool): Whether to handle parsing errors gracefully.
        """
        # Load .env if present, then require a valid API key
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Provide it via environment or a .env file."
            )
        self.debug = debug or os.getenv("PLOT_AGENT_DEBUG") == "1"

        # Configure logger
        self._logger = logging.getLogger("plot_agent")
        if self.debug:
            self._logger.setLevel(logging.DEBUG)
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        datefmt="%H:%M:%S",
                    )
                )
                self._logger.addHandler(handler)

        self.llm = ChatOpenAI(
            model=model,
            temperature=llm_temperature,
            timeout=llm_timeout,
            max_retries=llm_max_retries,
        )
        self.df = None
        self.df_info = None
        self.df_head = None
        self.sql_query = None
        self.execution_env = None
        self.chat_history = []
        # Internal graph-native message history, including tool messages
        self._graph_messages = []
        self.agent_executor = None
        self.generated_code = None
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.early_stopping_method = early_stopping_method
        self.handle_parsing_errors = handle_parsing_errors

    def set_df(self, df: pd.DataFrame, sql_query: Optional[str] = None):
        """
        Set the dataframe and capture its schema and sample.

        Args:
            df (pd.DataFrame): The pandas dataframe to set.
            sql_query (Optional[str]): The SQL query used to generate the dataframe.

        Returns:
            None
        """

        # Check df
        assert isinstance(df, pd.DataFrame), "The dataframe must be a pandas dataframe."
        assert not df.empty, "The dataframe must not be empty."

        if sql_query:
            assert isinstance(sql_query, str), "The SQL query must be a string."

        self.df = df

        # Capture df.info() output
        buffer = StringIO()
        df.info(buf=buffer)
        self.df_info = buffer.getvalue()

        # Capture df.head() as string representation
        self.df_head = df.head().to_string()

        # Store SQL query if provided
        self.sql_query = sql_query

        # Initialize execution environment
        self.execution_env = PlotAgentExecutionEnvironment(df)

        # Initialize the agent with tools
        self._initialize_agent()
        # Reset graph messages for a fresh session with this dataframe
        self._graph_messages = []
        if self.debug:
            self._logger.debug("set_df() initialized execution environment and graph")

    def execute_plotly_code(self, generated_code: str) -> str:
        """
        Execute the provided Plotly code and return the result.

        Args:
            generated_code (str): The Plotly code to execute.

        Returns:
            str: The result of the execution.
        """
        assert isinstance(generated_code, str), "The generated code must be a string."

        if not self.execution_env:
            return "Error: No dataframe has been set. Please set a dataframe first."

        # Store this as the last generated code
        self.generated_code = generated_code

        # Execute the generated code
        code_execution_result = self.execution_env.execute_code(generated_code)

        # Extract the results from the code execution
        code_execution_success = code_execution_result.get("success", False)
        code_execution_output = code_execution_result.get("output", "")
        code_execution_error = code_execution_result.get("error", "")

        # Check if the code executed successfully
        if code_execution_success:
            return f"Success: {code_execution_output}"
        else:
            return f"Error: {code_execution_error}\n{code_execution_output}"

    def does_fig_exist(self, *args, **kwargs) -> str:
        """
        Check if a figure object is available for display.

        Args:
            *args: Any positional arguments (ignored)
            **kwargs: Any keyword arguments (ignored)

        Returns:
            str: A message indicating whether a figure is available for display.
        """
        if not self.execution_env:
            return "No execution environment has been initialized. Please set a dataframe first."

        if self.execution_env.fig is not None:
            return "A figure is available for display."
        else:
            return "No figure has been created yet."

    def view_generated_code(self, *args, **kwargs) -> str:
        """
        View the generated code.
        """
        return self.generated_code or ""

    def _initialize_agent(self):
        """Initialize a LangGraph ReAct agent with tools and keep API compatibility."""

        # Initialize the tools
        tools = [
            Tool.from_function(
                func=self.execute_plotly_code,
                name="execute_plotly_code",
                description=(
                    "Execute the provided Plotly code and return a result indicating "
                    "if the code executed successfully and if a figure object was created."
                ),
                args_schema=GeneratedCodeInput,
            ),
            StructuredTool.from_function(
                func=self.does_fig_exist,
                name="does_fig_exist",
                description=(
                    "Check if a figure exists and is available for display. "
                    "This tool takes no arguments and returns a string indicating "
                    "if a figure is available for display or not."
                ),
                args_schema=DoesFigExistInput,
            ),
            StructuredTool.from_function(
                func=self.view_generated_code,
                name="view_generated_code",
                description=(
                    "View the generated code. "
                    "This tool takes no arguments and returns the generated code as a string."
                ),
                args_schema=ViewGeneratedCodeInput,
            ),
        ]

        # Prepare system prompt with dataframe information
        sql_context = ""
        if self.sql_query:
            sql_context = (
                "In case it is useful to help with the data understanding, the df was generated using the following SQL query:\n"
                f"```sql\n{self.sql_query}\n```"
            )

        # Store formatted system instructions for the graph state modifier
        self._system_message_content = self.system_prompt.format(
            df_info=self.df_info,
            df_head=self.df_head,
            sql_context=sql_context,
        )

        # Create a ReAct agent graph with the provided tools and system prompt
        self._graph = create_react_agent(
            self.llm,
            tools,
            prompt=self._system_message_content,
            debug=self.debug,
        )

        # Backwards-compatibility: expose under the old attribute name
        self.agent_executor = self._graph

    def process_message(self, user_message: str) -> str:
        """Process a user message and return the agent's response."""
        assert isinstance(user_message, str), "The user message must be a string."

        if not self.agent_executor:
            return "Please set a dataframe first using set_df() method."

        # Add user message to outward-facing chat history
        self.chat_history.append(HumanMessage(content=user_message))

        # Reset generated_code
        self.generated_code = None

        # Short-circuit empty inputs to avoid graph recursion
        if user_message.strip() == "":
            ai_content = (
                "Please provide a non-empty plotting request (e.g., 'scatter x vs y')."
            )
            self.chat_history.append(AIMessage(content=ai_content))
            if self.debug:
                self._logger.debug("empty message received; returning guidance without invoking graph")
            return ai_content

        # Short-circuit messages that are primarily raw code blocks without a visualization request
        if "```" in user_message and not re.search(
            r"\b(plot|chart|graph|visuali(s|z)e|figure|subplot|heatmap|bar|line|scatter)\b",
            user_message,
            flags=re.IGNORECASE,
        ):
            ai_content = (
                "I see a code snippet. Please describe the visualization you want (e.g., 'line chart of y over x')."
            )
            self.chat_history.append(AIMessage(content=ai_content))
            if self.debug:
                self._logger.debug("code-only message received; returning guidance without invoking graph")
            return ai_content

        # Build graph messages (includes tool call/observation history)
        graph_messages = [*self._graph_messages, HumanMessage(content=user_message)]
        if self.debug:
            self._logger.debug(f"process_message() user: {user_message}")
            self._logger.debug(f"graph message count before invoke: {len(graph_messages)}")
        # Invoke the LangGraph agent
        result = self.agent_executor.invoke(
            {"messages": graph_messages},
            config={"recursion_limit": self.max_iterations},
        )

        # Extract the latest AI message from the returned messages
        ai_messages = [m for m in result.get("messages", []) if isinstance(m, AIMessage)]
        ai_content = ai_messages[-1].content if ai_messages else ""

        # Persist full graph messages for future context
        self._graph_messages = result.get("messages", [])
        if self.debug:
            self._logger.debug(f"graph message count after invoke: {len(self._graph_messages)}")

        # Add agent response to outward-facing chat history
        self.chat_history.append(AIMessage(content=ai_content))

        # If the agent didn't execute the code via tool, but we have prior generated_code, execute it
        if self.execution_env and self.execution_env.fig is None and self.generated_code is not None:
            if self.debug:
                self._logger.debug("executing stored generated_code because no fig exists yet")
            exec_result = self.execution_env.execute_code(self.generated_code)
            if self.debug:
                self._logger.debug(f"execution result success={exec_result.get('success')} error={exec_result.get('error')!r}")

        # If the assistant returned code in the message, execute it to update the figure
        code_executed = False
        if self.execution_env and isinstance(ai_content, str):
            extracted_code = None
            if "```python" in ai_content:
                parts = ai_content.split("```python", 1)
                extracted_code = parts[1].split("```", 1)[0].strip() if len(parts) > 1 else None
            elif "```" in ai_content:
                # Fallback: extract first generic fenced code block
                parts = ai_content.split("```", 1)
                if len(parts) > 1:
                    extracted_code = parts[1].split("```", 1)[0].strip()
            if extracted_code:
                if (self.generated_code or "").strip() != extracted_code:
                    self.generated_code = extracted_code
                    if self.debug:
                        self._logger.debug("executing code extracted from AI message")
                    exec_result = self.execution_env.execute_code(extracted_code)
                    if self.debug:
                        self._logger.debug(f"execution result success={exec_result.get('success')} error={exec_result.get('error')!r}")
                    code_executed = True

        # If still no figure and no code was executed, run one guided retry to force tool usage
        if self.execution_env and self.execution_env.fig is None and not code_executed:
            if self.debug:
                self._logger.debug("guided retry: prompting model to use execute_plotly_code tool")
            guided_messages = [
                *self._graph_messages,
                HumanMessage(
                    content=(
                        "Please use the execute_plotly_code(generated_code) tool with the FULL code to "
                        "create a variable named 'fig', then call does_fig_exist(). Return the final "
                        "code in a fenced ```python block."
                    )
                ),
            ]
            retry_result = self.agent_executor.invoke(
                {"messages": guided_messages},
                config={"recursion_limit": max(3, self.max_iterations // 2)},
            )
            self._graph_messages = retry_result.get("messages", [])
            retry_ai_messages = [
                m for m in self._graph_messages if isinstance(m, AIMessage)
            ]
            retry_content = retry_ai_messages[-1].content if retry_ai_messages else ""
            if isinstance(retry_content, str):
                if "```python" in retry_content:
                    parts = retry_content.split("```python", 1)
                    retry_code = (
                        parts[1].split("```", 1)[0].strip() if len(parts) > 1 else None
                    )
                elif "```" in retry_content:
                    parts = retry_content.split("```", 1)
                    retry_code = (
                        parts[1].split("```", 1)[0].strip() if len(parts) > 1 else None
                    )
                else:
                    retry_code = None
                if retry_code:
                    if (self.generated_code or "").strip() != retry_code:
                        self.generated_code = retry_code
                        if self.debug:
                            self._logger.debug("executing code extracted from guided retry response")
                        exec_result = self.execution_env.execute_code(retry_code)
                        if self.debug:
                            self._logger.debug(f"execution result success={exec_result.get('success')} error={exec_result.get('error')!r}")

        return ai_content if isinstance(ai_content, str) else str(ai_content)

    def get_figure(self):
        """Return the current figure if one exists."""
        if self.execution_env and self.execution_env.fig:
            return self.execution_env.fig
        return None

    def reset_conversation(self):
        """Reset the conversation history."""
        self.chat_history = []
        self.generated_code = None
