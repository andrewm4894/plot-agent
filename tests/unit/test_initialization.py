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


def test_posthog_disabled_by_default(monkeypatch):
    """PostHog integration should be disabled when no key is provided."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("POSTHOG_PUBLIC_KEY", "")
    monkeypatch.setenv("POSTHOG_PROJECT_API_KEY", "")
    monkeypatch.setenv("POSTHOG_API_KEY", "")
    monkeypatch.setenv("POSTHOG_HOST", "")
    agent = PlotAgent()
    assert agent.posthog_enabled is False
    assert agent.posthog_public_key is None
    assert agent.posthog_host is None


def test_posthog_missing_dependency(monkeypatch):
    """Providing a PostHog key without the optional dependency should raise."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("POSTHOG_LLM_ANALYTICS", "true")
    monkeypatch.setenv("POSTHOG_PUBLIC_KEY", "phc_test_key")

    def _raise():
        raise ImportError("posthog unavailable")

    monkeypatch.setattr("plot_agent.callbacks._load_posthog_handler", _raise)

    with pytest.raises(ImportError):
        PlotAgent()


def test_posthog_custom_host(monkeypatch):
    """A custom PostHog host should be passed through when a handler is available."""                                                                          

    class DummyClient:
        def __init__(self, api_key: str, host: str):
            self.api_key = api_key
            self.host = host

    from langchain_core.callbacks.base import BaseCallbackHandler

    class DummyHandler(BaseCallbackHandler):
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("POSTHOG_LLM_ANALYTICS", "true")
    monkeypatch.setenv("POSTHOG_PUBLIC_KEY", "phc_test_key")
    monkeypatch.setenv("POSTHOG_HOST", "https://example.com")
    monkeypatch.setattr(
        "plot_agent.callbacks._load_posthog_handler", lambda: (DummyClient, DummyHandler)                                                                          
    )

    agent = PlotAgent()
    assert agent.posthog_enabled is True
    assert agent.posthog_public_key == "phc_test_key"
    assert agent.posthog_host == "https://example.com"
    assert isinstance(agent.posthog_client, DummyClient)
    assert agent.callback_manager._posthog_callback.kwargs["client"] is agent.posthog_client
