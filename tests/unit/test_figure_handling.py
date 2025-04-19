import pytest
import pandas as pd
from plot_agent.agent import PlotAgent


def test_does_fig_exist():
    """Test that does_fig_exist correctly reports figure existence."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Initially no figure should exist
    assert "No figure has been created yet" in agent.does_fig_exist()

    # Create a figure
    valid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    agent.execute_plotly_code(valid_code)

    # Now a figure should exist
    assert "A figure is available for display" in agent.does_fig_exist()


def test_get_figure():
    """Test that get_figure returns the current figure if it exists."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Initially no figure should exist
    assert agent.get_figure() is None

    # Create a figure
    valid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    agent.execute_plotly_code(valid_code)

    # Now a figure should exist
    assert agent.get_figure() is not None


def test_view_generated_code():
    """Test that view_generated_code returns the last generated code."""
    agent = PlotAgent()
    test_code = "test code"
    agent.generated_code = test_code
    assert agent.view_generated_code() == test_code


def test_tool_interaction():
    """Test interaction between different tools."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # First check if figure exists (should not)
    assert "No figure has been created yet" in agent.does_fig_exist()

    # Generate and execute code
    code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    result = agent.execute_plotly_code(code)
    assert "Code executed successfully" in result

    # Check if figure exists (should now exist)
    assert "A figure is available for display" in agent.does_fig_exist()

    # View the generated code
    assert code in agent.view_generated_code()


def test_tool_response_formatting():
    """Test formatting of tool responses."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    # Test execute_plotly_code response format
    code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    result = agent.execute_plotly_code(code)
    assert isinstance(result, str)
    assert "Code executed successfully" in result

    # Test does_fig_exist response format
    result = agent.does_fig_exist()
    assert isinstance(result, str)
    assert "figure" in result.lower()

    # Test view_generated_code response format
    result = agent.view_generated_code()
    assert isinstance(result, str)
    assert code in result 