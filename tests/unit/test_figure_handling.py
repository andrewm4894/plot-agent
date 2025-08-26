import pytest
import pandas as pd
from plot_agent.execution import PlotAgentExecutionEnvironment
from plot_agent.tools import does_fig_exist, view_generated_code


def test_does_fig_exist():
    """Check figure existence using the tool and a fake Context."""
    class _Ctx:
        def __init__(self, df):
            self.state = {"fig": {"fig_json": None}}
            self.store = {"df": df}
            self.logger = None

    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 4, 9]})
    ctx = _Ctx(df)
    assert does_fig_exist(None, ctx) is False
    env = PlotAgentExecutionEnvironment(df)
    env.execute_code("""import plotly.express as px
fig = px.scatter(df, x='x', y='y')""")
    ctx.state["fig"]["fig_json"] = env.fig.to_json()
    assert does_fig_exist(None, ctx) is True


def test_get_figure_with_env():
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 4, 9]})
    env = PlotAgentExecutionEnvironment(df)
    assert env.fig is None
    env.execute_code("""import plotly.express as px
fig = px.scatter(df, x='x', y='y')""")
    assert env.fig is not None


def test_view_generated_code():
    class _Ctx:
        def __init__(self):
            self.state = {}
            self.store = {}
            self.logger = None
    ctx = _Ctx()
    ctx.store["last_code"] = "abc"
    assert view_generated_code(None, ctx) == "abc"


def test_tool_interaction_minimal():
    class _Ctx:
        def __init__(self, df):
            self.state = {"fig": {"fig_json": None}}
            self.store = {"df": df, "last_code": "print('hi')"}
            self.logger = None
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 3]})
    ctx = _Ctx(df)
    assert does_fig_exist(None, ctx) is False
    assert view_generated_code(None, ctx) == "print('hi')"


def test_tool_response_formatting_replacement():
    df = pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1]})
    env = PlotAgentExecutionEnvironment(df)
    result = env.execute_code("""import plotly.express as px
fig = px.scatter(df, x='x', y='y')""")
    assert result["success"] is True