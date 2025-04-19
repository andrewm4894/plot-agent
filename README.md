# Plot Agent

[![Tests](https://github.com/andrewm4894/plot-agent/actions/workflows/test.yml/badge.svg)](https://github.com/andrewm4894/plot-agent/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/plot-agent.svg)](https://badge.fury.io/py/plot-agent)

An AI-powered data visualization assistant that helps users create Plotly visualizations in Python.

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

# ensure OPENAI_API_KEY is set and available for langchain

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

## Features

- AI-powered visualization generation
- Support for various Plotly chart types
- Automatic data preprocessing
- Interactive visualization capabilities
- Integration with LangChain for advanced AI capabilities

## Requirements

- Python 3.8 or higher
- Dependencies are automatically installed with the package

## License

This project is licensed under the MIT License - see the LICENSE file for details. 