"""Session management service for Vibe Plotter."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import threading
import uuid

import pandas as pd

from plot_agent.agent import PlotAgent


@dataclass
class SessionState:
    """State for a single user session."""

    session_id: str
    df: Optional[pd.DataFrame] = None
    metadata: Optional[dict] = None
    agent: Optional[PlotAgent] = None
    chat_history: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)

    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed = datetime.utcnow()

    def add_message(self, role: str, content: str) -> None:
        """Add a message to chat history."""
        self.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def clear_chat(self) -> None:
        """Clear chat history and reset agent conversation."""
        self.chat_history = []
        if self.agent:
            self.agent.reset_conversation()


class SessionManager:
    """Thread-safe session manager with TTL cleanup."""

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize session manager.

        Args:
            ttl_minutes: Time-to-live for sessions in minutes.
        """
        self._sessions: dict[str, SessionState] = {}
        self._lock = threading.Lock()
        self._ttl = timedelta(minutes=ttl_minutes)

    def get(self, session_id: str) -> Optional[SessionState]:
        """
        Get a session by ID.

        Args:
            session_id: The session identifier.

        Returns:
            SessionState if found, None otherwise.
        """
        with self._lock:
            state = self._sessions.get(session_id)
            if state:
                state.touch()
            return state

    def get_or_create(self, session_id: Optional[str] = None) -> SessionState:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Optional session ID. If None, generates a new one.

        Returns:
            SessionState for the session.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        with self._lock:
            if session_id in self._sessions:
                state = self._sessions[session_id]
                state.touch()
                return state

            state = SessionState(session_id=session_id)
            self._sessions[session_id] = state
            return state

    def create(self, session_id: Optional[str] = None) -> SessionState:
        """
        Create a new session.

        Args:
            session_id: Optional session ID. If None, generates a new one.

        Returns:
            New SessionState.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        with self._lock:
            state = SessionState(session_id=session_id)
            self._sessions[session_id] = state
            return state

    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: The session identifier.

        Returns:
            True if session was deleted, False if not found.
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def cleanup_expired(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of sessions removed.
        """
        now = datetime.utcnow()
        with self._lock:
            expired = [
                sid for sid, state in self._sessions.items()
                if now - state.last_accessed > self._ttl
            ]
            for sid in expired:
                del self._sessions[sid]
            return len(expired)

    def count(self) -> int:
        """Return the number of active sessions."""
        with self._lock:
            return len(self._sessions)


# Global session manager instance
session_manager = SessionManager(ttl_minutes=60)
