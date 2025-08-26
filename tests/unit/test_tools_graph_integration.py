import logging
import pandas as pd

from plot_agent.tools import (
    execute_plotly_code,
    ExecutePlotlyCodeArgs,
    get_dataframe_profile,
    GetDataframeProfileArgs,
    does_fig_exist,
    view_generated_code,
    DoesFigExistArgs,
    ViewGeneratedCodeArgs,
)


class _FakeCtx:
    def __init__(self, df=None):
        self.state = {"fig": {"fig_json": None}, "df_profile": None}
        self.store = {"df": df}
        self.logger = logging.getLogger("plot_agent_test")


def test_execute_plotly_code_success():
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 4, 9]})
    ctx = _FakeCtx(df)
    code = (
        "import plotly.express as px\n"
        "fig = px.scatter(df, x='x', y='y', title='ok')"
    )
    res = execute_plotly_code(ExecutePlotlyCodeArgs(code=code), ctx)
    assert res.status == "ok"
    assert isinstance(res.fig_json, str) and len(res.fig_json) > 0
    assert ctx.state["fig"]["fig_json"] == res.fig_json
    assert ctx.store.get("last_code") == code


def test_execute_plotly_code_no_df():
    ctx = _FakeCtx(df=None)
    res = execute_plotly_code(ExecutePlotlyCodeArgs(code="fig=None"), ctx)
    assert res.status == "error"
    assert "No dataframe" in (res.error or "")


def test_get_dataframe_profile_and_cache():
    df = pd.DataFrame({"a": [1, 2, 3]})
    ctx = _FakeCtx(df)
    args = GetDataframeProfileArgs(preview_rows=2)
    prof1 = get_dataframe_profile(args, ctx)
    assert prof1["columns"] == ["a"]
    assert isinstance(prof1["head"], list) and len(prof1["head"]) == 2
    # Cached on subsequent calls
    prof2 = get_dataframe_profile(args, ctx)
    assert prof2 == prof1
    assert ctx.state["df_profile"] == prof1


def test_does_fig_exist_and_view_code():
    df = pd.DataFrame({"x": [1], "y": [1]})
    ctx = _FakeCtx(df)
    # Initially false
    assert does_fig_exist(DoesFigExistArgs(), ctx) is False
    # Set fig
    ctx.state["fig"]["fig_json"] = "{}"
    assert does_fig_exist(DoesFigExistArgs(), ctx) is True
    # Store and view code
    ctx.store["last_code"] = "print('hi')"
    assert view_generated_code(ViewGeneratedCodeArgs(), ctx) == "print('hi')"

