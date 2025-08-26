from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

try:
    # LangGraph >=0.6 provides Context in langgraph.types
    from langgraph.types import Context
except Exception:  # pragma: no cover - fallback type for older envs
    class Context:  # type: ignore
        state: dict
        store: dict
        logger: any

from .execution import PlotAgentExecutionEnvironment


# === Tool Schemas ===


class ExecutePlotlyCodeArgs(BaseModel):
    code: str = Field(
        ..., max_length=20000, description="Pure Python code that defines a Plotly figure in variable `fig`."
    )


class ExecutePlotlyCodeResult(BaseModel):
    status: str
    fig_json: Optional[str] = None
    error: Optional[str] = None


class GetDataframeProfileArgs(BaseModel):
    preview_rows: int = Field(5, ge=0, le=20)


# === Tool Implementations (Context-aware) ===


def execute_plotly_code(args: ExecutePlotlyCodeArgs, ctx: Context) -> ExecutePlotlyCodeResult:
    """Run user code in the hardened sandbox and return fig as JSON, logging to ctx.logger."""
    logger = getattr(ctx, "logger", None)
    df = ctx.store.get("df") if hasattr(ctx, "store") else None
    if df is None:
        if logger:
            logger.warning("execute_plotly_code called without a dataframe bound in Context.store")
        return ExecutePlotlyCodeResult(status="error", error="No dataframe bound.")

    # Reuse existing sandbox executor
    env = PlotAgentExecutionEnvironment(df)
    result = env.execute_code(args.code)

    if not result.get("success"):
        if logger:
            logger.debug(f"plotly exec failed: {result.get('error')}\n{result.get('output')}")
        # keep last code in store for inspection/fix tool
        ctx.store["last_code"] = args.code
        return ExecutePlotlyCodeResult(status="error", error=result.get("error") or "execution failed")

    try:
        # Serialize figure to JSON to store in state; consumers can deserialize as needed
        fig = result.get("fig")
        fig_json = fig.to_json() if hasattr(fig, "to_json") else None
        # Update state fig
        if hasattr(ctx, "state"):
            ctx.state["fig"] = {"fig_json": fig_json}
        # Keep last code for view_generated_code tool
        ctx.store["last_code"] = args.code
        return ExecutePlotlyCodeResult(status="ok", fig_json=fig_json)
    except Exception as e:  # pragma: no cover
        if logger:
            logger.exception("failed to serialize fig to json")
        return ExecutePlotlyCodeResult(status="error", error=str(e))


def get_dataframe_profile(args: GetDataframeProfileArgs, ctx: Context) -> dict:
    """Return cached or computed df schema/preview to reduce hallucinations."""
    state = getattr(ctx, "state", {})
    cached = state.get("df_profile") if isinstance(state, dict) else None
    if cached is not None:
        return cached

    df = ctx.store.get("df") if hasattr(ctx, "store") else None
    if df is None:
        return {"error": "No dataframe bound."}

    try:
        columns = list(map(str, getattr(df, "columns", [])))
        dtypes = (
            {str(c): str(t) for c, t in getattr(df, "dtypes", {}).items()}
            if hasattr(df, "dtypes") and isinstance(getattr(df, "dtypes"), dict)
            else {str(c): str(df[c].dtype) for c in getattr(df, "columns", [])}
        )
        head = df.head(args.preview_rows).to_dict(orient="records") if hasattr(df, "head") else []
        profile = {"columns": columns, "dtypes": dtypes, "head": head}
        if isinstance(state, dict):
            state["df_profile"] = profile
        return profile
    except Exception as e:  # pragma: no cover
        if hasattr(ctx, "logger") and ctx.logger:
            ctx.logger.exception("df profiling failed")
        return {"error": str(e)}


# Optional helper tools mirroring existing functionality


class DoesFigExistArgs(BaseModel):
    pass


def does_fig_exist(_: DoesFigExistArgs, ctx: Context) -> bool:
    """Return True if a figure JSON is present in state."""
    state = getattr(ctx, "state", {})
    try:
        return bool(state.get("fig", {}).get("fig_json"))
    except Exception:
        return False


class ViewGeneratedCodeArgs(BaseModel):
    pass


def view_generated_code(_: ViewGeneratedCodeArgs, ctx: Context) -> str:
    """Return the last code string executed via the plotting tool (if any)."""
    return ctx.store.get("last_code", "") if hasattr(ctx, "store") else ""

