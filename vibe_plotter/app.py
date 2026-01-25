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


def dataset_picker_card(current_dataset: Optional[str] = None):
    """Dataset picker card."""
    dataset_options = [Option(d["name"], value=d["id"]) for d in FEATURED_DATASETS]

    return Card(
        Form(
            Grid(
                Div(
                    Label("UCI Dataset", cls="uk-form-label"),
                    Select(
                        Option("Select a dataset...", value="", selected=True, disabled=True),
                        *dataset_options,
                        id="dataset_id",
                        name="dataset_id",
                        cls="uk-select",
                    ),
                    cls="col-span-2"
                ),
                Div(
                    Button("Load", type="submit", cls=ButtonT.primary),
                    cls="flex items-end"
                ),
                cols=3,
                gap=4,
            ),
            hx_post="/load-dataset",
            hx_target="#data-preview",
            hx_swap="innerHTML",
        ),
        DividerSplit("OR", text_cls=TextPresets.muted_sm),
        Form(
            Grid(
                Div(
                    Label("CSV URL", cls="uk-form-label"),
                    Input(id="url", name="url", placeholder="https://example.com/data.csv", cls="uk-input"),
                    cls="col-span-2"
                ),
                Div(
                    Button("Load URL", type="submit", cls=ButtonT.secondary),
                    cls="flex items-end"
                ),
                cols=3,
                gap=4,
            ),
            hx_post="/load-url",
            hx_target="#data-preview",
            hx_swap="innerHTML",
        ),
        Div(id="data-preview", cls="mt-4"),
        header=Div(H4("Data Source"), P("Load a UCI dataset or provide a CSV URL", cls=TextPresets.muted_sm)),
    )


def data_preview_content(df, metadata: dict):
    """Data preview content."""
    rows = min(5, len(df))
    preview_df = df.head(rows)

    return Div(
        DivFullySpaced(
            Div(
                P(Strong(metadata.get("name", "Dataset")), cls=TextT.lg),
                P(f"{len(df):,} rows, {len(df.columns)} columns", cls=TextPresets.muted_sm),
            ),
            UkIcon("check-circle", cls="text-green-500", height=24, width=24),
        ),
        Div(
            Table(
                Thead(Tr(*[Th(str(col)[:15], cls="text-sm") for col in list(preview_df.columns)[:6]])),
                Tbody(*[
                    Tr(*[Td(str(preview_df.iloc[i, j])[:20], cls="text-sm") for j in range(min(6, len(preview_df.columns)))])
                    for i in range(rows)
                ]),
                cls="uk-table uk-table-small uk-table-striped mt-2"
            ),
            cls="overflow-x-auto"
        ),
        cls="p-4 bg-base-200 rounded-lg"
    )


def data_error_content(error: str):
    """Data error content."""
    return Div(
        DivLAligned(
            UkIcon("alert-circle", cls="text-red-500"),
            P(f"Error: {error}", cls="text-red-500 ml-2"),
        ),
        cls="p-4 bg-red-100 rounded-lg"
    )


def chat_card(chat_history: list, enabled: bool = False):
    """Chat interface card."""
    messages = []
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(
                Div(
                    Div(msg["content"], cls="bg-primary text-primary-content p-3 rounded-lg inline-block max-w-[80%]"),
                    cls="flex justify-end mb-3"
                )
            )
        else:
            messages.append(
                Div(
                    Div(msg["content"], cls="bg-base-200 p-3 rounded-lg inline-block max-w-[80%]"),
                    cls="flex justify-start mb-3"
                )
            )

    if not messages:
        messages = [
            Div(
                P("Describe the visualization you want to create...", cls=TextPresets.muted_sm),
                cls="text-center py-12"
            )
        ]

    return Card(
        Div(
            *messages,
            id="chat-messages",
            cls="h-72 overflow-y-auto p-3 border rounded-lg bg-base-100"
        ),
        Form(
            DivFullySpaced(
                Input(
                    id="message",
                    name="message",
                    placeholder="e.g., Create a scatter plot of sepal length vs petal width" if enabled else "Load a dataset first...",
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
            hx_on__after_request="this.reset(); htmx.trigger('#plot-area', 'refresh');",
            cls="mt-4",
        ),
        header=Div(H4("Chat"), P("Describe your visualization in natural language", cls=TextPresets.muted_sm)),
    )


def chat_message_fragment(user_msg: str, assistant_msg: str):
    """Fragment for new chat messages."""
    return Div(
        Div(
            Div(user_msg, cls="bg-primary text-primary-content p-3 rounded-lg inline-block max-w-[80%]"),
            cls="flex justify-end mb-3"
        ),
        Div(
            Div(assistant_msg, cls="bg-base-200 p-3 rounded-lg inline-block max-w-[80%]"),
            cls="flex justify-start mb-3"
        ),
    )


def plot_card(figure=None, title: str = None, summary: str = None, code: str = None):
    """Plot display card."""
    if figure:
        plot_html = figure.to_html(include_plotlyjs=False, full_html=False, config={"displayModeBar": True})
        content = Div(
            H5(title, cls="mb-2") if title else None,
            P(summary, cls=TextPresets.muted_sm + " mb-4") if summary else None,
            Div(Safe(plot_html), cls="w-full min-h-[400px]"),
            DivFullySpaced(
                Div(),
                Div(
                    A(Button(UkIcon("download", height=14, cls="mr-1"), "HTML", cls=(ButtonT.secondary, "btn-sm")), href="/export/html"),
                    A(Button(UkIcon("image", height=14, cls="mr-1"), "PNG", cls=(ButtonT.secondary, "btn-sm")), href="/export/png"),
                    A(Button(UkIcon("code", height=14, cls="mr-1"), "Code", cls=(ButtonT.secondary, "btn-sm")), href="/export/code"),
                    cls="space-x-2"
                ),
                cls="mt-4"
            ),
        )
    else:
        content = Div(
            DivCentered(
                UkIcon("bar-chart-2", height=64, width=64, cls="opacity-20"),
                P("Your visualization will appear here", cls=TextPresets.muted_sm + " mt-4"),
                cls="py-20"
            ),
        )

    return Card(
        Div(content, id="plot-content"),
        header=Div(H4("Visualization"), P("Interactive Plotly chart", cls=TextPresets.muted_sm)),
        id="plot-area",
        hx_trigger="refresh",
        hx_get="/plot-refresh",
        hx_target="#plot-content",
        hx_swap="innerHTML",
    )


def plot_content_fragment(figure=None, title: str = None, summary: str = None, code: str = None):
    """Fragment for plot content refresh."""
    if figure:
        plot_html = figure.to_html(include_plotlyjs=False, full_html=False, config={"displayModeBar": True})
        return Div(
            H5(title, cls="mb-2") if title else None,
            P(summary, cls=TextPresets.muted_sm + " mb-4") if summary else None,
            Div(Safe(plot_html), cls="w-full min-h-[400px]"),
            DivFullySpaced(
                Div(),
                Div(
                    A(Button(UkIcon("download", height=14, cls="mr-1"), "HTML", cls=(ButtonT.secondary, "btn-sm")), href="/export/html"),
                    A(Button(UkIcon("image", height=14, cls="mr-1"), "PNG", cls=(ButtonT.secondary, "btn-sm")), href="/export/png"),
                    A(Button(UkIcon("code", height=14, cls="mr-1"), "Code", cls=(ButtonT.secondary, "btn-sm")), href="/export/code"),
                    cls="space-x-2"
                ),
                cls="mt-4"
            ),
        )
    else:
        return Div(
            DivCentered(
                UkIcon("bar-chart-2", height=64, width=64, cls="opacity-20"),
                P("Your visualization will appear here", cls=TextPresets.muted_sm + " mt-4"),
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
                P("Create beautiful visualizations with natural language", cls=TextPresets.muted_sm),
                cls="text-center mb-8"
            ),
            Grid(
                Div(
                    dataset_picker_card(
                        current_dataset=state.metadata.get("name") if state.metadata else None
                    ),
                    chat_card(
                        chat_history=state.chat_history,
                        enabled=has_data
                    ),
                    cls="space-y-6"
                ),
                Div(
                    plot_card(
                        figure=viz_data.get("figure"),
                        title=viz_data.get("title"),
                        summary=viz_data.get("summary"),
                        code=viz_data.get("code"),
                    ),
                ),
                cols_lg=2,
                cols_md=1,
                gap=6,
            ),
            Div(
                P("Powered by ", A("plot-agent", href="https://github.com/andrewm4894/plot-agent", cls="underline"), " and ", A("FastHTML", href="https://fastht.ml", cls="underline"), cls=TextPresets.muted_sm),
                cls="text-center mt-12 pb-6"
            ),
            cls=(ContainerT.xl, "py-6"),
        ),
    )


@rt("/load-dataset")
def post(session, dataset_id: int):
    """Load a UCI dataset."""
    session_id, state = get_session_state(session)

    try:
        df, metadata = DatasetService.load_uci_dataset(dataset_id)
        agent = AgentService.create_agent(session_id)
        AgentService.initialize_agent_with_df(agent, df)

        state.df = df
        state.metadata = metadata
        state.agent = agent
        state.chat_history = []

        return data_preview_content(df, metadata)

    except Exception as e:
        return data_error_content(str(e))


@rt("/load-url")
def post(session, url: str):
    """Load a CSV from URL."""
    session_id, state = get_session_state(session)

    try:
        df, metadata = DatasetService.load_csv_from_url_sync(url)
        agent = AgentService.create_agent(session_id)
        AgentService.initialize_agent_with_df(agent, df)

        state.df = df
        state.metadata = metadata
        state.agent = agent
        state.chat_history = []

        return data_preview_content(df, metadata)

    except Exception as e:
        return data_error_content(str(e))


@rt("/chat")
def post(session, message: str):
    """Process a chat message."""
    session_id, state = get_session_state(session)

    if not state.agent:
        return Div(P("Please load a dataset first.", cls="text-red-500 p-2"))

    if not message.strip():
        return Div(P("Please enter a message.", cls="text-red-500 p-2"))

    try:
        response = AgentService.process_message_sync(state.agent, message)
        state.add_message("user", message)
        state.add_message("assistant", response)
        return chat_message_fragment(message, response)

    except Exception as e:
        return Div(P(f"Error: {str(e)}", cls="text-red-500 p-2"))


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
