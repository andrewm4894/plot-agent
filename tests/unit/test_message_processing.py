import pytest
import pandas as pd
from plot_agent.agent import PlotAgent
from langchain_core.messages import HumanMessage, AIMessage


def test_process_message():
    """Test that process_message updates chat history and handles responses."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df, sql_query="SELECT x, y FROM df")

    # Test processing a message
    response = agent.process_message("Create a scatter plot")

    # Check that chat history was updated
    assert len(agent.chat_history) == 2  # One human message and one AI message
    assert isinstance(agent.chat_history[0], HumanMessage)
    assert isinstance(agent.chat_history[1], AIMessage)
    assert agent.chat_history[0].content == "Create a scatter plot"


def test_reset_conversation():
    """Test that reset_conversation clears the chat history."""
    agent = PlotAgent()
    agent.chat_history = ["message1", "message2"]
    agent.reset_conversation()
    assert agent.chat_history == []


def test_process_empty_message():
    """Test processing of empty messages."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    response = agent.process_message("")
    assert len(agent.chat_history) == 2  # Should still create chat history entries
    assert isinstance(agent.chat_history[0], HumanMessage)
    assert isinstance(agent.chat_history[1], AIMessage)


def test_process_message_with_code_blocks():
    """Test processing messages that contain code blocks."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
    agent.set_df(df)

    message = "Here's some code:\n```python\nprint('test')\n```"
    response = agent.process_message(message)
    assert len(agent.chat_history) == 2
    assert "```python" in agent.chat_history[0].content


def test_memory_cleanup():
    """Test memory cleanup after multiple plot generations."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})

    agent = PlotAgent()
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