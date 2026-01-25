"""Configuration for Vibe Plotter."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # LLM Provider - supports OpenRouter or OpenAI
    # If OPENROUTER_API_KEY is set, it will be used; otherwise falls back to OPENAI_API_KEY
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Determine which provider is active
    LLM_PROVIDER = "openrouter" if OPENROUTER_API_KEY else ("openai" if OPENAI_API_KEY else None)

    # PostHog
    POSTHOG_ENABLED = os.getenv("POSTHOG_ENABLED", "false").lower() == "true"
    POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "")
    POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

    # App settings
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", "60"))

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration."""
        errors = []
        if not cls.OPENROUTER_API_KEY and not cls.OPENAI_API_KEY:
            errors.append("Either OPENROUTER_API_KEY or OPENAI_API_KEY is required")
        return errors


config = Config()
