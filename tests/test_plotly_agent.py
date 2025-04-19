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
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50]
    })
    
    agent = PlotlyAgent()
    agent.set_df(df)
    
    assert agent.df is not None
    assert agent.df_info is not None
    assert agent.df_head is not None
    assert agent.execution_env is not None
    assert agent.agent_executor is not None

def test_execute_plotly_code():
    """Test that execute_plotly_code works with valid code."""
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50]
    })
    
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
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50]
    })
    
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
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50]
    })
    
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
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50]
    })
    
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
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 20, 30, 40, 50]
    })
    
    agent = PlotlyAgent()
    agent.set_df(df)
    
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