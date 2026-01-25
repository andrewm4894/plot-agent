"""Dataset picker component for Vibe Plotter."""

from fasthtml.common import *

from vibe_plotter.services.uci_service import FEATURED_DATASETS


def dataset_picker(current_dataset: str = None, has_data: bool = False) -> Div:
    """
    Create the dataset picker component.

    Args:
        current_dataset: Name of the currently loaded dataset.
        has_data: Whether data is currently loaded.

    Returns:
        Dataset picker component.
    """
    return Div(
        H2("1. Choose a Dataset"),
        Div(
            # UCI Dataset Selection
            Div(
                H4("UCI ML Datasets"),
                P("Select a popular dataset from the UCI ML Repository:"),
                Select(
                    Option("Select a dataset...", value="", disabled=True, selected=True),
                    *[
                        Option(
                            f"{d['name']} ({d['instances']} rows, {d['task']})",
                            value=str(d['id'])
                        )
                        for d in FEATURED_DATASETS
                    ],
                    id="uci-dataset-select",
                    name="dataset_id",
                    hx_post="/load-dataset",
                    hx_target="#data-preview",
                    hx_swap="innerHTML",
                    hx_indicator="#loading-indicator",
                ),
                cls="dataset-option"
            ),
            # Custom URL Input
            Div(
                H4("Or Load from URL"),
                P("Paste a link to a CSV file:"),
                Form(
                    Div(
                        Input(
                            type="url",
                            name="url",
                            placeholder="https://example.com/data.csv",
                            id="csv-url-input",
                            cls="url-input"
                        ),
                        Button(
                            "Load CSV",
                            type="submit",
                            cls="btn-load"
                        ),
                        cls="url-input-group"
                    ),
                    hx_post="/load-url",
                    hx_target="#data-preview",
                    hx_swap="innerHTML",
                    hx_indicator="#loading-indicator",
                ),
                cls="dataset-option"
            ),
            cls="dataset-options"
        ),
        # Loading indicator
        Div(
            Span(cls="htmx-indicator", aria_busy="true"),
            " Loading dataset...",
            id="loading-indicator",
            cls="loading"
        ),
        # Data preview area
        Div(
            data_preview_placeholder() if not has_data else None,
            id="data-preview"
        ),
        id="dataset-picker",
        cls="section"
    )


def data_preview_placeholder() -> Div:
    """Create placeholder for data preview."""
    return Div(
        P("No dataset loaded yet. Select a dataset above to get started."),
        cls="preview-placeholder"
    )


def data_preview(df, metadata: dict) -> Div:
    """
    Create data preview component.

    Args:
        df: The loaded DataFrame.
        metadata: Dataset metadata.

    Returns:
        Data preview component.
    """
    # Create a simple HTML table for preview
    preview_rows = min(5, len(df))
    columns = list(df.columns)

    return Div(
        # Dataset info
        Div(
            H4(metadata.get("name", "Dataset")),
            P(metadata.get("abstract", "")[:200] + "..." if len(metadata.get("abstract", "")) > 200 else metadata.get("abstract", "")),
            Div(
                Span(f"{metadata.get('num_instances', len(df))} rows", cls="badge"),
                Span(f"{metadata.get('num_features', len(columns))} columns", cls="badge"),
                Span(metadata.get("task", ""), cls="badge") if metadata.get("task") else None,
                cls="badges"
            ),
            cls="dataset-info"
        ),
        # Column list
        Details(
            Summary(f"Columns ({len(columns)})"),
            Ul(*[Li(col) for col in columns]),
            cls="columns-list"
        ),
        # Data preview table
        Div(
            H5("Preview (first 5 rows)"),
            Table(
                Thead(
                    Tr(*[Th(col) for col in columns[:10]])  # Limit to 10 columns for display
                ),
                Tbody(
                    *[
                        Tr(*[Td(str(df.iloc[i][col])[:50]) for col in columns[:10]])
                        for i in range(preview_rows)
                    ]
                ),
                cls="data-table"
            ),
            P("(Showing first 10 columns)" if len(columns) > 10 else None),
            cls="table-container"
        ),
        # Success indicator
        Div(
            P("Dataset loaded successfully! Now describe the visualization you want below."),
            cls="success-message"
        ),
        cls="data-preview-content"
    )


def dataset_error(error_message: str) -> Div:
    """Create dataset loading error display."""
    return Div(
        P(f"Error loading dataset: {error_message}"),
        cls="error-message"
    )
