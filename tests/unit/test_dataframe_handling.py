import pytest
import pandas as pd
from plot_agent.agent import PlotAgent


def test_set_df():
    """Test that set_df properly sets up the dataframe and environment."""
    # Create a sample dataframe
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    assert agent.df is not None
    assert agent.df_info is not None
    assert agent.df_head is not None
    assert agent.execution_env is not None
    assert agent.agent_executor is not None


def test_set_df_with_sql_query():
    """Test that set_df properly handles SQL query context."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    sql_query = "SELECT x, y FROM table"
    agent = PlotAgent()
    agent.set_df(df, sql_query=sql_query)

    assert agent.sql_query == sql_query


def test_large_dataframe_handling():
    """Test handling of large dataframes."""
    # Create a large dataframe
    df = pd.DataFrame({"x": range(10000), "y": range(10000)})

    agent = PlotAgent()
    agent.set_df(df)

    # Test plot generation with large dataframe
    code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    result = agent.execute_plotly_code(code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None


def test_input_validation():
    """Test validation of input parameters."""
    # Test invalid dataframe input
    with pytest.raises(AssertionError):
        agent = PlotAgent()
        agent.set_df("not a dataframe")

    # Test invalid SQL query input
    df = pd.DataFrame({"x": [1, 2, 3]})
    agent = PlotAgent()
    with pytest.raises(AssertionError):
        agent.set_df(df, sql_query=123)  # SQL query should be string 