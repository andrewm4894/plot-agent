"""
This module contains the models for the PlotAgent.
"""

from pydantic import BaseModel, Field


class PlotDescriptionInput(BaseModel):
    """Model indicating that the plot_description function takes a plot_description argument."""

    plot_description: str = Field(
        ..., description="Description of the plot the user wants to create"
    )


class GeneratedCodeInput(BaseModel):
    """Model indicating that the generated_code function takes a generated_code argument."""

    generated_code: str = Field(
        ..., description="Python code that creates a Plotly figure"
    )


class DoesFigExistInput(BaseModel):
    """Model indicating that the does_fig_exist function takes no arguments."""

    pass


class ViewGeneratedCodeInput(BaseModel):
    """Model indicating that the view_generated_code function takes no arguments."""

    pass
