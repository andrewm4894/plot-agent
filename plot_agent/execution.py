"""
This module contains the PlotAgentExecutionEnvironment class, which is used to safely execute LLM‑generated plotting code and capture `fig`.

Security features:
  • Only allow imports from a fixed list of packages (pandas, numpy,
    matplotlib, plotly, sklearn)
  • AST scan rejects any import outside that list and any __dunder__ access
  • Sandbox builtins to include only a minimal safe set + our _safe_import
  • Enforce a 60 second timeout via signal.alarm
"""
import ast
import base64
import builtins
import logging
import signal
import threading
import traceback
from io import StringIO
import contextlib
from typing import Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _timeout_handler(signum, frame):
    raise TimeoutError("Code execution timed out")


# List of allowed modules
_ALLOWED_MODULES = {
    "pandas",
    "numpy",
    "matplotlib",
    "plotly",
    "sklearn",
    "scipy",
}


# Wrap the real __import__ so only our allowlist can get in
_orig_import = builtins.__import__


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    """
    Wrap the real __import__ so only our allowlist can get in
    """
    root = name.split(".", 1)[0]
    if root in _ALLOWED_MODULES:
        return _orig_import(name, globals, locals, fromlist, level)
    # If the module is not in the allowlist, raise an ImportError
    raise ImportError(f"Import of module '{name}' is not allowed.")


class PlotAgentExecutionEnvironment:
    """
    Environment to safely execute LLM‑generated plotting code and capture `fig`.

    Security features:
      • Only allow imports from a fixed list of packages (pandas, numpy,
        matplotlib, plotly, sklearn)
      • AST scan rejects any import outside that list and any __dunder__ access
      • Sandbox builtins to include only a minimal safe set + our _safe_import
      • Enforce a 60 second timeout via signal.alarm
      • Capture both stdout & stderr
      • Purge any old `fig` between runs
    """

    TIMEOUT_SECONDS = 60

    # A lean set of builtins, plus our safe-import hook
    _SAFE_BUILTINS = {
        "abs": abs,
        "all": all,
        "any": any,
        "bin": bin,
        "bool": bool,
        "chr": chr,
        "dict": dict,
        "divmod": divmod,
        "enumerate": enumerate,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "pow": pow,
        "print": print,
        "range": range,
        "reversed": reversed,
        "round": round,
        "set": set,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        # basic exceptions so user code can raise/catch
        "BaseException": BaseException,
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "NameError": NameError,
        "IndexError": IndexError,
        "KeyError": KeyError,
        # our import guard
        "__import__": _safe_import,
    }

    def __init__(self, df: pd.DataFrame, include_plot_image: bool = False):
        """
        Initialize the execution environment with a dataframe.

        Args:
            df: The pandas dataframe to use for plotting.
            include_plot_image: If True, generate a PNG image of the plot after execution.
        """
        self.df = df
        self.include_plot_image = include_plot_image
        self._logger = logging.getLogger("plot_agent.execution")
        # Base namespace for both globals & locals
        self._base_ns = {
            "__builtins__": self._SAFE_BUILTINS,
            "df": df,
            "pd": pd,
            "np": np,
            "plt": plt,
            "px": px,
            "go": go,
            "make_subplots": make_subplots,
        }
        self.fig = None
        self.plot_title = None
        self.plot_summary = None
        self.plot_image_base64 = None

    def _generate_plot_png(self, fig, width: int = 800, height: int = 600) -> Optional[str]:
        """
        Generate PNG as base64 data URI from a Plotly figure.

        Args:
            fig: The Plotly figure to convert.
            width: Image width in pixels.
            height: Image height in pixels.

        Returns:
            Base64-encoded data URI string, or None if generation fails.
        """
        try:
            import plotly.io as pio
            img_bytes = pio.to_image(fig, format='png', width=width, height=height)
            b64 = base64.b64encode(img_bytes).decode('utf-8')
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            self._logger.warning(f"Failed to generate plot PNG: {e}")
            return None

    def _validate_ast(self, node: ast.AST):
        """
        Walk the AST and enforce:
         • any Import/ImportFrom must be from _ALLOWED_MODULES
         • no __dunder__ attribute access
        """
        # Walk the AST and enforce:
        for child in ast.walk(node):
            # Check for imports
            if isinstance(child, ast.Import):
                # Check for imports
                for alias in child.names:
                    root = alias.name.split(".", 1)[0]
                    # Check if the module is in the allowlist
                    if root not in _ALLOWED_MODULES:
                        raise ValueError(f"Import of '{alias.name}' is not allowed.")
            # Check for import-froms
            elif isinstance(child, ast.ImportFrom):
                root = (child.module or "").split(".", 1)[0]
                if root not in _ALLOWED_MODULES:
                    raise ValueError(f"Import-from of '{child.module}' is not allowed.")
            # Check for dunder attribute access
            elif isinstance(child, ast.Attribute) and child.attr.startswith("__"):
                raise ValueError("Access to dunder attributes is forbidden.")

    def execute_code(self, generated_code: str):
        """
        Execute the user code in a locked‑down sandbox.

        Returns a dict with:
          - fig: The figure if created, else None
          - output: Captured stdout
          - error: Captured stderr or exception text
          - success: True if fig was produced and no errors
        """

        # Copy the base namespace
        ns = self._base_ns.copy()
        # Purge any old variables
        ns.pop("fig", None)
        ns.pop("plot_title", None)
        ns.pop("plot_summary", None)

        try:
            # Parse the generated code
            tree = ast.parse(generated_code)
            # Validate the AST
            self._validate_ast(tree)
        except Exception as e:
            # If the code is rejected on safety grounds, return an error
            return {
                "fig": None,
                "plot_title": None,
                "plot_summary": None,
                "output": "",
                "error": f"Code rejected on safety grounds: {e}",
                "success": False,
            }

        # Set a timeout only if running on the main thread; signals are not supported in worker threads
        timeout_set = False
        try:
            if threading.current_thread() is threading.main_thread():
                signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(self.TIMEOUT_SECONDS)
                timeout_set = True
        except Exception:
            # If setting the signal handler fails (e.g., not in main thread), proceed without timeout
            timeout_set = False

        # Execute the code
        out_buf, err_buf = StringIO(), StringIO()
        try:
            # Redirect stdout and stderr
            with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(
                err_buf
            ):
                # Execute the code
                exec(generated_code, ns, ns)
        except TimeoutError as te:
            # If the code execution timed out, return an error
            tb = traceback.format_exc()
            return {
                "fig": None,
                "plot_title": None,
                "plot_summary": None,
                "output": out_buf.getvalue(),
                "error": f"Code execution timed out: {te}\n{tb}",
                "success": False,
            }
        except Exception as e:
            # If there was an error, return an error
            tb = traceback.format_exc()
            return {
                "fig": None,
                "plot_title": None,
                "plot_summary": None,
                "output": out_buf.getvalue(),
                "error": f"Error executing code: {e}\n{tb}",
                "success": False,
            }
        finally:
            # Reset the timeout if it was set
            if timeout_set:
                try:
                    signal.alarm(0)
                except Exception:
                    pass

        # Get the variables
        fig = ns.get("fig")
        plot_title = ns.get("plot_title")
        plot_summary = ns.get("plot_summary")

        # Store the variables
        self.fig = fig
        self.plot_title = plot_title
        self.plot_summary = plot_summary

        # Generate PNG if enabled and figure exists
        self.plot_image_base64 = None
        if self.include_plot_image and fig is not None:
            self.plot_image_base64 = self._generate_plot_png(fig)

        # Validate required variables
        missing_vars = []
        if fig is None:
            missing_vars.append("fig")
        if plot_title is None:
            missing_vars.append("plot_title")
        if plot_summary is None:
            missing_vars.append("plot_summary")
        
        if missing_vars:
            return {
                "fig": fig,
                "plot_title": plot_title,
                "plot_summary": plot_summary,
                "output": out_buf.getvalue(),
                "error": f"Missing required variables: {', '.join(missing_vars)}. Please create variables named: {', '.join(missing_vars)}.",
                "success": False,
            }
        
        # Validate that plot_title and plot_summary are strings
        validation_errors = []
        if not isinstance(plot_title, str):
            validation_errors.append("plot_title must be a string")
        if not isinstance(plot_summary, str):
            validation_errors.append("plot_summary must be a string")
        
        if validation_errors:
            return {
                "fig": fig,
                "plot_title": plot_title,
                "plot_summary": plot_summary,
                "output": out_buf.getvalue(),
                "error": f"Validation errors: {'; '.join(validation_errors)}.",
                "success": False,
            }

        # Return the result
        return {
            "fig": fig,
            "plot_title": plot_title,
            "plot_summary": plot_summary,
            "plot_image_base64": self.plot_image_base64,
            "output": "Code executed successfully. 'fig', 'plot_title', and 'plot_summary' objects were created.",
            "error": "",
            "success": True,
        }
