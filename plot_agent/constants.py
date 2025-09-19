"""
Constants and default values for the PlotAgent package.
"""

# Agent Configuration Defaults
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_VERBOSE = True
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_EARLY_STOPPING_METHOD = "force"
DEFAULT_HANDLE_PARSING_ERRORS = True
DEFAULT_DEBUG = False

# LLM Configuration Defaults
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_LLM_TIMEOUT = 60
DEFAULT_LLM_MAX_RETRIES = 1

# Execution Environment Constants
DEFAULT_TIMEOUT_SECONDS = 60

# Allowed modules for code execution
ALLOWED_MODULES = {
    "pandas",
    "numpy", 
    "matplotlib",
    "plotly",
    "sklearn",
    "scipy",
}

# PostHog Configuration
DEFAULT_POSTHOG_HOST = "https://us.i.posthog.com"
POSTHOG_ENV_VARS = [
    "POSTHOG_PUBLIC_KEY",
    "POSTHOG_PROJECT_API_KEY", 
    "POSTHOG_API_KEY",
    "POSTHOG_HOST",
]
POSTHOG_LLM_ANALYTICS_ENV_VAR = "POSTHOG_LLM_ANALYTICS"

# Environment Variables
OPENAI_API_KEY_ENV_VAR = "OPENAI_API_KEY"
PLOT_AGENT_DEBUG_ENV_VAR = "PLOT_AGENT_DEBUG"

# Required Variables for Code Execution
REQUIRED_EXECUTION_VARIABLES = ["fig", "plot_title", "plot_summary"]

# Error Messages
MISSING_API_KEY_ERROR = "OPENAI_API_KEY is not set. Provide it via environment or a .env file."
MISSING_DF_ERROR = "No dataframe has been set. Please set a dataframe first."
EMPTY_DF_ERROR = "The dataframe must not be empty."
INVALID_DF_TYPE_ERROR = "The dataframe must be a pandas dataframe."
INVALID_SQL_TYPE_ERROR = "The SQL query must be a string."
INVALID_MESSAGE_TYPE_ERROR = "The user message must be a string."
INVALID_CODE_TYPE_ERROR = "The generated code must be a string."

# Tool Names
TOOL_EXECUTE_PLOTLY_CODE = "execute_plotly_code"
TOOL_DOES_FIG_EXIST = "does_fig_exist"
TOOL_VIEW_GENERATED_CODE = "view_generated_code"
TOOL_CHECK_PLOT_OUTPUTS = "check_plot_outputs"

# Tool Descriptions
TOOL_DESCRIPTIONS = {
    TOOL_EXECUTE_PLOTLY_CODE: (
        "Execute the provided Plotly code and return a result indicating "
        "if the code executed successfully and if a figure object was created."
    ),
    TOOL_DOES_FIG_EXIST: (
        "Check if a figure exists and is available for display. "
        "This tool takes no arguments and returns a string indicating "
        "if a figure is available for display or not."
    ),
    TOOL_VIEW_GENERATED_CODE: (
        "View the generated code. "
        "This tool takes no arguments and returns the generated code as a string."
    ),
    TOOL_CHECK_PLOT_OUTPUTS: (
        "Check if all required plot outputs (fig, plot_title, plot_summary) are available. "
        "This tool takes no arguments and returns the status of all plot outputs."
    ),
}

# Response Messages
EMPTY_MESSAGE_RESPONSE = "Please provide a non-empty plotting request (e.g., 'scatter x vs y')."
CODE_ONLY_MESSAGE_RESPONSE = "I see a code snippet. Please describe the visualization you want (e.g., 'line chart of y over x')."
NO_DF_SET_RESPONSE = "Please set a dataframe first using set_df() method."
FIG_AVAILABLE_RESPONSE = "A figure is available for display."
NO_FIG_RESPONSE = "No figure has been created yet."
ALL_OUTPUTS_AVAILABLE_RESPONSE = "All required plot outputs are available: fig, plot_title, and plot_summary."

# Code Execution Messages
CODE_EXECUTION_SUCCESS_PREFIX = "Success: "
CODE_EXECUTION_ERROR_PREFIX = "Error: "
CODE_EXECUTION_SUCCESS_MESSAGE = "Code executed successfully. 'fig', 'plot_title', and 'plot_summary' objects were created."

# Validation Error Messages
MISSING_VARIABLES_ERROR = "Missing required variables: {missing_vars}. Please create variables named: {missing_vars}."
PLOT_TITLE_TYPE_ERROR = "plot_title must be a string"
PLOT_SUMMARY_TYPE_ERROR = "plot_summary must be a string"
VALIDATION_ERRORS_PREFIX = "Validation errors: "

# Import Error Messages
POSTHOG_IMPORT_ERROR = (
    "PostHog integration requires the optional 'posthog' package. Install it with `pip install posthog`."
)

# Timeout Error Messages
TIMEOUT_ERROR_MESSAGE = "Code execution timed out"
CODE_REJECTED_ERROR_PREFIX = "Code rejected on safety grounds: "
CODE_EXECUTION_ERROR_PREFIX = "Error executing code: "

# Guided Retry Messages
GUIDED_RETRY_MESSAGE = (
    "Please use the execute_plotly_code(generated_code) tool with the FULL code to "
    "create a variable named 'fig', then call does_fig_exist(). Return the final "
    "code in a fenced ```python block."
)

# Logging Configuration
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%H:%M:%S"
