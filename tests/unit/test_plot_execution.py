import pytest
import pandas as pd
from plot_agent.agent import PlotAgent


def test_execute_plotly_code():
    """Test that execute_plotly_code works with valid code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Test with valid plotly code
    valid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""

    result = agent.execute_plotly_code(valid_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None


def test_execute_plotly_code_with_error():
    """Test that execute_plotly_code handles errors properly."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Test with invalid code
    invalid_code = """import plotly.express as px
fig = px.scatter(df, x='non_existent_column', y='y')"""

    result = agent.execute_plotly_code(invalid_code)
    assert "Error" in result
    assert agent.execution_env.fig is None


def test_execute_plotly_code_without_df():
    """Test that execute_plotly_code handles the case when no dataframe is set."""
    agent = PlotAgent()
    result = agent.execute_plotly_code("some code")
    assert "Error" in result and "No dataframe has been set" in result


def test_handle_syntax_error():
    """Test handling of syntax errors in generated code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    invalid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y'  # Missing closing parenthesis"""

    result = agent.execute_plotly_code(invalid_code)
    assert "Error: Code rejected on safety grounds: '(' was never closed (<unknown>, line 2)" in result
    assert agent.execution_env.fig is None


def test_handle_runtime_error():
    """Test handling of runtime errors in generated code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    error_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y', color='non_existent_column')"""

    result = agent.execute_plotly_code(error_code)
    assert "Error" in result
    assert agent.execution_env.fig is None


def test_tool_validation():
    """Test validation of tool inputs."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Test with invalid code (empty string)
    result = agent.execute_plotly_code("")
    assert "Error" in result

    # Test with invalid code (None)
    with pytest.raises(AssertionError):
        agent.execute_plotly_code(None) 