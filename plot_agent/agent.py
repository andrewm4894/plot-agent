"""
This module contains the PlotAgent class, which is used to generate Plotly code based on a user's plot description.
"""

import os
import re
import logging
from io import StringIO
from typing import Optional, List, Any, Dict

import pandas as pd
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
    CheckPlotOutputsInput,
)
from plot_agent.execution import PlotAgentExecutionEnvironment
from plot_agent.callbacks import create_callback_manager
from plot_agent.constants import (
    DEFAULT_MODEL,
    DEFAULT_VERBOSE,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_EARLY_STOPPING_METHOD,
    DEFAULT_HANDLE_PARSING_ERRORS,
    DEFAULT_DEBUG,
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_LLM_TIMEOUT,
    DEFAULT_LLM_MAX_RETRIES,
    OPENAI_API_KEY_ENV_VAR,
    PLOT_AGENT_DEBUG_ENV_VAR,
    MISSING_API_KEY_ERROR,
    MISSING_DF_ERROR,
    EMPTY_DF_ERROR,
    INVALID_DF_TYPE_ERROR,
    INVALID_SQL_TYPE_ERROR,
    INVALID_MESSAGE_TYPE_ERROR,
    INVALID_CODE_TYPE_ERROR,
    TOOL_EXECUTE_PLOTLY_CODE,
    TOOL_DOES_FIG_EXIST,
    TOOL_VIEW_GENERATED_CODE,
    TOOL_CHECK_PLOT_OUTPUTS,
    TOOL_DESCRIPTIONS,
    EMPTY_MESSAGE_RESPONSE,
    CODE_ONLY_MESSAGE_RESPONSE,
    NO_DF_SET_RESPONSE,
    FIG_AVAILABLE_RESPONSE,
    NO_FIG_RESPONSE,
    ALL_OUTPUTS_AVAILABLE_RESPONSE,
    CODE_EXECUTION_SUCCESS_PREFIX,
    CODE_EXECUTION_ERROR_PREFIX,
    GUIDED_RETRY_MESSAGE,
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_DATE_FORMAT,
)


class PlotAgent:
    """
    A class that uses an LLM to generate Plotly code based on a user's plot description.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        system_prompt: Optional[str] = None,
        verbose: bool = DEFAULT_VERBOSE,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        early_stopping_method: str = DEFAULT_EARLY_STOPPING_METHOD,
        handle_parsing_errors: bool = DEFAULT_HANDLE_PARSING_ERRORS,
        llm_temperature: float = DEFAULT_LLM_TEMPERATURE,
        llm_timeout: int = DEFAULT_LLM_TIMEOUT,
        llm_max_retries: int = DEFAULT_LLM_MAX_RETRIES,
        debug: bool = DEFAULT_DEBUG,
        posthog_public_key: Optional[str] = None,
        posthog_host: Optional[str] = None,
        posthog_client: Optional[Any] = None,
        posthog_callback_options: Optional[Dict[str, Any]] = None,
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
            posthog_public_key (Optional[str]): Optional PostHog public API key for LLM analytics.
            posthog_host (Optional[str]): Optional PostHog ingestion host. Defaults to
                "https://us.i.posthog.com" when a key is provided.
            posthog_client (Optional[Any]): Optional pre-configured PostHog client instance.
            posthog_callback_options (Optional[Dict[str, Any]]): Additional kwargs forwarded to
                `posthog.ai.langchain.CallbackHandler` (e.g. `distinct_id`, `trace_id`).
        """
        # Load .env if present, then require a valid API key
        load_dotenv()
        openai_api_key = os.getenv(OPENAI_API_KEY_ENV_VAR)
        if not openai_api_key:
            raise RuntimeError(MISSING_API_KEY_ERROR)
        self.debug = debug or os.getenv(PLOT_AGENT_DEBUG_ENV_VAR) == "1"

        # Set up callback handlers for analytics and monitoring
        self.callback_manager = create_callback_manager(
            posthog_public_key=posthog_public_key,
            posthog_host=posthog_host,
            posthog_client=posthog_client,
            posthog_callback_options=posthog_callback_options,
        )
        
        # Expose PostHog properties for backward compatibility
        self.posthog_client = self.callback_manager.posthog_client
        self.posthog_public_key = self.callback_manager.posthog_public_key
        self.posthog_host = self.callback_manager.posthog_host
        self.posthog_enabled = self.callback_manager.posthog_enabled

        # Configure logger
        self._logger = logging.getLogger("plot_agent")
        if self.debug:
            self._logger.setLevel(logging.DEBUG)
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter(
                        DEFAULT_LOG_FORMAT,
                        datefmt=DEFAULT_LOG_DATE_FORMAT,
                    )
                )
                self._logger.addHandler(handler)

        llm_kwargs = dict(
            model=model,
            temperature=llm_temperature,
            timeout=llm_timeout,
            max_retries=llm_max_retries,
        )
        # Callbacks are applied at request time for full propagation to child runs.
        self.llm = ChatOpenAI(**llm_kwargs)
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
        assert isinstance(df, pd.DataFrame), INVALID_DF_TYPE_ERROR
        assert not df.empty, EMPTY_DF_ERROR

        if sql_query:
            assert isinstance(sql_query, str), INVALID_SQL_TYPE_ERROR

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
        assert isinstance(generated_code, str), INVALID_CODE_TYPE_ERROR

        if not self.execution_env:
            return f"{CODE_EXECUTION_ERROR_PREFIX}{MISSING_DF_ERROR}"

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
            return f"{CODE_EXECUTION_SUCCESS_PREFIX}{code_execution_output}"
        else:
            return f"{CODE_EXECUTION_ERROR_PREFIX}{code_execution_error}\n{code_execution_output}"

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
            return f"{CODE_EXECUTION_ERROR_PREFIX}{MISSING_DF_ERROR}"

        if self.execution_env.fig is not None:
            return FIG_AVAILABLE_RESPONSE
        else:
            return NO_FIG_RESPONSE

    def check_plot_outputs(self, *args, **kwargs) -> str:
        """
        Check if all required plot outputs (fig, plot_title, plot_summary) are available.

        Args:
            *args: Any positional arguments (ignored)
            **kwargs: Any keyword arguments (ignored)

        Returns:
            str: A message indicating which plot outputs are available.
        """
        if not self.execution_env:
            return f"{CODE_EXECUTION_ERROR_PREFIX}{MISSING_DF_ERROR}"

        available = []
        missing = []
        
        if self.execution_env.fig is not None:
            available.append("fig")
        else:
            missing.append("fig")
            
        if self.execution_env.plot_title is not None:
            available.append("plot_title")
        else:
            missing.append("plot_title")
            
        if self.execution_env.plot_summary is not None:
            available.append("plot_summary")
        else:
            missing.append("plot_summary")
        
        if not missing:
            return ALL_OUTPUTS_AVAILABLE_RESPONSE
        else:
            status = f"Available: {', '.join(available) if available else 'none'}. Missing: {', '.join(missing)}."
            return status

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
                name=TOOL_EXECUTE_PLOTLY_CODE,
                description=TOOL_DESCRIPTIONS[TOOL_EXECUTE_PLOTLY_CODE],
                args_schema=GeneratedCodeInput,
            ),
            StructuredTool.from_function(
                func=self.does_fig_exist,
                name=TOOL_DOES_FIG_EXIST,
                description=TOOL_DESCRIPTIONS[TOOL_DOES_FIG_EXIST],
                args_schema=DoesFigExistInput,
            ),
            StructuredTool.from_function(
                func=self.view_generated_code,
                name=TOOL_VIEW_GENERATED_CODE,
                description=TOOL_DESCRIPTIONS[TOOL_VIEW_GENERATED_CODE],
                args_schema=ViewGeneratedCodeInput,
            ),
            StructuredTool.from_function(
                func=self.check_plot_outputs,
                name=TOOL_CHECK_PLOT_OUTPUTS,
                description=TOOL_DESCRIPTIONS[TOOL_CHECK_PLOT_OUTPUTS],
                args_schema=CheckPlotOutputsInput,
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
        assert isinstance(user_message, str), INVALID_MESSAGE_TYPE_ERROR

        if not self.agent_executor:
            return NO_DF_SET_RESPONSE

        # Add user message to outward-facing chat history
        self.chat_history.append(HumanMessage(content=user_message))

        # Reset generated_code
        self.generated_code = None

        # Short-circuit empty inputs to avoid graph recursion
        if user_message.strip() == "":
            ai_content = EMPTY_MESSAGE_RESPONSE
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
            ai_content = CODE_ONLY_MESSAGE_RESPONSE
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
        invoke_config = {"recursion_limit": self.max_iterations}
        if self.callback_manager.has_callbacks():
            invoke_config["callbacks"] = self.callback_manager.get_callbacks()

        result = self.agent_executor.invoke(
            {"messages": graph_messages},
            config=invoke_config,
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
                HumanMessage(content=GUIDED_RETRY_MESSAGE),
            ]
            retry_config = {"recursion_limit": max(3, self.max_iterations // 2)}
            if self.callback_manager.has_callbacks():
                retry_config["callbacks"] = self.callback_manager.get_callbacks()

            retry_result = self.agent_executor.invoke(
                {"messages": guided_messages},
                config=retry_config,
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

    def get_plot_title(self):
        """Return the current plot title if one exists."""
        if self.execution_env and self.execution_env.plot_title:
            return self.execution_env.plot_title
        return None

    def get_plot_summary(self):
        """Return the current plot summary if one exists."""
        if self.execution_env and self.execution_env.plot_summary:
            return self.execution_env.plot_summary
        return None

    def reset_conversation(self):
        """Reset the conversation history."""
        self.chat_history = []
        self.generated_code = None
        if self.execution_env:
            self.execution_env.fig = None
            self.execution_env.plot_title = None
            self.execution_env.plot_summary = None
