# Vibe Plotter

A web application showcasing [plot-agent](https://github.com/andrewm4894/plot-agent) for AI-powered data visualization. Built with [FastHTML](https://fastht.ml) and [MonsterUI](https://monsterui.answer.ai/).

## Features

- **UCI Dataset Browser**: Load popular machine learning datasets from the UCI ML Repository
- **CSV URL Support**: Load data from any public CSV URL
- **Natural Language Visualization**: Describe what you want to see in plain English
- **Interactive Charts**: Plotly-powered visualizations with zoom, pan, and hover
- **Export Options**: Download as HTML, PNG, or Python code
- **LLM Analytics**: Optional PostHog integration for tracking LLM usage

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- OpenAI API key or OpenRouter API key

### Installation

```bash
# Clone the repository
git clone https://github.com/andrewm4894/plot-agent.git
cd plot-agent

# Install dependencies
make app-install
```

### Configuration

Create a `.env` file in the project root:

```bash
# LLM Provider (choose one)
OPENAI_API_KEY=sk-...           # For OpenAI directly
# OR
OPENROUTER_API_KEY=sk-or-...    # For OpenRouter (access to multiple models)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1  # Optional, this is the default

# Model selection
LLM_MODEL=gpt-4o-mini           # Or any OpenRouter model like anthropic/claude-3.5-sonnet

# Optional: PostHog LLM Analytics
POSTHOG_ENABLED=true
POSTHOG_API_KEY=phc_...
POSTHOG_HOST=https://us.i.posthog.com
```

### Running Locally

```bash
# Production mode
make app

# Development mode (with auto-reload)
make app-dev
```

Visit http://localhost:8000

## Usage

1. **Load a Dataset**: Select a UCI dataset from the dropdown or enter a CSV URL
2. **Describe Your Visualization**: The chat input is pre-filled with "plot this" - just click send for an automatic visualization, or type a specific request
3. **Iterate**: Ask for modifications like "color by species" or "add a trendline"
4. **Export**: Download as HTML (interactive), PNG (static image), or Python code

## Architecture

```
vibe_plotter/
├── app.py                 # Main FastHTML application
├── config.py              # Configuration management
├── requirements.txt       # App-specific dependencies
└── services/
    ├── agent_service.py   # PlotAgent wrapper
    ├── session_service.py # Session management
    └── uci_service.py     # UCI dataset loading
```

## Deployment

### Render

The app is configured for deployment on [Render](https://render.com) using the `render.yaml` blueprint:

```bash
# Deploy via Render Dashboard
# 1. Connect your GitHub repo
# 2. Select "Blueprint" deployment
# 3. Configure environment variables
```

### Environment Variables for Production

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key |
| `OPENROUTER_API_KEY` | Yes* | OpenRouter API key (alternative to OpenAI) |
| `LLM_MODEL` | No | Model to use (default: gpt-4o-mini) |
| `POSTHOG_ENABLED` | No | Enable PostHog analytics (default: false) |
| `POSTHOG_API_KEY` | No | PostHog project API key |
| `SESSION_SECRET` | No | Secret for session cookies |

*Either `OPENAI_API_KEY` or `OPENROUTER_API_KEY` is required.

## Tech Stack

- **[FastHTML](https://fastht.ml)**: Python web framework with HTMX
- **[MonsterUI](https://monsterui.answer.ai/)**: Tailwind-based UI components for FastHTML
- **[plot-agent](https://github.com/andrewm4894/plot-agent)**: AI-powered Plotly visualization
- **[ucimlrepo](https://github.com/uci-ml-repo/ucimlrepo)**: UCI ML Repository Python API
- **[Plotly](https://plotly.com/python/)**: Interactive visualization library

## License

MIT License - see the [LICENSE](../LICENSE) file for details.
