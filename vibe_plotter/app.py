"""
Vibe Plotter - A FastHTML app showcasing plot-agent for agentic data visualization.
"""

import os
import uuid
from typing import Optional

from fasthtml.common import *
from monsterui.all import *

from vibe_plotter.config import config
from vibe_plotter.services.uci_service import DatasetService, FEATURED_DATASETS
from vibe_plotter.services.session_service import session_manager
from vibe_plotter.services.agent_service import AgentService


# PostHog JavaScript snippet
def posthog_script(session_id: str) -> Script:
    """Generate PostHog tracking script."""
    if not config.POSTHOG_ENABLED or not config.POSTHOG_API_KEY:
        return Script("")

    return Script(f"""
        !function(t,e){{var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){{function g(t,e){{var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){{var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e}},u.people.toString=function(){{return u.toString(1)+".people (stub)"}},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])}}),e.__SV=1)}}(document,window.posthog||[]);
        posthog.init('{config.POSTHOG_API_KEY}', {{
            api_host: '{config.POSTHOG_HOST}',
            person_profiles: 'identified_only',
            capture_pageview: true,
            capture_pageleave: true,
        }});
        window.VIBE_SESSION_ID = '{session_id}';
        posthog.register({{ '$ai_session_id': '{session_id}' }});
        window.trackEvent = function(eventName, properties) {{
            posthog.capture(eventName, properties || {{}});
        }};
    """)


# Plotly JS CDN
plotly_cdn = Script(src="https://cdn.plot.ly/plotly-2.27.0.min.js")

# Create FastHTML app with MonsterUI theme and session support
app, rt = fast_app(
    hdrs=(
        Theme.blue.headers(),
        plotly_cdn,
    ),
    secret_key=os.getenv("SESSION_SECRET", "vibe-plotter-secret-key-change-in-prod"),
)


def get_session_state(session) -> tuple[str, any]:
    """Get or create session state."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]
    state = session_manager.get_or_create(session_id)
    return session_id, state


# === UI Components ===

def navbar():
    """Top navigation bar."""
    return NavBar(
        A("GitHub", href="https://github.com/andrewm4894/plot-agent", target="_blank"),
        brand=DivLAligned(
            UkIcon("bar-chart-2", height=28, width=28),
            H3("Vibe Plotter", cls="ml-2"),
        ),
    )


def settings_panel():
    """Settings panel with data source configuration."""
    dataset_options = [Option(d["name"], value=d["id"]) for d in FEATURED_DATASETS]

    return Details(
        Summary(
            DivFullySpaced(
                DivLAligned(
                    UkIcon("settings", height=20, width=20, cls="mr-2"),
                    Span("Settings & Data Source", cls="font-medium"),
                ),
                UkIcon("chevron-down", height=16, width=16, cls="transition-transform"),
            ),
            cls="cursor-pointer p-4 hover:bg-base-200 rounded-lg list-none"
        ),
        Div(
            Div(
                P("Load a dataset to start creating visualizations", cls=TextPresets.muted_sm + " mb-4"),
                Grid(
                    Form(
                        DivLAligned(
                            Div(
                                Label("UCI Dataset", cls="uk-form-label text-sm"),
                                Select(
                                    Option("Select a dataset...", value="", selected=True, disabled=True),
                                    *dataset_options,
                                    id="dataset_id",
                                    name="dataset_id",
                                    cls="uk-select",
                                ),
                                cls="flex-1"
                            ),
                            Button("Load", type="submit", cls=ButtonT.primary + " ml-2"),
                            cls="items-end"
                        ),
                        hx_post="/load-dataset",
                        hx_target="#data-preview",
                        hx_swap="innerHTML",
                    ),
                    Form(
                        DivLAligned(
                            Div(
                                Label("Or CSV URL", cls="uk-form-label text-sm"),
                                Input(id="url", name="url", placeholder="https://example.com/data.csv", cls="uk-input"),
                                cls="flex-1"
                            ),
                            Button("Load", type="submit", cls=ButtonT.secondary + " ml-2"),
                            cls="items-end"
                        ),
                        hx_post="/load-url",
                        hx_target="#data-preview",
                        hx_swap="innerHTML",
                    ),
                    cols_md=2,
                    cols_sm=1,
                    gap=4,
                ),
            ),
            cls="px-4 pb-4"
        ),
        cls="border rounded-lg bg-base-100",
        open=True,
    )


def data_preview_panel(df=None, metadata: dict = None):
    """Collapsible data preview panel."""
    if df is not None and metadata:
        rows = min(5, len(df))
        preview_df = df.head(rows)

        content = Div(
            DivFullySpaced(
                DivLAligned(
                    UkIcon("check-circle", cls="text-green-500 mr-2", height=20, width=20),
                    Span(Strong(metadata.get("name", "Dataset")), cls="mr-2"),
                    Span(f"({len(df):,} rows, {len(df.columns)} cols)", cls=TextPresets.muted_sm),
                ),
                Button("Reset", cls=ButtonT.ghost + " btn-sm text-red-500", hx_post="/reset"),
            ),
            Div(
                Table(
                    Thead(Tr(*[Th(str(col)[:12], cls="text-xs") for col in list(preview_df.columns)[:8]])),
                    Tbody(*[
                        Tr(*[Td(str(preview_df.iloc[i, j])[:15], cls="text-xs") for j in range(min(8, len(preview_df.columns)))])
                        for i in range(rows)
                    ]),
                    cls="uk-table uk-table-small uk-table-striped"
                ),
                cls="overflow-x-auto mt-3"
            ),
        )
        summary_icon = "database"
        summary_text = f"Data Preview: {metadata.get('name', 'Dataset')}"
        is_open = False
    else:
        content = Div(
            P("No data loaded yet. Use the settings above to load a dataset.", cls=TextPresets.muted_sm + " text-center py-4"),
        )
        summary_icon = "database"
        summary_text = "Data Preview"
        is_open = False

    return Details(
        Summary(
            DivLAligned(
                UkIcon(summary_icon, height=18, width=18, cls="mr-2"),
                Span(summary_text, cls="font-medium text-sm"),
            ),
            cls="cursor-pointer p-3 hover:bg-base-200 rounded-lg list-none"
        ),
        Div(content, cls="px-3 pb-3", id="data-preview-content"),
        cls="border rounded-lg bg-base-100",
        id="data-preview",
        open=is_open,
    )


def data_preview_content(df, metadata: dict):
    """Data preview content for HTMX updates."""
    rows = min(5, len(df))
    preview_df = df.head(rows)

    # Return the full Details element to replace
    return Details(
        Summary(
            DivLAligned(
                UkIcon("database", height=18, width=18, cls="mr-2"),
                Span(f"Data Preview: {metadata.get('name', 'Dataset')}", cls="font-medium text-sm"),
            ),
            cls="cursor-pointer p-3 hover:bg-base-200 rounded-lg list-none"
        ),
        Div(
            DivFullySpaced(
                DivLAligned(
                    UkIcon("check-circle", cls="text-green-500 mr-2", height=20, width=20),
                    Span(Strong(metadata.get("name", "Dataset")), cls="mr-2"),
                    Span(f"({len(df):,} rows, {len(df.columns)} cols)", cls=TextPresets.muted_sm),
                ),
                Button("Reset", cls=ButtonT.ghost + " btn-sm text-red-500", hx_post="/reset"),
            ),
            Div(
                Table(
                    Thead(Tr(*[Th(str(col)[:12], cls="text-xs") for col in list(preview_df.columns)[:8]])),
                    Tbody(*[
                        Tr(*[Td(str(preview_df.iloc[i, j])[:15], cls="text-xs") for j in range(min(8, len(preview_df.columns)))])
                        for i in range(rows)
                    ]),
                    cls="uk-table uk-table-small uk-table-striped"
                ),
                cls="overflow-x-auto mt-3"
            ),
            cls="px-3 pb-3"
        ),
        cls="border rounded-lg bg-base-100",
        id="data-preview",
        open=True,
    )


def data_error_content(error: str):
    """Data error content."""
    return Details(
        Summary(
            DivLAligned(
                UkIcon("alert-circle", height=18, width=18, cls="mr-2 text-red-500"),
                Span("Data Preview: Error", cls="font-medium text-sm text-red-500"),
            ),
            cls="cursor-pointer p-3 hover:bg-base-200 rounded-lg list-none"
        ),
        Div(
            P(f"Error loading data: {error}", cls="text-red-500 text-sm"),
            cls="px-3 pb-3"
        ),
        cls="border border-red-200 rounded-lg bg-red-50",
        id="data-preview",
        open=True,
    )


def chat_panel(chat_history: list, enabled: bool = False, default_message: str = ""):
    """Collapsible chat panel for visualization requests."""
    # Build chat history content
    messages = []
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(
                Div(
                    Div(msg["content"], cls="bg-primary text-primary-content px-3 py-2 rounded-lg inline-block max-w-[85%] text-sm"),
                    cls="flex justify-end mb-2"
                )
            )
        else:
            messages.append(
                Div(
                    Div(msg["content"], cls="bg-base-200 px-3 py-2 rounded-lg inline-block max-w-[85%] text-sm"),
                    cls="flex justify-start mb-2"
                )
            )

    # Chat history section - always include the div so HTMX has a target
    history_section = Div(
        *messages,
        id="chat-messages",
        cls="max-h-48 overflow-y-auto mb-3 border-b pb-3" if messages else "hidden"
    )

    # Default message when dataset is loaded but no chat history
    input_value = default_message if enabled and not chat_history else ""

    return Details(
        Summary(
            DivFullySpaced(
                DivLAligned(
                    UkIcon("message-circle", height=20, width=20, cls="mr-2"),
                    Span("Chat", cls="font-medium"),
                    Span(f"({len(chat_history)} messages)" if chat_history else "", cls=TextPresets.muted_sm + " ml-2") if chat_history else None,
                ),
                UkIcon("chevron-down", height=16, width=16, cls="transition-transform"),
            ),
            cls="cursor-pointer p-4 hover:bg-base-200 rounded-lg list-none"
        ),
        Div(
            history_section,
            Form(
                DivFullySpaced(
                    Input(
                        id="message",
                        name="message",
                        value=input_value,
                        placeholder="Describe your visualization..." if enabled else "Load a dataset first...",
                        cls="uk-input flex-1 mr-2",
                        disabled=not enabled,
                    ),
                    Button(
                        UkIcon("send", height=18),
                        type="submit",
                        cls=ButtonT.primary,
                        disabled=not enabled,
                    ),
                ),
                hx_post="/chat",
                hx_target="#chat-messages",
                hx_swap="beforeend",
                hx_on__after_request="this.reset(); document.getElementById('chat-messages').classList.remove('hidden'); htmx.trigger('#plot-area', 'refresh');",
            ),
            cls="px-4 pb-4",
            id="chat-content",
        ),
        cls="border rounded-lg bg-base-100",
        open=True,  # Keep open by default since it's the main interaction point
    )


def chat_message_fragment(user_msg: str, assistant_msg: str):
    """Fragment for new chat messages."""
    return Div(
        Div(
            Div(user_msg, cls="bg-primary text-primary-content px-4 py-2 rounded-2xl rounded-br-sm inline-block max-w-[85%] text-sm"),
            cls="flex justify-end mb-2"
        ),
        Div(
            Div(assistant_msg, cls="bg-base-200 px-4 py-2 rounded-2xl rounded-bl-sm inline-block max-w-[85%] text-sm"),
            cls="flex justify-start mb-2"
        ),
    )


def plot_panel(figure=None, title: str = None, summary: str = None, code: str = None):
    """Plot display panel at the bottom."""
    if figure:
        plot_html = figure.to_html(include_plotlyjs=False, full_html=False, config={"displayModeBar": True, "responsive": True})
        content = Div(
            Div(
                H5(title, cls="m-0") if title else None,
                P(summary, cls=TextPresets.muted_sm + " mt-1") if summary else None,
                cls="mb-3" if title or summary else None
            ) if title or summary else None,
            Div(Safe(plot_html), cls="w-full", style="min-height: 450px;"),
            DivFullySpaced(
                Div(),
                Div(
                    A(Button(UkIcon("download", height=14, cls="mr-1"), "HTML", cls=(ButtonT.ghost, "btn-sm")), href="/export/html"),
                    A(Button(UkIcon("image", height=14, cls="mr-1"), "PNG", cls=(ButtonT.ghost, "btn-sm")), href="/export/png"),
                    A(Button(UkIcon("code", height=14, cls="mr-1"), "Code", cls=(ButtonT.ghost, "btn-sm")), href="/export/code"),
                    cls="space-x-1"
                ),
                cls="mt-3 pt-3 border-t"
            ),
        )
    else:
        content = Div(
            DivCentered(
                UkIcon("bar-chart-2", height=80, width=80, cls="opacity-10"),
                P("Your visualization will appear here", cls=TextPresets.muted_sm + " mt-4"),
                P("Load a dataset and describe what you want to see", cls=TextPresets.muted_sm),
                cls="py-20"
            ),
        )

    return Card(
        Div(content, id="plot-content"),
        header=DivLAligned(
            UkIcon("trending-up", height=20, width=20, cls="mr-2"),
            H5("Visualization", cls="m-0"),
        ),
        id="plot-area",
        hx_trigger="refresh",
        hx_get="/plot-refresh",
        hx_target="#plot-content",
        hx_swap="innerHTML",
        body_cls="p-4",
    )


def plot_content_fragment(figure=None, title: str = None, summary: str = None, code: str = None):
    """Fragment for plot content refresh."""
    if figure:
        plot_html = figure.to_html(include_plotlyjs=False, full_html=False, config={"displayModeBar": True, "responsive": True})
        return Div(
            Div(
                H5(title, cls="m-0") if title else None,
                P(summary, cls=TextPresets.muted_sm + " mt-1") if summary else None,
                cls="mb-3" if title or summary else None
            ) if title or summary else None,
            Div(Safe(plot_html), cls="w-full", style="min-height: 450px;"),
            DivFullySpaced(
                Div(),
                Div(
                    A(Button(UkIcon("download", height=14, cls="mr-1"), "HTML", cls=(ButtonT.ghost, "btn-sm")), href="/export/html"),
                    A(Button(UkIcon("image", height=14, cls="mr-1"), "PNG", cls=(ButtonT.ghost, "btn-sm")), href="/export/png"),
                    A(Button(UkIcon("code", height=14, cls="mr-1"), "Code", cls=(ButtonT.ghost, "btn-sm")), href="/export/code"),
                    cls="space-x-1"
                ),
                cls="mt-3 pt-3 border-t"
            ),
        )
    else:
        return Div(
            DivCentered(
                UkIcon("bar-chart-2", height=80, width=80, cls="opacity-10"),
                P("Your visualization will appear here", cls=TextPresets.muted_sm + " mt-4"),
                P("Load a dataset and describe what you want to see", cls=TextPresets.muted_sm),
                cls="py-20"
            ),
        )


# === Routes ===

@rt("/")
def get(session):
    """Main page."""
    session_id, state = get_session_state(session)

    has_data = state.df is not None
    has_viz = state.agent and AgentService.has_visualization(state.agent)

    viz_data = {}
    if has_viz:
        viz_data = AgentService.get_visualization_data(state.agent)

    return (
        Title("Vibe Plotter - AI-Powered Data Visualization"),
        posthog_script(session_id),
        Container(
            navbar(),
            Div(
                # Settings & Data Source (collapsible)
                settings_panel(),

                # Data Preview (collapsible)
                data_preview_panel(
                    df=state.df,
                    metadata=state.metadata,
                ),

                # Chat Panel
                chat_panel(
                    chat_history=state.chat_history,
                    enabled=has_data,
                    default_message="plot this" if has_data and not state.chat_history else "",
                ),

                # Visualization (at bottom)
                plot_panel(
                    figure=viz_data.get("figure"),
                    title=viz_data.get("title"),
                    summary=viz_data.get("summary"),
                    code=viz_data.get("code"),
                ),

                cls="space-y-4"
            ),
            Div(
                P("Powered by ", A("plot-agent", href="https://github.com/andrewm4894/plot-agent", cls="underline"), " and ", A("FastHTML", href="https://fastht.ml", cls="underline"), cls=TextPresets.muted_sm),
                cls="text-center mt-8 pb-4"
            ),
            cls=(ContainerT.lg, "py-4"),
        ),
    )


@rt("/load-dataset")
def post(session, dataset_id: int):
    """Load a UCI dataset."""
    from starlette.responses import Response

    session_id, state = get_session_state(session)

    try:
        df, metadata = DatasetService.load_uci_dataset(dataset_id)
        agent = AgentService.create_agent(session_id)
        AgentService.initialize_agent_with_df(agent, df)

        state.df = df
        state.metadata = metadata
        state.agent = agent
        state.chat_history = []

        # Use HX-Redirect header to tell HTMX to redirect
        return Response(content="", headers={"HX-Redirect": "/"})

    except Exception as e:
        return data_error_content(str(e))


@rt("/load-url")
def post(session, url: str):
    """Load a CSV from URL."""
    from starlette.responses import Response

    session_id, state = get_session_state(session)

    try:
        df, metadata = DatasetService.load_csv_from_url_sync(url)
        agent = AgentService.create_agent(session_id)
        AgentService.initialize_agent_with_df(agent, df)

        state.df = df
        state.metadata = metadata
        state.agent = agent
        state.chat_history = []

        # Use HX-Redirect header to tell HTMX to redirect
        return Response(content="", headers={"HX-Redirect": "/"})

    except Exception as e:
        return data_error_content(str(e))


@rt("/chat")
def post(session, message: str):
    """Process a chat message."""
    session_id, state = get_session_state(session)

    if not state.agent:
        return Div(P("Please load a dataset first.", cls="text-red-500 text-sm p-2"))

    if not message.strip():
        return Div(P("Please enter a message.", cls="text-red-500 text-sm p-2"))

    try:
        response = AgentService.process_message_sync(state.agent, message)
        state.add_message("user", message)
        state.add_message("assistant", response)
        return chat_message_fragment(message, response)

    except Exception as e:
        return Div(P(f"Error: {str(e)}", cls="text-red-500 text-sm p-2"))


@rt("/plot-refresh")
def get(session):
    """Refresh the plot display."""
    session_id, state = get_session_state(session)

    if not state.agent:
        return plot_content_fragment()

    viz_data = AgentService.get_visualization_data(state.agent)

    return plot_content_fragment(
        figure=viz_data.get("figure"),
        title=viz_data.get("title"),
        summary=viz_data.get("summary"),
        code=viz_data.get("code"),
    )


@rt("/export/{format}")
def get(session, format: str):
    """Export the current figure."""
    from starlette.responses import Response

    session_id, state = get_session_state(session)

    if not state.agent or not AgentService.has_visualization(state.agent):
        return Response(content="No visualization available", status_code=404)

    try:
        if format == "html":
            content = state.agent.export_html()
            return Response(
                content=content,
                media_type="text/html",
                headers={"Content-Disposition": "attachment; filename=plot.html"}
            )
        elif format == "png":
            content = state.agent.export_png()
            return Response(
                content=content,
                media_type="image/png",
                headers={"Content-Disposition": "attachment; filename=plot.png"}
            )
        elif format == "json":
            content = state.agent.export_json()
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=plot.json"}
            )
        elif format == "code":
            content = state.agent.export_code()
            return Response(
                content=content,
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=plot.py"}
            )
        else:
            return Response(content="Invalid export format", status_code=400)

    except Exception as e:
        return Response(content=f"Export error: {str(e)}", status_code=500)


@rt("/health")
def get():
    """Health check endpoint."""
    return {"status": "healthy", "sessions": session_manager.count()}


@rt("/reset")
def post(session):
    """Reset the current session."""
    session_id, state = get_session_state(session)
    state.df = None
    state.metadata = None
    state.agent = None
    state.chat_history = []
    return RedirectResponse("/", status_code=303)


def serve():
    """Run the app with uvicorn."""
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    serve()
