"""Layout components for Vibe Plotter."""

from fasthtml.common import *


def header() -> Header:
    """Create the page header."""
    return Header(
        Div(
            H1("Vibe Plotter", cls="title"),
            P("AI-powered data visualization with natural language", cls="subtitle"),
            cls="header-content"
        ),
        cls="site-header"
    )


def footer() -> Footer:
    """Create the page footer."""
    return Footer(
        Div(
            P(
                "Powered by ",
                A("plot-agent", href="https://github.com/andrewm4894/plot-agent", target="_blank"),
                " and ",
                A("PostHog", href="https://posthog.com", target="_blank"),
            ),
            cls="footer-content"
        ),
        cls="site-footer"
    )


def page_layout(*content, title: str = "Vibe Plotter") -> Titled:
    """
    Create the full page layout.

    Args:
        *content: Page content elements.
        title: Page title.

    Returns:
        Complete page structure.
    """
    return Titled(
        title,
        header(),
        Main(
            *content,
            cls="container"
        ),
        footer(),
    )


def section(title: str, *content, section_id: str = None, cls: str = "") -> Section:
    """
    Create a section with a title.

    Args:
        title: Section title.
        *content: Section content.
        section_id: Optional section ID.
        cls: Additional CSS classes.

    Returns:
        Section element.
    """
    attrs = {"cls": f"section {cls}".strip()}
    if section_id:
        attrs["id"] = section_id

    return Section(
        H2(title),
        *content,
        **attrs
    )


def card(title: str, *content, card_id: str = None) -> Article:
    """
    Create a card component.

    Args:
        title: Card title.
        *content: Card content.
        card_id: Optional card ID.

    Returns:
        Article element styled as a card.
    """
    attrs = {"cls": "card"}
    if card_id:
        attrs["id"] = card_id

    return Article(
        Header(H3(title)),
        *content,
        **attrs
    )


def loading_indicator(text: str = "Loading...") -> Div:
    """Create a loading indicator."""
    return Div(
        Span(cls="spinner", aria_busy="true"),
        Span(text),
        cls="loading-indicator"
    )


def error_message(message: str) -> Div:
    """Create an error message display."""
    return Div(
        P(message),
        cls="error-message",
        role="alert"
    )


def success_message(message: str) -> Div:
    """Create a success message display."""
    return Div(
        P(message),
        cls="success-message",
        role="status"
    )
