# Plot Agent

[![Tests](https://github.com/andrewm4894/plot-agent/actions/workflows/test.yml/badge.svg)](https://github.com/andrewm4894/plot-agent/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/plot-agent.svg)](https://badge.fury.io/py/plot-agent)

An AI-powered data visualization assistant that helps users create Plotly visualizations in Python.

Built on LangGraph with tool-calling to reliably execute generated Plotly code in a sandbox and keep the current `fig` in sync.

## Installation

You can install the package using pip:

```bash
pip install plot-agent
```

## Usage

See more examples in [/examples/](https://nbviewer.org/github/andrewm4894/plot-agent/tree/main/examples/) (via nbviewer so that can see the charts easily).

Here's a simple minimal example of how to use Plot Agent:

```python
import pandas as pd
from plot_agent.agent import PlotAgent

# ensure OPENAI_API_KEY is set (env or .env); optional debug via PLOT_AGENT_DEBUG=1

# Create a sample dataframe
df = pd.DataFrame({
    'x': [1, 2, 3, 4, 5],
    'y': [10, 20, 30, 40, 50]
})

# Initialize the agent
agent = PlotAgent()

# Set the dataframe
agent.set_df(df)

# Process a visualization request
response = agent.process_message("Create a line plot of x vs y")

# Print generated code
print(agent.generated_code)

# Get fig
fig = agent.get_figure()
fig.show()
```

`agent.generated_code`:

```python
import pandas as pd
import plotly.graph_objects as go

# Creating a line plot of x vs y
# Create a figure object
fig = go.Figure()

# Add a line trace to the figure
fig.add_trace(
    go.Scatter(
        x=df['x'],  # The x values
        y=df['y'],  # The y values
        mode='lines+markers',  # Display both lines and markers
        name='Line Plot',  # Name of the trace
        line=dict(color='blue', width=2)  # Specify line color and width
    )
)

# Adding titles and labels
fig.update_layout(
    title='Line Plot of x vs y',  # Plot title
    xaxis_title='x',  # x-axis label
    yaxis_title='y',  # y-axis label
    template='plotly_white'  # A clean layout
)
```

## How it works

```mermaid
flowchart TD
    A[User message] --> B{LangGraph ReAct Agent}
    subgraph Tools
      T1[execute_plotly_code<br/>- runs code in sandbox<br/>- returns success/fig/error]
      T2[does_fig_exist]
      T3[view_generated_code]
    end
    B -- tool call --> T1
    T1 -- result --> B
    B -- optional --> T2
    B -- optional --> T3
    B --> C[AI response]
    C --> D{Agent wrapper}
    D -- persist messages --> B
    D -- extract code blocks --> E[Sandbox execution]
    E --> F[fig]
    F --> G[get_figure]
```

- The LangGraph agent plans and decides when to call tools.
- The wrapper persists full graph messages between turns and executes any returned code blocks to keep `fig` updated.
- A safe execution environment runs code with an allowlist and a main-thread-only timeout.

## Features

- AI-powered visualization generation
- Support for various Plotly chart types
- Automatic data preprocessing
- Interactive visualization capabilities
- LangGraph-based tool calling and control flow
- Debug logging via `PlotAgent(debug=True)` or `PLOT_AGENT_DEBUG=1`

## Requirements

- Python 3.8 or higher
- Dependencies are automatically installed with the package

## Development

- Run unit tests:

```bash
make test
```

- Execute all example notebooks:

```bash
make run-examples
```

- Execute with debug logs enabled:

```bash
make run-examples-debug
```

- Quick CLI repro that prints evolving code each step:

```bash
make run-example-script
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 