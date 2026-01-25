"""
Vibe Plotter - A FastHTML app showcasing plot-agent for agentic data visualization.
"""

import os
import uuid
from typing import Optional

from fasthtml.common import *
from starlette.responses import Response

from vibe_plotter.config import config
from vibe_plotter.services.uci_service import DatasetService
from vibe_plotter.services.session_service import session_manager
from vibe_plotter.services.agent_service import AgentService
from vibe_plotter.components.layout import header, footer
from vibe_plotter.components.dataset_picker import (
    dataset_picker,
    data_preview,
    dataset_error,
)
from vibe_plotter.components.chat import (
    chat_interface,
    chat_messages_fragment,
    chat_placeholder,
)
from vibe_plotter.components.plot_display import (
    plot_display,
    plot_content,
    plot_error,
)


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
        // Link to backend session
        window.VIBE_SESSION_ID = '{session_id}';
        posthog.register({{ '$ai_session_id': '{session_id}' }});

        // Track custom events
        window.trackEvent = function(eventName, properties) {{
            posthog.capture(eventName, properties || {{}});
        }};
    """)


# Custom CSS link
custom_css = Link(rel="stylesheet", href="/static/custom.css")

# Plotly JS CDN
plotly_cdn = Script(src="https://cdn.plot.ly/plotly-2.27.0.min.js")

# App headers
app_headers = (
    plotly_cdn,
    custom_css,
)

# Create FastHTML app
app, rt = fast_app(
    hdrs=app_headers,
    pico=True,
    static_path="vibe_plotter/static",
)


def get_session(request) -> tuple[str, any]:
    """Get or create session from request."""
    session_id = request.cookies.get("vibe_session_id")
    if not session_id:
        session_id = str(uuid.uuid4())

    state = session_manager.get_or_create(session_id)
    return session_id, state


@rt("/")
def get(request):
    """Main page."""
    session_id, state = get_session(request)

    has_data = state.df is not None
    has_viz = state.agent and AgentService.has_visualization(state.agent)

    # Get visualization data if available
    viz_data = {}
    if has_viz:
        viz_data = AgentService.get_visualization_data(state.agent)

    response = Titled(
        "Vibe Plotter",
        posthog_script(session_id),
        header(),
        Main(
            dataset_picker(
                current_dataset=state.metadata.get("name") if state.metadata else None,
                has_data=has_data
            ),
            chat_interface(
                chat_history=state.chat_history,
                enabled=has_data
            ),
            plot_display(
                figure=viz_data.get("figure"),
                title=viz_data.get("title"),
                summary=viz_data.get("summary"),
                code=viz_data.get("code"),
            ),
            cls="container"
        ),
        footer(),
    )

    # Set session cookie
    resp = Response(
        content=to_xml(response),
        media_type="text/html"
    )
    resp.set_cookie("vibe_session_id", session_id, max_age=3600, httponly=True)
    return resp


@rt("/load-dataset")
def post(request, dataset_id: int):
    """Load a UCI dataset."""
    session_id, state = get_session(request)

    try:
        # Load the dataset
        df, metadata = DatasetService.load_uci_dataset(dataset_id)

        # Create agent and initialize with data
        agent = AgentService.create_agent(session_id)
        AgentService.initialize_agent_with_df(agent, df)

        # Update session state
        state.df = df
        state.metadata = metadata
        state.agent = agent
        state.chat_history = []

        # Track event
        if config.POSTHOG_ENABLED:
            Script(f"trackEvent('dataset_loaded', {{source: 'uci', dataset_id: {dataset_id}, name: '{metadata.get('name', '')}'}});")

        return data_preview(df, metadata)

    except Exception as e:
        return dataset_error(str(e))


@rt("/load-url")
def post(request, url: str):
    """Load a CSV from URL."""
    session_id, state = get_session(request)

    try:
        # Load the dataset
        df, metadata = DatasetService.load_csv_from_url_sync(url)

        # Create agent and initialize with data
        agent = AgentService.create_agent(session_id)
        AgentService.initialize_agent_with_df(agent, df)

        # Update session state
        state.df = df
        state.metadata = metadata
        state.agent = agent
        state.chat_history = []

        return data_preview(df, metadata)

    except Exception as e:
        return dataset_error(str(e))


@rt("/chat")
def post(request, message: str):
    """Process a chat message."""
    session_id, state = get_session(request)

    if not state.agent:
        return Div(
            P("Please load a dataset first.", cls="error-message"),
        )

    if not message.strip():
        return Div(
            P("Please enter a message.", cls="error-message"),
        )

    try:
        # Process the message
        response = AgentService.process_message_sync(state.agent, message)

        # Add to chat history
        state.add_message("user", message)
        state.add_message("assistant", response)

        # Return both messages for append
        return chat_messages_fragment(message, response)

    except Exception as e:
        return Div(
            P(f"Error: {str(e)}", cls="error-message"),
        )


@rt("/plot-refresh")
def get(request):
    """Refresh the plot display."""
    session_id, state = get_session(request)

    if not state.agent:
        return plot_content()

    viz_data = AgentService.get_visualization_data(state.agent)

    return plot_content(
        figure=viz_data.get("figure"),
        title=viz_data.get("title"),
        summary=viz_data.get("summary"),
        code=viz_data.get("code"),
    )


@rt("/export/{format}")
def get(request, format: str):
    """Export the current figure."""
    session_id, state = get_session(request)

    if not state.agent or not AgentService.has_visualization(state.agent):
        return Response(
            content="No visualization available",
            status_code=404
        )

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
            return Response(
                content="Invalid export format",
                status_code=400
            )

    except Exception as e:
        return Response(
            content=f"Export error: {str(e)}",
            status_code=500
        )


@rt("/health")
def get():
    """Health check endpoint."""
    return {"status": "healthy", "sessions": session_manager.count()}


@rt("/reset")
def post(request):
    """Reset the current session."""
    session_id, state = get_session(request)

    state.df = None
    state.metadata = None
    state.agent = None
    state.chat_history = []

    return RedirectResponse("/", status_code=303)


# Serve static files
@rt("/static/{filepath:path}")
def get(filepath: str):
    """Serve static files."""
    import mimetypes
    from pathlib import Path

    static_dir = Path(__file__).parent / "static"
    file_path = static_dir / filepath

    if not file_path.exists():
        return Response(content="Not found", status_code=404)

    content_type, _ = mimetypes.guess_type(str(file_path))
    with open(file_path, "rb") as f:
        return Response(
            content=f.read(),
            media_type=content_type or "application/octet-stream"
        )


def serve():
    """Run the app with uvicorn."""
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    serve()
