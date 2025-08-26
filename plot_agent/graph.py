from __future__ import annotations

from typing import Any, Dict, Optional

from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage

from .state import AgentState
from .tools import (
    ExecutePlotlyCodeArgs,
    GetDataframeProfileArgs,
    DoesFigExistArgs,
    ViewGeneratedCodeArgs,
)
from .execution import PlotAgentExecutionEnvironment
from .prompt import SYSTEM_PROMPT


class PlotAgent:
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        *,
        df: Optional[Any] = None,
        checkpoint_path: Optional[str] = None,
        model: str = "gpt-4o-mini",
        llm_temperature: float = 0.0,
        llm_timeout: int = 60,
        llm_max_retries: int = 1,
    ) -> None:
        # Store DF in the agent-level store; Context will expose it to tools
        self._store: Dict[str, Any] = {"df": df}

        # Define tool wrappers bound to this agent's store (no Context param)
        def _execute_plotly_code(code: str) -> Dict[str, Optional[str]]:
            """Execute Plotly code in a sandbox and return a structured result with fig_json or error."""
            df = self._store.get("df")
            if df is None:
                return {"status": "error", "fig_json": None, "error": "No dataframe bound."}
            env = PlotAgentExecutionEnvironment(df)
            result = env.execute_code(code)
            if not result.get("success"):
                self._store["last_code"] = code
                return {"status": "error", "fig_json": None, "error": result.get("error")}
            fig = result.get("fig")
            fig_json = fig.to_json() if hasattr(fig, "to_json") else None
            self._store["last_code"] = code
            self._store["_last_fig_json"] = fig_json
            return {"status": "ok", "fig_json": fig_json, "error": None}

        def _get_dataframe_profile(preview_rows: int = 5) -> Dict[str, Any]:
            """Return dataframe schema preview; cached per process."""
            if self._store.get("df_profile_cache") is not None:
                return self._store["df_profile_cache"]
            df = self._store.get("df")
            if df is None:
                return {"error": "No dataframe bound."}
            columns = list(map(str, getattr(df, "columns", [])))
            try:
                dtypes = {str(c): str(df[c].dtype) for c in getattr(df, "columns", [])}
            except Exception:
                dtypes = {}
            head = df.head(preview_rows).to_dict(orient="records") if hasattr(df, "head") else []
            profile = {"columns": columns, "dtypes": dtypes, "head": head}
            self._store["df_profile_cache"] = profile
            return profile

        def _does_fig_exist() -> bool:
            """Return True if last execution produced a figure JSON."""
            # We check store for a cached fig_json in last tool result during run()
            return bool(self._store.get("_last_fig_json"))

        def _view_generated_code() -> str:
            """Return the last generated/ran code if available."""
            return self._store.get("last_code", "")

        tools = [
            StructuredTool.from_function(
                func=_execute_plotly_code,
                name="execute_plotly_code",
                description=_execute_plotly_code.__doc__ or "Execute Plotly code and return fig_json",
            ),
            StructuredTool.from_function(
                func=_get_dataframe_profile,
                name="get_dataframe_profile",
                description=_get_dataframe_profile.__doc__ or "Return dataframe schema preview",
            ),
            StructuredTool.from_function(
                func=_does_fig_exist,
                name="does_fig_exist",
                description=_does_fig_exist.__doc__ or "Check whether a figure exists",
            ),
            StructuredTool.from_function(
                func=_view_generated_code,
                name="view_generated_code",
                description=_view_generated_code.__doc__ or "View last generated code",
            ),
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])

        # Optional checkpointing; import only if requested and available
        checkpointer = None
        if checkpoint_path:
            try:
                from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore

                checkpointer = SqliteSaver.from_conn_string(checkpoint_path)
            except Exception:
                # Fallback to no checkpointing if optional dependency/module is missing
                checkpointer = None

        # Use provided LLM or create a default OpenAI chat model
        if llm is None:
            try:
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(
                    model=model,
                    temperature=llm_temperature,
                    timeout=llm_timeout,
                    max_retries=llm_max_retries,
                )
            except Exception as e:  # pragma: no cover
                raise RuntimeError(
                    "Failed to initialize default ChatOpenAI. Provide llm explicitly or set OPENAI_API_KEY."
                ) from e

        # create_react_agent wires the loop with tool calling and state
        self.graph = create_react_agent(
            llm,
            tools=tools,
            # state_schema=AgentState,  # Remove custom state for now
            prompt=SYSTEM_PROMPT,  # Pass system prompt
        )

        # create_react_agent in recent versions returns a compiled app already.
        # If a checkpointer is provided, re-compile with it; otherwise use as-is.
        try:
            if checkpointer is not None and hasattr(self.graph, "compile"):
                self.app = self.graph.compile(checkpointer=checkpointer)
            else:
                self.app = self.graph
        except Exception:
            # Fallback to direct assignment if compile is not available
            self.app = self.graph

    def run(self, prompt: str, *, thread_id: Optional[str] = None):
        # Use simple state format expected by create_react_agent
        state = {
            "messages": [HumanMessage(content=prompt)],
        }

        # Don't use thread_id without checkpointing
        config = {"recursion_limit": 20}  # Allow more recursion for the agent to complete
        if self.app.checkpointer and thread_id:
            config["configurable"] = {"thread_id": thread_id}

        # Invoke the agent once - the create_react_agent handles the loop internally
        result = self.app.invoke(state, config)
        
        # Attach latest fig_json from store so callers have a stable place to read it
        fig_json = self._store.get("_last_fig_json")
        if not isinstance(result, dict):
            result = {"messages": result}
        result["fig"] = {"fig_json": fig_json}
        return result

    def get_last_code(self) -> Optional[str]:
        """Get the last generated code from the agent."""
        return self._store.get("last_code")
    
    async def astream(self, prompt: str, *, thread_id: Optional[str] = None):
        # Use simple state format expected by create_react_agent
        state = {
            "messages": [HumanMessage(content=prompt)],
        }
        async for event in self.app.astream_events(
            state,
            version="v2",
            config={"configurable": {"thread_id": thread_id or "default"}},
        ):
            yield event

