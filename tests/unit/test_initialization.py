import pytest
from plot_agent.agent import PlotAgent


def test_plotly_agent_initialization():
    """Test that PlotAgent initializes correctly."""
    agent = PlotAgent()
    assert agent.llm is not None
    assert agent.df is None
    assert agent.df_info is None
    assert agent.df_head is None
    assert agent.sql_query is None
    assert agent.execution_env is None
    assert agent.chat_history == []
    assert agent.agent_executor is None
    assert agent.generated_code is None


def test_agent_initialization_with_custom_prompt():
    """Test agent initialization with custom system prompt."""
    custom_prompt = "Custom system prompt for testing"
    agent = PlotAgent(system_prompt=custom_prompt)
    assert agent.system_prompt == custom_prompt


def test_agent_initialization_with_different_model():
    """Test agent initialization with different model names."""
    agent = PlotAgent(model="gpt-3.5-turbo")
    assert agent.llm.model_name == "gpt-3.5-turbo"


def test_agent_initialization_with_verbose():
    """Test agent initialization with verbose settings."""
    agent = PlotAgent(verbose=False)
    assert agent.verbose == False
    assert agent.agent_executor is None  # Agent executor not initialized yet


def test_agent_initialization_with_max_iterations():
    """Test agent initialization with different max iterations."""
    agent = PlotAgent(max_iterations=5)
    assert agent.max_iterations == 5


def test_agent_initialization_with_early_stopping():
    """Test agent initialization with different early stopping methods."""
    agent = PlotAgent(early_stopping_method="generate")
    assert agent.early_stopping_method == "generate" 