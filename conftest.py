"""Pytest configuration and fixtures for plot-agent tests."""

import pytest


@pytest.fixture(autouse=True)
def clear_posthog_env(monkeypatch):
    """Clear PostHog environment variables for all tests to avoid conflicts."""
    monkeypatch.setenv("POSTHOG_LLM_ANALYTICS", "")
    monkeypatch.setenv("POSTHOG_PUBLIC_KEY", "")
    monkeypatch.setenv("POSTHOG_PROJECT_API_KEY", "")
    monkeypatch.setenv("POSTHOG_API_KEY", "")
    monkeypatch.setenv("POSTHOG_HOST", "")
