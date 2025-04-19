import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import StringIO
import traceback
import sys
import re
from typing import Dict, List, Optional, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI


DEFAULT_SYSTEM_PROMPT = """
You are an expert data visualization assistant that helps users create Plotly visualizations in Python.
Your job is to generate Python and Plotly code based on the user's request that will create the desired visualization
of their pandas DataFrame (df).

You have access to a pandas df with the following information:

df.info():
```plaintext
{df_info}
```

df.head():
```plaintext
{df_head}
```

{sql_context}

NOTES:
- You must use the execute_plotly_code(generated_code) tool to test and run your code
- You must paste the full code, not just a reference to the code
- You must not use fig.show() in your code as it will be executed in a headless environment
- If you need to do any data cleaning or wrangling, do it in the code before generating the plotly code as preprocessing steps assume the data is in the pandas df object
- Do not use fig.show() in your code as it will be executed in a headless environment.

IMPORTANT CODE FORMATTING INSTRUCTIONS:
1. Include thorough, detailed comments in your code to explain what each section does
2. Use descriptive variable names
3. DO NOT include fig.show() in your code - the visualization will be rendered externally
4. Ensure your code creates a variable named 'fig' that contains the Plotly figure object
5. Structure your code with proper spacing for readability

When a user asks for a visualization:
1. YOU MUST ALWAYS use the execute_plotly_code(generated_code) tool to test and run your code
2. If there are errors, fix the code and run it again with execute_plotly_code(generated_code)
3. Check that a figure object is available using does_fig_exist(). does_fig_exist() takes no arguments.

IMPORTANT: The code you generate MUST be executed using the execute_plotly_code tool or no figure will be created!
YOU MUST CALL execute_plotly_code WITH THE FULL CODE, NOT JUST A REFERENCE TO THE CODE.

YOUR WORKFLOW MUST BE:
1. execute_plotly_code(generated_code) → 2. check that a figure object is available using does_fig_exist() → 3. (if needed) fix and execute again

Always return the final working code (with all the comments) to the user along with an explanation of what the visualization shows.
Make sure to follow best practices for data visualization, such as appropriate chart types, labels, and colors.

Remember that users may want to iterate on their visualizations, so be responsive to requests for changes.
"""


# Define input schemas for the tools
class PlotDescriptionInput(BaseModel):
    plot_description: str = Field(
        ..., description="Description of the plot the user wants to create"
    )


class GeneratedCodeInput(BaseModel):
    generated_code: str = Field(
        ..., description="Python code that creates a Plotly figure"
    )


class PlotlyAgentExecutionEnvironment:
    """Environment to safely execute plotly code and capture the fig object."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.locals_dict = {
            "df": df,
            "px": px,
            "go": go,
            "pd": pd,
            "np": np,
            "plt": plt,
            "make_subplots": make_subplots,
        }
        self.output = None
        self.error = None
        self.fig = None

    def preprocess_code(self, generated_code: str) -> str:
        """Preprocess code to remove fig.show() calls."""
        # Remove fig.show() calls
        generated_code = re.sub(r"fig\.show\(\s*\)", "", generated_code)
        generated_code = re.sub(r"fig\.show\(.*\)", "", generated_code)
        return generated_code

    def execute_code(self, generated_code: str) -> Dict[str, Any]:
        """
        Execute the provided code and capture the fig object if created.

        Args:
            generated_code (str): The code to execute.

        Returns:
            Dict[str, Any]: A dictionary containing the fig object, output, error, and success status.
        """
        self.output = None
        self.error = None

        # Preprocess code to remove fig.show() calls
        processed_code = self.preprocess_code(generated_code)

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        try:
            # Execute the code
            exec(processed_code, globals(), self.locals_dict)

            # Check if a fig object was created
            if "fig" in self.locals_dict:
                self.fig = self.locals_dict["fig"]
                self.output = "Code executed successfully. Figure object was created."
            else:
                print(f"no fig object created: {processed_code}")
                self.error = "Code executed without errors, but no 'fig' object was created. Make sure your code creates a variable named 'fig'."

        except Exception as e:
            self.error = f"Error executing code: {str(e)}\n{traceback.format_exc()}"

        finally:
            # Restore stdout
            sys.stdout = old_stdout
            captured_output = mystdout.getvalue()

            if captured_output.strip():
                if self.output:
                    self.output += f"\nOutput:\n{captured_output}"
                else:
                    self.output = f"Output:\n{captured_output}"

        return {
            "fig": self.fig,
            "output": self.output,
            "error": self.error,
            "success": self.error is None and self.fig is not None,
        }


class PlotlyAgent:
    """
    A class that uses an LLM to generate Plotly code based on a user's plot description.
    """

    def __init__(self, model="gpt-4o-mini", system_prompt: Optional[str] = None):
        """
        Initialize the PlotlyAgent.

        Args:
            model (str): The model to use for the LLM.
            system_prompt (Optional[str]): The system prompt to use for the LLM.
        """
        self.llm = ChatOpenAI(model=model)
        self.df = None
        self.df_info = None
        self.df_head = None
        self.sql_query = None
        self.execution_env = None
        self.chat_history = []
        self.agent_executor = None
        self.generated_code = None
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    def set_df(self, df: pd.DataFrame, sql_query: Optional[str] = None):
        """
        Set the dataframe and capture its schema and sample.

        Args:
            df (pd.DataFrame): The pandas dataframe to set.
            sql_query (Optional[str]): The SQL query used to generate the dataframe.

        Returns:
            None
        """
        self.df = df

        # Capture df.info() output
        buffer = StringIO()
        df.info(buf=buffer)
        self.df_info = buffer.getvalue()

        # Capture df.head() as string representation
        self.df_head = df.head().to_string()

        # Store SQL query if provided
        self.sql_query = sql_query

        # Initialize execution environment
        self.execution_env = PlotlyAgentExecutionEnvironment(df)

        # Initialize the agent with tools
        self._initialize_agent()

    def execute_plotly_code(self, generated_code: str) -> str:
        """
        Execute the provided Plotly code and return the result.

        Args:
            generated_code (str): The Plotly code to execute.

        Returns:
            str: The result of the execution.
        """
        if not self.execution_env:
            return "Error: No dataframe has been set. Please set a dataframe first."

        # Store this as the last generated code
        self.generated_code = generated_code

        result = self.execution_env.execute_code(generated_code)

        if result["success"]:
            return f"Code executed successfully! A figure object was created.\n{result.get('output', '')}"
        else:
            return f"Error: {result.get('error', 'Unknown error')}\n{result.get('output', '')}"

    def does_fig_exist(self, *args, **kwargs) -> str:
        """
        Check if a figure object is available for display.

        Args:
            *args: Any positional arguments (ignored)
            **kwargs: Any keyword arguments (ignored)

        Returns:
            str: A message indicating whether a figure is available for display.
        """
        if not self.execution_env:
            return "No execution environment has been initialized. Please set a dataframe first."

        if self.execution_env.fig is not None:
            return "A figure is available for display."
        else:
            return "No figure has been created yet."

    def _initialize_agent(self):
        """Initialize the LangChain agent with the necessary tools and prompt."""
        tools = [
            Tool.from_function(
                func=self.execute_plotly_code,
                name="execute_plotly_code",
                description="Execute the provided Plotly code and return the result",
                args_schema=GeneratedCodeInput,
            ),
            Tool.from_function(
                func=self.does_fig_exist,
                name="does_fig_exist",
                description="Check if a figure exists and is available for display",
                args_schema=None,
            ),
        ]

        # Create system prompt with dataframe information
        sql_context = ""
        if self.sql_query:
            sql_context = f"In case it is useful to help with the data understanding, the df was generated using the following SQL query:\n```sql\n{self.sql_query}\n```"

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.system_prompt.format(
                        df_info=self.df_info,
                        df_head=self.df_head,
                        sql_context=sql_context,
                    ),
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_openai_tools_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            early_stopping_method="force",
            handle_parsing_errors=True,
        )

    def process_message(self, user_message: str) -> str:
        """Process a user message and return the agent's response."""
        if not self.agent_executor:
            return "Please set a dataframe first using set_df() method."

        # Add user message to chat history
        self.chat_history.append(HumanMessage(content=user_message))

        # Reset generated_code
        self.generated_code = None

        # Get response from agent
        response = self.agent_executor.invoke(
            {"input": user_message, "chat_history": self.chat_history}
        )

        # Add agent response to chat history
        self.chat_history.append(AIMessage(content=response["output"]))

        # If the agent didn't execute the code, but did generate code, execute it directly
        if self.execution_env.fig is None and self.generated_code is not None:
            self.execution_env.execute_code(self.generated_code)

        # If we can extract code from the response when no code was executed, try that too
        if self.execution_env.fig is None and "```python" in response["output"]:
            code_blocks = response["output"].split("```python")
            if len(code_blocks) > 1:
                generated_code = code_blocks[1].split("```")[0].strip()
                self.execution_env.execute_code(generated_code)

        # Return the agent's response
        return response["output"]

    def get_figure(self):
        """Return the current figure if one exists."""
        if self.execution_env and self.execution_env.fig:
            return self.execution_env.fig
        return None

    def reset_conversation(self):
        """Reset the conversation history."""
        self.chat_history = []
