import pytest
import pandas as pd
from plot_agent.agent import PlotAgent


def test_execution_environment_with_different_plot_types():
    """Test execution environment with different types of plots."""
    df = pd.DataFrame(
        {
            "x": [1, 2, 3, 4, 5],
            "y": [10, 20, 30, 40, 50],
            "category": ["A", "B", "A", "B", "A"],
        }
    )

    agent = PlotAgent()
    agent.set_df(df)

    # Test scatter plot
    scatter_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    result = agent.execute_plotly_code(scatter_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None

    # Test bar plot
    bar_code = """import plotly.express as px
fig = px.bar(df, x='category', y='y')"""
    result = agent.execute_plotly_code(bar_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None

    # Test line plot
    line_code = """import plotly.express as px
fig = px.line(df, x='x', y='y')"""
    result = agent.execute_plotly_code(line_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None


def test_execution_environment_with_subplots():
    """Test execution environment with subplots."""
    df = pd.DataFrame(
        {"x": [1, 2, 3, 4, 5], "y1": [10, 20, 30, 40, 50], "y2": [50, 40, 30, 20, 10]}
    )

    agent = PlotAgent()
    agent.set_df(df)

    subplot_code = """import plotly.subplots as sp
import plotly.graph_objects as go
fig = sp.make_subplots(rows=1, cols=2)
fig.add_trace(go.Scatter(x=df['x'], y=df['y1']), row=1, col=1)
fig.add_trace(go.Scatter(x=df['x'], y=df['y2']), row=1, col=2)"""

    result = agent.execute_plotly_code(subplot_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None


def test_execution_environment_with_data_preprocessing():
    """Test execution environment with data preprocessing steps."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    preprocessing_code = """import plotly.express as px
# Preprocessing steps
df['y_normalized'] = (df['y'] - df['y'].min()) / (df['y'].max() - df['y'].min())
fig = px.scatter(df, x='x', y='y_normalized')"""

    result = agent.execute_plotly_code(preprocessing_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None


def test_complex_plot_handling():
    """Test handling of complex plots with multiple traces and layouts."""
    df = pd.DataFrame(
        {
            "x": [1, 2, 3, 4, 5],
            "y1": [10, 20, 30, 40, 50],
            "y2": [50, 40, 30, 20, 10],
            "category": ["A", "B", "A", "B", "A"],
        }
    )

    agent = PlotAgent()
    agent.set_df(df)

    complex_code = """import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['x'], y=df['y1'], name='Trace 1'))
fig.add_trace(go.Scatter(x=df['x'], y=df['y2'], name='Trace 2'))
fig.update_layout(
    title='Complex Plot',
    xaxis_title='X Axis',
    yaxis_title='Y Axis',
    showlegend=True,
    template='plotly_white'
)"""

    result = agent.execute_plotly_code(complex_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None 