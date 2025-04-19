import pytest
import pandas as pd
import numpy as np
from plot_agent.agent import PlotlyAgent
from langchain_core.messages import HumanMessage, AIMessage


def test_plotly_agent_initialization():
    """Test that PlotlyAgent initializes correctly."""
    agent = PlotlyAgent()
    assert agent.llm is not None
    assert agent.df is None
    assert agent.df_info is None
    assert agent.df_head is None
    assert agent.sql_query is None
    assert agent.execution_env is None
    assert agent.chat_history == []
    assert agent.agent_executor is None
    assert agent.generated_code is None


def test_set_df():
    """Test that set_df properly sets up the dataframe and environment."""
    # Create a sample dataframe
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    assert agent.df is not None
    assert agent.df_info is not None
    assert agent.df_head is not None
    assert agent.execution_env is not None
    assert agent.agent_executor is not None


def test_execute_plotly_code():
    """Test that execute_plotly_code works with valid code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
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

    agent = PlotlyAgent()
    agent.set_df(df)

    # Test with invalid code
    invalid_code = """import plotly.express as px
fig = px.scatter(df, x='non_existent_column', y='y')"""

    result = agent.execute_plotly_code(invalid_code)
    assert "Error" in result
    assert agent.execution_env.fig is None


def test_does_fig_exist():
    """Test that does_fig_exist correctly reports figure existence."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    # Initially no figure should exist
    assert "No figure has been created yet" in agent.does_fig_exist()

    # Create a figure
    valid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    agent.execute_plotly_code(valid_code)

    # Now a figure should exist
    assert "A figure is available for display" in agent.does_fig_exist()


def test_reset_conversation():
    """Test that reset_conversation clears the chat history."""
    agent = PlotlyAgent()
    agent.chat_history = ["message1", "message2"]
    agent.reset_conversation()
    assert agent.chat_history == []


def test_view_generated_code():
    """Test that view_generated_code returns the last generated code."""
    agent = PlotlyAgent()
    test_code = "test code"
    agent.generated_code = test_code
    assert agent.view_generated_code() == test_code


def test_get_figure():
    """Test that get_figure returns the current figure if it exists."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    # Initially no figure should exist
    assert agent.get_figure() is None

    # Create a figure
    valid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y')"""
    agent.execute_plotly_code(valid_code)

    # Now a figure should exist
    assert agent.get_figure() is not None


def test_process_message():
    """Test that process_message updates chat history and handles responses."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df, sql_query="SELECT x, y FROM df")

    # Test processing a message
    response = agent.process_message("Create a scatter plot")

    # Check that chat history was updated
    assert len(agent.chat_history) == 2  # One human message and one AI message
    assert isinstance(agent.chat_history[0], HumanMessage)
    assert isinstance(agent.chat_history[1], AIMessage)
    assert agent.chat_history[0].content == "Create a scatter plot"


def test_execute_plotly_code_without_df():
    """Test that execute_plotly_code handles the case when no dataframe is set."""
    agent = PlotlyAgent()
    result = agent.execute_plotly_code("some code")
    assert "Error" in result and "No dataframe has been set" in result


def test_set_df_with_sql_query():
    """Test that set_df properly handles SQL query context."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    sql_query = "SELECT x, y FROM table"
    agent = PlotlyAgent()
    agent.set_df(df, sql_query=sql_query)

    assert agent.sql_query == sql_query


def test_agent_initialization_with_custom_prompt():
    """Test agent initialization with custom system prompt."""
    custom_prompt = "Custom system prompt for testing"
    agent = PlotlyAgent(system_prompt=custom_prompt)
    assert agent.system_prompt == custom_prompt


def test_agent_initialization_with_different_model():
    """Test agent initialization with different model names."""
    agent = PlotlyAgent(model="gpt-3.5-turbo")
    assert agent.llm.model_name == "gpt-3.5-turbo"


def test_agent_initialization_with_verbose():
    """Test agent initialization with verbose settings."""
    agent = PlotlyAgent(verbose=False)
    assert agent.verbose == False
    assert agent.agent_executor is None  # Agent executor not initialized yet


def test_agent_initialization_with_max_iterations():
    """Test agent initialization with different max iterations."""
    agent = PlotlyAgent(max_iterations=5)
    assert agent.max_iterations == 5


def test_agent_initialization_with_early_stopping():
    """Test agent initialization with different early stopping methods."""
    agent = PlotlyAgent(early_stopping_method="generate")
    assert agent.early_stopping_method == "generate"


def test_process_empty_message():
    """Test processing of empty messages."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    response = agent.process_message("")
    assert len(agent.chat_history) == 2  # Should still create chat history entries
    assert isinstance(agent.chat_history[0], HumanMessage)
    assert isinstance(agent.chat_history[1], AIMessage)


def test_process_message_with_code_blocks():
    """Test processing messages that contain code blocks."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    message = "Here's some code:\n```python\nprint('test')\n```"
    response = agent.process_message(message)
    assert len(agent.chat_history) == 2
    assert "```python" in agent.chat_history[0].content


def test_execution_environment_with_different_plot_types():
    """Test execution environment with different types of plots."""
    df = pd.DataFrame(
        {
            "x": [1, 2, 3, 4, 5],
            "y": [10, 20, 30, 40, 50],
            "category": ["A", "B", "A", "B", "A"],
        }
    )

    agent = PlotlyAgent()
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

    agent = PlotlyAgent()
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

    agent = PlotlyAgent()
    agent.set_df(df)

    preprocessing_code = """import plotly.express as px
# Preprocessing steps
df['y_normalized'] = (df['y'] - df['y'].min()) / (df['y'].max() - df['y'].min())
fig = px.scatter(df, x='x', y='y_normalized')"""

    result = agent.execute_plotly_code(preprocessing_code)
    assert "Code executed successfully" in result
    assert agent.execution_env.fig is not None


def test_handle_syntax_error():
    """Test handling of syntax errors in generated code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    invalid_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y'  # Missing closing parenthesis"""

    result = agent.execute_plotly_code(invalid_code)
    assert "Error" in result
    assert "SyntaxError" in result
    assert agent.execution_env.fig is None


def test_handle_runtime_error():
    """Test handling of runtime errors in generated code."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    error_code = """import plotly.express as px
fig = px.scatter(df, x='x', y='y', color='non_existent_column')"""

    result = agent.execute_plotly_code(error_code)
    assert "Error" in result
    assert agent.execution_env.fig is None


def test_tool_interaction():
    """Test interaction between different tools."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
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


def test_tool_validation():
    """Test validation of tool inputs."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    # Test with invalid code (empty string)
    result = agent.execute_plotly_code("")
    assert "Error" in result

    # Test with invalid code (None)
    with pytest.raises(AssertionError):
        agent.execute_plotly_code(None)


def test_tool_response_formatting():
    """Test formatting of tool responses."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
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


def test_memory_cleanup():
    """Test memory cleanup after multiple plot generations."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotlyAgent()
    agent.set_df(df)

    # Generate multiple plots
    for i in range(5):
        code = f"""import plotly.express as px
fig = px.scatter(df, x='x', y='y', title='Plot {i}')"""
        result = agent.execute_plotly_code(code)
        assert "Code executed successfully" in result
        assert agent.execution_env.fig is not None

    # Reset conversation and check memory
    agent.reset_conversation()
    assert len(agent.chat_history) == 0
    assert agent.generated_code is None


def test_large_dataframe_handling():
    """Test handling of large dataframes."""
    # Create a large dataframe
    df = pd.DataFrame({"x": range(10000), "y": range(10000)})

    agent = PlotlyAgent()
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
        agent = PlotlyAgent()
        agent.set_df("not a dataframe")

    # Test invalid SQL query input
    df = pd.DataFrame({"x": [1, 2, 3]})
    agent = PlotlyAgent()
    with pytest.raises(AssertionError):
        agent.set_df(df, sql_query=123)  # SQL query should be string

    # Test invalid message input
    agent.set_df(df)
    with pytest.raises(AssertionError):
        agent.process_message(123)  # Message should be string

    # Test invalid code input
    with pytest.raises(AssertionError):
        agent.execute_plotly_code(123)  # Code should be string


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

    agent = PlotlyAgent()
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
