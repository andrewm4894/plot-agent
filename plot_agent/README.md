## plot_agent package overview

This package contains the implementation of Plot Agent: a LangGraph-powered assistant that generates and executes Plotly code safely.

### Files

- `__init__.py`
  - Exports two agent classes:
    - `PlotAgent` (new graph-based agent in `graph.py`)
    - `LegacyPlotAgent` (alias for the classic agent in `agent.py`)

- `agent.py` (legacy)
  - Original agent that wires tools to a ReAct loop and manages chat history externally.
  - Uses `PlotAgentExecutionEnvironment` to run generated code and keep a live `fig`.
  - Public API examples:
    - `agent = PlotAgent()`
    - `agent.set_df(df)`
    - `agent.process_message("Create a scatter plot of x vs y")`
    - `agent.get_figure()`
  - Status: legacy; emits a deprecation warning at initialization.

- `graph.py` (current)
  - New graph-first `PlotAgent` that uses `langgraph` v0.6+ `create_react_agent` with typed state and Context-aware tools.
  - Stores the dataframe in the LangGraph Context `store` so tools can access it.
  - Optional SQLite checkpointing (imported lazily; no hard dependency at import time).
  - Minimal usage:
    ```python
    from langchain_openai import ChatOpenAI
    from plot_agent.graph import PlotAgent

    llm = ChatOpenAI(model="gpt-4o-mini")
    agent = PlotAgent(llm, df=my_dataframe)
    result = agent.run("Create a bar chart of category vs value")
    ```

- `execution.py`
  - Hardened sandbox for executing LLM-generated Python/Plotly code.
  - Safeguards include AST allowlisting, restricted builtins/imports, timeout, stdout/stderr capture.
  - Class: `PlotAgentExecutionEnvironment(df)` with `execute_code(code)` returning `{fig, output, error, success}`.

- `models.py` (legacy schemas)
  - Pydantic models used by the legacy agent’s tool definitions (e.g., `GeneratedCodeInput`).

- `prompt.py`
  - `DEFAULT_SYSTEM_PROMPT`: Legacy agent’s detailed instructions and workflow.
  - `SYSTEM_PROMPT`: New agent’s concise tool-first contract (always call `execute_plotly_code`).
  - `CODE_TEMPLATE`: Small helper snippet for common code generation.

- `state.py`
  - Typed LangGraph state used by the new agent.
  - `AgentState`: `messages` (append-only), `fig` (replace), `df_profile` (replace/cache).
  - `FigState`: holds `fig_json` for the latest generated figure.

- `tools.py`
  - Context-aware tool implementations and Pydantic schemas.
  - Tools:
    - `execute_plotly_code(ExecutePlotlyCodeArgs)` → runs code via `PlotAgentExecutionEnvironment`, updates `state.fig.fig_json`, returns a structured result.
    - `get_dataframe_profile(GetDataframeProfileArgs)` → computes and caches `df_profile` in state.
    - `does_fig_exist(DoesFigExistArgs)` → checks whether `fig_json` exists in state.
    - `view_generated_code(ViewGeneratedCodeArgs)` → returns the last executed code from `Context.store`.

### Choosing an agent

- Prefer `plot_agent.graph.PlotAgent` for new development (typed state, Context, structured tools).
- Keep `plot_agent.agent.PlotAgent` if you rely on the prior message-processing API; both can coexist.

### Checkpointing (optional)

- If you provide `checkpoint_path` to `plot_agent.graph.PlotAgent`, the agent compiles with a SQLite checkpointer when available:
  - `pip install sqlalchemy aiosqlite`
  - The import is lazy; if the optional modules are missing, the agent simply runs without checkpointing.

