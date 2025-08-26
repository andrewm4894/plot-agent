import pytest
import pandas as pd
from plot_agent.execution import PlotAgentExecutionEnvironment


def test_execute_plotly_code():
    """Test that execute_plotly_code works with valid code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    env = PlotAgentExecutionEnvironment(df)

    # Test with valid plotly code
    valid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""

    result = env.execute_code(valid_code)
    assert result["success"] is True
    assert env.fig is not None


def test_execute_plotly_code_with_error():
    """Test that execute_plotly_code handles errors properly."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    env = PlotAgentExecutionEnvironment(df)

    # Test with invalid code
    invalid_code = """import plotly.express as px
fig = px.scatter(df, x='non_existent_column', y='y')"""

    result = env.execute_code(invalid_code)
    assert result["success"] is False
    assert env.fig is None


def test_execute_plotly_code_without_df():
    """Test that executing without a df raises on env init."""
    with pytest.raises(AssertionError):
        PlotAgentExecutionEnvironment(None)  # type: ignore[arg-type]


def test_handle_syntax_error():
    """Test handling of syntax errors in generated code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    env = PlotAgentExecutionEnvironment(df)

    invalid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y'  # Missing closing parenthesis"""

    result = env.execute_code(invalid_code)
    assert result["success"] is False
    assert "Code rejected on safety grounds" in result["error"]
    assert env.fig is None


def test_handle_runtime_error():
    """Test handling of runtime errors in generated code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    env = PlotAgentExecutionEnvironment(df)

    error_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y', color='non_existent_column')"""

    result = env.execute_code(error_code)
    assert result["success"] is False
    assert env.fig is None


def test_tool_validation():
    """Test validation of tool inputs (basic)."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    env = PlotAgentExecutionEnvironment(df)

    # Test with invalid code (empty string) → parse error path
    result = env.execute_code("")
    assert result["success"] is False