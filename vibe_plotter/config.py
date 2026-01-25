"""Configuration for Vibe Plotter."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

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
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        return errors


config = Config()
