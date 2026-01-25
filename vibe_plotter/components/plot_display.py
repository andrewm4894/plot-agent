"""Plot display component for Vibe Plotter."""

from fasthtml.common import *
from typing import Optional

# Try to import fh_plotly for Plotly rendering
try:
    from fh_plotly import plotly2fasthtml
    FH_PLOTLY_AVAILABLE = True
except ImportError:
    FH_PLOTLY_AVAILABLE = False


def plot_display(
    figure=None,
    title: str = None,
    summary: str = None,
    code: str = None,
    show_code: bool = False
) -> Div:
    """
    Create the plot display component.

    Args:
        figure: Plotly figure object.
        title: Plot title.
        summary: Plot summary/insights.
        code: Generated Python code.
        show_code: Whether to show the code by default.

    Returns:
        Plot display component.
    """
    return Div(
        H2("3. Your Visualization"),
        Div(
            plot_content(figure, title, summary, code, show_code),
            id="plot-content",
            hx_get="/plot-refresh",
            hx_trigger="refresh from:body",
            hx_swap="innerHTML"
        ),
        id="plot-display",
        cls="section"
    )


def plot_content(
    figure=None,
    title: str = None,
    summary: str = None,
    code: str = None,
    show_code: bool = False
) -> Div:
    """
    Create the plot content (for HTMX refresh).

    Args:
        figure: Plotly figure object.
        title: Plot title.
        summary: Plot summary/insights.
        code: Generated Python code.
        show_code: Whether to show the code by default.

    Returns:
        Plot content component.
    """
    if figure is None:
        return plot_placeholder()

    content = []

    # Title
    if title:
        content.append(H3(title, cls="plot-title"))

    # Summary/insights
    if summary:
        content.append(
            Div(
                P(summary),
                cls="plot-summary"
            )
        )

    # Plot figure
    if FH_PLOTLY_AVAILABLE:
        content.append(
            Div(
                plotly2fasthtml(figure),
                cls="plot-container"
            )
        )
    else:
        # Fallback: render as HTML iframe
        html_content = figure.to_html(full_html=False, include_plotlyjs='cdn')
        content.append(
            Div(
                NotStr(html_content),
                cls="plot-container"
            )
        )

    # Export buttons
    content.append(export_buttons())

    # Code viewer (collapsible)
    if code:
        content.append(
            Details(
                Summary("View Generated Code"),
                Pre(Code(code, cls="language-python")),
                open=show_code,
                cls="code-viewer"
            )
        )

    return Div(*content, cls="plot-content-inner")


def plot_placeholder() -> Div:
    """Create placeholder for when no plot exists."""
    return Div(
        Div(
            P("No visualization yet."),
            P("Load a dataset and describe what you want to see!"),
            cls="placeholder-content"
        ),
        cls="plot-placeholder"
    )


def export_buttons() -> Div:
    """Create export buttons component."""
    return Div(
        A(
            "Download HTML",
            href="/export/html",
            cls="btn btn-export",
            download="plot.html"
        ),
        A(
            "Download PNG",
            href="/export/png",
            cls="btn btn-export",
            download="plot.png"
        ),
        A(
            "Download Code",
            href="/export/code",
            cls="btn btn-export",
            download="plot.py"
        ),
        A(
            "Download JSON",
            href="/export/json",
            cls="btn btn-export",
            download="plot.json"
        ),
        cls="export-buttons"
    )


def plot_error(error_message: str) -> Div:
    """Create plot error display."""
    return Div(
        P(f"Error creating visualization: {error_message}"),
        cls="error-message"
    )
