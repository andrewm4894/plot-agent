import pytest
import pandas as pd
from plot_agent.execution import PlotAgentExecutionEnvironment


def test_execution_environment_init():
    """Ensure the execution environment initializes with a dataframe."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})
    env = PlotAgentExecutionEnvironment(df)
    assert env.df is not None


def test_execute_with_large_dataframe():
    """Test handling of large dataframes by executing a simple plot."""
    df = pd.DataFrame({"x": range(10000), "y": range(10000)})
    env = PlotAgentExecutionEnvironment(df)
    code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    result = env.execute_code(code)
    assert result["success"] is True


    assert env.fig is not None


def test_input_exec_error():
    """Ensure execution errors are surfaced."""
    df = pd.DataFrame({"x": [1, 2, 3]})
    env = PlotAgentExecutionEnvironment(df)
    bad_code = """import plotly.express as px
fig = px.scatter(df, x='missing', y='x')"""
    result = env.execute_code(bad_code)
    assert result["success"] is False