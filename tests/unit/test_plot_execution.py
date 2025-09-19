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
fig = px.scatter(df, x='x', y='y')
plot_title = "Scatter Plot of X vs Y"
plot_summary = "This scatter plot shows the relationship between X and Y values."
"""

    result = agent.execute_plotly_code(valid_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None
    assert agent.execution_env.plot_title is not None
    assert agent.execution_env.plot_summary is not None


def test_execute_plotly_code_with_error():
    """Test that execute_plotly_code handles errors properly."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Test with invalid code
    invalid_code = """import plotly.express as px
fig = px.scatter(df, x='non_existent_column', y='y')
plot_title = "Invalid Plot"
plot_summary = "This plot has an error."
"""

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
fig = px.scatter(df, x='x', y='y'  # Missing closing parenthesis
plot_title = "Test"
plot_summary = "Test summary"
"""

    result = agent.execute_plotly_code(invalid_code)
    assert "Error executing code: Code rejected on safety grounds: '(' was never closed (<unknown>, line 2)" in result
    assert agent.execution_env.fig is None


def test_handle_runtime_error():
    """Test handling of runtime errors in generated code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    error_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y', color='non_existent_column')
plot_title = "Error Plot"
plot_summary = "This plot will have an error."
"""

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


def test_missing_plot_title_and_summary():
    """Test that code without plot_title and plot_summary fails validation."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Test with code missing plot_title and plot_summary
    incomplete_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""

    result = agent.execute_plotly_code(incomplete_code)
    assert "Error" in result
    assert "Missing required variables" in result
    assert "plot_title" in result
    assert "plot_summary" in result
    assert agent.execution_env.fig is not None  # fig was created
    assert agent.execution_env.plot_title is None
    assert agent.execution_env.plot_summary is None


def test_invalid_plot_title_and_summary_types():
    """Test that plot_title and plot_summary must be strings."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Test with non-string plot_title and plot_summary
    invalid_types_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')
plot_title = 123  # Should be string
plot_summary = ['not', 'a', 'string']  # Should be string
"""

    result = agent.execute_plotly_code(invalid_types_code)
    assert "Error" in result
    assert "Validation errors" in result
    assert "plot_title must be a string" in result
    assert "plot_summary must be a string" in result