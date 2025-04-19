import sys
from io import StringIO
import traceback
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
from typing import Dict, Any


class PlotAgentExecutionEnvironment:
    """
    Environment to safely execute plotly code and capture the fig object.

    Args:
        df (pd.DataFrame): The dataframe to use for the execution environment.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize the execution environment with the given dataframe.

        Args:
            df (pd.DataFrame): The dataframe to use for the execution environment.
        """
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

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        try:
            # Execute the code
            exec(generated_code, globals(), self.locals_dict)

            # Check if a fig object was created
            if "fig" in self.locals_dict:
                self.fig = self.locals_dict["fig"]
                self.output = "Code executed successfully. 'fig' object was created."
            else:
                print(f"no fig object created: {generated_code}")
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
