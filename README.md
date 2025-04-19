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

Here's a simple example of how to use Plot Agent:

```python
import pandas as pd
from plot_agent.plotly_agent import PlotlyAgent


# Create a sample dataframe
df = pd.DataFrame({
    'x': [1, 2, 3, 4, 5],
    'y': [10, 20, 30, 40, 50]
})

# Initialize the agent
agent = PlotlyAgent()

# Set the dataframe
agent.set_df(df)

# Process a visualization request
response = agent.process_message("Create a line plot of x vs y")
fig = agent.get_figure()
fig.show()
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