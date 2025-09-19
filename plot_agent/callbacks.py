"""Callback handlers for LLM analytics and monitoring."""

import os
from typing import List, Any, Optional, Dict, Tuple
from langchain_core.callbacks.base import BaseCallbackHandler

from plot_agent.constants import (
    DEFAULT_POSTHOG_HOST,
    POSTHOG_ENV_VARS,
    POSTHOG_LLM_ANALYTICS_ENV_VAR,
    POSTHOG_IMPORT_ERROR,
)


def _load_posthog_handler():
    """Dynamically import PostHog client and LangChain callback handler."""
    from posthog import Posthog
    from posthog.ai.langchain import CallbackHandler
    return Posthog, CallbackHandler


class CallbackManager:
    """Manages callback handlers for LLM analytics and monitoring."""
    
    def __init__(self):
        self._callbacks: List[BaseCallbackHandler] = []
        self._posthog_callback: Optional[BaseCallbackHandler] = None
        self.posthog_client = None
        self.posthog_public_key = None
        self.posthog_host = None
        self.posthog_enabled = False
    
    def setup_posthog(
        self,
        posthog_public_key: Optional[str] = None,
        posthog_host: Optional[str] = None,
        posthog_client: Optional[Any] = None,
        posthog_callback_options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Set up PostHog LLM analytics callback.
        
        Args:
            posthog_public_key: PostHog public API key
            posthog_host: PostHog ingestion host
            posthog_client: Pre-configured PostHog client
            posthog_callback_options: Additional callback options
            
        Returns:
            True if PostHog was successfully set up, False otherwise
        """
        # Check if PostHog analytics is enabled
        if not self._is_posthog_enabled():
            return False
            
        # Resolve PostHog configuration
        resolved_posthog_key = (
            posthog_public_key
            or os.getenv(POSTHOG_ENV_VARS[0])  # POSTHOG_PUBLIC_KEY
            or os.getenv(POSTHOG_ENV_VARS[1])  # POSTHOG_PROJECT_API_KEY
            or os.getenv(POSTHOG_ENV_VARS[2])  # POSTHOG_API_KEY
        )
        resolved_posthog_host = (
            posthog_host or os.getenv(POSTHOG_ENV_VARS[3]) or DEFAULT_POSTHOG_HOST  # POSTHOG_HOST
        )
        
        # Check if we have a valid key or client
        if not resolved_posthog_key and not posthog_client:
            return False
            
        # Validate key is not empty
        if resolved_posthog_key and not resolved_posthog_key.strip():
            return False
        
        try:
            Posthog, PosthogCallbackHandler = _load_posthog_handler()
        except ImportError as exc:
            raise ImportError(POSTHOG_IMPORT_ERROR) from exc
        
        # Set up PostHog client
        client = posthog_client
        if client is None:
            client = Posthog(resolved_posthog_key, host=resolved_posthog_host)
        
        # Set up callback handler
        callback_options = dict(posthog_callback_options or {})
        if "client" in callback_options:
            raise ValueError(
                "Provide a custom PostHog client via the `posthog_client` parameter instead of `posthog_callback_options`."
            )
        
        callback_kwargs = {**callback_options, "client": client}
        self._posthog_callback = PosthogCallbackHandler(**callback_kwargs)
        self._callbacks.append(self._posthog_callback)
        
        # Store configuration
        self.posthog_client = client
        self.posthog_public_key = resolved_posthog_key or getattr(client, "project_api_key", None)
        self.posthog_host = (
            resolved_posthog_host if resolved_posthog_key and client is not posthog_client else getattr(client, "host", None)
        )
        self.posthog_enabled = True
        
        return True
    
    def _is_posthog_enabled(self) -> bool:
        """Check if PostHog analytics is enabled via environment variable."""
        return os.getenv(POSTHOG_LLM_ANALYTICS_ENV_VAR, "false").lower() in ("true", "1", "yes", "on")
    
    def get_callbacks(self) -> List[BaseCallbackHandler]:
        """Get all configured callback handlers."""
        return self._callbacks.copy()
    
    def has_callbacks(self) -> bool:
        """Check if any callbacks are configured."""
        return len(self._callbacks) > 0


def create_callback_manager(
    posthog_public_key: Optional[str] = None,
    posthog_host: Optional[str] = None,
    posthog_client: Optional[Any] = None,
    posthog_callback_options: Optional[Dict[str, Any]] = None,
) -> CallbackManager:
    """
    Create and configure a callback manager with available analytics providers.
    
    Args:
        posthog_public_key: PostHog public API key
        posthog_host: PostHog ingestion host  
        posthog_client: Pre-configured PostHog client
        posthog_callback_options: Additional PostHog callback options
        
    Returns:
        Configured CallbackManager instance
    """
    manager = CallbackManager()
    
    # Set up PostHog if enabled
    manager.setup_posthog(
        posthog_public_key=posthog_public_key,
        posthog_host=posthog_host,
        posthog_client=posthog_client,
        posthog_callback_options=posthog_callback_options,
    )
    
    return manager
