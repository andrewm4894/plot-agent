"""Chat interface component for Vibe Plotter."""

from fasthtml.common import *
from typing import Optional


def chat_interface(
    chat_history: list = None,
    enabled: bool = False,
    is_processing: bool = False
) -> Div:
    """
    Create the chat interface component.

    Args:
        chat_history: List of chat messages.
        enabled: Whether chat is enabled (data loaded).
        is_processing: Whether a message is being processed.

    Returns:
        Chat interface component.
    """
    chat_history = chat_history or []

    return Div(
        H2("2. Describe Your Visualization"),
        # Chat history display
        Div(
            *[chat_message(msg) for msg in chat_history] if chat_history else [
                chat_placeholder(enabled)
            ],
            id="chat-messages",
            cls="chat-messages"
        ),
        # Chat input form
        Form(
            Div(
                Textarea(
                    name="message",
                    placeholder="Describe the visualization you want... e.g., 'Create a scatter plot of sepal length vs sepal width, colored by species'" if enabled else "Load a dataset first to start chatting",
                    id="chat-input",
                    rows="3",
                    disabled=not enabled,
                    cls="chat-textarea"
                ),
                Button(
                    "Send" if not is_processing else "Processing...",
                    type="submit",
                    disabled=not enabled or is_processing,
                    cls="btn-send",
                    id="send-btn"
                ),
                cls="chat-input-group"
            ),
            hx_post="/chat",
            hx_target="#chat-messages",
            hx_swap="beforeend",
            hx_indicator="#chat-loading",
            hx_on__after_request="this.reset(); htmx.trigger('#plot-display', 'refresh');",
            id="chat-form"
        ),
        # Loading indicator for chat
        Div(
            Span(cls="htmx-indicator", aria_busy="true"),
            " Generating visualization...",
            id="chat-loading",
            cls="loading"
        ),
        id="chat-interface",
        cls="section"
    )


def chat_placeholder(enabled: bool = False) -> Div:
    """Create placeholder for empty chat."""
    if enabled:
        return Div(
            P("No messages yet. Describe the visualization you want to create!"),
            P("Examples:", cls="examples-label"),
            Ul(
                Li("Create a bar chart showing the count of each species"),
                Li("Make a scatter plot of petal length vs petal width"),
                Li("Show a correlation heatmap of all numeric columns"),
                Li("Create a histogram of sepal length with 20 bins"),
            ),
            cls="chat-placeholder"
        )
    else:
        return Div(
            P("Please load a dataset above to start creating visualizations."),
            cls="chat-placeholder disabled"
        )


def chat_message(msg: dict) -> Div:
    """
    Create a single chat message component.

    Args:
        msg: Message dict with 'role' and 'content' keys.

    Returns:
        Chat message component.
    """
    role = msg.get("role", "user")
    content = msg.get("content", "")

    role_label = "You" if role == "user" else "Vibe Plotter"
    role_class = "user-message" if role == "user" else "assistant-message"

    return Div(
        Div(
            Strong(role_label),
            cls="message-header"
        ),
        Div(
            P(content),
            cls="message-content"
        ),
        cls=f"chat-message {role_class}"
    )


def chat_history(messages: list) -> Div:
    """
    Create chat history display.

    Args:
        messages: List of message dicts.

    Returns:
        Chat history component.
    """
    return Div(
        *[chat_message(msg) for msg in messages],
        id="chat-messages",
        cls="chat-messages"
    )


def user_message_display(content: str) -> Div:
    """Create a user message display (for HTMX swap)."""
    return chat_message({"role": "user", "content": content})


def assistant_message_display(content: str) -> Div:
    """Create an assistant message display (for HTMX swap)."""
    return chat_message({"role": "assistant", "content": content})


def chat_messages_fragment(user_content: str, assistant_content: str) -> Div:
    """
    Create a fragment with both user and assistant messages.

    Args:
        user_content: User's message content.
        assistant_content: Assistant's response content.

    Returns:
        Fragment with both messages.
    """
    return Div(
        user_message_display(user_content),
        assistant_message_display(assistant_content),
    )
