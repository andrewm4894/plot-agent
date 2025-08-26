from __future__ import annotations

from typing import Optional, TypedDict

from langgraph.graph import MessagesState
from pydantic import BaseModel


class FigState(BaseModel):
    fig_json: Optional[str] = None


class AgentState(TypedDict):
    """Graph state typed with LangGraph channel semantics.

    - messages: conversation history (append-only via MessagesState)
    - fig: latest figure JSON (replace semantics)
    - df_profile: cached dataframe profile for grounding (replace semantics)
    """

    messages: MessagesState
    fig: FigState
    df_profile: Optional[dict]
    # Step budget for the prebuilt ReAct agent loop
    remaining_steps: int

