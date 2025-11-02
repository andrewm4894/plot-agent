"""Tests for the view_plot_image functionality."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, mock_open
import tempfile
import base64

from plot_agent.models import ViewPlotImageInput
from plot_agent.execution import PlotAgentExecutionEnvironment


def test_view_plot_image_input_model():
    """Test that ViewPlotImageInput model exists and works correctly."""
    # Should accept no arguments
    input_model = ViewPlotImageInput()
    assert input_model is not None


def test_view_plot_image_method_exists():
    """Test that view_plot_image method exists in PlotAgent class."""
    from plot_agent.agent import PlotAgent
    
    # Check method exists without initializing (to avoid API key requirement)
    assert hasattr(PlotAgent, 'view_plot_image')
    assert callable(getattr(PlotAgent, 'view_plot_image'))


def test_view_plot_image_no_execution_env():
    """Test view_plot_image behavior when no execution environment exists."""
    from plot_agent.agent import PlotAgent
    
    # Create a mock agent with no execution environment
    mock_agent = Mock(spec=PlotAgent)
    mock_agent.execution_env = None
    
    # Call the actual method
    result = PlotAgent.view_plot_image(mock_agent)
    
    expected = "No execution environment has been initialized. Please set a dataframe first."
    assert result == expected


def test_view_plot_image_no_figure():
    """Test view_plot_image behavior when no figure exists."""
    from plot_agent.agent import PlotAgent
    
    # Create a mock execution environment with no figure
    mock_execution_env = Mock()
    mock_execution_env.fig = None
    
    mock_agent = Mock(spec=PlotAgent)
    mock_agent.execution_env = mock_execution_env
    
    # Call the actual method
    result = PlotAgent.view_plot_image(mock_agent)
    
    expected = "No figure has been created yet. Please execute code to create a figure first."
    assert result == expected


@patch('tempfile.NamedTemporaryFile')
@patch('builtins.open', new_callable=mock_open)
def test_view_plot_image_png_success(mock_file, mock_temp):
    """Test successful PNG export with vision analysis fallback."""
    from plot_agent.agent import PlotAgent
    
    # Mock temporary file
    mock_temp.return_value.__enter__.return_value.name = '/tmp/test.png'
    
    # Mock figure with successful to_image
    mock_fig = Mock()
    test_image_bytes = b'fake_png_data'
    mock_fig.to_image.return_value = test_image_bytes
    
    # Mock execution environment
    mock_execution_env = Mock()
    mock_execution_env.fig = mock_fig
    
    mock_agent = Mock(spec=PlotAgent)
    mock_agent.execution_env = mock_execution_env
    mock_agent.debug = False  # Add debug attribute
    mock_agent._logger = Mock()  # Add logger attribute
    
    # Call the actual method
    result = PlotAgent.view_plot_image(mock_agent)
    
    # Verify figure.to_image was called with correct parameters
    mock_fig.to_image.assert_called_once_with(format="png", width=800, height=600, scale=2)
    
    # Verify file was written (check that it was called with the right parameters)
    assert mock_file.call_count >= 1
    assert any(call[0] == ('/tmp/test.png', 'wb') for call in mock_file.call_args_list)
    mock_file.return_value.__enter__.return_value.write.assert_called_with(test_image_bytes)
    
    # Check result contains expected fallback information (vision will fail without proper mocking)
    assert ("Vision analysis failed" in result or "VISUAL ANALYSIS RESULTS" in result)
    assert "/tmp/test.png" in result
    assert "PNG (800x600, scale=2)" in result
    assert str(len(test_image_bytes)) in result


@patch('tempfile.NamedTemporaryFile')
@patch('builtins.open', new_callable=mock_open)
def test_view_plot_image_png_fallback_to_html(mock_file, mock_temp):
    """Test fallback to HTML when PNG export fails."""
    from plot_agent.agent import PlotAgent
    
    # Mock temporary file
    mock_temp.return_value.__enter__.return_value.name = '/tmp/test.png'
    
    # Mock figure with failing to_image but working to_html
    mock_fig = Mock()
    mock_fig.to_image.side_effect = Exception("Chrome not found")
    mock_fig.to_html.return_value = "<html>test plot</html>"
    
    # Mock execution environment
    mock_execution_env = Mock()
    mock_execution_env.fig = mock_fig
    
    mock_agent = Mock(spec=PlotAgent)
    mock_agent.execution_env = mock_execution_env
    
    # Call the actual method
    result = PlotAgent.view_plot_image(mock_agent)
    
    # Verify PNG was attempted first
    mock_fig.to_image.assert_called_once_with(format="png", width=800, height=600, scale=2)
    
    # Verify HTML fallback was used
    mock_fig.to_html.assert_called_once()
    mock_file.assert_called_once_with('/tmp/test.html', 'w')
    mock_file.return_value.__enter__.return_value.write.assert_called_once_with("<html>test plot</html>")
    
    # Check result contains expected fallback information (updated messages)
    assert "PNG export failed" in result
    assert "Chrome not found" in result
    assert "/tmp/test.html" in result
    assert "HTML" in result
    assert "kaleido" in result


def test_view_plot_image_with_real_execution_environment():
    """Test view_plot_image with a real execution environment and figure."""
    # Create a real dataframe and execution environment
    df = pd.DataFrame({
        'x': range(5),
        'y': np.random.randint(1, 10, 5),
        'category': ['A', 'B', 'A', 'B', 'A']
    })
    
    exec_env = PlotAgentExecutionEnvironment(df)
    
    # Execute code to create a figure
    code = """
import plotly.express as px
fig = px.scatter(df, x='x', y='y', color='category', title='Test Plot')
plot_title = "Test Scatter Plot"
plot_summary = "A test scatter plot"
"""
    
    result = exec_env.execute_code(code)
    assert result['success'] == True
    assert exec_env.fig is not None
    
    # Create a mock agent with this execution environment
    from plot_agent.agent import PlotAgent
    mock_agent = Mock(spec=PlotAgent)
    mock_agent.execution_env = exec_env
    mock_agent.debug = False  # Add debug attribute
    mock_agent._logger = Mock()  # Add logger attribute
    
    # Call view_plot_image - this will likely fall back to HTML due to missing Chrome
    result = PlotAgent.view_plot_image(mock_agent)
    
    # Should not be an error message about missing execution env or figure
    assert "No execution environment" not in result
    assert "No figure has been created" not in result
    
    # Should either succeed with PNG or fall back to HTML
    assert ("Plot image saved successfully!" in result or 
            "Plot saved as HTML" in result or
            "Error saving plot image:" in result)


def test_view_plot_image_integration_with_agent_tools():
    """Test that view_plot_image is properly integrated as a tool."""
    from plot_agent.agent import PlotAgent
    from plot_agent.models import ViewPlotImageInput
    
    # Check that ViewPlotImageInput is imported in agent.py
    assert hasattr(PlotAgent, 'view_plot_image')
    
    # Check that ViewPlotImageInput model works
    input_model = ViewPlotImageInput()
    assert input_model is not None
    
    # The tool should be available in the agent's tool list when initialized
    # (We can't test this without an API key, but we can verify the method exists)
    assert callable(getattr(PlotAgent, 'view_plot_image'))


@patch('tempfile.NamedTemporaryFile')
@patch('builtins.open', new_callable=mock_open)
@patch('plot_agent.agent.ChatOpenAI')
def test_multimodal_vision_analysis(mock_openai_class, mock_file, mock_temp):
    """Test the complete multimodal vision analysis functionality."""
    from plot_agent.agent import PlotAgent
    
    # Mock temporary file
    mock_temp.return_value.__enter__.return_value.name = '/tmp/test.png'
    
    # Mock figure with successful to_image
    mock_fig = Mock()
    test_image_bytes = b'fake_png_data_for_vision_test'
    mock_fig.to_image.return_value = test_image_bytes
    
    # Mock execution environment
    mock_execution_env = Mock()
    mock_execution_env.fig = mock_fig
    
    mock_agent = Mock(spec=PlotAgent)
    mock_agent.execution_env = mock_execution_env
    mock_agent.debug = False
    mock_agent._logger = Mock()
    
    # Mock vision LLM response
    mock_response = Mock()
    mock_response.content = "I can see the plot has good color contrast and clear labels."
    mock_openai_instance = Mock()
    mock_openai_instance.invoke.return_value = mock_response
    mock_openai_class.return_value = mock_openai_instance
    
    # Call the actual method
    result = PlotAgent.view_plot_image(mock_agent)
    
    # Verify PNG export was attempted
    mock_fig.to_image.assert_called_once_with(format="png", width=800, height=600, scale=2)
    
    # Verify vision LLM was created with correct parameters
    mock_openai_class.assert_called_once_with(
        model="gpt-4o",
        temperature=0.1,
        timeout=30,
        max_retries=1
    )
    
    # Verify multimodal message was sent
    mock_openai_instance.invoke.assert_called_once()
    call_args = mock_openai_instance.invoke.call_args[0][0]
    
    # Check message structure
    assert len(call_args) == 1
    message = call_args[0]
    assert hasattr(message, 'content')
    assert isinstance(message.content, list)
    assert len(message.content) == 2
    
    # Check text and image components
    text_part = message.content[0]
    image_part = message.content[1]
    assert text_part["type"] == "text"
    assert image_part["type"] == "image_url"
    assert "data:image/png;base64," in image_part["image_url"]["url"]
    
    # Check result contains vision analysis
    assert "🔍 **VISUAL ANALYSIS RESULTS**" in result
    assert "I can see the plot has good color contrast" in result
    assert "Agent can see the plot!" in result