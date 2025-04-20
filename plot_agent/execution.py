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
import builtins
import signal
import traceback
from io import StringIO
import contextlib

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

    def __init__(self, df: pd.DataFrame):
        """
        Initialize the execution environment with a dataframe.
        """
        self.df = df
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
        # Purge any old `fig`
        ns.pop("fig", None)

        try:
            # Parse the generated code
            tree = ast.parse(generated_code)
            # Validate the AST
            self._validate_ast(tree)
        except Exception as e:
            # If the code is rejected on safety grounds, return an error
            return {
                "fig": None,
                "output": "",
                "error": f"Code rejected on safety grounds: {e}",
                "success": False,
            }

        # Set a timeout
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(self.TIMEOUT_SECONDS)

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
                "output": out_buf.getvalue(),
                "error": f"Code execution timed out: {te}\n{tb}",
                "success": False,
            }
        except Exception as e:
            # If there was an error, return an error
            tb = traceback.format_exc()
            return {
                "fig": None,
                "output": out_buf.getvalue(),
                "error": f"Error executing code: {e}\n{tb}",
                "success": False,
            }
        finally:
            # Reset the timeout
            signal.alarm(0)

        # Get the `fig`
        fig = ns.get("fig")
        self.fig = fig
        if fig is None:
            return {
                "fig": None,
                "output": out_buf.getvalue(),
                "error": "No `fig` created. Assign your figure to a variable named `fig`.",
                "success": False,
            }

        # Return the result
        return {
            "fig": fig,
            "output": "Code executed successfully. 'fig' object was created.",
            "error": "",
            "success": True,
        }
