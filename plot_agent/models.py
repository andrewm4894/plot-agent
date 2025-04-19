from pydantic import BaseModel, Field


# Define input schemas for the tools
class PlotDescriptionInput(BaseModel):
    plot_description: str = Field(
        ..., description="Description of the plot the user wants to create"
    )


class GeneratedCodeInput(BaseModel):
    generated_code: str = Field(
        ..., description="Python code that creates a Plotly figure"
    )


class DoesFigExistInput(BaseModel):
    """Model indicating that the does_fig_exist function takes no arguments."""

    pass


class ViewGeneratedCodeInput(BaseModel):
    """Model indicating that the view_generated_code function takes no arguments."""

    pass